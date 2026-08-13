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
