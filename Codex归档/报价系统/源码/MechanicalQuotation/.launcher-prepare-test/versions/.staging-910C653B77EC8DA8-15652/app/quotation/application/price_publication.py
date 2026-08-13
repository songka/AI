"""Helpers shared by company-price publication workflows."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


def build_supplier_provenance_index(
    pricing_source_records: Iterable[Mapping[str, Any]],
) -> dict[str, str | None]:
    """Map source record IDs to their supplier IDs without inventing provenance."""

    index: dict[str, str | None] = {}
    for record in pricing_source_records:
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            continue
        supplier_id = str(record.get("supplier_id") or "").strip() or None
        index[record_id] = supplier_id
    return index


def origin_supplier_id_for(
    origin_price_record_id: str,
    provenance_index: Mapping[str, str | None],
) -> str | None:
    """Return recorded supplier provenance, or ``None`` when the source has none."""

    return provenance_index.get(origin_price_record_id)


def prepare_published_pricebook(
    draft: Mapping[str, Any],
    import_package: Mapping[str, Any],
    *,
    price_version_id: str,
    version: str,
    approved_by: str,
    approved_at: str,
) -> dict[str, Any]:
    """Validate and promote a reviewed draft into a published snapshot."""

    if draft.get("status") != "DRAFT":
        raise ValueError("Only a DRAFT pricebook can be published")
    if draft.get("blocking_errors", 0):
        raise ValueError("Draft has blocking publication errors")

    prices = copy.deepcopy(list(draft.get("company_prices", [])))
    if not prices:
        raise ValueError("Draft has no company prices")

    provenance = build_supplier_provenance_index(
        import_package.get("pricing_source_records", [])
    )
    seen: set[tuple[str, str, str | None, str]] = set()
    for price in prices:
        key = (
            str(price.get("target_type") or ""),
            str(price.get("canonical_code") or ""),
            price.get("specification"),
            str(price.get("unit") or ""),
        )
        if not all((key[0], key[1], key[3])):
            raise ValueError(f"Price record has an incomplete key: {key}")
        if key in seen:
            raise ValueError(f"Duplicate company price: {key}")
        seen.add(key)
        if float(price.get("unit_price") or 0) <= 0:
            raise ValueError(f"Company price must be positive: {key}")
        if price.get("price_basis") != "EXCLUDING_TAX":
            raise ValueError(f"Company price must be EXCLUDING_TAX: {key}")

        origin_record_id = str(price.get("origin_price_record_id") or "").strip()
        if origin_record_id:
            price["origin_supplier_id"] = origin_supplier_id_for(
                origin_record_id, provenance
            )
        price["price_version_id"] = price_version_id
        price["approved_by"] = approved_by
        price["approved_at"] = approved_at
        if price.get("canonical_code") == "COATING_RAL9003":
            price["selection_reason"] = (
                "使用原 Excel 歷史內部烤漆 25 元/m² 規則，完成正式發布流程驗證"
            )

    published = copy.deepcopy(dict(draft))
    published.update(
        {
            "price_version_id": price_version_id,
            "version": version,
            "status": "PUBLISHED",
            "approved_by": approved_by,
            "approved_at": approved_at,
            "record_count": len(prices),
            "material_count": sum(p["target_type"] == "MATERIAL" for p in prices),
            "process_count": sum(p["target_type"] == "PROCESS" for p in prices),
            "surface_count": sum(p["target_type"] == "SURFACE" for p in prices),
            "company_prices": prices,
        }
    )
    canonical = json.dumps(prices, sort_keys=True, ensure_ascii=False)
    published["snapshot_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return published


def build_current_version_pointer(
    snapshot: Mapping[str, Any], *, snapshot_path: str, activated_by: str, activated_at: str
) -> dict[str, Any]:
    """Build the activation pointer for an already-published snapshot."""

    if snapshot.get("status") != "PUBLISHED":
        raise ValueError("Current pointer may only target a PUBLISHED snapshot")
    return {
        "current_version": snapshot["price_version_id"],
        "snapshot_path": snapshot_path,
        "activated_at": activated_at,
        "activated_by": activated_by,
        "notes": snapshot.get("notes", ""),
    }
