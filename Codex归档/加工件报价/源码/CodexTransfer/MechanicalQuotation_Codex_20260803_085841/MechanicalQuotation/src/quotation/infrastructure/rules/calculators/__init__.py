"""Rule Engine — modular calculators for quotation formulas.

Each calculator:
1. Takes a QuotationFeature + price lookup function
2. Applies a formula (weight × price, time × rate, ...)
3. Returns QuoteItem with formula/input_values/result evidence
4. Preserves resolution trace from PriceLookupResult (Phase 4.7)
"""

from __future__ import annotations

import uuid
from typing import Callable, TYPE_CHECKING

from quotation.domain.quote import QuoteItem, PriceSource, QuoteConfidence

if TYPE_CHECKING:
    from quotation.infrastructure.rules.published_pricebook_loader import PriceLookupResult


# ---------------------------------------------------------------------------
# Evidence model for formula traceability
# ---------------------------------------------------------------------------

class CalculationEvidence:
    """Structured evidence of how a price was calculated."""

    def __init__(self, formula: str, input_values: dict[str, float], result: float):
        self.formula = formula
        self.input_values = input_values
        self.result = result

    def to_string(self) -> str:
        parts = [f"{k}={v}" for k, v in self.input_values.items()]
        return f"{', '.join(parts)} -> {self.formula} = {self.result:.2f} CNY"


# ---------------------------------------------------------------------------
# Unknown Cost Item (NOT default 0)
# ---------------------------------------------------------------------------

