"""Train the GCS price model from BOM features, never from part numbers."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from audit_gcs_pricing import load_machining_rows

from quotation.infrastructure.parser.description_parser import DescriptionParser
from quotation.infrastructure.parser.material_normalizer import normalize_material
from quotation.infrastructure.rules.feature_price_calibration import (
    canonical_dimensions,
    normalize_surface_family,
)

RIDGE_ALPHA = 0.01


def _training_rows(bom_path: Path) -> tuple[list[dict], list[int]]:
    parser = DescriptionParser()
    unique_items: dict[str, dict] = {}
    excluded_rows: list[int] = []
    for row in load_machining_rows(bom_path):
        unique_items.setdefault(row["item"], row)

    records: list[dict] = []
    for row in unique_items.values():
        parsed = parser.parse(
            bom_item="CALIBRATION_SOURCE",
            description=row["description"],
            source_row=row["source_row"],
            unit_cost=row["historical_price"],
        ).parsed_part
        dimensions = canonical_dimensions(parsed.dimensions_raw)
        material = normalize_material(parsed.material or "").normalized or parsed.material
        if not material or dimensions is None or row["historical_price"] <= 0:
            excluded_rows.append(row["source_row"])
            continue
        records.append(
            {
                "source_row": row["source_row"],
                "material": material,
                "dimensions": dimensions,
                "surface_family": normalize_surface_family(parsed.surface_treatment),
                "price": row["historical_price"],
            }
        )
    return records, excluded_rows


def _feature_vector(record: dict, materials: list[str], surfaces: list[str]) -> list[float]:
    d1, d2, d3 = record["dimensions"]
    values = [
        1.0,
        math.log(d1 + 1),
        math.log(d2 + 1),
        math.log(d3 + 1),
        math.log(d1 * d2 * d3 + 1),
        math.log(d1 * d2 + 1),
    ]
    values.extend(1.0 if record["material"] == category else 0.0 for category in materials[1:])
    values.extend(1.0 if record["surface_family"] == category else 0.0 for category in surfaces[1:])
    return values


def _fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    matrix = x.T @ x + RIDGE_ALPHA * np.eye(x.shape[1])
    return np.linalg.solve(matrix, x.T @ y)


def _validation(x: np.ndarray, log_prices: np.ndarray) -> dict:
    actual = np.exp(log_prices)
    predicted: list[float] = []
    for index in range(len(actual)):
        mask = np.arange(len(actual)) != index
        coefficients = _fit(x[mask], log_prices[mask])
        predicted.append(float(np.exp(x[index] @ coefficients)))
    absolute_errors = [abs(a - p) for a, p in zip(actual, predicted, strict=True)]
    apes = [
        error / a * 100 for error, a in zip(absolute_errors, actual, strict=True)
    ]
    buckets = {"<=10%": 0, "10-20%": 0, "20-30%": 0, ">30%": 0}
    for ape in apes:
        if ape <= 10:
            buckets["<=10%"] += 1
        elif ape <= 20:
            buckets["10-20%"] += 1
        elif ape <= 30:
            buckets["20-30%"] += 1
        else:
            buckets[">30%"] += 1
    return {
        "method": "LEAVE_ONE_OUT_CROSS_VALIDATION",
        "case_count": len(actual),
        "leave_one_out_wape_pct": round(sum(absolute_errors) / sum(actual) * 100, 2),
        "leave_one_out_mean_ape_pct": round(sum(apes) / len(apes), 2),
        "leave_one_out_mae_cny": round(sum(absolute_errors) / len(absolute_errors), 2),
        "buckets": buckets,
    }


def build_model(bom_path: Path) -> dict:
    source_bytes = bom_path.read_bytes()
    records, excluded_rows = _training_rows(bom_path)
    materials = sorted({record["material"] for record in records})
    surfaces = sorted({record["surface_family"] for record in records})
    x = np.array([_feature_vector(record, materials, surfaces) for record in records])
    log_prices = np.log(np.array([record["price"] for record in records]))
    coefficients = _fit(x, log_prices)
    domains: dict[str, dict] = {}
    for material in materials:
        values = [record["dimensions"] for record in records if record["material"] == material]
        domains[material] = {
            "sample_count": len(values),
            "minimum": [min(value[index] for value in values) for index in range(3)],
            "maximum": [max(value[index] for value in values) for index in range(3)],
        }
    return {
        "price_version_id": "GCS-FEATURE-CALIBRATION-V1.0",
        "status": "ACTIVE_REVIEW_REQUIRED",
        "model_type": "RIDGE_LOG_PRICE_FROM_DRAWING_FEATURES",
        "production_matching_fields": [
            "material",
            "overall_dimensions",
            "surface_treatment_family",
        ],
        "prohibited_matching_fields": ["part_number", "drawing_number", "file_name"],
        "source_type": "BOM_PRICE_CALIBRATION_BENCHMARK",
        "source_file": bom_path.name,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
        "source_modified_at": datetime.fromtimestamp(
            bom_path.stat().st_mtime, timezone.utc
        ).isoformat(),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_count": len(records),
        "excluded_source_rows": excluded_rows,
        "source_rows": sorted(record["source_row"] for record in records),
        "price_basis": "BOM_UNIT_COST_BASIS_UNSPECIFIED",
        "model": {
            "ridge_alpha": RIDGE_ALPHA,
            "feature_names": [
                "intercept",
                "log_dimension_1",
                "log_dimension_2",
                "log_dimension_3",
                "log_volume",
                "log_face_area",
                *[f"material={value}" for value in materials[1:]],
                *[f"surface={value}" for value in surfaces[1:]],
            ],
            "material_categories": materials,
            "surface_categories": surfaces,
            "coefficients": [round(float(value), 12) for value in coefficients],
        },
        "material_dimension_domains": domains,
        "validation": _validation(x, log_prices),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = build_model(args.bom)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation = model["validation"]
    print(
        f"训练样本 {model['training_count']}；留一法 WAPE "
        f"{validation['leave_one_out_wape_pct']:.2f}%"
    )


if __name__ == "__main__":
    main()
