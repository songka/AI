"""Unified launcher for the quotation system.

Usage:
    .venv/Scripts/python -m quotation.launcher --ui
    .venv/Scripts/python -m quotation.launcher --api
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any


def _start_shared_sync() -> Any:
    """Refresh shared published data once, then keep a daemon refresh loop."""

    from quotation.application.settings_service import UserSettingsService

    settings_service = UserSettingsService()
    settings = settings_service.load()
    if not settings.get("smb_sync_enabled", True):
        return None
    service = settings_service.shared_storage_service()
    service.sync()
    service.start_background(int(settings.get("smb_sync_interval_seconds", 60)))
    return service


def launch_ui() -> None:
    """Launch the Tkinter demo UI."""
    from quotation.ui.demo_app import main

    sync = _start_shared_sync()
    try:
        main()
    finally:
        if sync is not None:
            sync.stop_background()


def launch_api() -> None:
    """Launch the FastAPI server."""
    import uvicorn

    from quotation.api.main import app

    sync = _start_shared_sync()
    pid_path = Path("runtime/api.pid")
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(os.getpid()), encoding="ascii")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
    finally:
        pid_path.unlink(missing_ok=True)
        if sync is not None:
            sync.stop_background()


def main() -> None:
    parser = argparse.ArgumentParser(description="機械加工件智能報價系統 Launcher")
    parser.add_argument(
        "--ui", action="store_true", help="Launch Tkinter demo UI"
    )
    parser.add_argument(
        "--api", action="store_true", help="Launch FastAPI server on 127.0.0.1:8000"
    )
    parser.add_argument("--self-check", action="store_true", help="Run portable package checks")
    parser.add_argument("--smoke", action="store_true", help="Run headless packaged demo smoke")
    args = parser.parse_args()

    if args.ui:
        launch_ui()
    elif args.api:
        launch_api()
    elif args.self_check:
        from quotation.portable_checks import run_self_check
        raise SystemExit(run_self_check())
    elif args.smoke:
        from quotation.portable_checks import run_smoke
        raise SystemExit(run_smoke())
    else:
        # Windows users normally start the portable app by double-clicking the
        # executable, which supplies no arguments.  Treat that as the primary UI
        # entry point instead of printing help and immediately closing the console.
        launch_ui()


if __name__ == "__main__":
    main()