def make_unknown_item(
    category: str,
    name: str,
    reason: str,
    confidence: QuoteConfidence = QuoteConfidence.UNCERTAIN,
) -> QuoteItem:
    """Create an explicit Unknown Cost Item — not a default 0."""
    return QuoteItem(
        line_id=f"UNK-{uuid.uuid4().hex[:6]}",
        category=category,
        name=f"{name} (未定價)",
        quantity=0, unit="", unit_price=0, amount=0,
        source=PriceSource.U,
        note=f"UNKNOWN: {reason}",
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Price lookup function type (Phase 4.7: returns PriceLookupResult | None)
# ---------------------------------------------------------------------------

PriceLookup = Callable[[str, str], "PriceLookupResult | None"]


def _apply_trace(item: QuoteItem, result: "PriceLookupResult | None") -> QuoteItem:
    """Copy resolution trace fields from PriceLookupResult to QuoteItem."""
    if result is None:
        return item
    item.quote_price_source = "C"
    item.price_version_id = result.price_version_id
    item.company_price_id = result.company_price_id
    item.origin_price_record_id = result.origin_price_record_id
    item.origin_supplier_id = result.origin_supplier_id
    item.origin_price_source = result.origin_price_source
    item.price_basis = result.price_basis
    item.effective_from = result.effective_from
    item.resolution_source = result.resolution_source
    item.fallback_reason = result.fallback_reason
    item.fallback_approval_status = result.fallback_approval_status
    item.fallback_warning = result.fallback_warning
    if result.unit:
        item.unit = result.unit
    return item


# ---------------------------------------------------------------------------
# Material Calculator
# ---------------------------------------------------------------------------

def calc_material(
    material: str | None,
    weight_kg: float,
    loss_rate: float,
    lookup: PriceLookup,
    origin_source: str = "C",
) -> QuoteItem:
    """材料費 = weight × unit_price × (1 + loss_rate)."""
    if not material or weight_kg <= 0:
        return make_unknown_item("material", material or "unknown",
                                 f"weight={weight_kg}")

    price_result = lookup("material", material)
    if price_result is None:
        return make_unknown_item("material", material,
                                 f"Material '{material}' not in price rules")

    unit_price = price_result.unit_price
    amount = round(weight_kg * unit_price * (1 + loss_rate), 2)
    item = QuoteItem(
        line_id=f"MAT-{uuid.uuid4().hex[:6]}",
        category="material",
        name=f"{material} 材料費",
        quantity=weight_kg,
        unit="kg",
        unit_price=unit_price,
        amount=amount,
        source=PriceSource.C,
        rule_id=f"MAT_{material}",
        evidence=CalculationEvidence(
            formula="weight × unit_price × (1 + loss_rate)",
            input_values={"weight_kg": weight_kg, "unit_price": unit_price, "loss_rate": loss_rate},
            result=amount,
        ).to_string(),
        confidence=QuoteConfidence.HIGH,
    )
    return _apply_trace(item, price_result)


# ---------------------------------------------------------------------------
# Machining Calculator (CNC, TAP, etc.)
# ---------------------------------------------------------------------------

_CNC_TIME_PER_HOLE = 0.1       # hours per hole
_CNC_TIME_PER_THREAD = 0.05    # hours per thread
_TAP_TIME_PER_THREAD = 0.05    # hours per thread
_CNC_BASE_HOURS = 0.5          # minimum setup

def calc_machining(
    process_name: str,
    hours: float,
    lookup: PriceLookup,
) -> QuoteItem:
    """加工費 = hours × rate."""
    price_result = lookup("process", process_name)
    if price_result is None:
        return make_unknown_item("process", process_name,
                                 f"Process '{process_name}' not in price rules")

    rate = price_result.unit_price
    amount = round(hours * rate, 2)
    item = QuoteItem(
        line_id=f"PROC-{uuid.uuid4().hex[:6]}",
        category="process",
        name=f"{process_name} 加工費",
        quantity=hours,
        unit="hour",
        unit_price=rate,
        amount=amount,
        source=PriceSource.C,
        rule_id=f"PROC_{process_name}",
        evidence=CalculationEvidence(
            formula="hours × rate",
            input_values={"hours": hours, "rate": rate},
            result=amount,
        ).to_string(),
        confidence=QuoteConfidence.HIGH if hours > 0 else QuoteConfidence.MEDIUM,
    )
    return _apply_trace(item, price_result)


def estimate_cnc_hours(hole_count: int, thread_count: int) -> float:
    return max(_CNC_BASE_HOURS, _CNC_BASE_HOURS + hole_count * _CNC_TIME_PER_HOLE + thread_count * _CNC_TIME_PER_THREAD)


def estimate_tap_hours(thread_count: int) -> float:
    return max(0.2, thread_count * _TAP_TIME_PER_THREAD) if thread_count > 0 else 0.0


# ---------------------------------------------------------------------------
# Surface Calculator
# ---------------------------------------------------------------------------

def calc_surface(
    treatment: str | None,
    weight_kg: float,
    lookup: PriceLookup,
) -> QuoteItem | None:
    """表面處理費 = weight × price (by_weight mode)."""
    if not treatment:
        return None

    price_result = lookup("surface", treatment)
    if price_result is None:
        return make_unknown_item("surface", treatment,
                                 f"Surface '{treatment}' not in price rules")

    unit_price = price_result.unit_price
    amount = round(weight_kg * unit_price, 2)
    item = QuoteItem(
        line_id=f"SURF-{uuid.uuid4().hex[:6]}",
        category="surface",
        name=treatment,
        quantity=weight_kg,
        unit="kg",
        unit_price=unit_price,
        amount=amount,
        source=PriceSource.C,
        rule_id=f"SURF_{treatment}",
        evidence=CalculationEvidence(
            formula="weight × unit_price",
            input_values={"weight_kg": weight_kg, "unit_price": unit_price},
            result=amount,
        ).to_string(),
        confidence=QuoteConfidence.HIGH,
    )
    return _apply_trace(item, price_result)


# ---------------------------------------------------------------------------
# Frame Calculator
# ---------------------------------------------------------------------------

def calc_frame_profile(
    profile_type: str | None,
    length_mm: float,
    lookup: PriceLookup,
) -> QuoteItem:
    """型材費 = length_m × rate."""
    length_m = length_mm / 1000.0
    price_result = lookup("material", profile_type or "鋁型材")

    if price_result is not None:
        rate = price_result.unit_price
        source = PriceSource.C
        amount = round(length_m * rate, 2)
        item = QuoteItem(
            line_id=f"FRM-{uuid.uuid4().hex[:6]}",
            category="material",
            name=f"{profile_type or '型材'} 材料費",
            quantity=length_m,
            unit="m",
            unit_price=rate,
            amount=amount,
            source=source,
            rule_id="FRAME_PROFILE",
            evidence=CalculationEvidence(
                formula="length × rate",
                input_values={"length_m": length_m, "rate": rate},
                result=amount,
            ).to_string(),
            confidence=QuoteConfidence.MEDIUM,
        )
        return _apply_trace(item, price_result)
    else:
        # Industry fallback
        rate = 30.0
        amount = round(length_m * rate, 2)
        return QuoteItem(
            line_id=f"FRM-{uuid.uuid4().hex[:6]}",
            category="material",
            name=f"{profile_type or '型材'} 材料費",
            quantity=length_m,
            unit="m",
            unit_price=rate,
            amount=amount,
            source=PriceSource.E,
            rule_id="FRAME_PROFILE",
            evidence=CalculationEvidence(
                formula="length × rate",
                input_values={"length_m": length_m, "rate": rate},
                result=amount,
            ).to_string(),
            confidence=QuoteConfidence.MEDIUM,
        )


def calc_frame_joints(
    joint_count: int,
    lookup: PriceLookup,
) -> QuoteItem:
    """連接件費 = count × rate."""
    rate = 5.0  # industry rate
    amount = round(joint_count * rate, 2)
    item = QuoteItem(
        line_id=f"FRM-J-{uuid.uuid4().hex[:6]}",
        category="material",
        name="連接件",
        quantity=joint_count,
        unit="pcs",
        unit_price=rate,
        amount=amount,
        source=PriceSource.E,
        rule_id="FRAME_JOINT",
        evidence=CalculationEvidence(
            formula="count × rate",
            input_values={"joint_count": joint_count, "rate": rate},
            result=amount,
        ).to_string(),
        confidence=QuoteConfidence.MEDIUM,
    )
    return _apply_trace(item, None)


# ---------------------------------------------------------------------------
# Assembly Calculator
# ---------------------------------------------------------------------------

def calc_assembly(
    assembly_type: str | None,
    hours: float,
    lookup: PriceLookup,
) -> QuoteItem:
    """組裝費 = hours × labor_rate."""
    price_result = lookup("process", "鉗工")
    rate = price_result.unit_price if price_result else 88.0
    amount = round(hours * rate, 2)
    item = QuoteItem(
        line_id=f"ASM-{uuid.uuid4().hex[:6]}",
        category="process",
        name=f"{assembly_type or '組裝'} 人工費",
        quantity=hours,
        unit="hour",
        unit_price=rate,
        amount=amount,
        source=PriceSource.C if price_result else PriceSource.E,
        rule_id="LABOR_ASSEMBLY",
        evidence=CalculationEvidence(
            formula="hours × rate",
            input_values={"hours": hours, "rate": rate},
            result=amount,
        ).to_string(),
        confidence=QuoteConfidence.MEDIUM,
    )
    if price_result:
        return _apply_trace(item, price_result)
    return item
