"""Supplier Price Record — immutable, multi-source, versioned."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    MATERIAL = "MATERIAL"
    PROFILE = "PROFILE"
    PROCESS = "PROCESS"
    SURFACE = "SURFACE"
    OTHER = "OTHER"


class PriceStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    CONFLICT = "CONFLICT"
    UNIT_CONFLICT = "UNIT_CONFLICT"
    PENDING_EFFECTIVE_DATE = "PENDING_EFFECTIVE_DATE_CONFIRMATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNKNOWN_PRICE = "UNKNOWN_PRICE"
    AMBIGUOUS_MATERIAL_SPEC = "AMBIGUOUS_MATERIAL_SPEC"


class PriceSourceType(str, Enum):
    S = "S"  # Supplier Quote (原始供應商報價)
    C = "C"  # Company Published (公司審核發布)
    M = "M"  # Manual Override (單次人工覆寫)


class SupplierPriceRecord(BaseModel):
    """Immutable supplier price record. Never overwritten."""

    price_record_id: str = Field(..., description="PR-XXX")
    supplier_id: str
    supplier_name: str | None = None

    target_type: TargetType
    material_code: str | None = None       # "SPCC", "A6061-T6"
    material_spec: str | None = None        # "2mm", "40x40", "A級"
    process_code: str | None = None
    surface_code: str | None = None

    unit_price: float | None = Field(default=None, gt=0)
    unit: str = "kg"
    currency: str = "CNY"
    tax_included: bool = False
    tax_rate: float | None = None

    effective_from: str | None = None       # ISO date
    effective_to: str | None = None
    quote_number: str | None = None

    # Source tracing
    source_file: str | None = None
    source_sheet: str | None = None
    source_cell: str | None = None           # "C11"

    status: PriceStatus = PriceStatus.DRAFT
    conflict_note: str | None = None

    created_by: str | None = None
    approved_by: str | None = None
    created_at: str | None = None
