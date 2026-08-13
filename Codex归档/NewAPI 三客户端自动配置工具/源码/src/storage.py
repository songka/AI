from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import keyring

from .models import ScanCache

APP_NAME = "NewAPIClientConfigurator"
TOKEN_KEY = "gateway-token"
BACKUP_TOKEN_PREFIX = "backup-token-"
BACKUP_ENV = ("NEWAPI_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_MODEL", "ANTHROPIC_SMALL_FAST_MODEL", "OPENCODE_CONFIG")


def app_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home())) / ".newapi-configurator"
    base.mkdir(parents=True, exist_ok=True)
    return base


def opencode_config_path() -> Path:
    """OpenCode's official per-user global configuration location."""
    path = Path.home() / ".config" / "opencode"
    path.mkdir(parents=True, exist_ok=True)
    return path / "opencode.json"


def cache_path() -> Path:
    return app_dir() / "model_capabilities.json"


def save_cache(cache: ScanCache) -> None:
    cache_path().write_text(cache.model_dump_json(indent=2), encoding="utf-8")


def load_cache() -> ScanCache | None:
    try:
        return ScanCache.model_validate_json(cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def save_token(token: str) -> None:
    keyring.set_password(APP_NAME, TOKEN_KEY, token)


def load_token() -> str:
    try:
        return keyring.get_password(APP_NAME, TOKEN_KEY) or ""
    except keyring.errors.KeyringError:
        return ""


def backup_root() -> Path:
    path = app_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _environment_value(name: str) -> str | None:
    if os.name != "nt":
        return os.environ.get(name)
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except FileNotFoundError:
        return None


def _set_environment_value(name: str, value: str | None) -> None:
    if os.name != "nt":
        if value is None: os.environ.pop(name, None)
        else: os.environ[name] = value
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        if value is None:
            try: winreg.DeleteValue(key, name)
            except FileNotFoundError: pass
        else:
            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)


def create_backup() -> Path:
    """Save file and user-environment state before any configuration write.

    The manifest intentionally excludes secret values. Auth tokens are saved in
    Credential Manager under a unique backup key instead.
    """
    backup_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    folder = backup_root() / backup_id
    folder.mkdir()
    files: dict[str, dict[str, Any]] = {}
    tracked = {
        "codex": Path.home() / ".codex" / "config.toml",
        "claude": Path.home() / ".claude" / "settings.json",
        "opencode": opencode_config_path(),
    }
    for name, source in tracked.items():
        target = folder / f"{name}{source.suffix}.bak"
        if source.exists():
            shutil.copy2(source, target)
            files[name] = {"path": str(source), "backup": target.name, "existed": True}
        else:
            files[name] = {"path": str(source), "backup": None, "existed": False}
    environment: dict[str, bool] = {}
    for name in BACKUP_ENV:
        value = _environment_value(name)
        environment[name] = value is not None
        if name in {"NEWAPI_API_KEY", "ANTHROPIC_AUTH_TOKEN"} and value is not None:
            keyring.set_password(APP_NAME, f"{BACKUP_TOKEN_PREFIX}{backup_id}-{name}", value)
        elif value is not None:
            (folder / f"env-{name}.txt").write_text(value, encoding="utf-8")
    (folder / "manifest.json").write_text(json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "files": files, "environment": environment}, ensure_ascii=False, indent=2), encoding="utf-8")
    return folder


def list_backups() -> list[Path]:
    return sorted((path for path in backup_root().iterdir() if path.is_dir() and (path / "manifest.json").exists()), reverse=True)


def restore_backup(folder: Path) -> None:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"].values():
        target = Path(entry["path"])
        if entry["existed"]:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(folder / entry["backup"], target)
        elif target.exists():
            target.unlink()
    backup_id = folder.name
    for name, existed in manifest["environment"].items():
        if not existed:
            _set_environment_value(name, None)
        elif name in {"NEWAPI_API_KEY", "ANTHROPIC_AUTH_TOKEN"}:
            value = keyring.get_password(APP_NAME, f"{BACKUP_TOKEN_PREFIX}{backup_id}-{name}")
            if value is None:
                raise RuntimeError(f"备份中的凭据项不可用：{name}")
            _set_environment_value(name, value)
        else:
            _set_environment_value(name, (folder / f"env-{name}.txt").read_text(encoding="utf-8"))
