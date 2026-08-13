"""Unified launcher for the quotation system.

Usage:
    .venv/Scripts/python -m quotation.launcher --ui
    .venv/Scripts/python -m quotation.launcher --api
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def launch_ui() -> None:
    """Launch the Tkinter demo UI."""
    from quotation.ui.demo_app import main
    main()


def launch_api() -> None:
    """Launch the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "quotation.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="機械加工件智能報價系統 Launcher")
    parser.add_argument(
        "--ui", action="store_true", help="Launch Tkinter demo UI"
    )
    parser.add_argument(
        "--api", action="store_true", help="Launch FastAPI server on 127.0.0.1:8000"
    )
    args = parser.parse_args()

    if args.ui:
        launch_ui()
    elif args.api:
        launch_api()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
