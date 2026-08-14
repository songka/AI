"""Archive Codex projects and conversations into a Git repository.

The exporter intentionally keeps only human-readable user/assistant messages,
redacts common credentials, and copies source files with a deny-list for secrets,
dependencies and build outputs. It is safe to run repeatedly: files are
deterministic and Git only commits when the archive changed.

Example:
    python codex_archive_sync.py --repo C:/Users/name/Documents/CodexArchive
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ARCHIVE_ROOT_NAME = "Codex归档"
MAX_PART_CHARS = 200_000
MAX_SOURCE_FILE_BYTES = 10 * 1024 * 1024
EXCLUDED_DIRECTORY_NAMES = {
    ".git", ".idea", ".vscode", ".codex", ".claude", ".opencode",
    ".venv", "venv", "node_modules", "__pycache__",
    "build", "dist", ".next", ".nuxt", ".pytest_cache", ".mypy_cache", ".tox",
    "coverage", "target", "bin", "obj", "site-packages", "__pypackages__",
    ".launcher-payload", ".launcher-payload-fast-test-v7", "packages",
}
EXCLUDED_DIRECTORY_PREFIXES = ("codex-archive-",)
EXCLUDED_FILE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development", "auth.json",
    "credentials.json", "secrets.json", "id_rsa", "id_ed25519",
}
EXCLUDED_SUFFIXES = {".pem", ".key", ".pfx", ".p12", ".pyc", ".sqlite", ".db", ".log"}
SOURCE_SUFFIXES = {
    ".py", ".pyw", ".ps1", ".psm1", ".bat", ".cmd", ".sh",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".cs", ".csproj", ".sln", ".props", ".targets",
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx",
    ".java", ".kt", ".kts", ".go", ".rs", ".rb", ".php", ".swift",
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
    ".sql", ".r", ".lua", ".dart", ".ex", ".exs",
    ".md", ".mdx", ".txt", ".rst", ".adoc",
    ".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".xml",
    ".gitignore", ".gitattributes", ".editorconfig",
}
SOURCE_FILE_NAMES = {
    "makefile", "dockerfile", "license", "copying", "readme", "requirements",
    "gemfile", "rakefile", "procfile", "nuget.config",
}
SECRET_PATTERNS = (
    (re.compile(r"(?i)(bearer\s+)[a-z0-9_\-\.]{12,}"), r"\1[已脱敏]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "[已脱敏 OpenAI 密钥]"),
    (re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{12,}\b"), "[已脱敏 GitHub 密钥]"),
    (re.compile(r"(?i)(\"?(?:api[_-]?key|token|secret|password)\"?\s*[:=]\s*[\"']?)[^\s\"',}]{8,}"), r"\1[已脱敏]"),
)


@dataclass(frozen=True)
class Session:
    session_id: str
    title: str
    updated_at: str
    path: Path
    cwd: Path | None


def redact(text: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def safe_name(value: str, fallback: str = "未命名") -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    value = re.sub(r"\s+", " ", value)
    return (value[:96] or fallback)


def json_lines(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        yield item
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def collect_index(codex_home: Path) -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for item in json_lines(codex_home / "session_index.jsonl"):
        session_id = item.get("id")
        if isinstance(session_id, str):
            index[session_id] = (str(item.get("thread_name") or session_id), str(item.get("updated_at") or ""))
    return index


def extract_text(value: Any) -> list[str]:
    """Extract textual content from Codex response payload shapes."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for part in value for text in extract_text(part)]
    if not isinstance(value, dict):
        return []
    content_type = value.get("type")
    if content_type in {"input_text", "output_text", "text"} and isinstance(value.get("text"), str):
        return [value["text"]]
    if content_type in {"input_text", "output_text", "text"} and isinstance(value.get("content"), str):
        return [value["content"]]
    # Only descend into established content containers; this avoids exporting
    # hidden reasoning or tool payloads unintentionally.
    text: list[str] = []
    for key in ("content", "text", "message"):
        if key in value:
            text.extend(extract_text(value[key]))
    return text


