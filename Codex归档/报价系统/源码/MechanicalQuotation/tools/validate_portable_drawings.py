#!/usr/bin/env python
"""Validate external DWG/PDF pairs using the packaged Python runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from quotation.application.file_scanner import FileScanner
from quotation.application.quotation_service import QuotationApplicationService
from quotation.infrastructure.dwg.converter import DwgConversionService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--drawing", action="append", default=[])
    args = parser.parse_args()

    bundles = FileScanner().scan_directory(args.directory, recursive=False)
    requested = {item.casefold() for item in args.drawing}
    if requested:
        bundles = [bundle for bundle in bundles if bundle.drawing_number.casefold() in requested]
    results = QuotationApplicationService().quote_batch(bundles, use_ai=False)
    payload = {
        "converter_health": DwgConversionService().health(),
        "results": [
            {
                "drawing_number": result.drawing_number,
                "files": [item.file_name for item in result.bundle.files],
                "status": result.status,
                "errors": result.errors,
                "warnings": result.warnings,
                "dwg_conversion": result.dwg_conversion,
                "supplementary_analysis": result.supplementary_analysis,
            }
            for result in results
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if results and all(item.status == "COMPLETE" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
