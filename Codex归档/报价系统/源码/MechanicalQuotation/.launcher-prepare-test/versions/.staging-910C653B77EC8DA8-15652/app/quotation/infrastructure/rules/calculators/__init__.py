"""Rule Engine — modular calculators for quotation formulas.

Each calculator:
1. Takes a QuotationFeature + price lookup function
2. Applies a formula (weight × price, time × rate, ...)
3. Returns QuoteItem with formula/input_values/result evidence
4. Preserves resolution trace from PriceLookupResult (Phase 4.7)
"""

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING, Callable

from quotation.domain.quote import QuoteItem, PriceSource, QuoteConfidence
from quotation.utils.normalization import normalize_profile_spec

if TYPE_CHECKING:
    from quotation.infrastructure.rules.published_pricebook_loader import PriceLookupResult


# ---------------------------------------------------------------------------
# Evidence model for formula traceability
# ---------------------------------------------------------------------------

class CalculationEvidence:
    """Structured evidence of how a price was calculated."""

    def __init__(
        self,
        formula: str,
        input_values: dict[str, float | Decimal],
        result: float | Decimal,
    ):
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
    quantity: float = 0,
    unit: str = "",
) -> QuoteItem:
    """Create an explicit Unknown Cost Item — not a default 0."""
    return QuoteItem(
        line_id=f"UNK-{uuid.uuid4().hex[:6]}",
        category=category,
        name=f"{name}（未定价）",
        quantity=quantity, unit=unit, unit_price=0, amount=0,
        source=PriceSource.U,
        note=f"未定价原因：{reason}",
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
    if result.resolution_source == "LEGACY_YAML_DRAFT":
        item.source = PriceSource.U
        item.quote_price_source = "U"
        item.confidence = QuoteConfidence.UNCERTAIN
    else:
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
    weight_kg: float | Decimal,
    loss_rate: float | Decimal,
    lookup: PriceLookup,
    origin_source: str = "C",
    calculation_trace: dict[str, float | Decimal | str] | None = None,
) -> QuoteItem:
    """材料費 = weight × unit_price × (1 + loss_rate)."""
    if not material or weight_kg <= 0:
        return make_unknown_item(
            "material",
            material or "材料待确认",
            f"缺少明确材料，或无法根据图纸计算重量（当前重量：{weight_kg} 千克）",
        )

    price_result = lookup("material", material)
    if price_result is None:
        return make_unknown_item("material", material, f"价格表中没有材料“{material}”的可用价格")

    weight = Decimal(str(weight_kg))
    unit_price = Decimal(str(price_result.unit_price))
    loss = Decimal(str(loss_rate))
    unrounded_amount = weight * unit_price * (Decimal("1") + loss)
    amount = unrounded_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    evidence_inputs: dict[str, float | Decimal] = {
        "weight_kg": weight,
        "unit_price": unit_price,
        "loss_rate": loss,
    }
    for key in ("area_mm2", "thickness_mm", "volume_mm3", "density_g_cm3"):
        value = (calculation_trace or {}).get(key)
        if value is not None:
            evidence_inputs[key] = Decimal(str(value))
    item = QuoteItem(
        line_id=f"MAT-{uuid.uuid4().hex[:6]}",
        category="material",
        name=f"{material} 材料費",
        quantity=float(weight),
        unit="kg",
        unit_price=float(unit_price),
        amount=float(amount),
        source=PriceSource.C,
        rule_id=f"MAT_{material}",
        evidence=CalculationEvidence(
            formula="weight × unit_price × (1 + loss_rate)",
            input_values=evidence_inputs,
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
        item = make_unknown_item(
            "process",
            process_name,
            f"价格表中没有工序“{process_name}”的可用价格",
            quantity=hours,
            unit="小时",
        )
        item.evidence = f"预计工时={hours}小时；公司尚未发布该工序小时费率"
        return item

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
    weight_kg: float | Decimal,
    lookup: PriceLookup,
    surface_area_mm2: float | Decimal = 0,
) -> QuoteItem | None:
    """Calculate surface cost by the resolved price unit (kg or m²)."""
    if not treatment:
        return None

    price_result = lookup("surface", treatment)
    if price_result is None:
        return make_unknown_item("surface", treatment, f"价格表中没有表面处理“{treatment}”的可用价格")

    unit_price = Decimal(str(price_result.unit_price))
    if price_result.unit == "m2":
        quantity = Decimal(str(surface_area_mm2)) / Decimal("1000000")
        if quantity <= 0:
            return make_unknown_item(
                "surface",
                treatment,
                f"表面处理“{treatment}”按平方米计价，但图纸中无法取得有效面积",
            )
        unit = "m2"
        formula = "surface_area_m2 x unit_price"
        inputs = {"surface_area_m2": quantity, "unit_price": unit_price}
    else:
        quantity = Decimal(str(weight_kg))
        unit = price_result.unit or "kg"
        formula = "weight_kg x unit_price"
        inputs = {"weight_kg": quantity, "unit_price": unit_price}
    amount = (quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    item = QuoteItem(
        line_id=f"SURF-{uuid.uuid4().hex[:6]}",
        category="surface",
        name=treatment,
        quantity=float(quantity),
        unit=unit,
        unit_price=float(unit_price),
        amount=float(amount),
        source=PriceSource.C,
        rule_id=f"SURF_{treatment}",
        evidence=CalculationEvidence(
            formula=formula,
            input_values=inputs,
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
    profile_spec: str | None = None,
) -> QuoteItem:
    """型材費 = length_m × rate."""
    length_m = length_mm / 1000.0
    normalized_spec = normalize_profile_spec(profile_spec or profile_type)
    is_aluminum_profile = bool(
        profile_type and ("鋁型材" in profile_type or "AL_PROFILE" in profile_type.upper())
    )
    lookup_name = (
        f"AL_PROFILE:{normalized_spec}"
        if is_aluminum_profile and normalized_spec
        else profile_type or "鋁型材"
    )
    display_name = " ".join(part for part in (profile_type or "型材", normalized_spec) if part)
    price_result = lookup("material", lookup_name)

    if price_result is not None:
        rate = price_result.unit_price
        source = PriceSource.C
        amount = round(length_m * rate, 2)
        item = QuoteItem(
            line_id=f"FRM-{uuid.uuid4().hex[:6]}",
            category="material",
            name=f"{display_name} 材料費",
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
            name=f"{display_name} 材料費",
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
    if hours <= 0:
        return make_unknown_item(
            "process",
            f"{assembly_type or '組裝'} 人工費",
            "图纸识别到装配结构，但无法取得可靠装配工时",
            quantity=1,
            unit="项",
        )
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
