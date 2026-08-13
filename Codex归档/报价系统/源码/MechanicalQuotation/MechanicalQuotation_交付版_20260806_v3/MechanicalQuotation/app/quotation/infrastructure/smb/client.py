"""Safe filesystem access to the quotation system's SMB public slot."""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SMB_ROOT = (
    r"\\10.97.0.210\lfaf_Engineer\Mechanical\3-標準文檔"
    r"\10-自動報價系統\data"
)

PUBLIC_DIRECTORIES = (
    "data",
    "rules/draft",
    "rules/published",
    "rules/archive",
    "prices/draft",
    "prices/published",
    "prices/archive",
    "history",
    "audit",
    "change-requests",
    "logs",
    "templates",
    "suppliers",
    "suppliers/prices",
)


def load_shared_storage_settings(
    settings_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load non-secret SMB options with environment overrides."""

    options: dict[str, Any] = {
        "smb_root": DEFAULT_SMB_ROOT,
        "smb_cache_dir": "runtime/cache/smb",
        "smb_sync_enabled": True,
    }
    candidates = (
        (Path(settings_path),)
        if settings_path is not None
        else (
            Path("config/user_settings.json"),
            Path("runtime/config/user_settings.json"),
        )
    )
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            loaded = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        for key in options:
            if key in loaded:
                options[key] = loaded[key]
        break
    if os.getenv("MECHANICAL_QUOTATION_SMB_ROOT"):
        options["smb_root"] = os.environ["MECHANICAL_QUOTATION_SMB_ROOT"]
    if os.getenv("MECHANICAL_QUOTATION_SMB_CACHE_DIR"):
        options["smb_cache_dir"] = os.environ["MECHANICAL_QUOTATION_SMB_CACHE_DIR"]
    return options


def cached_public_path(relative_path: str | Path, fallback: str | Path) -> Path:
    """Return a synchronized public file when enabled, otherwise its bundled fallback."""

    options = load_shared_storage_settings()
    cached = Path(str(options["smb_cache_dir"])) / Path(relative_path)
    if bool(options["smb_sync_enabled"]) and cached.is_file():
        return cached
    return Path(fallback)


class SmbStorageClient:
    """Treat an SMB share as a constrained document store.

    Authentication is intentionally delegated to the current Windows user. No
    SMB credentials are stored by this application.
    """

    def __init__(self, root: str | Path = DEFAULT_SMB_ROOT) -> None:
        self.root = Path(root)

    def resolve(self, relative_path: str | Path) -> Path:
        """Resolve a path while preventing access outside the public slot."""

        relative = Path(relative_path)
        if relative.is_absolute() or relative.anchor or ".." in relative.parts:
            raise ValueError("路径必须位于报价系统 SMB 公共槽内")
        if not relative.parts:
            raise ValueError("公共槽相对路径不能为空")
        return self.root.joinpath(*relative.parts)

    def health(self) -> dict[str, Any]:
        """Return a non-mutating connectivity check."""

        started = time.perf_counter()
        error: str | None = None
        try:
            available = self.root.is_dir()
            if available:
                next(self.root.iterdir(), None)
            else:
                error = "SMB 公共槽不存在或当前 Windows 用户无权访问"
        except OSError as exc:
            available = False
            error = f"SMB 公共槽访问失败：{exc}"
        return {
            "configured": bool(str(self.root)),
            "available": available,
            "root": str(self.root),
            "auth_type": "current_user",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": error,
        }

    def initialize_layout(self) -> dict[str, Any]:
        """Create the approved public directory structure without overwriting data."""

        self.root.mkdir(parents=True, exist_ok=True)
        for relative in PUBLIC_DIRECTORIES:
            self.resolve(relative).mkdir(parents=True, exist_ok=True)
        manifest_path = self.resolve("system-manifest.json")
        if not manifest_path.exists():
            self.write_json_atomic(
                "system-manifest.json",
                {
                    "schema_version": 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "storage_role": "SMB_DOCUMENT_STORE_ONLY",
                    "auth_type": "current_user",
                },
            )
        return self.health()

    def write_json_atomic(self, relative_path: str | Path, payload: dict[str, Any]) -> Path:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(target)
        return target

    def write_text_atomic(self, relative_path: str | Path, content: str) -> Path:
        """Atomically replace a UTF-8 text control file inside the public slot."""

        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
        return target

    def copy_atomic(
        self,
        source: str | Path,
        relative_destination: str | Path,
        *,
        overwrite: bool = False,
    ) -> bool:
        """Copy one file into the public slot and avoid partial published files."""

        source_path = Path(source)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        target = self.resolve(relative_destination)
        if target.exists() and not overwrite:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        shutil.copy2(source_path, temporary)
        temporary.replace(target)
        return True

    def bootstrap_published_data(
        self, project_root: str | Path, *, overwrite: bool = False
    ) -> dict[str, Any]:
        """Place the current approved rules and prices in an initialized slot."""

        project = Path(project_root)
        pointer = json.loads(
            (project / "data" / "current-version-pointer.json").read_text(encoding="utf-8")
        )
        mappings = {
            project / "rules" / "quotation-rules.yaml": (
                "rules/published/quotation-rules.yaml"
            ),
            project / "data" / "current-version-pointer.json": (
                "prices/published/current-version-pointer.json"
            ),
            project / "data" / pointer["snapshot_path"]: (
                f"prices/published/{Path(pointer['snapshot_path']).name}"
            ),
            project / "data" / "feature-price-calibration-gcs-v1.0.json": (
                "prices/published/feature-price-calibration-gcs-v1.0.json"
            ),
            project
            / "rules"
            / "imports"
            / "r01-v1.0"
            / "pricing-rules-excel-r01-v1.0.json": (
                "prices/published/pricing-source-records-r01-v1.0.json"
            ),
        }
        self.initialize_layout()
        copied: list[str] = []
        skipped: list[str] = []
        for source, destination in mappings.items():
            if self.copy_atomic(source, destination, overwrite=overwrite):
                copied.append(destination)
            else:
                skipped.append(destination)
        version = str(pointer.get("current_version") or "UNKNOWN")
        version_path = self.resolve("prices/published/version.txt")
        if overwrite or not version_path.exists():
            temporary = version_path.with_name(".version.txt.tmp")
            temporary.write_text(version + "\n", encoding="utf-8")
            temporary.replace(version_path)
            copied.append("prices/published/version.txt")
        else:
            skipped.append("prices/published/version.txt")
        return {
            "root": str(self.root),
            "price_version": version,
            "copied": copied,
            "skipped_existing": skipped,
        }
