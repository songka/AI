"""Runtime wiring for encrypted SMB users and the local offline cache."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from quotation.application.auth_service import AuthService
from quotation.application.settings_service import UserSettingsService
from quotation.domain.user import User
from quotation.infrastructure.auth.encrypted_user_store import EncryptedUserStore
from quotation.infrastructure.secrets.secret_locator import SecretLocator


class MirroredEncryptedUserStore:
    """Use the SMB user document when available and keep an encrypted cache."""

    def __init__(self, primary_path: str | Path, cache_path: str | Path, key: str) -> None:
        self.primary = EncryptedUserStore(primary_path, key)
        self.cache = EncryptedUserStore(cache_path, key)
        self.last_source = "none"

    @property
    def path(self) -> Path:
        return self.primary.path

    def load(self):
        if _is_file(self.primary.path):
            users = self.primary.load()
            self._refresh_cache()
            self.last_source = "smb"
            return users
        if _is_file(self.cache.path):
            self.last_source = "cache"
            return self.cache.load()
        self.last_source = "none"
        return []

    def save(self, users):
        try:
            target = self.primary.save(users)
            self._refresh_cache()
            self.last_source = "smb"
            return target
        except OSError:
            self.last_source = "cache"
            return self.cache.save(users)

    def _refresh_cache(self) -> None:
        self.cache.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache.path.with_suffix(self.cache.path.suffix + ".tmp")
        shutil.copyfile(self.primary.path, temporary)
        temporary.replace(self.cache.path)


class AuthRuntime:
    """Build authentication services from non-secret settings and a local secret."""

    def __init__(self, settings_service: UserSettingsService | None = None) -> None:
        self.settings_service = settings_service or UserSettingsService()

    def paths(self) -> tuple[Path, Path]:
        settings = self.settings_service.load()
        primary = Path(settings["smb_root"]) / "data" / "users.json"
        cache = Path(settings["smb_cache_dir"]) / "data" / "users.json"
        return primary, cache

    def status(self) -> dict[str, Any]:
        primary, cache = self.paths()
        settings = self.settings_service.load()
        key = SecretLocator.get_user_store_key()
        primary_exists = _is_file(primary)
        cache_exists = _is_file(cache)
        storage_available = _is_dir(primary.parent)
        return {
            "auth_enabled": bool(settings.get("auth_enabled", False)),
            "configured": bool(key),
            "user_store_exists": primary_exists or cache_exists,
            "smb_storage_available": storage_available,
            "smb_user_store_available": primary_exists,
            "cache_user_store_available": cache_exists,
            "setup_required": storage_available and not primary_exists and not cache_exists,
        }

    def build_service(self, key: str | None = None) -> AuthService:
        actual_key = key or SecretLocator.get_user_store_key()
        if not actual_key:
            raise RuntimeError("尚未配置用户资料加密口令")
        primary, cache = self.paths()
        store = MirroredEncryptedUserStore(primary, cache, actual_key)
        resource_root = (
            Path(sys._MEIPASS)
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parents[3]
        )
        return AuthService(  # type: ignore[arg-type]
            store,
            roles_path=resource_root / "config" / "roles.yaml",
            permissions_path=resource_root / "config" / "permissions.yaml",
        )

    def initialize_admin(
        self,
        *,
        encryption_key: str,
        username: str,
        password: str,
        display_name: str,
    ):
        status = self.status()
        if status["user_store_exists"]:
            raise ValueError("用户库已经初始化，不能覆盖现有用户")
        if not status["smb_storage_available"]:
            raise OSError("SMB 公共用户资料目录不可用，不能建立独立的本地管理员")
        service = self.build_service(encryption_key)
        user = service.create_initial_admin(username, password, display_name)
        SecretLocator.save_user_store_key(encryption_key)
        return user

    def configure_existing_key(self, encryption_key: str) -> AuthService:
        """Validate a key against the existing encrypted store before saving it."""

        service = self.build_service(encryption_key)
        if not service.store.load():
            raise ValueError("用户库为空，不能作为现有用户库接入")
        SecretLocator.save_user_store_key(encryption_key)
        return service

    def recover_initial_admin(
        self, *, encryption_key: str, username: str, new_password: str
    ) -> tuple[AuthService, User]:
        """Recover only an unclaimed bootstrap admin after decrypting the user store."""

        service = self.build_service(encryption_key)
        user = service.recover_initial_admin_password(username, new_password)
        SecretLocator.save_user_store_key(encryption_key)
        return service, user


def _is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def _is_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except OSError:
        return False
