#!/usr/bin/env python
"""Prepare runtime secrets from a source key file.

Usage:
    .venv/Scripts/python tools/prepare_runtime_secrets.py --source "D:\\path\\to\\key.txt"

This tool reads the key, strips whitespace, validates it, and copies it to
runtime/secrets/deepseek_api_key.txt (which is .gitignored).

The source path is NEVER written to any config file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare runtime secrets for the quotation system")
    parser.add_argument(
        "--source", required=True,
        help="Path to the source key file (absolute path, used only once)",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        sys.exit(1)

    # Read key
    try:
        key_content = source_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"ERROR: Failed to read source file: {e}")
        sys.exit(1)

    if not key_content:
        print("ERROR: Key file is empty")
        sys.exit(1)

    # Determine target
    # Find project root (where pyproject.toml is)
    current = Path.cwd()
    for _ in range(5):
        if (current / "pyproject.toml").exists():
            break
        if current.parent == current:
            print("ERROR: Cannot find project root (pyproject.toml)")
            sys.exit(1)
        current = current.parent

    target_dir = current / "runtime" / "secrets"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "deepseek_api_key.txt"

    # Write key
    try:
        target_file.write_text(key_content, encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Failed to write key file: {e}")
        sys.exit(1)

    # Verify
    verify = target_file.read_text(encoding="utf-8").strip()
    if verify != key_content:
        print("ERROR: Key verification failed")
        sys.exit(1)

    print(f"SUCCESS: Key copied to {target_file}")
    print(f"Key length: {len(key_content)} characters")
    print("Key content NOT displayed for security.")


if __name__ == "__main__":
    main()
