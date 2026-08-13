"""Quote domain model.

Represents a complete quotation with itemized cost breakdown,
price source tracking (C/H/E/AI/M/U), and confidence levels.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PriceSource(str, Enum):
    """Price origin code — Constitution §6."""
    C = "C"       # 公司規則 Confirmed
    H = "H"       # 歷史報價 Historical
    E = "E"       # 行業參考 Industry reference
    AI = "AI"     # AI 建議
    M = "M"       # 人工確認 Manual
    U = "U"       # 未知 Unknown


class QuoteConfidence(str, Enum):
    """Confidence level of a quote item."""
    HIGH = "high"           # C source, rule exact match
    MEDIUM = "medium"       # H source, historical similar
    LOW = "low"             # E source, industry estimate
    UNCERTAIN = "uncertain" # AI/M source, needs review


class QuoteStatus(str, Enum):
    COMPLETE = "COMPLETE"        # All items priced
    INCOMPLETE = "INCOMPLETE"    # Has unknown (U) items


# ---------------------------------------------------------------------------
# QuoteItem — single line item
# ---------------------------------------------------------------------------

class QuoteItem(BaseModel):
    """A single line item in a quotation."""

    # -- Identity --
    line_id: str = Field(..., description="Line item ID")

    # -- Description --
    category: str = Field(
        ..., description="Cost category: material | process | surface | purchased | other"
    )
    name: str = Field(..., description="Item name/description")

    # -- Calculation --
    quantity: float = Field(default=1.0, ge=0, description="Quantity (0=unknown)")
    unit: str = Field(default="ST", description="Unit of measure")
    unit_price: float = Field(default=0.0, ge=0, description="Unit price (CNY)")
    amount: float = Field(default=0.0, ge=0, description="Line total = quantity × unit_price")

    # -- Source & evidence --
    source: PriceSource = Field(default=PriceSource.U, description="Price origin")
    rule_id: str | None = Field(default=None, description="Matched rule ID")
    bom_ref: str | None = Field(default=None, description="Reference BOM item")
    evidence: str | None = Field(
        default=None,
        description="Calculation evidence, e.g. '86.9kg × 9CNY/kg = ¥782'",
    )

    # -- Confidence --
    confidence: QuoteConfidence = Field(
        default=QuoteConfidence.MEDIUM, description="Confidence level"
    )

    # -- Notes --
    note: str | None = Field(default=None)

    # -- AI reference estimate (never included in official totals before review) --
    ai_estimated_unit_price: float | None = Field(default=None, ge=0)
    ai_estimated_amount: float | None = Field(default=None, ge=0)
    ai_estimated_unit: str | None = Field(default=None)
    ai_estimate_reason: str | None = Field(default=None)
    ai_estimate_confidence: float | None = Field(default=None, ge=0, le=1)

    # -- Resolution trace (Phase 4.7 Published Pricebook) --
    quote_price_source: str | None = Field(default=None, description="C | H | E | AI | M | U")
    price_version_id: str | None = Field(default=None, description="Pricebook version used")
    company_price_id: str | None = Field(default=None, description="Company price record ID")
    origin_price_record_id: str | None = Field(default=None, description="Origin supplier price record")
    origin_supplier_id: str | None = Field(default=None, description="Origin supplier ID")
    origin_price_source: str | None = Field(default=None, description="S | I | M | AI | H | PENDING")
    price_basis: str | None = Field(default=None, description="EXCLUDING_TAX | INCLUDING_TAX")
    effective_from: str | None = Field(default=None, description="Price effective date")
    resolution_source: str | None = Field(default=None, description="PUBLISHED_COMPANY_PRICEBOOK | LEGACY_YAML | LEGACY_YAML_DRAFT")
    fallback_reason: str | None = Field(default=None, description="Reason for fallback if not from primary source")
    fallback_approval_status: str | None = Field(default=None, description="Approval status of fallback source")
    fallback_warning: bool = Field(default=False, description="True if fallback source is DRAFT")


# ---------------------------------------------------------------------------
# Quote — aggregate root
# ---------------------------------------------------------------------------

class Quote(BaseModel):
    """A complete quotation for one part."""

    # -- Identity --
    id: str = Field(..., description="Quote ID (UUID)")
    drawing_id: str = Field(..., description="Source Drawing.id")
    feature_id: str | None = Field(default=None, description="Source Feature.id")

    # -- Part info --
    part_number: str | None = Field(default=None, description="Part/drawing number")
    part_name: str | None = Field(default=None, description="Part name")
    material: str | None = Field(default=None, description="Material")
    quantity: int = Field(default=1, ge=1, description="Quoted quantity")

    # -- Line items --
    items: list[QuoteItem] = Field(default_factory=list, description="Quote line items")

    # -- Subtotals --
    subtotal_material: float = Field(default=0.0, ge=0, description="Material subtotal")
    subtotal_process: float = Field(default=0.0, ge=0, description="Process subtotal")
    subtotal_surface: float = Field(default=0.0, ge=0, description="Surface treatment subtotal")
    subtotal_purchased: float = Field(default=0.0, ge=0, description="Purchased parts subtotal")
    total: float = Field(default=0.0, ge=0, description="Grand total (CNY)")

    # -- Source summary --
    source_summary: dict[str, float] = Field(
        default_factory=dict,
        description="Total amount by price source, e.g. {'C': 500, 'H': 200, 'U': 100}",
    )
    unknown_count: int = Field(
        default=0, ge=0, description="Number of items with source=U"
    )
    cost_completion: float = Field(
        default=100.0, ge=0.0, le=100.0,
        description="Cost completion %: completed items / total items × 100"
    )

    # -- Metadata --
    quoted_at: str | None = Field(default=None, description="ISO datetime")
    quoted_by: str = Field(default="SYSTEM")

    # -- Version tracking (Phase 4) --
    quote_date: str | None = Field(default=None, description="報價日期 ISO date")
    price_version: str | None = Field(default=None, description="Price rules version used")
    rule_version: str | None = Field(default=None, description="Rule engine version")

    # -- Status (Phase 4.2) --
    quotation_status: str = Field(default="COMPLETE", description="COMPLETE | INCOMPLETE")
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_reason: str | None = Field(default=None)

    def model_post_init(self, __context: object) -> None:
        """Auto-compute subtotals, total, source summary, and unknown count.

        Resets computed fields before accumulation to ensure idempotency
        (model_post_init is called on every model_validate, not just creation).
        """
        # Reset before accumulation (idempotent)
        self.subtotal_material = 0.0
        self.subtotal_process = 0.0
        self.subtotal_surface = 0.0
        self.subtotal_purchased = 0.0
        self.total = 0.0
        self.source_summary = {}
        self.unknown_count = 0

        for item in self.items:
            match item.category:
                case "material":
                    self.subtotal_material += item.amount
                case "process":
                    self.subtotal_process += item.amount
                case "surface":
                    self.subtotal_surface += item.amount
                case "purchased":
                    self.subtotal_purchased += item.amount
                case _:
                    # "other" — not categorized, still counted in total
                    pass

        self.total = (
            self.subtotal_material
            + self.subtotal_process
            + self.subtotal_surface
            + self.subtotal_purchased
        )

        # Also include any items not in the 4 standard categories
        for item in self.items:
            if item.category not in ("material", "process", "surface", "purchased"):
                self.total += item.amount

        # Source summary
        summary: dict[str, float] = {}
        for item in self.items:
            key = item.source.value
            summary[key] = summary.get(key, 0.0) + item.amount
        self.source_summary = summary

        # Unknown count
        self.unknown_count = sum(
            1 for item in self.items if item.source == PriceSource.U
        )
