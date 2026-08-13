"""Accuracy metrics for the final quotation validation report."""

from __future__ import annotations

from statistics import median
from typing import Any


def calculate_accuracy_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate WAPE, MAE, median absolute error, and exclusive APE buckets."""

    comparable = [case for case in cases if float(case.get("historical_price") or 0) > 0]
    absolute_errors = [
        abs(float(case["system_price"]) - float(case["historical_price"]))
        for case in comparable
    ]
    historical_total = sum(float(case["historical_price"]) for case in comparable)
    apes = [
        error / float(case["historical_price"]) * 100
        for error, case in zip(absolute_errors, comparable)
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
        "comparable_cases": len(comparable),
        "wape_pct": round(sum(absolute_errors) / historical_total * 100, 2)
        if historical_total else 0.0,
        "mae_cny": round(sum(absolute_errors) / len(absolute_errors), 2)
        if absolute_errors else 0.0,
        "median_absolute_deviation_cny": round(median(absolute_errors), 2)
        if absolute_errors else 0.0,
        "mean_ape_pct": round(sum(apes) / len(apes), 2) if apes else 0.0,
        "buckets": buckets,
    }
