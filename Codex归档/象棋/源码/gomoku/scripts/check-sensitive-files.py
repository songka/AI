from __future__ import annotations

import argparse
import re
from pathlib import Path


FORBIDDEN_FILE_PARTS = (
    ".env",
    "credentials",
    "password",
    "passwd",
    "secret",
    "token",
)
FORBIDDEN_SUFFIXES = (".key", ".pem", ".pfx", ".p12", ".log", ".pyc")
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "packages"}


def credential_patterns() -> tuple[re.Pattern[str], ...]:
    names = ("api" + "_key", "access" + "_token", "password", "client" + "_secret")
    assignment = re.compile(
        rf"(?i)\b(?:{'|'.join(names)})\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{{8,}}"
    )
    private_key = re.compile("-----BEGIN " + "PRIVATE KEY-----")
    return assignment, private_key


def is_forbidden_filename(path: Path) -> bool:
    lower_name = path.name.lower()
    return (
        any(part in lower_name for part in FORBIDDEN_FILE_PARTS)
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
    )


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    patterns = credential_patterns()
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if is_forbidden_filename(path):
            findings.append(f"forbidden filename: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(pattern.search(content) for pattern in patterns):
            findings.append(f"credential-like content: {relative}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()
    findings = [
        f"{root}: {finding}"
        for root in args.roots
        for finding in scan(root.resolve())
    ]
    if findings:
        print("SENSITIVE FILE CHECK FAILED")
        print("\n".join(findings))
        return 1
    print("SENSITIVE FILE CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