def inspect_session(path: Path, index: dict[str, tuple[str, str]]) -> Session | None:
    session_id = path.stem.rsplit("-", 1)[-1]
    cwd: Path | None = None
    for item in json_lines(path):
        if item.get("type") != "session_meta":
            continue
        payload = item.get("payload") or {}
        if isinstance(payload, dict):
            session_id = str(payload.get("id") or payload.get("session_id") or session_id)
            value = payload.get("cwd")
            if isinstance(value, str) and value:
                cwd = Path(value)
        break
    title, updated_at = index.get(session_id, (session_id, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()))
    return Session(session_id=session_id, title=title, updated_at=updated_at, path=path, cwd=cwd)


def markdown_for_session(session: Session) -> str:
    lines = [f"# {session.title}", "", f"- 会话 ID：`{session.session_id}`", f"- 最后更新：{session.updated_at}", f"- 来源：Codex 本地会话", ""]
    for item in json_lines(session.path):
        if item.get("type") != "response_item":
            continue
        payload = item.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        role = payload.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = "\n".join(part.strip() for part in extract_text(payload.get("content")) if part.strip())
        if not content:
            continue
        lines.extend([f"## {'用户' if role == 'user' else '助手'}", "", redact(content), ""])
    return "\n".join(lines).rstrip() + "\n"


def write_parts(destination: Path, stem: str, content: str) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    chunks = [content[offset:offset + MAX_PART_CHARS] for offset in range(0, len(content), MAX_PART_CHARS)] or [content]
    paths: list[Path] = []
    for number, chunk in enumerate(chunks, start=1):
        path = destination / f"{stem}-{number:03d}.md"
        if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != chunk:
            path.write_text(chunk, encoding="utf-8")
        paths.append(path)
    for obsolete in destination.glob(f"{stem}-*.md"):
        if obsolete not in paths:
            obsolete.unlink()
    return paths


def should_copy(path: Path) -> bool:
    if any(part.lower() in EXCLUDED_DIRECTORY_NAMES for part in path.parts):
        return False
    name = path.name.lower()
    if name in EXCLUDED_FILE_NAMES or name.startswith(".env."):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    # Strict allow-list: archives, executables, virtual-environment payloads,
    # databases and other opaque files are never considered project source.
    return path.suffix.lower() in SOURCE_SUFFIXES or name in SOURCE_FILE_NAMES


def contains_secret(path: Path) -> bool:
    """Avoid publishing a source file when it contains a recognisable secret."""
    try:
        if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
            return True
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return True
    return any(pattern.search(text) for pattern, _ in SECRET_PATTERNS)


