"""Resolve configurable runtime paths for source and portable deployments."""

from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_DATABASE_ADDRESS = "runtime/data/quotation_history.db"


def runtime_root() -> Path:
    """Return the application root without depending on the current directory."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    current = Path.cwd().resolve()
    for _ in range(6):
        if (current / "pyproject.toml").is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path.cwd().resolve()


def resolve_database_address(address: str | Path | None = None) -> Path:
    """Resolve a database file from a local/shared directory or explicit DB file."""

    raw = str(address or DEFAULT_DATABASE_ADDRESS).strip().strip('"')
    if not raw:
        raw = DEFAULT_DATABASE_ADDRESS
    expanded = os.path.expandvars(os.path.expanduser(raw))
    path = Path(expanded)
    if not path.is_absolute():
        path = runtime_root() / path
    if path.suffix.casefold() not in {".db", ".sqlite", ".sqlite3"}:
        path = path / "quotation_history.db"
    return path


def is_shared_database(path: str | Path) -> bool:
    """Return whether the resolved path is a Windows UNC/network path."""

    return str(path).startswith("\\\\")
