"""Secret management — runtime API key loading.

Never hardcode keys in source. Load from env vars or runtime sidecar files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class SecretLocator:
    """Locates API keys without hardcoding paths.

    Search order:
    1. Environment variable: MECHANICAL_QUOTATION_DEEPSEEK_KEY
    2. Runtime secrets dir (relative to executable or project root):
       runtime/secrets/deepseek_api_key.txt
    """

    ENV_VAR = "MECHANICAL_QUOTATION_DEEPSEEK_KEY"
    SECRET_FILE = "runtime/secrets/deepseek_api_key.txt"
    USER_STORE_ENV_VAR = "MECHANICAL_QUOTATION_USER_STORE_KEY"
    USER_STORE_SECRET_FILE = "runtime/secrets/user_store_key.txt"

    @classmethod
    def get_deepseek_key(cls) -> str | None:
        """Get DeepSeek API key from env var or runtime secret file.

        Returns None if not configured — callers must handle gracefully.
        """
        # 1. Environment variable
        key = os.environ.get(cls.ENV_VAR)
        if key and key.strip():
            return key.strip()

        # 2. Runtime secret file
        secret_path = cls._find_secret_path()
        if secret_path and secret_path.exists():
            content = secret_path.read_text(encoding="utf-8").strip()
            if content:
                return content

        return None

    @classmethod
    def _find_secret_path(cls) -> Path | None:
        """Find the runtime secrets directory."""
        # Check executable directory (PyInstaller mode)
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent
            path = exe_dir / cls.SECRET_FILE
            if path.exists():
                return path

        # Check project root (dev mode) — look for pyproject.toml
        current = Path.cwd()
        for _ in range(5):
            if (current / "pyproject.toml").exists():
                path = current / cls.SECRET_FILE
                if path.exists():
                    return path
            if current.parent == current:
                break
            current = current.parent

        # Fallback: cwd
        path = Path.cwd() / cls.SECRET_FILE
        if path.exists():
            return path

        return None

    @classmethod
    def is_configured(cls) -> bool:
        return cls.get_deepseek_key() is not None

    @classmethod
    def save_deepseek_key(cls, key: str) -> Path:
        """Save a non-empty AI key to the private runtime sidecar file."""

        value = key.strip()
        if not value:
            raise ValueError("Key 文件为空")
        target = cls._runtime_root() / cls.SECRET_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(value, encoding="utf-8")
        temporary.replace(target)
        return target

    @classmethod
    def remove_deepseek_key(cls) -> bool:
        """Remove only the application sidecar key; environment variables remain."""

        target = cls._runtime_root() / cls.SECRET_FILE
        if not target.is_file():
            return False
        target.unlink()
        return True

    @classmethod
    def get_user_store_key(cls) -> str | None:
        """读取用户资料加密口令；绝不从项目配置或 SMB 明文读取。"""

        key = os.environ.get(cls.USER_STORE_ENV_VAR)
        if key and key.strip():
            return key.strip()
        secret_path = cls._find_named_secret_path(cls.USER_STORE_SECRET_FILE)
        if secret_path and secret_path.is_file():
            content = secret_path.read_text(encoding="utf-8").strip()
            return content or None
        return None

    @classmethod
    def save_user_store_key(cls, key: str) -> Path:
        """将用户输入的口令保存到本机受忽略的运行时侧车文件。"""

        if len(key.strip()) < 16:
            raise ValueError("用户资料加密口令至少需要 16 个字符")
        target = cls._runtime_root() / cls.USER_STORE_SECRET_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(key.strip(), encoding="utf-8")
        temporary.replace(target)
        return target

    @classmethod
    def _find_named_secret_path(cls, relative_path: str) -> Path | None:
        if getattr(sys, "frozen", False):
            path = Path(sys.executable).parent / relative_path
            if path.exists():
                return path
        current = Path.cwd()
        for _ in range(5):
            if (current / "pyproject.toml").exists():
                path = current / relative_path
                if path.exists():
                    return path
            if current.parent == current:
                break
            current = current.parent
        path = Path.cwd() / relative_path
        return path if path.exists() else None

    @classmethod
    def _runtime_root(cls) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        current = Path.cwd()
        for _ in range(5):
            if (current / "pyproject.toml").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return Path.cwd()
