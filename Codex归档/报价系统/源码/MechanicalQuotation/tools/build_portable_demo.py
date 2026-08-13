#!/usr/bin/env python
"""Build portable demo distribution.

Usage:
    .venv/Scripts/python tools/build_portable_demo.py

Creates dist/MechanicalQuotation/ with all runtime files needed.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    dist_dir = project_root / "dist" / "MechanicalQuotation"

    print("=" * 60)
    print("Building portable demo distribution...")
    print(f"  Source: {project_root}")
    print(f"  Target: {dist_dir}")
    print("=" * 60)

    # Clean dist
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)

    # Copy runtime secrets
    secrets_src = project_root / "runtime" / "secrets"
    secrets_dst = dist_dir / "runtime" / "secrets"
    if secrets_src.exists():
        shutil.copytree(secrets_src, secrets_dst)
        print("  [OK] Runtime secrets copied")
    else:
        secrets_dst.mkdir(parents=True)
        (secrets_dst / ".gitkeep").touch()
        print("  [WARN] No runtime secrets found — AI will be disabled")

    # Copy rules
    rules_dst = dist_dir / "rules"
    shutil.copytree(project_root / "rules", rules_dst)
    print("  [OK] Rules copied")

    # Copy data
    data_dst = dist_dir / "data"
    shutil.copytree(project_root / "data", data_dst)
    print("  [OK] Data copied")

    # Copy config
    config_dst = dist_dir / "config"
    if (project_root / "config").exists():
        shutil.copytree(project_root / "config", config_dst)
        print("  [OK] Config copied")

    # Create exports dir
    (dist_dir / "exports").mkdir(exist_ok=True)
    print("  [OK] Exports directory created")

    # Create start scripts
    _write_bat(dist_dir / "start_ui.bat", [
        "@echo off",
        "title Mechanical Quotation System - Demo UI",
        "echo Starting Mechanical Quotation Demo UI...",
        f'cd /d "{dist_dir}"',
        "echo.",
        "echo NOTE: This is a portable demo package.",
        "echo To run, install Python with dependencies:",
        "echo   pip install ezdxf click pydantic httpx fastapi uvicorn openpyxl python-multipart",
        "echo.",
        "echo Then run:",
        "echo   python -m quotation.launcher --ui",
        "echo.",
        "pause",
    ])

    _write_bat(dist_dir / "start_api.bat", [
        "@echo off",
        "title Mechanical Quotation System - REST API",
        "echo Starting Mechanical Quotation REST API...",
        f'cd /d "{dist_dir}"',
        "echo.",
        "echo NOTE: This is a portable demo package.",
        "echo To run, install Python with dependencies:",
        "echo   pip install ezdxf click pydantic httpx fastapi uvicorn openpyxl python-multipart",
        "echo.",
        "echo Then run:",
        "echo   python -m quotation.launcher --api",
        "echo   Swagger: http://127.0.0.1:8000/docs",
        "echo.",
        "pause",
    ])

    print("  [OK] Start scripts created")

    # Check PyInstaller
    pyinstaller_ok = False
    try:
        import PyInstaller
        pyinstaller_ok = True
    except ImportError:
        pass

    if pyinstaller_ok:
        print("\n  [INFO] PyInstaller available — run 'pyinstaller' separately for EXE build")
    else:
        print("\n  [WARN] PyInstaller not installed. EXE packaging skipped.")
        print("    Install with: pip install pyinstaller")
        print("    Then run: pyinstaller --onedir --name MechanicalQuotation src/quotation/launcher.py")

    print(f"\n  Portable demo built at: {dist_dir}")
    print("=" * 60)


def _write_bat(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
