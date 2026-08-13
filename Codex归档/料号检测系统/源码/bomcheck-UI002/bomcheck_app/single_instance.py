from __future__ import annotations

import os
import tempfile
from pathlib import Path

import portalocker


class AlreadyRunningError(RuntimeError):
    pass


class SingleInstanceLock:
    def __init__(self, name: str) -> None:
        self.name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name)
        self.path = self._lock_dir() / f"{self.name}.lock"
        self._handle = None

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+", encoding="utf-8")
        try:
            portalocker.lock(handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except portalocker.exceptions.LockException as exc:
            handle.close()
            raise AlreadyRunningError(f"{self.name} is already running") from exc
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        self._handle = handle

    def release(self) -> None:
        if not self._handle:
            return
        try:
            portalocker.unlock(self._handle)
        finally:
            self._handle.close()
            self._handle = None

    @staticmethod
    def _lock_dir() -> Path:
        root = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        return Path(root) / "BOMCheck" / "locks"
