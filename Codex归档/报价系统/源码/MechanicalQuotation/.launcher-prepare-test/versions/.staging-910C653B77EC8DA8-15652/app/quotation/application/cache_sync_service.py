"""Synchronize published SMB documents to a safe local read cache."""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from quotation.infrastructure.smb.client import SmbStorageClient


class SyncStatus(str, Enum):
    ONLINE = "online"
    ONLINE_SYNCING = "syncing"
    OFFLINE_CACHE = "offline_cache"
    SYNC_ERROR = "sync_error"


@dataclass(frozen=True)
class SyncResult:
    status: SyncStatus
    changed_files: int
    total_files: int
    using_cache: bool
    last_sync: str | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "changed_files": self.changed_files,
            "total_files": self.total_files,
            "using_cache": self.using_cache,
            "last_sync": self.last_sync,
            "error": self.error,
        }


class CacheSyncService:
    """Copy versioned public data locally; never write into published data."""

    RESOURCE_ROOTS = (
        "data",
        "rules/published",
        "prices/published",
        "suppliers",
        "templates",
    )

    def __init__(self, client: SmbStorageClient, cache_dir: str | Path) -> None:
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.manifest_path = self.cache_dir / "cache-manifest.json"
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start_background(
        self, interval_seconds: int = 60, *, sync_immediately: bool = False
    ) -> None:
        """Periodically refresh the cache without blocking quotation work."""

        if self._thread is not None and self._thread.is_alive():
            return
        interval = max(int(interval_seconds), 5)
        self._stop_event.clear()

        def worker() -> None:
            if sync_immediately and not self._stop_event.is_set():
                self.sync()
            while not self._stop_event.wait(interval):
                self.sync()

        self._thread = threading.Thread(
            target=worker, name="quotation-smb-sync", daemon=True
        )
        self._thread.start()

    def stop_background(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def sync(self) -> SyncResult:
        health = self.client.health()
        manifest = self._read_manifest()
        if not health["available"]:
            return SyncResult(
                status=SyncStatus.OFFLINE_CACHE,
                changed_files=0,
                total_files=len(manifest.get("files", {})),
                using_cache=bool(manifest.get("files")),
                last_sync=manifest.get("last_sync"),
                error=health["error"],
            )

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            previous = manifest.get("files", {})
            current: dict[str, dict[str, str]] = {}
            changed = 0
            synced_at = datetime.now(timezone.utc).isoformat()
            for source, relative in self._iter_remote_files():
                digest = self._sha256(source)
                key = relative.as_posix()
                current[key] = {"sha256": digest, "cached_at": synced_at}
                if previous.get(key, {}).get("sha256") == digest:
                    current[key]["cached_at"] = previous[key]["cached_at"]
                    continue
                target = self.cache_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.tmp")
                shutil.copy2(source, temporary)
                temporary.replace(target)
                changed += 1

            payload = {
                "cache_version": int(manifest.get("cache_version", 0)) + 1,
                "source_root": str(self.client.root),
                "last_sync": synced_at,
                "files": current,
            }
            self._write_manifest(payload)
            return SyncResult(
                status=SyncStatus.ONLINE,
                changed_files=changed,
                total_files=len(current),
                using_cache=False,
                last_sync=synced_at,
            )
        except (OSError, ValueError) as exc:
            return SyncResult(
                status=SyncStatus.SYNC_ERROR,
                changed_files=0,
                total_files=len(manifest.get("files", {})),
                using_cache=bool(manifest.get("files")),
                last_sync=manifest.get("last_sync"),
                error=f"SMB 同步失败：{exc}",
            )

    def health(self) -> dict[str, Any]:
        manifest = self._read_manifest()
        return {
            "smb": self.client.health(),
            "cache_dir": str(self.cache_dir),
            "cache_available": bool(manifest.get("files")),
            "cached_files": len(manifest.get("files", {})),
            "last_sync": manifest.get("last_sync"),
        }

    def _iter_remote_files(self):
        for relative_root in self.RESOURCE_ROOTS:
            root = self.client.resolve(relative_root)
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if path.is_file() and not path.name.startswith("."):
                    yield path, path.relative_to(self.client.root)

    def _read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            return {}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}

    def _write_manifest(self, payload: dict[str, Any]) -> None:
        temporary = self.manifest_path.with_name(".cache-manifest.json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.manifest_path)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
