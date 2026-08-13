"""Initialize the approved SMB public slot and publish current read-only data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from quotation.infrastructure.smb.client import DEFAULT_SMB_ROOT, SmbStorageClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化机械报价系统 SMB 公共资料槽")
    parser.add_argument("--root", default=DEFAULT_SMB_ROOT, help="SMB 公共槽根路径")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖同名已发布资料；默认保护公共槽中的现有文件",
    )
    args = parser.parse_args()
    client = SmbStorageClient(args.root)
    result = client.bootstrap_published_data(PROJECT_ROOT, overwrite=args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
