# -*- coding: utf-8 -*-
"""Promote a reviewed company-price draft and activate its immutable snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from quotation.application.price_publication import (
    build_current_version_pointer,
    prepare_published_pricebook,
)


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as target:
        json.dump(payload, target, ensure_ascii=False, indent=2)
        target.write("\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--import-package", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--pointer", type=Path, required=True)
    parser.add_argument("--price-version-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--approved-by", required=True)
    args = parser.parse_args()

    now = datetime.now(timezone.utc).isoformat()
    snapshot = prepare_published_pricebook(
        _read_json(args.draft),
        _read_json(args.import_package),
        price_version_id=args.price_version_id,
        version=args.version,
        approved_by=args.approved_by,
        approved_at=now,
    )
    pointer = build_current_version_pointer(
        snapshot,
        snapshot_path=args.snapshot.name,
        activated_by=args.approved_by,
        activated_at=now,
    )
    args.snapshot.parent.mkdir(parents=True, exist_ok=True)
    _write_json(args.snapshot, snapshot)
    _write_json(args.pointer, pointer)
    print(
        f"Published {snapshot['price_version_id']}: "
        f"{snapshot['record_count']} records, SHA256={snapshot['snapshot_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
