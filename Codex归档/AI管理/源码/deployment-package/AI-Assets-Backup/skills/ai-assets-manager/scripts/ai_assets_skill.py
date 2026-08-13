#!/usr/bin/env python3
"""Portable, dependency-free control script for the AI Assets Manager skill."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

VERSION = "1.0.6"
SELF_ID = "skill/ai-assets-manager"
SHARE_ROOT = Path(r"\\10.97.0.210\lfaf_Engineer")
PUBLIC = Path(r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets")
BACKUP = Path(r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup")
ASSET_ID = re.compile(r"^(skill|cli|agent)/[a-z0-9][a-z0-9._-]*$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
IGNORED_PARTS = {".git", ".svn", "__pycache__", ".ai-assets", "dist", "build"}
SECRET_NAMES = {
    ".env", ".env.local", "credentials.json", "credential.json",
    "secrets.json", "secret.json", "id_rsa", "id_ed25519",
}
SECRET_SUFFIXES = {".pem", ".pfx", ".p12", ".key", ".kdbx"}


def emit(value: dict, code: int = 0) -> int:
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return code


def version_key(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError(f"无效 SemVer: {value}")
    return tuple(map(int, match.groups()))


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(data, encoding="utf-8")
    temporary.replace(path)


def smb_principal() -> str | None:
    if os.name != "nt":
        return None
    command = (
        "Get-SmbConnection -ErrorAction SilentlyContinue | "
        "Where-Object {$_.ServerName -ieq '10.97.0.210' -and "
        "$_.ShareName -ieq 'lfaf_Engineer'} | Select-Object -First 1 "
        "-ExpandProperty UserName"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=8, check=False,
        )
        principal = result.stdout.strip()
        if principal:
            return principal
    except (OSError, subprocess.SubprocessError):
        pass
    return native_smb_principal(SHARE_ROOT)


def native_smb_principal(repository: Path) -> str | None:
    """Read the account bound to a UNC resource from the Windows network provider."""
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


def resolve_role(repository: Path, principal: str) -> tuple[str, list[str]]:
    policy = read_json(repository / "config" / "roles.json")
    role = policy.get("defaultRole", "user")
    for role_name, definition in policy.get("roles", {}).items():
        if principal.casefold() in {
            str(account).casefold() for account in definition.get("accounts", [])
        }:
            role = role_name
            break
    actions = policy.get("roles", {}).get(role, {}).get("actions", [])
    return role, actions


def path_accessible(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def repository_accessible() -> bool:
    return path_accessible(PUBLIC / "registry.json")


def readiness_state() -> tuple[str, str | None]:
    principal = smb_principal()
    if not path_accessible(SHARE_ROOT) or not principal:
        return "login_required", None
    if not repository_accessible():
        return "setup_required", principal
    return "ready", principal


def gate() -> int:
    state, principal = readiness_state()
    if state == "login_required":
        script = Path(__file__).with_name("secure-login.ps1")
        instruction = (
            "尚未登录 AI Assets SMB。请在文件资源管理器或独立 PowerShell 窗口运行：\n"
            f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script}"\n'
            "只在弹出的 Windows 凭据窗口输入账号和密码；不要在 AI 对话中输入。"
        )
        return emit({"state": "login_required", "login_instruction": instruction})
    if state == "setup_required":
        return emit({
            "state": "setup_required",
            "principal": principal,
            "setup_instruction": (
                f"SMB 已登录为 {principal}，但 Hub 尚未初始化：{PUBLIC / 'registry.json'} 不存在。"
                "请由管理员运行部署包中的 scripts\\deploy-secure-launch.ps1，完成后再继续。"
            ),
        })
    try:
        role, actions = resolve_role(BACKUP if (BACKUP / "config/roles.json").is_file() else PUBLIC, principal)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return emit({"state": "error", "message": f"角色配置不可用: {exc}"}, 2)
    prompts = {
        "user": "可查询、安装、切换版本，或把本地更新提交为候选版本。",
        "reviewer": "可执行用户操作，并审核或驳回候选版本；不能发布。",
        "publisher": "可发布已审核版本，并从备份权威槽单向镜像到公共槽。",
        "administrator": "可分配账户角色、审核、发布、镜像和恢复仓库。",
    }
    return emit({
        "state": "ready", "principal": principal, "role": role,
        "allowed_actions": actions, "role_prompt": prompts.get(role, prompts["user"]),
        "public_repository": str(PUBLIC), "backup_repository": str(BACKUP),
    })


def content_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(root)
        if path.is_dir() or any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if relative.name in {"asset-state.json"} or relative.suffix == ".zip":
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def source_files(root: Path):
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(root)
        if path.is_dir() or any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if relative.name == "asset-state.json" or relative.suffix == ".zip":
            continue
        yield path, relative


def file_snapshot(root: Path) -> dict[str, str]:
    values = {}
    for path, relative in source_files(root):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        values[relative.as_posix()] = digest.hexdigest()
    return values


def generated_release_notes(root: Path, manifest: dict) -> tuple[str, dict[str, str]]:
    current = file_snapshot(root)
    previous_path = root / ".ai-assets" / "packaged-files.json"
    previous = read_json(previous_path).get("files", {}) if previous_path.is_file() else {}
    if not previous:
        return f"首次发布 {manifest['id']} {manifest['version']}。", current
    added = sorted(set(current) - set(previous))
    removed = sorted(set(previous) - set(current))
    modified = sorted(path for path in set(current) & set(previous) if current[path] != previous[path])
    parts = []
    if added:
        parts.append("新增：" + "、".join(added[:20]))
    if modified:
        parts.append("更新：" + "、".join(modified[:20]))
    if removed:
        parts.append("移除：" + "、".join(removed[:20]))
    if not parts:
        raise ValueError("未检测到内容变化；请修改资产，或使用 --release-notes 输入需要发布的说明")
    return "；".join(parts) + "。", current


def assert_no_obvious_secrets(root: Path) -> None:
    blocked = [
        str(relative) for path, relative in source_files(root)
        if path.name.casefold() in SECRET_NAMES
        or path.suffix.casefold() in SECRET_SUFFIXES
        or "password" in path.name.casefold()
        or "credential" in path.name.casefold()
    ]
    if blocked:
        raise ValueError(
            "草稿包含疑似凭据/私钥文件，已拒绝上传 SMB: " + ", ".join(blocked[:10])
        )


def parse_dependency(value: str) -> dict:
    asset, separator, constraint = value.partition("@")
    if not separator or not ASSET_ID.fullmatch(asset) or not constraint:
        raise ValueError(f"依赖格式应为 skill|cli|agent/name@版本约束: {value}")
    return {"id": asset, "version": constraint, "required": True}


def command_init(args: argparse.Namespace) -> int:
    if gate_for_internal() is not None:
        return gate()
    root = args.path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    asset_id = f"{args.type}/{args.name}"
    if not ASSET_ID.fullmatch(asset_id):
        raise ValueError(f"无效资产 ID: {asset_id}")
    version_key(args.version)
    manifest = {
        "schemaVersion": 1, "id": asset_id, "version": args.version,
        "owner": args.owner or os.environ.get("USERNAME", "unknown"),
        "dependencies": [parse_dependency(item) for item in args.dependency],
    }
    write_json(root / "asset-manifest.json", manifest)
    backup = draft_backup(root)
    return emit({"state": "initialized", "path": str(root), "manifest": manifest, "automatic_backup": backup})


def command_status(args: argparse.Namespace) -> int:
    if gate_for_internal() is not None:
        return gate()
    root = args.path.resolve()
    manifest_path = root / "asset-manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"缺少 {manifest_path}")
    manifest = read_json(manifest_path)
    digest = content_digest(root)
    state_path = root / ".ai-assets" / "asset-state.json"
    previous = read_json(state_path) if state_path.is_file() else {}
    backup = draft_backup(root)
    return emit({
        "state": "local", "id": manifest.get("id"), "version": manifest.get("version"),
        "sha256": digest, "unpublished": digest != previous.get("packagedSha256"),
        "last_packaged_sha256": previous.get("packagedSha256"),
        "automatic_backup": backup,
    })


def command_bump(args: argparse.Namespace) -> int:
    if gate_for_internal() is not None:
        return gate()
    version_key(args.version)
    path = args.path.resolve() / "asset-manifest.json"
    manifest = read_json(path)
    old = manifest.get("version")
    manifest["version"] = args.version
    write_json(path, manifest)
    backup = draft_backup(args.path.resolve())
    return emit({
        "state": "version_changed", "id": manifest.get("id"),
        "from": old, "to": args.version, "automatic_backup": backup,
    })


def command_package(args: argparse.Namespace) -> int:
    if gate_for_internal() is not None:
        return gate()
    root = args.path.resolve()
    manifest = read_json(root / "asset-manifest.json")
    asset_id = manifest.get("id", "")
    if not ASSET_ID.fullmatch(asset_id):
        raise ValueError(f"无效资产 ID: {asset_id}")
    version_key(manifest.get("version", ""))
    if args.release_notes and not args.release_notes.strip():
        raise ValueError("更新说明不能为空")
    if args.release_notes:
        release_notes = args.release_notes.strip()
        snapshot = file_snapshot(root)
        notes_source = "user"
    else:
        release_notes, snapshot = generated_release_notes(root, manifest)
        notes_source = "generated"
    digest = content_digest(root)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    filename = f"{asset_id.replace('/', '-')}-{manifest['version']}.zip"
    archive = output / filename
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
            relative = path.relative_to(root)
            if path.is_dir() or any(part in IGNORED_PARTS for part in relative.parts):
                continue
            if path == archive or relative.name == "asset-state.json" or relative.suffix == ".zip":
                continue
            bundle.write(path, relative.as_posix())
    artifact_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    write_json(root / ".ai-assets" / "asset-state.json", {
        "packagedSha256": digest, "artifactSha256": artifact_hash,
        "version": manifest["version"], "artifact": str(archive),
    })
    write_json(root / ".ai-assets" / "packaged-files.json", {"files": snapshot})
    submission = {
        "id": asset_id, "owner": manifest.get("owner", "unknown"),
        "release": {
            "version": manifest["version"], "channel": "stable",
            "releaseNotes": release_notes,
            "dependencies": manifest.get("dependencies", []),
            "artifact": {"type": "repository", "location": filename, "sha256": artifact_hash},
        },
    }
    write_json(output / f"{filename}.submission.json", submission)
    backup = draft_backup(root)
    return emit({
        "state": "packaged", "artifact": str(archive), "sha256": artifact_hash,
        "submission": str(output / f"{filename}.submission.json"),
        "release_notes": release_notes, "release_notes_source": notes_source,
        "automatic_backup": backup,
    })


def git(*arguments: str, cwd: Path | None = None, allow_no_changes: bool = False) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments], cwd=cwd, capture_output=True, text=True,
            timeout=120, check=False,
        )
    except OSError as exc:
        raise ValueError("未找到 Git，无法建立草稿历史备份") from exc
    if result.returncode and not (
        allow_no_changes and result.returncode == 1 and "nothing to commit" in (result.stdout + result.stderr)
    ):
        raise ValueError(f"Git 命令失败: {' '.join(arguments)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def safe_principal(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "unknown"


def sync_shadow(source: Path, shadow: Path) -> None:
    shadow.mkdir(parents=True, exist_ok=True)
    for child in shadow.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for path, relative in source_files(source):
        destination = shadow / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def draft_backup(source: Path) -> dict:
    manifest = read_json(source / "asset-manifest.json")
    asset_id = manifest.get("id", "")
    if not ASSET_ID.fullmatch(asset_id):
        raise ValueError(f"无效资产 ID: {asset_id}")
    assert_no_obvious_secrets(source)
    principal = smb_principal()
    if not principal:
        raise ValueError("无法确认 SMB 登录身份")
    kind, name = asset_id.split("/", 1)
    relative = Path("drafts") / safe_principal(principal) / kind / f"{name}.git"
    public_remote = PUBLIC / relative
    backup_remote = BACKUP / relative
    local_base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "AIAssetHub" / "draft-worktrees"
    shadow = local_base / safe_principal(principal) / kind / name
    if not (shadow / ".git").is_dir():
        shadow.mkdir(parents=True, exist_ok=True)
        git("init", cwd=shadow)
        git("config", "user.name", principal, cwd=shadow)
        git("config", "user.email", f"{safe_principal(principal)}@ai-assets.local", cwd=shadow)
    sync_shadow(source, shadow)
    git("add", "--all", cwd=shadow)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=shadow, check=False
    )
    changed = result.returncode != 0
    if changed:
        git("commit", "-m", f"draft backup {asset_id}@{manifest.get('version', 'unknown')}", cwd=shadow)
    commit = git("rev-parse", "HEAD", cwd=shadow)
    outcomes = {}
    for label, remote in (("public", public_remote), ("backup", backup_remote)):
        if not remote.exists():
            remote.parent.mkdir(parents=True, exist_ok=True)
            git("init", "--bare", str(remote))
        remote_name = f"smb-{label}"
        remotes = git("remote", cwd=shadow).splitlines()
        if remote_name in remotes:
            git("remote", "set-url", remote_name, str(remote), cwd=shadow)
        else:
            git("remote", "add", remote_name, str(remote), cwd=shadow)
        # Never force: divergence indicates direct SMB modification or another writer.
        git("push", remote_name, "HEAD:refs/heads/main", cwd=shadow)
        outcomes[label] = str(remote)
    return {
        "state": "draft_backed_up", "id": asset_id, "commit": commit,
        "new_commit": changed, "repositories": outcomes,
        "published": False,
        "note": "这是用户私有草稿 Git 历史，不会进入正式版本索引。",
    }


def command_draft_backup(args: argparse.Namespace) -> int:
    if gate_for_internal() is not None:
        return gate()
    return emit(draft_backup(args.path.resolve()))


def self_release() -> tuple[dict, Path]:
    registry = read_json(PUBLIC / "registry.json")
    package = next((item for item in registry.get("packages", []) if item.get("id") == SELF_ID), None)
    if not package:
        raise ValueError(f"Hub 尚未登记 {SELF_ID}")
    releases = [item for item in package.get("releases", []) if item.get("channel") == "stable"]
    if not releases:
        raise ValueError("Hub 没有稳定版管理 Skill")
    release = max(releases, key=lambda item: version_key(item["version"]))
    return release, PUBLIC


def command_self_check() -> int:
    if gate_for_internal() is not None:
        return gate()
    release, _ = self_release()
    return emit({
        "state": "update_available" if version_key(release["version"]) > version_key(VERSION) else "current",
        "installed": VERSION, "latest": release["version"], "asset": SELF_ID,
    })


def gate_for_internal() -> str | None:
    state, _ = readiness_state()
    return None if state == "ready" else state


def command_self_update() -> int:
    if gate_for_internal() is not None:
        return gate()
    skill_root = Path(__file__).resolve().parents[1]
    if any((ancestor / ".git").is_dir() for ancestor in [skill_root, *skill_root.parents]):
        raise ValueError("拒绝更新 Git 开发源；请只更新复制到 Code 客户端 skills 目录的安装副本")
    release, repository = self_release()
    if version_key(release["version"]) <= version_key(VERSION):
        return emit({"state": "current", "installed": VERSION, "latest": release["version"]})
    artifact = release["artifact"]
    source = repository / artifact["location"]
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_hash.casefold() != artifact["sha256"].casefold():
        raise ValueError("更新包 SHA-256 与 Hub 登记值不一致")
    parent = skill_root.parent
    staging = Path(tempfile.mkdtemp(prefix=".ai-assets-manager-", dir=parent))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    rollback = parent / f".ai-assets-manager.backup.{stamp}.{VERSION}"
    try:
        with zipfile.ZipFile(source) as bundle:
            bundle.extractall(staging)
        if not (staging / "SKILL.md").is_file() or not (staging / "scripts" / "ai_assets_skill.py").is_file():
            raise ValueError("更新包不是有效的 AI Assets Manager Skill")
        skill_root.replace(rollback)
        staging.replace(skill_root)
        prune_backups(parent)
    except Exception:
        if not skill_root.exists() and rollback.exists():
            rollback.replace(skill_root)
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return emit({
        "state": "updated", "from": VERSION, "to": release["version"],
        "backup": str(rollback), "backups_retained": 3, "restart_required": True,
        "next_step": "关闭并重新打开当前 Code/Agent 会话；如异常，运行 self-rollback。",
    })


def backup_directories(parent: Path) -> list[Path]:
    return sorted(
        (item for item in parent.glob(".ai-assets-manager.backup.*") if item.is_dir()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )


def prune_backups(parent: Path) -> None:
    for obsolete in backup_directories(parent)[3:]:
        shutil.rmtree(obsolete)


def command_self_backups() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    backups = [str(item) for item in backup_directories(skill_root.parent)]
    return emit({"state": "backups", "maximum": 3, "items": backups})


def command_self_rollback(args: argparse.Namespace) -> int:
    skill_root = Path(__file__).resolve().parents[1]
    parent = skill_root.parent
    candidates = backup_directories(parent)
    selected = args.backup.resolve() if args.backup else (candidates[0] if candidates else None)
    if selected is None or selected not in candidates:
        raise ValueError("没有可用备份，或指定目录不属于本 Skill 的历史备份")
    if not (selected / "SKILL.md").is_file():
        raise ValueError("备份缺少 SKILL.md")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    current_backup = parent / f".ai-assets-manager.backup.{stamp}.{VERSION}"
    skill_root.replace(current_backup)
    try:
        selected.replace(skill_root)
    except Exception:
        current_backup.replace(skill_root)
        raise
    prune_backups(parent)
    return emit({
        "state": "rolled_back", "restored": str(selected),
        "previous_current_backup": str(current_backup),
        "backups_retained": 3, "restart_required": True,
        "next_step": "关闭并重新打开当前 Code/Agent 会话。",
    })


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="AI Assets portable Skill control plane")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("gate")
    init = commands.add_parser("init")
    init.add_argument("--path", type=Path, required=True)
    init.add_argument("--type", choices=["skill", "cli", "agent"], required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--version", default="0.1.0")
    init.add_argument("--owner")
    init.add_argument("--dependency", action="append", default=[])
    status = commands.add_parser("status")
    status.add_argument("--path", type=Path, required=True)
    bump = commands.add_parser("bump")
    bump.add_argument("--path", type=Path, required=True)
    bump.add_argument("--version", required=True)
    package = commands.add_parser("package")
    package.add_argument("--path", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--release-notes")
    draft = commands.add_parser("draft-backup")
    draft.add_argument("--path", type=Path, required=True)
    commands.add_parser("self-check")
    commands.add_parser("self-update")
    commands.add_parser("self-backups")
    rollback = commands.add_parser("self-rollback")
    rollback.add_argument("--backup", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return {
            "gate": gate,
            "init": lambda: command_init(args),
            "status": lambda: command_status(args),
            "bump": lambda: command_bump(args),
            "package": lambda: command_package(args),
            "draft-backup": lambda: command_draft_backup(args),
            "self-check": command_self_check,
            "self-update": command_self_update,
            "self-backups": command_self_backups,
            "self-rollback": lambda: command_self_rollback(args),
        }[args.command]()
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        return emit({"state": "error", "message": str(exc)}, 2)


if __name__ == "__main__":
    raise SystemExit(main())
