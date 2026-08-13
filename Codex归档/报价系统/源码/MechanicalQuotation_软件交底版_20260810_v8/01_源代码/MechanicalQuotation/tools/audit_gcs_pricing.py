"""Audit GCS drawing quotations against the approved BOM unit costs.

The script is deliberately read-only for its BOM and drawing inputs.  It writes
the reproducible audit result under ``runtime/price-audit`` by default.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openpyxl

from quotation.application.quotation_service import QuotationApplicationService
from quotation.application.validation_metrics import calculate_accuracy_metrics

ITEM_RE = re.compile(r"^(UC\d+)", re.IGNORECASE)
DRAWING_SUFFIXES = {".dwg", ".dxf"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).replace("\xa0", " ").strip()


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _reference_amount(value: Any) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", _text(value))
    return float(match.group(0)) if match else None


def load_machining_rows(bom_path: Path) -> list[dict[str, Any]]:
    workbook = openpyxl.load_workbook(bom_path, read_only=True, data_only=True)
    sheet = workbook.active
    rows: list[dict[str, Any]] = []
    for row_number, values in enumerate(sheet.iter_rows(values_only=True), start=1):
        cells = [_text(value) for value in values]
        if len(cells) < 9:
            continue
        match = ITEM_RE.match(cells[1])
        description = " ".join(value for value in cells[2:4] if value)
        if not match or "加工件" not in description:
            continue
        rows.append(
            {
                "source_row": row_number,
                "level": cells[0],
                "item": match.group(1).upper(),
                "description": description,
                "uom": cells[5],
                "quantity": _number(values[6]),
                "historical_price": _number(values[7]),
                "historical_extended": _number(values[8]),
                "remark": cells[9] if len(cells) > 9 else "",
            }
        )
    return rows


def index_drawings(root: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in DRAWING_SUFFIXES:
            continue
        match = ITEM_RE.match(path.name)
        if match:
            result[match.group(1).upper()].append(path)
    return result


def choose_drawing(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return sorted(
        paths, key=lambda path: (path.suffix.lower() != ".dwg", len(str(path)), str(path))
    )[0]


def audit(bom_path: Path, drawings_root: Path, run_quotes: bool) -> dict[str, Any]:
    rows = load_machining_rows(bom_path)
    drawing_index = index_drawings(drawings_root)
    unique: dict[str, dict[str, Any]] = {}
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    conflicts: list[dict[str, Any]] = []
    for row in rows:
        occurrences[row["item"]].append(row)
        previous = unique.setdefault(row["item"], row)
        if previous["historical_price"] != row["historical_price"]:
            conflicts.append(
                {
                    "item": row["item"],
                    "first_row": previous["source_row"],
                    "first_price": previous["historical_price"],
                    "other_row": row["source_row"],
                    "other_price": row["historical_price"],
                }
            )

    service = QuotationApplicationService() if run_quotes else None
    cases: list[dict[str, Any]] = []
    for item, source in sorted(unique.items()):
        drawing = choose_drawing(drawing_index.get(item, []))
        case = dict(source)
        case.update(
            {
                "occurrence_count": len(occurrences[item]),
                "drawing_path": str(drawing) if drawing else None,
                "system_price": None,
                "feature_reference_price": None,
                "status": "NO_DRAWING" if drawing is None else "NOT_RUN",
                "absolute_error": None,
                "deviation_pct": None,
                "feature_reference_absolute_error": None,
                "feature_reference_deviation_pct": None,
                "source_summary": {},
                "quote_items": [],
                "warnings": [],
                "errors": [],
            }
        )
        if service is not None and drawing is not None:
            result = service.quote_single_file(drawing)
            case["status"] = getattr(result.status, "value", str(result.status))
            case["warnings"] = result.warnings
            case["errors"] = result.errors
            if result.quote is not None:
                actual = source["historical_price"]
                system = result.quote.total
                case["system_price"] = round(system, 2)
                case["absolute_error"] = round(abs(system - actual), 2)
                case["deviation_pct"] = (
                    round((system - actual) / actual * 100, 2) if actual else None
                )
                case["source_summary"] = result.quote.source_summary
                calibrated_items = [
                    quote_item
                    for quote_item in result.quote.items
                    if quote_item.resolution_source == "FEATURE_CALIBRATION_MODEL"
                ]
                feature_reference = (
                    calibrated_items[0].amount
                    if calibrated_items
                    else _reference_amount(
                        result.feature_summary.get("feature_calibration_reference")
                    )
                )
                if feature_reference is not None:
                    case["feature_reference_price"] = round(feature_reference, 2)
                    case["feature_reference_absolute_error"] = round(
                        abs(feature_reference - actual), 2
                    )
                    case["feature_reference_deviation_pct"] = (
                        round((feature_reference - actual) / actual * 100, 2)
                        if actual
                        else None
                    )
                case["quote_items"] = [
                    {
                        "category": quote_item.category,
                        "name": quote_item.name,
                        "amount": quote_item.amount,
                        "source": quote_item.source.value,
                        "resolution_source": quote_item.resolution_source,
                        "evidence": quote_item.evidence,
                    }
                    for quote_item in result.quote.items
                ]
        cases.append(case)

    comparable = [
        case for case in cases if case["system_price"] is not None and case["historical_price"] > 0
    ]
    complete = [
        case
        for case in comparable
        if not any(item["source"] == "U" for item in case["quote_items"])
    ]
    feature_comparable = [
        {**case, "system_price": case["feature_reference_price"]}
        for case in cases
        if case["feature_reference_price"] is not None and case["historical_price"] > 0
    ]
    return {
        "audit_version": "GCS-PRICE-AUDIT-V1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bom_path": str(bom_path),
        "drawings_root": str(drawings_root),
        "summary": {
            "machining_rows": len(rows),
            "unique_items": len(unique),
            "items_with_drawings": sum(1 for item in unique if drawing_index.get(item)),
            "items_without_drawings": sum(1 for item in unique if not drawing_index.get(item)),
            "duplicate_price_conflicts": len(conflicts),
            "actual_extended_total": round(sum(row["historical_extended"] for row in rows), 2),
            "accuracy": calculate_accuracy_metrics(comparable) if run_quotes else None,
            "official_complete_accuracy": (
                calculate_accuracy_metrics(complete) if run_quotes else None
            ),
            "feature_reference_accuracy": (
                calculate_accuracy_metrics(feature_comparable) if run_quotes else None
            ),
        },
        "conflicts": conflicts,
        "cases": cases,
    }


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "gcs-price-audit.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = output_dir / "gcs-price-audit.csv"
    fields = [
        "item",
        "source_row",
        "description",
        "quantity",
        "historical_price",
        "historical_extended",
        "drawing_path",
        "system_price",
        "absolute_error",
        "deviation_pct",
        "feature_reference_price",
        "feature_reference_absolute_error",
        "feature_reference_deviation_pct",
        "status",
        "occurrence_count",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report["cases"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bom", type=Path, required=True)
    parser.add_argument("--drawings", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("runtime/price-audit"))
    parser.add_argument(
        "--quote", action="store_true", help="Run the production quotation pipeline"
    )
    args = parser.parse_args()
    report = audit(args.bom, args.drawings, args.quote)
    write_outputs(report, args.output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
