#!/usr/bin/env python3
"""Self-service, multi-version package hub for AI Skills, CLIs, and Agents."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import getpass
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import defaultdict, deque
from pathlib import Path

from ai_assets import ASSET_ID, ROOT, satisfies, version_tuple

REGISTRY = ROOT / "registry.json"
SUBMISSIONS = ROOT / "submissions"


def default_install_root() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    return Path(base) / "AIAssetHub" / "installed" if base else Path.home() / ".ai-asset-hub" / "installed"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False, dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json_exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(content)


@contextlib.contextmanager
def repository_lock(repository: Path, timeout: float = 10.0):
    """Serialize registry writes across SMB clients using exclusive file creation."""
    lock_path = repository / ".registry.lock"
    deadline = time.monotonic() + timeout
    payload = json.dumps({"host": socket.gethostname(), "pid": os.getpid(), "time": time.time()})
    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise ValueError(f"仓库正在被其他维护者更新；锁文件为 {lock_path}")
            time.sleep(0.2)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def package_map(registry: dict) -> dict[str, dict]:
    return {package["id"]: package for package in registry.get("packages", [])}


def release_map(package: dict) -> dict[str, dict]:
    return {release["version"]: release for release in package.get("releases", [])}


def validate_release(asset_id: str, release: dict) -> list[str]:
    errors: list[str] = []
    try:
        version_tuple(release.get("version", ""))
    except ValueError as exc:
        errors.append(str(exc))
    if release.get("channel") not in {"stable", "preview", "deprecated"}:
        errors.append("channel 必须为 stable、preview 或 deprecated")
    artifact = release.get("artifact", {})
    if artifact.get("type") not in {"repository", "local", "url"}:
        errors.append("artifact.type 必须为 repository 或 url")
    if not artifact.get("location"):
        errors.append("artifact.location 不能为空")
    digest = artifact.get("sha256", "")
    if len(digest) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in digest):
        errors.append("artifact.sha256 必须是 64 位十六进制值")
    for dep in release.get("dependencies", []):
        if not ASSET_ID.fullmatch(dep.get("id", "")):
            errors.append(f"依赖 ID 无效: {dep.get('id')}")
        try:
            # Exercise the constraint parser with an arbitrary version.
            satisfies("0.0.0", dep.get("version", ""))
        except ValueError as exc:
            errors.append(f"{asset_id} -> {dep.get('id')}: {exc}")
    return errors


def validation_errors(registry: dict) -> list[str]:
    errors: list[str] = []
    if registry.get("registryVersion") != 1:
        errors.append("registryVersion 必须为 1")
    seen: set[str] = set()
    packages = package_map(registry)
    for package in registry.get("packages", []):
        asset_id = package.get("id", "")
        if not ASSET_ID.fullmatch(asset_id):
            errors.append(f"资产 ID 无效: {asset_id}")
        if asset_id in seen:
            errors.append(f"资产 ID 重复: {asset_id}")
        seen.add(asset_id)
        if not package.get("owner"):
            errors.append(f"{asset_id}: 缺少 owner")
        versions: set[str] = set()
        for release in package.get("releases", []):
            version = release.get("version", "")
            if version in versions:
                errors.append(f"{asset_id}: 版本重复 {version}")
            versions.add(version)
            errors.extend(f"{asset_id}@{version}: {item}" for item in validate_release(asset_id, release))
            for dep in release.get("dependencies", []):
                if dep.get("required", True) and dep.get("id") not in packages:
                    errors.append(f"{asset_id}@{version}: 缺少依赖包 {dep.get('id')}")
    return errors


def load_registry_with_fallback(primary: Path, backup: Path | None = None) -> tuple[dict, Path]:
    failures: list[str] = []
    repositories = [primary] + ([backup] if backup and backup != primary else [])
    for repository in repositories:
        try:
            registry = read_json(repository / "registry.json")
            errors = validation_errors(registry)
            if errors:
                failures.append(f"{repository}: {'；'.join(errors)}")
                continue
            if repository != primary:
                print(f"警告：公开仓库不可用，已切换到备份仓库 {repository}", file=sys.stderr)
            return registry, repository
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{repository}: {exc}")
    raise ValueError("所有仓库均不可用：" + "；".join(failures))


def current_principal() -> str:
    explicit = os.environ.get("AI_ASSET_ACTOR", "").strip()
    if explicit:
        return explicit
    domain = os.environ.get("USERDOMAIN", "").strip()
    username = os.environ.get("USERNAME", "").strip() or getpass.getuser()
    return f"{domain}\\{username}" if domain else username


def native_smb_principal(repository: Path) -> str | None:
    """Read the account actually bound to a UNC resource using Windows MPR."""
    if os.name != "nt":
        return None
    parts = str(repository).lstrip("\\").split("\\")
    if len(parts) < 2:
        return None
    remote = rf"\\{parts[0]}\{parts[1]}"
    try:
        import ctypes
        from ctypes import wintypes

        function = ctypes.windll.mpr.WNetGetUserW
        function.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        function.restype = wintypes.DWORD
        length = wintypes.DWORD(256)
        buffer = ctypes.create_unicode_buffer(length.value)
        result = function(remote, buffer, ctypes.byref(length))
        if result == 234 and length.value > 256:
            buffer = ctypes.create_unicode_buffer(length.value)
            result = function(remote, buffer, ctypes.byref(length))
        return buffer.value.strip() if result == 0 and buffer.value.strip() else None
    except (AttributeError, OSError, ValueError):
        return None


def repository_principal(repository: Path, require_smb_identity: bool = False) -> str:
    raw = str(repository)
    if not raw.startswith("\\\\"):
        return current_principal()
    parts = raw.lstrip("\\").split("\\")
    if len(parts) < 2:
        return current_principal()
    server, share = parts[0], parts[1]
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "Get-SmbConnection | Select-Object ServerName,ShareName,UserName | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            connections = json.loads(result.stdout)
            if isinstance(connections, dict):
                connections = [connections]
            for connection in connections:
                if (
                    str(connection.get("ServerName", "")).casefold() == server.casefold()
                    and str(connection.get("ShareName", "")).casefold() == share.casefold()
                    and connection.get("UserName")
                ):
                    return str(connection["UserName"])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        pass
    principal = native_smb_principal(repository)
    if principal:
        return principal
    if require_smb_identity:
        raise ValueError(
            "无法从 Windows SMB 会话确认实际登录账户，拒绝执行特权操作"
        )
    return current_principal()


def authorize(repository: Path, action: str, principal: str | None = None) -> str:
    principal = principal or current_principal()
    roles_path = repository / "config" / "roles.json"
    if not roles_path.exists():
        if action in {"asset.list", "asset.install", "asset.activate", "candidate.submit"}:
            return "user"
        raise ValueError(f"缺少角色配置，拒绝特权操作: {roles_path}")
    policy = read_json(roles_path)
    normalized = principal.casefold()
    selected_role = policy.get("defaultRole", "user")
    for role, definition in policy.get("roles", {}).items():
        accounts = {str(account).casefold() for account in definition.get("accounts", [])}
        if normalized in accounts:
            selected_role = role
            break
    definition = policy.get("roles", {}).get(selected_role, {})
    if action not in definition.get("actions", []):
        raise ValueError(f"当前 SMB 角色 {selected_role} 无权执行 {action}")
    return selected_role


def command_accounts(
    repository: Path,
    operation: str,
    account: str | None = None,
    role: str | None = None,
) -> int:
    roles_path = repository / "config" / "roles.json"
    with repository_lock(repository):
        policy = read_json(roles_path)
        roles = policy.get("roles", {})
        if operation == "list":
            for role_name, definition in roles.items():
                accounts = definition.get("accounts", [])
                rendered = ", ".join(accounts) if accounts else "（未分配）"
                print(f"{role_name}: {rendered}")
            return 0
        if not account:
            raise ValueError("assign/remove 必须指定 --account")
        normalized = account.casefold()
        previous_roles: list[str] = []
        for role_name, definition in roles.items():
            existing = definition.setdefault("accounts", [])
            if any(str(item).casefold() == normalized for item in existing):
                previous_roles.append(role_name)
                definition["accounts"] = [
                    item for item in existing if str(item).casefold() != normalized
                ]
        if operation == "assign":
            if role not in roles:
                raise ValueError(f"未知角色: {role}")
            roles[role].setdefault("accounts", []).append(account)
            roles[role]["accounts"].sort(key=str.casefold)
            result = f"已把 {account} 分配为 {role}"
        elif operation == "remove":
            if not previous_roles:
                raise ValueError(f"账户未被显式分配: {account}")
            result = f"已移除 {account} 的角色分配；该账户将使用默认 user 角色"
        else:
            raise ValueError(f"未知账户操作: {operation}")
        if not roles.get("administrator", {}).get("accounts"):
            raise ValueError("操作会移除最后一个管理员，已拒绝")
        write_json(roles_path, policy)
    print(result)
    return 0


def choose_release(package: dict, constraints: list[str], channel: str) -> dict | None:
    allowed_channels = {
        "stable": {"stable"},
        "preview": {"stable", "preview"},
        "deprecated": {"deprecated"},
        "any": {"stable", "preview", "deprecated"},
    }[channel]
    candidates = [
        release for release in package.get("releases", [])
        if release.get("channel") in allowed_channels
        and all(satisfies(release["version"], constraint) for constraint in constraints)
    ]
    return max(candidates, key=lambda item: version_tuple(item["version"]), default=None)


def resolve(registry: dict, root_id: str, root_constraint: str, channel: str) -> tuple[dict[str, dict], list[str]]:
    packages = package_map(registry)
    if root_id not in packages:
        raise ValueError(f"仓库中不存在 {root_id}")
    selected: dict[str, dict] = {}
    seen_states: set[tuple[tuple[str, str], ...]] = set()

    # Rebuild constraints from the latest selection each round. This prevents
    # dependencies belonging to a previously selected release from becoming stale.
    for _ in range(sum(len(p.get("releases", [])) for p in packages.values()) * 2 + len(packages) + 2):
        constraints: dict[str, list[str]] = defaultdict(list)
        constraints[root_id].append(root_constraint)
        for release in selected.values():
            for dep in release.get("dependencies", []):
                if dep.get("required", True) and dep["version"] not in constraints[dep["id"]]:
                    constraints[dep["id"]].append(dep["version"])

        next_selected: dict[str, dict] = {}
        for asset_id in sorted(constraints):
            if asset_id not in packages:
                raise ValueError(f"仓库中缺少依赖包 {asset_id}")
            release = choose_release(packages[asset_id], constraints[asset_id], channel)
            if release is None:
                joined = " 且 ".join(constraints[asset_id])
                raise ValueError(f"{asset_id} 没有满足 {joined}（channel={channel}）的版本")
            next_selected[asset_id] = release
        state = tuple(sorted((item, release["version"]) for item, release in next_selected.items()))
        if state == tuple(sorted((item, release["version"]) for item, release in selected.items())):
            selected = next_selected
            break
        if state in seen_states:
            raise ValueError("依赖版本选择发生振荡，请收紧或调整依赖约束")
        seen_states.add(state)
        selected = next_selected
    else:
        raise ValueError("依赖解析未能收敛，请检查版本间的依赖变化")

    indegree = {asset_id: 0 for asset_id in selected}
    consumers: dict[str, list[str]] = defaultdict(list)
    for asset_id, release in selected.items():
        for dep in release.get("dependencies", []):
            if dep.get("required", True) and dep["id"] in selected:
                indegree[asset_id] += 1
                consumers[dep["id"]].append(asset_id)
    queue = deque(sorted(item for item, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        item = queue.popleft()
        order.append(item)
        for consumer in sorted(consumers[item]):
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                queue.append(consumer)
    if len(order) != len(selected):
        raise ValueError("所选版本形成循环依赖")
    return selected, order


def parse_spec(spec: str) -> tuple[str, str]:
    if "@" in spec:
        asset_id, version = spec.rsplit("@", 1)
        version_tuple(version)
        return asset_id, version
    return spec, ">=0.0.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def acquire(artifact: dict, destination: Path, repository: Path) -> None:
    source_type = artifact["type"]
    location = artifact["location"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=destination.parent) as handle:
        temporary = Path(handle.name)
    try:
        if source_type in {"repository", "local"}:
            source = (repository / location).resolve()
            repository_resolved = repository.resolve()
            if source != repository_resolved and repository_resolved not in source.parents:
                raise ValueError(f"SMB 制品必须位于公共仓库内: {location}")
            shutil.copyfile(source, temporary)
        else:
            with urllib.request.urlopen(location, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        actual = sha256(temporary)
        expected = artifact["sha256"].lower()
        if actual != expected:
            raise ValueError(f"制品校验失败: 期望 {expected}，实际 {actual}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def command_install(
    registry: dict, spec: str, root: Path, channel: str, activate: bool, repository: Path
) -> int:
    asset_id, constraint = parse_spec(spec)
    selected, order = resolve(registry, asset_id, constraint, channel)
    print("解析结果（依赖优先）:")
    for item in order:
        print(f"- {item}@{selected[item]['version']}")
    for item in order:
        release = selected[item]
        package_dir = root / item / release["version"]
        artifact_path = package_dir / "artifact"
        metadata_path = package_dir / "release.json"
        if artifact_path.exists() and sha256(artifact_path) == release["artifact"]["sha256"].lower():
            print(f"已存在: {item}@{release['version']}")
        else:
            acquire(release["artifact"], artifact_path, repository)
            write_json(metadata_path, release)
            print(f"已下载: {item}@{release['version']}")
        if activate:
            write_json(root / item / "current.json", {"version": release["version"]})
    if activate:
        print("已激活本次解析出的全部版本。")
    return 0


def command_activate(registry: dict, spec: str, root: Path) -> int:
    asset_id, version = parse_spec(spec)
    if version.startswith(">"):
        raise ValueError("activate 必须指定精确版本，例如 skill/code-review@1.1.0")
    release = release_map(package_map(registry).get(asset_id, {})).get(version)
    if release is None:
        raise ValueError(f"仓库中不存在 {asset_id}@{version}")
    artifact = root / asset_id / version / "artifact"
    if not artifact.exists():
        raise ValueError(f"尚未安装 {asset_id}@{version}")
    write_json(root / asset_id / "current.json", {"version": version})
    print(f"已激活 {asset_id}@{version}")
    return 0


def command_submit(manifest_path: Path, repository: Path, artifact_path: Path | None = None) -> int:
    manifest = read_json(manifest_path)
    asset_id = manifest.get("id", "")
    if not ASSET_ID.fullmatch(asset_id) or not manifest.get("owner"):
        raise ValueError("提交必须包含有效 id 和 owner")
    release = manifest.get("release", {})
    if not str(release.get("releaseNotes", "")).strip():
        raise ValueError("候选版本缺少更新说明；请由智能体根据差异生成，或请用户输入")
    filename = f"{asset_id.replace('/', '__')}@{release.get('version', 'invalid')}.json"
    destination = repository / "submissions" / filename
    if destination.exists():
        raise ValueError(f"候选提交已存在: {destination.name}")
    if artifact_path is not None:
        if not artifact_path.is_file():
            raise ValueError(f"制品文件不存在: {artifact_path}")
        kind, name = asset_id.split("/", 1)
        relative = Path("submissions") / "payloads" / kind / name / release.get("version", "invalid") / artifact_path.name
        payload_destination = repository / relative
        payload_destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with artifact_path.open("rb") as source, payload_destination.open("xb") as output:
                shutil.copyfileobj(source, output)
        except FileExistsError as exc:
            raise ValueError(f"候选制品已存在: {relative.as_posix()}") from exc
        release["artifact"] = {
            "type": "repository",
            "location": relative.as_posix(),
            "sha256": sha256(payload_destination),
        }
    errors = validate_release(asset_id, release)
    if errors:
        raise ValueError("；".join(errors))
    try:
        write_json_exclusive(destination, {**manifest, "status": "pending"})
    except FileExistsError as exc:
        raise ValueError(f"候选提交已存在: {destination.name}") from exc
    print(f"已提交候选版本: {destination}")
    print("下一步：由审核者执行 review，通过后由发布者执行 publish。")
    return 0


def command_review(
    submission_path: Path, decision: str, reviewer: str, note: str = ""
) -> int:
    manifest = read_json(submission_path)
    if manifest.get("status") != "pending":
        raise ValueError("只能审核 pending 状态的提交")
    if decision not in {"reviewed", "rejected"}:
        raise ValueError("审核决定必须为 reviewed 或 rejected")
    manifest["status"] = decision
    manifest["review"] = {
        "reviewer": reviewer,
        "reviewedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "note": note,
    }
    write_json(submission_path, manifest)
    print(f"审核完成：{submission_path.name} -> {decision}")
    return 0


def command_approve(
    repository: Path,
    submission_path: Path,
    source_repository: Path | None = None,
    publisher: str | None = None,
) -> int:
    source_repository = source_repository or repository
    with repository_lock(repository):
        # Reload after acquiring the SMB lock so concurrent approvals cannot overwrite each other.
        registry_path = repository / "registry.json"
        registry = read_json(registry_path)
        manifest = read_json(submission_path)
        if manifest.get("status") != "reviewed":
            raise ValueError("只能发布 reviewed 状态的提交；请先由审核者执行 review")
        asset_id = manifest["id"]
        release = manifest["release"]
        if not str(release.get("releaseNotes", "")).strip():
            raise ValueError("更新说明为空，拒绝发布")
        errors = validate_release(asset_id, release)
        if errors:
            raise ValueError("；".join(errors))
        packages = package_map(registry)
        if asset_id not in packages:
            package = {"id": asset_id, "owner": manifest["owner"], "releases": []}
            registry["packages"].append(package)
        else:
            package = packages[asset_id]
            if package["owner"] != manifest["owner"]:
                raise ValueError("提交 owner 与仓库登记 owner 不一致")
        if release["version"] in release_map(package):
            raise ValueError(f"版本已存在: {asset_id}@{release['version']}")
        artifact = release["artifact"]
        candidate_prefix = "submissions/payloads/"
        if artifact["type"] == "repository" and artifact["location"].replace("\\", "/").startswith(candidate_prefix):
            source = (source_repository / artifact["location"]).resolve()
            if not source.is_file() or sha256(source) != artifact["sha256"].lower():
                raise ValueError("候选制品缺失或 SHA-256 不匹配")
            kind, name = asset_id.split("/", 1)
            relative = Path("artifacts") / kind / name / release["version"] / source.name
            final_artifact = repository / relative
            final_artifact.parent.mkdir(parents=True, exist_ok=True)
            if final_artifact.exists():
                if sha256(final_artifact) != artifact["sha256"].lower():
                    raise ValueError(f"正式制品路径已被不同内容占用: {relative.as_posix()}")
            else:
                with source.open("rb") as candidate, final_artifact.open("xb") as output:
                    shutil.copyfileobj(candidate, output)
            artifact["location"] = relative.as_posix()
        package["releases"].append(release)
        package["releases"].sort(key=lambda item: version_tuple(item["version"]))
        errors = validation_errors(registry)
        if errors:
            raise ValueError("批准后仓库校验失败：" + "；".join(errors))
        write_json(registry_path, registry)
        manifest["status"] = "published"
        manifest["publication"] = {
            "publisher": publisher or current_principal(),
            "publishedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        write_json(submission_path, manifest)
    print(f"已批准 {asset_id}@{release['version']} 并写入 {registry_path}")
    return 0


def command_mirror(authority: Path, public: Path) -> int:
    """Restore the public distribution share from the authoritative backup share."""
    if authority == public:
        raise ValueError("备份仓库和公开仓库不能是同一个地址")
    registry = read_json(authority / "registry.json")
    errors = validation_errors(registry)
    if errors:
        raise ValueError("备份仓库校验失败：" + "；".join(errors))
    restored = 0
    with repository_lock(public):
        for package in registry.get("packages", []):
            for release in package.get("releases", []):
                artifact = release.get("artifact", {})
                if artifact.get("type") not in {"repository", "local"}:
                    continue
                destination = public / artifact["location"]
                if destination.exists() and sha256(destination) == artifact["sha256"].lower():
                    continue
                acquire(artifact, destination, authority)
                restored += 1
        # Registry is written last, so clients never see an index before its artifacts exist.
        write_json(public / "registry.json", registry)
    print(f"镜像完成：从 {authority} 恢复 {restored} 个制品，并更新 {public / 'registry.json'}")
    return 0


def dashboard_path(repository: Path) -> Path:
    """Return <014-AI>/AI-Assets-Hub for the configured .../014-AI/data/AI-Assets path."""
    return repository.parent.parent / "AI-Assets-Hub"


def command_web_export(repository: Path, output: Path) -> int:
    registry, active_repository = load_registry_with_fallback(repository, None)
    packages = []
    dependency_count = 0
    release_count = 0
    for package in sorted(registry.get("packages", []), key=lambda item: item["id"]):
        releases = []
        for release in sorted(
            package.get("releases", []),
            key=lambda item: version_tuple(item["version"]),
            reverse=True,
        ):
            dependencies = release.get("dependencies", [])
            dependency_count += len(dependencies)
            release_count += 1
            releases.append({
                "version": release["version"],
                "channel": release["channel"],
                "releaseNotes": release.get("releaseNotes", "旧版本未登记更新说明"),
                "dependencies": dependencies,
            })
        packages.append({"id": package["id"], "owner": package.get("owner", ""), "releases": releases})
    statuses: dict[str, int] = defaultdict(int)
    submissions = active_repository / "submissions"
    if submissions.is_dir():
        for path in submissions.glob("*.json"):
            try:
                statuses[read_json(path).get("status", "unknown")] += 1
            except (OSError, json.JSONDecodeError):
                statuses["invalid"] += 1
    payload = {
        "registryVersion": registry["registryVersion"],
        "generation": registry.get("generation"),
        "issuedAt": registry.get("issuedAt"),
        "exportedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "counts": {
            "packages": len(packages),
            "releases": release_count,
            "dependencies": dependency_count,
        },
        "submissionStatuses": dict(sorted(statuses.items())),
        "packages": packages,
    }
    output.mkdir(parents=True, exist_ok=True)
    target = output / "hub-data.js"
    target.write_text(
        "window.AI_ASSETS_HUB_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    print(f"网页数据已更新: {target}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Skill/CLI 多版本仓库")
    parser.add_argument(
        "--repo", type=Path, default=Path(os.environ.get("AI_ASSET_REPO", ROOT)),
        help="SMB 公共仓库路径，例如 \\\\fileserver\\AI-Assets；也可设置 AI_ASSET_REPO",
    )
    parser.add_argument(
        "--backup-repo", type=Path,
        default=Path(os.environ["AI_ASSET_BACKUP_REPO"]) if os.environ.get("AI_ASSET_BACKUP_REPO") else None,
        help="SMB 备份/权威仓库路径；也可设置 AI_ASSET_BACKUP_REPO",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    releases = sub.add_parser("releases")
    releases.add_argument("asset_id", nargs="?")
    view = sub.add_parser("view", help="查看有权限使用者可拉取的正式资产和版本")
    view.add_argument("asset_id", nargs="?")
    install = sub.add_parser("install")
    install.add_argument("spec", help="例如 skill/code-review@1.1.0")
    install.add_argument("--channel", choices=["stable", "preview", "deprecated", "any"], default="stable")
    install.add_argument("--root", type=Path, default=default_install_root())
    install.add_argument("--activate", action="store_true")
    pull = sub.add_parser("pull", help="拉取指定正式版本并自动安装依赖")
    pull.add_argument("spec", help="例如 skill/code-review@1.1.0")
    pull.add_argument("--channel", choices=["stable", "preview", "deprecated", "any"], default="stable")
    pull.add_argument("--root", type=Path, default=default_install_root())
    pull.add_argument("--activate", action="store_true")
    activate = sub.add_parser("activate")
    activate.add_argument("spec")
    activate.add_argument("--root", type=Path, default=default_install_root())
    submit = sub.add_parser("submit")
    submit.add_argument("manifest", type=Path)
    submit.add_argument("--artifact", type=Path, help="同时上传的 Skill/CLI 制品文件")
    approve = sub.add_parser("approve")
    approve.add_argument("submission", type=Path)
    review = sub.add_parser("review", help="审核候选版本，不执行发布")
    review.add_argument("submission", type=Path)
    review.add_argument("--decision", choices=["reviewed", "rejected"], required=True)
    review.add_argument("--note", default="")
    publish = sub.add_parser("publish", help="把已审核候选发布到备份权威仓库")
    publish.add_argument("submission", type=Path)
    accounts = sub.add_parser("accounts", help="管理员分配和查看账户角色")
    account_sub = accounts.add_subparsers(dest="account_operation", required=True)
    account_sub.add_parser("list")
    assign = account_sub.add_parser("assign")
    assign.add_argument("--account", required=True, help="例如 DOMAIN\\username")
    assign.add_argument(
        "--role", required=True,
        choices=["administrator", "reviewer", "publisher", "user"],
    )
    remove = account_sub.add_parser("remove")
    remove.add_argument("--account", required=True)
    sub.add_parser("mirror", help="从备份权威仓库单向恢复公开仓库")
    web_export = sub.add_parser("web-export", help="生成可由 file:// 静态网页读取的 Hub 数据")
    web_export.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        repository = args.repo.resolve()
        backup_repository = args.backup_repo.resolve() if args.backup_repo else None
        policy_repository = backup_repository if backup_repository and (backup_repository / "config" / "roles.json").exists() else repository
        privileged = args.command in {
            "review", "approve", "publish", "accounts", "mirror"
        }
        actor = repository_principal(
            policy_repository, require_smb_identity=privileged
        )
        if args.command == "submit":
            authorize(policy_repository, "candidate.submit", actor)
            artifact = args.artifact.resolve() if args.artifact else None
            return command_submit(args.manifest.resolve(), repository, artifact)
        if args.command == "review":
            if backup_repository is None:
                raise ValueError("review 必须配置备份权威仓库")
            authorize(policy_repository, "candidate.review", actor)
            submission = args.submission
            if not submission.is_absolute() and not submission.exists():
                submission = repository / "submissions" / submission
            return command_review(submission.resolve(), args.decision, actor, args.note)
        if args.command in {"approve", "publish"}:
            if backup_repository is None:
                raise ValueError("publish 必须配置备份权威仓库")
            authorize(policy_repository, "release.publish", actor)
            submission = args.submission
            if not submission.is_absolute() and not submission.exists():
                submission = repository / "submissions" / submission
            authority = backup_repository or repository
            return command_approve(authority, submission.resolve(), repository, actor)
        if args.command == "accounts":
            if backup_repository is None:
                raise ValueError("accounts 必须配置备份权威仓库")
            authorize(backup_repository, "accounts.manage", actor)
            result = command_accounts(
                backup_repository,
                args.account_operation,
                getattr(args, "account", None),
                getattr(args, "role", None),
            )
            if args.account_operation != "list":
                public_config = repository / "config" / "roles.json"
                public_config.parent.mkdir(parents=True, exist_ok=True)
                write_json(public_config, read_json(backup_repository / "config" / "roles.json"))
                print(f"已同步角色配置到公开槽: {public_config}")
            return result
        if args.command == "mirror":
            authorize(policy_repository, "repository.mirror", actor)
            if backup_repository is None:
                raise ValueError("mirror 需要 --backup-repo 或 AI_ASSET_BACKUP_REPO")
            result = command_mirror(backup_repository, repository)
            if result == 0:
                command_web_export(repository, dashboard_path(repository))
            return result
        if args.command == "web-export":
            authorize(policy_repository, "asset.list", actor)
            output = args.output.resolve() if args.output else dashboard_path(repository)
            return command_web_export(repository, output)

        registry, active_repository = load_registry_with_fallback(repository, backup_repository)
        if args.command == "validate":
            authorize(policy_repository, "asset.list", actor)
            errors = validation_errors(registry)
            if errors:
                print("校验失败:")
                for error in errors:
                    print(f"- {error}")
                return 1
            print(f"校验通过: {len(registry['packages'])} 个包。")
            return 0
        if args.command in {"releases", "view"}:
            authorize(policy_repository, "asset.list", actor)
            packages = package_map(registry)
            selected = [packages[args.asset_id]] if args.asset_id in packages else packages.values()
            if args.asset_id and args.asset_id not in packages:
                raise ValueError(f"未知资产: {args.asset_id}")
            for package in selected:
                versions = ", ".join(
                    f"{r['version']} ({r['channel']})"
                    for r in sorted(package["releases"], key=lambda x: version_tuple(x["version"]), reverse=True)
                )
                print(f"{package['id']}: {versions}")
            return 0
        if args.command in {"install", "pull"}:
            authorize(policy_repository, "asset.install", actor)
            return command_install(
                registry, args.spec, args.root.resolve(), args.channel, args.activate, active_repository
            )
        if args.command == "activate":
            authorize(policy_repository, "asset.activate", actor)
            return command_activate(registry, args.spec, args.root.resolve())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
