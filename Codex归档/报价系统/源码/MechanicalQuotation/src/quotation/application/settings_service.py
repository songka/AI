"""Safe user-settings management for the desktop application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quotation.application.cache_sync_service import CacheSyncService
from quotation.application.runtime_paths import (
    DEFAULT_DATABASE_ADDRESS,
    resolve_database_address,
)
from quotation.infrastructure.dwg.converter import (
    DEFAULT_SETTINGS_PATH,
    PORTABLE_SETTINGS_PATH,
    DwgConversionService,
)
from quotation.infrastructure.secrets.secret_locator import SecretLocator
from quotation.infrastructure.smb.client import DEFAULT_SMB_ROOT, SmbStorageClient


class UserSettingsService:
    """Read and update non-secret sidecar settings without exposing API keys."""

    def __init__(self, settings_path: str | Path | None = None) -> None:
        self._settings_path = Path(settings_path) if settings_path else self._default_path()

    @staticmethod
    def _default_path() -> Path:
        return PORTABLE_SETTINGS_PATH if PORTABLE_SETTINGS_PATH.exists() else DEFAULT_SETTINGS_PATH

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    def load(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "dwg_converter_path": "",
            "api_host": "127.0.0.1",
            "api_port": 8000,
            "smb_root": DEFAULT_SMB_ROOT,
            "smb_cache_dir": "runtime/cache/smb",
            "smb_sync_enabled": True,
            "smb_sync_interval_seconds": 60,
            "auth_enabled": False,
            "database_address": DEFAULT_DATABASE_ADDRESS,
        }
        if not self._settings_path.is_file():
            return defaults
        try:
            loaded = json.loads(self._settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return defaults
        for key in defaults:
            if key in loaded:
                defaults[key] = loaded[key]
        return defaults

    def save(
        self,
        *,
        dwg_converter_path: str,
        api_host: str,
        api_port: int,
        smb_root: str | None = None,
        smb_cache_dir: str | None = None,
        smb_sync_enabled: bool | None = None,
        smb_sync_interval_seconds: int | None = None,
        auth_enabled: bool | None = None,
        database_address: str | None = None,
    ) -> Path:
        converter = (
            Path(dwg_converter_path.strip().strip('"'))
            if dwg_converter_path.strip()
            else None
        )
        if converter is not None and not converter.is_file():
            raise ValueError("所选 DWG 转换器不存在")
        if converter is not None and converter.name.casefold() != "odafileconverter.exe":
            raise ValueError("请选择 ODAFileConverter.exe")
        if api_host not in {"127.0.0.1", "localhost"}:
            raise ValueError("为保证本机数据安全，接口地址只能使用 127.0.0.1 或 localhost")
        if not 1 <= int(api_port) <= 65535:
            raise ValueError("接口端口必须在 1 到 65535 之间")
        current = self.load()
        shared_root = str(smb_root if smb_root is not None else current["smb_root"]).strip()
        cache_dir = str(
            smb_cache_dir if smb_cache_dir is not None else current["smb_cache_dir"]
        ).strip()
        if not shared_root:
            raise ValueError("SMB 公共槽路径不能为空")
        if not cache_dir:
            raise ValueError("SMB 本地缓存路径不能为空")
        database_value = str(
            database_address
            if database_address is not None
            else current["database_address"]
        ).strip()
        if not database_value:
            raise ValueError("数据库地址不能为空")
        database_path = resolve_database_address(database_value)
        if database_path.exists() and database_path.is_dir():
            raise ValueError("数据库地址应为目录或 .db/.sqlite 文件，不能指向同名文件夹")
        payload = {
            "dwg_converter_path": str(converter) if converter else "",
            "dwg_converter_note": "外部 ODA 转换器路径；第三方程序不包含在本系统中",
            "api_host": api_host,
            "api_port": int(api_port),
            "smb_root": shared_root,
            "smb_auth_type": "current_user",
            "smb_cache_dir": cache_dir,
            "smb_sync_enabled": (
                bool(smb_sync_enabled)
                if smb_sync_enabled is not None
                else bool(current["smb_sync_enabled"])
            ),
            "smb_sync_interval_seconds": int(
                smb_sync_interval_seconds
                if smb_sync_interval_seconds is not None
                else current["smb_sync_interval_seconds"]
            ),
            "auth_enabled": (
                bool(auth_enabled)
                if auth_enabled is not None
                else bool(current["auth_enabled"])
            ),
            "database_address": database_value,
        }
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._settings_path.with_suffix(self._settings_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self._settings_path)
        return self._settings_path

    def status(self) -> dict[str, Any]:
        settings = self.load()
        sync = CacheSyncService(
            SmbStorageClient(settings["smb_root"]), settings["smb_cache_dir"]
        )
        return {
            "settings": settings,
            "settings_path": str(self._settings_path),
            "converter": DwgConversionService().health(),
            "ai_configured": SecretLocator.is_configured(),
            "shared_storage": sync.health(),
            "database": {
                "address": settings["database_address"],
                "resolved_path": str(resolve_database_address(settings["database_address"])),
                "exists": resolve_database_address(settings["database_address"]).is_file(),
            },
        }

    def sync_shared_storage(self) -> dict[str, Any]:
        settings = self.load()
        if not settings["smb_sync_enabled"]:
            raise ValueError("SMB 自动同步已停用")
        service = CacheSyncService(
            SmbStorageClient(settings["smb_root"]), settings["smb_cache_dir"]
        )
        return service.sync().to_dict()

    def shared_storage_service(self) -> CacheSyncService:
        settings = self.load()
        return CacheSyncService(
            SmbStorageClient(settings["smb_root"]), settings["smb_cache_dir"]
        )
