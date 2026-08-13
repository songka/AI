#!/usr/bin/env python3
"""Safely archive AI coding transcripts and explicitly selected project source.

The tool is intentionally conservative: preview is read-only, `--commit` is
required for a Git commit, and `--push` is required for a remote upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ARCHIVE_NAME = "AI归档"
MAX_PART_CHARS = 200_000
MAX_FILE_BYTES = 10 * 1024 * 1024
EXCLUDED_DIRS = {
    ".git", ".svn", ".hg", ".idea", ".vscode", ".codex", ".claude", ".opencode",
    ".env", ".venv", "venv", "env", "node_modules", "site-packages", "__pypackages__",
    "__pycache__", "build", "dist", "target", "bin", "obj", "coverage", ".next", ".nuxt",
    ".pytest_cache", ".mypy_cache", ".tox", "vendor", "packages",
}
EXCLUDED_NAMES = {
    ".env", "auth.json", "credentials.json", "secrets.json", "id_rsa", "id_ed25519",
}
EXCLUDED_SUFFIXES = {
    ".exe", ".dll", ".msi", ".zip", ".7z", ".rar", ".tar", ".gz", ".bz2",
    ".pem", ".key", ".pfx", ".p12", ".sqlite", ".db", ".log", ".pyc",
}
ALLOWED_SUFFIXES = {
    ".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".cs", ".csproj",
    ".sln", ".props", ".targets", ".java", ".kt", ".kts", ".go", ".rs", ".rb", ".php",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".dart", ".html", ".css", ".scss",
    ".vue", ".svelte", ".sql", ".sh", ".ps1", ".psm1", ".bat", ".cmd", ".md", ".txt",
    ".rst", ".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".xml",
    ".gitignore", ".gitattributes", ".editorconfig",
}
ALLOWED_NAMES = {"makefile", "dockerfile", "license", "copying", "readme", "requirements", "gemfile", "rakefile", "procfile"}
SECRET_PATTERNS = (
    (re.compile(r"(?i)(bearer\s+)[a-z0-9_.-]{12,}"), r"\1[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{12,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"(?i)(\b(?:api[_-]?key|token|secret|password)\b\s*[:=]\s*[\"']?)[^\s\"',}]{8,}"), r"\1[REDACTED]"),
)


@dataclass(frozen=True)
class Session:
    product: str
    session_id: str
    title: str
    updated_at: str
    path: Path
    project: Path | None


def json_lines(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        yield value
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def safe_name(value: str, fallback: str = "unnamed") -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return re.sub(r"\s+", " ", value)[:96] or fallback


def redact(value: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def extract_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [part for item in value for part in extract_text(item)]
    if not isinstance(value, dict):
        return []
    if value.get("type") in {"text", "input_text", "output_text"}:
        text = value.get("text") or value.get("content")
        return [text] if isinstance(text, str) else []
    result: list[str] = []
    for key in ("content", "text", "message"):
        if key in value:
            result.extend(extract_text(value[key]))
    return result


def codex_sessions(home: Path) -> list[Session]:
    index: dict[str, tuple[str, str]] = {}
    for item in json_lines(home / "session_index.jsonl"):
        if isinstance(item.get("id"), str):
            index[item["id"]] = (str(item.get("thread_name") or item["id"]), str(item.get("updated_at") or ""))
    result: list[Session] = []
    for path in (home / "sessions").rglob("*.jsonl") if (home / "sessions").is_dir() else []:
        sid, cwd = path.stem, None
        for item in json_lines(path):
            if item.get("type") == "session_meta" and isinstance(item.get("payload"), dict):
                payload = item["payload"]
                sid = str(payload.get("id") or sid)
                if isinstance(payload.get("cwd"), str): cwd = Path(payload["cwd"])
                break
        title, updated = index.get(sid, (sid, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()))
        result.append(Session("codex", sid, title, updated, path, cwd))
    return result


def claude_sessions(home: Path) -> list[Session]:
    root = home / ".claude" / "projects"
    result: list[Session] = []
    if not root.is_dir(): return result
    for path in root.rglob("*.jsonl"):
        project = None
        # Claude's directory name is not treated as a local path; export the
        # transcript without inferring or publishing it.
        result.append(Session("claude-code", path.stem, path.stem, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), path, project))
    return result


def generic_sessions(product: str, roots: list[Path]) -> list[Session]:
    result: list[Session] = []
    for root in roots:
        if not root.is_dir(): continue
        for path in list(root.rglob("*.jsonl")) + list(root.rglob("*.json")):
            result.append(Session(product, hashlib.sha256(str(path).encode()).hexdigest()[:16], path.stem, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), path, None))
    return result


def session_markdown(session: Session) -> str:
    lines = [f"# {session.title}", "", f"- 产品：{session.product}", f"- 会话 ID：`{session.session_id}`", f"- 最后更新：{session.updated_at}", ""]
    emitted = 0
    for item in json_lines(session.path):
        payload = item.get("payload") if session.product == "codex" else item
        if not isinstance(payload, dict): continue
        role = payload.get("role")
        if role not in {"user", "assistant"}:
            message = payload.get("message")
            if isinstance(message, dict):
                role, payload = message.get("role"), message
        if role not in {"user", "assistant"}: continue
        content = "\n".join(part.strip() for part in extract_text(payload.get("content")) if part.strip())
        if content:
            lines.extend([f"## {'用户' if role == 'user' else '助手'}", "", redact(content), ""])
            emitted += 1
    return "\n".join(lines).rstrip() + "\n" if emitted else ""


def path_allowed(relative: Path) -> bool:
    if any(part.lower() in EXCLUDED_DIRS for part in relative.parts): return False
    name = relative.name.lower()
    return not (name in EXCLUDED_NAMES or name.startswith(".env.") or relative.suffix.lower() in EXCLUDED_SUFFIXES) and (relative.suffix.lower() in ALLOWED_SUFFIXES or name in ALLOWED_NAMES)


def file_has_secret(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES: return True
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return True
    return any(pattern.search(text) for pattern, _ in SECRET_PATTERNS)


def write_if_changed(path: Path, data: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == data: return False
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(data, encoding="utf-8"); return True


def copy_source(source: Path, destination: Path, preview: bool) -> tuple[int, int]:
    copied = skipped = 0
    if not source.is_dir(): return copied, skipped
    for root, directories, files in os.walk(source, topdown=True):
        directories[:] = [name for name in directories if name.lower() not in EXCLUDED_DIRS and not name.lower().startswith("ai-archive")]
        for name in files:
            original = Path(root) / name; relative = original.relative_to(source)
            if not path_allowed(relative) or file_has_secret(original): skipped += 1; continue
            target = destination / relative
            if target.exists() and target.stat().st_size == original.stat().st_size and target.read_bytes() == original.read_bytes(): continue
            copied += 1
            if not preview:
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(original, target)
    return copied, skipped


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), "-c", f"safe.directory={repo}", *args], text=True, capture_output=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely archive AI coding conversations and source")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--product", choices=["codex", "claude", "opencode", "generic"], action="append")
    parser.add_argument("--transcript-root", type=Path, action="append", default=[])
    parser.add_argument("--project-root", type=Path, action="append", default=[])
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not (repo / ".git").exists(): raise SystemExit(f"Not a Git repository: {repo}")
    if args.push and not args.commit: raise SystemExit("--push requires --commit")
    products = set(args.product or ["codex", "claude", "opencode"])
    home = Path.home(); sessions: list[Session] = []
    if "codex" in products: sessions.extend(codex_sessions(home / ".codex"))
    if "claude" in products: sessions.extend(claude_sessions(home))
    if {"opencode", "generic"} & products:
        known = [home / ".local" / "share" / "opencode", Path(os.getenv("APPDATA", home)) / "opencode", Path(os.getenv("LOCALAPPDATA", home)) / "opencode"]
        sessions.extend(generic_sessions("opencode", list(args.transcript_root) or known))
    sessions.sort(key=lambda item: (item.product, item.updated_at, item.session_id))
    archive = repo / ARCHIVE_NAME; changed = source_copied = source_skipped = transcript_written = 0
    groups: dict[tuple[str, str], list[Session]] = defaultdict(list)
    for session in sessions:
        key = str(session.project) if session.project else session.product
        groups[(session.product, key)].append(session)
    for source in args.project_root:
        groups[("project", str(source.resolve()))]
    manifest: list[dict[str, Any]] = []
    for (product, key), group in groups.items():
        project = group[0].project if group and group[0].project else (Path(key) if product == "project" else None)
        project_name = safe_name(project.name if project else product)
        project_id = hashlib.sha256(f"{product}:{key}".encode()).hexdigest()[:12]
        folder = archive / safe_name(product) / f"{project_name}-{project_id}"
        meta = json.dumps({"product": product, "name": project_name, "project_id": project_id}, ensure_ascii=False, indent=2) + "\n"
        if args.preview:
            changed += int(not (folder / "project.json").exists())
        else:
            changed += write_if_changed(folder / "project.json", meta)
        if project:
            copied, skipped = copy_source(project, folder / "源码", args.preview); source_copied += copied; source_skipped += skipped
        for session in group:
            content = session_markdown(session)
            if not content: continue
            stamp = re.sub(r"\D", "", session.updated_at)[:8] or "unknown"
            stem = f"{stamp}-{safe_name(session.title)}-{session.session_id[:8]}"
            for index, offset in enumerate(range(0, len(content), MAX_PART_CHARS), 1):
                target = folder / "对话" / f"{stem}-{index:03d}.md"; part = content[offset:offset + MAX_PART_CHARS]
                if args.preview: changed += int(not target.exists() or target.read_text(encoding="utf-8", errors="replace") != part)
                else: transcript_written += write_if_changed(target, part)
        manifest.append({"product": product, "project_id": project_id, "sessions": len(group)})
    summary = json.dumps({"projects": manifest}, ensure_ascii=False, indent=2) + "\n"
    if not args.preview: changed += write_if_changed(archive / "同步清单.json", summary)
    print(json.dumps({"preview": args.preview, "sessions": len(sessions), "projects": len(groups), "changed_or_new_files": changed + transcript_written + source_copied, "source_files_copied": source_copied, "source_files_rejected": source_skipped}, ensure_ascii=False))
    if args.preview or not args.commit: return 0
    add = git(repo, "add", ARCHIVE_NAME)
    if add.returncode: raise SystemExit(add.stderr)
    if not git(repo, "status", "--porcelain").stdout.strip(): print("No Git changes."); return 0
    commit = git(repo, "-c", "user.name=AI Archive", "-c", "user.email=ai-archive@users.noreply.github.com", "commit", "-m", f"Archive AI conversations {datetime.now().date().isoformat()}")
    if commit.returncode: raise SystemExit(commit.stderr or commit.stdout)
    if args.push:
        push = git(repo, "-c", "http.version=HTTP/1.1", "push", "origin", "HEAD:main")
        if push.returncode: raise SystemExit(push.stderr or push.stdout)
    return 0


if __name__ == "__main__": raise SystemExit(main())
