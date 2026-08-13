"""Price Book — aggregated company price rules with audit trail."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PriceBookEntry(BaseModel):
    """A single published price rule in the company price book."""

    entry_id: str
    material_code: str | None = None
    material_spec: str | None = None
    unit_price: float = 0.0
    unit: str = "kg"
    source: str = "C"                     # Always C for published
    origin_supplier_id: str | None = None  # Trace back to supplier
    origin_price_record_id: str | None = None
    effective_date: str | None = None
    version: str = "1.0"
    status: str = "ACTIVE"


class MaterialLossRule(BaseModel):
    """Material loss rate — not hardcoded 5%."""

    material: str
    part_type: str | None = None
    loss_rate: float = 0.05
    effective_date: str | None = None
    source: str = "LEGACY_FORMULA"
    confidence: float = 0.5


class TaxProfile(BaseModel):
    tax_profile_id: str
    tax_rate: float
    tax_type: str = "VAT"
    effective_from: str | None = None
    effective_to: str | None = None
    source: str = "SYSTEM_DEFAULT"        # LEGACY_FORMULA | SYSTEM_DEFAULT
    status: str = "PENDING_CONFIRMATION"