def copy_project(source: Path, destination: Path) -> int:
    if not source.is_dir():
        return 0
    copied = 0
    # Prune excluded trees before enumerating their files.  This matters for
    # projects containing a Python virtual environment or frontend dependency
    # tree: neither belongs in a source archive and walking them is expensive.
    for root, directories, files in os.walk(source, topdown=True):
        directories[:] = [
            directory for directory in directories
            if directory.lower() not in EXCLUDED_DIRECTORY_NAMES
            and not directory.lower().startswith(EXCLUDED_DIRECTORY_PREFIXES)
        ]
        root_path = Path(root)
        for filename in files:
            path = root_path / filename
            relative = path.relative_to(source)
            if not should_copy(relative):
                continue
            target = destination / relative
            try:
                if target.exists() and target.stat().st_size == path.stat().st_size and target.stat().st_mtime_ns >= path.stat().st_mtime_ns:
                    continue
            except OSError:
                pass
            if contains_secret(path):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
    return copied


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), "-c", f"safe.directory={repo}", "-c", "http.version=HTTP/1.1", *args], text=True, capture_output=True, encoding="utf-8", errors="replace", check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex 会话与项目归档同步器")
    parser.add_argument("--repo", required=True, type=Path, help="songka/AI 的本地 Git 克隆目录")
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--no-push", action="store_true", help="仅生成和提交，不推送 GitHub")
    args = parser.parse_args()
    repo, codex_home = args.repo.resolve(), args.codex_home.expanduser()
    # A linked Git worktree has a `.git` file, while an ordinary clone has a
    # `.git` directory.  Both forms are valid repository roots.
    if not (repo / ".git").exists():
        raise SystemExit(f"不是 Git 仓库：{repo}")
    sessions_dir = codex_home / "sessions"
    if not sessions_dir.is_dir():
        raise SystemExit(f"未找到 Codex 会话目录：{sessions_dir}")

    index = collect_index(codex_home)
    sessions: list[Session] = []
    for path in sessions_dir.rglob("*.jsonl"):
        session = inspect_session(path, index)
        if session:
            sessions.append(session)
    sessions.sort(key=lambda value: value.updated_at)

    archive = repo / ARCHIVE_ROOT_NAME
    projects: dict[Path | None, list[Session]] = defaultdict(list)
    for session in sessions:
        projects[session.cwd].append(session)

    project_manifest: list[dict[str, Any]] = []
    for project_path, group in projects.items():
        project_name = safe_name(project_path.name if project_path else "未关联项目")
        project_key = hashlib.sha256(str(project_path or "").encode("utf-8")).hexdigest()[:16]
        # Preserve distinct same-name projects without leaking full local paths.
        folder = archive / project_name
        if folder.exists() and (folder / "project.json").exists():
            try:
                known = json.loads((folder / "project.json").read_text(encoding="utf-8"))
                if known.get("project_key") != project_key:
                    identifier = project_key[:8]
                    folder = archive / f"{project_name}-{identifier}"
            except (OSError, ValueError):
                pass
        folder.mkdir(parents=True, exist_ok=True)
        # Keep this metadata stable so a run with no real content changes does
        # not create a pointless Git commit.  The local path is never stored.
        (folder / "project.json").write_text(json.dumps({"name": project_name, "project_key": project_key}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        source_count = copy_project(project_path, folder / "源码") if project_path else 0
        conversations = folder / "对话"
        for session in group:
            timestamp = re.sub(r"[^0-9]", "", session.updated_at)[:8] or "unknown-date"
            stem = f"{timestamp}-{safe_name(session.title)}-{session.session_id[:8]}"
            existing_parts = list(conversations.glob(f"{stem}-*.md")) if conversations.exists() else []
            try:
                if existing_parts and min(part.stat().st_mtime_ns for part in existing_parts) >= session.path.stat().st_mtime_ns:
                    continue
            except OSError:
                pass
            write_parts(conversations, stem, markdown_for_session(session))
        project_manifest.append({"project": project_name, "session_count": len(group), "source_files": source_count})

    (archive / "README.md").write_text("# Codex 自动归档\n\n本目录由 `codex_archive_sync.py` 自动生成。对话已做常见凭据脱敏；每个项目独立目录，长对话自动分段。\n", encoding="utf-8")
    (archive / "同步清单.json").write_text(json.dumps({"projects": project_manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    git(repo, "add", ARCHIVE_ROOT_NAME)
    status = git(repo, "status", "--porcelain")
    if not status.stdout.strip():
        print("归档无变更，无需提交。")
        return 0
    commit = git(repo, "-c", "user.name=Codex Archive", "-c", "user.email=codex-archive@users.noreply.github.com", "commit", "-m", f"Archive Codex projects and sessions {datetime.now().date().isoformat()}")
    if commit.returncode:
        raise SystemExit(commit.stderr or commit.stdout)
    if not args.no_push:
        # `HEAD:main` also works from a linked/detached worktree and always
        # pushes the commit that was just created, rather than another local
        # branch that may be checked out elsewhere.
        push = git(repo, "push", "origin", "HEAD:main")
        if push.returncode:
            raise SystemExit(push.stderr or push.stdout)
    print(f"已归档 {len(sessions)} 个会话、{len(project_manifest)} 个项目。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
