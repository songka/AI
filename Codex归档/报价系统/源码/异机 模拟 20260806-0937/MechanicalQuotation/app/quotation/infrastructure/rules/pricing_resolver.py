"""Pricing Resolver - price lookup with Published Pricebook priority (Phase 4.7).

Priority order:
1. Published Company Pricebook (C) — R01-COMPANY-PRICE-V1.0 snapshot
2. Legacy YAML (C) — rules/quotation-rules.yaml fallback
3. Historical (H)
4. Industry estimate (E)
5. AI suggestion (AI)
6. Manual (M) — single-quote only
7. Unknown (U)

Pending Supplier S MUST NOT be auto-used for quotation.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from quotation.domain.quotation_feature import (
    AssemblyQuotationFeature,
    FrameQuotationFeature,
    MachiningQuotationFeature,
    SheetMetalQuotationFeature,
)
from quotation.domain.quote import PriceSource, QuoteConfidence, QuoteItem
from quotation.infrastructure.rules.calculators import (
    calc_assembly,
    calc_frame_joints,
    calc_frame_profile,
    calc_machining,
    calc_material,
    calc_surface,
    estimate_cnc_hours,
    estimate_tap_hours,
)
from quotation.infrastructure.rules.feature_price_calibration import (
    FeaturePriceCalibration,
)
from quotation.infrastructure.rules.published_pricebook_loader import (
    PriceLookupResult,
    PublishedPricebookLoader,
)
from quotation.utils.normalization import normalize_profile_spec

logger = logging.getLogger("quotation.infrastructure.rules.pricing_resolver")

DEFAULT_RULES_DIR = Path("rules")
DEFAULT_RULES_NAME = "quotation-rules.yaml"
VERSIONED_PATTERN = re.compile(r"quotation-rules_V(\d+\.\d+)\.yaml")
_PROCESS_ALIASES = {"TAP": "鉗工", "攻牙": "鉗工"}


def find_rules_file(rules_dir: str | Path | None = None) -> Path | None:
    """Find the rules file, preferring latest versioned file."""
    d = Path(rules_dir or DEFAULT_RULES_DIR)
    if not d.exists():
        return None
    default = d / DEFAULT_RULES_NAME
    if default.exists():
        return default
    best: tuple[int, int, Path] | None = None
    for f in d.glob("quotation-rules_V*.yaml"):
        m = VERSIONED_PATTERN.match(f.name)
        if m:
            parts = m.group(1).split(".")
            major, minor = int(parts[0]), int(parts[1])
            if best is None or (major, minor) > (best[0], best[1]):
                best = (major, minor, f)
    if best:
        return best[2]
    return None


class PricingResolver:
    """Look up prices with Published Company Pricebook priority.

    Priority chain:
    1. Published Company Pricebook C  (PUBLISHED_COMPANY_PRICEBOOK)
    2. Legacy YAML C                  (LEGACY_YAML or LEGACY_YAML_DRAFT fallback)
    3. H / E / AI / M / U            (not yet implemented)
    """

    def __init__(
        self,
        rules_path: str | Path | None = None,
        calibration_model_path: str | Path | None = None,
    ):
        # Legacy YAML
        p = Path(rules_path) if rules_path else find_rules_file()
        if p is None or not p.exists():
            raise FileNotFoundError(
                "No rules file found. Expected: rules/quotation-rules.yaml "
                "or rules/quotation-rules_V*.yaml"
            )
        self._rules_path = p
        self._rules = self._load(p)
        self.price_version = self._rules.get("version", "1.0")
        self._legacy_version = self.price_version
        self._legacy_status = str(self._rules.get("status", ""))
        self._legacy_is_draft = "DRAFT" in self._legacy_status.upper()
        self._feature_calibration = FeaturePriceCalibration(calibration_model_path)

        # Published Company Pricebook (Phase 4.7)
        self._published_loader = PublishedPricebookLoader()
        if self._published_loader.is_active:
            logger.info(
                "PricingResolver: published pricebook ACTIVE (%s), "
                "legacy YAML as fallback (%s, status=%s)",
                self._published_loader.price_version,
                self._legacy_version,
                self._legacy_status,
            )
        else:
            logger.warning(
                "PricingResolver: published pricebook NOT available (%s), "
                "using legacy YAML only (%s, status=%s)",
                self._published_loader.load_error,
                self._legacy_version,
                self._legacy_status,
            )

    @property
    def rules_file_name(self) -> str:
        return self._rules_path.name

    @property
    def is_using_published_pricebook(self) -> bool:
        return self._published_loader.is_active

    # -- Price lookup (Phase 4.7: returns PriceLookupResult | None) --

    def lookup(self, category: str, name: str) -> PriceLookupResult | None:
        """Look up a price, trying Published Pricebook first, then Legacy YAML."""
        if category == "material":
            return self._lookup_material(name)
        elif category == "process":
            return self._lookup_process(name)
        elif category == "surface":
            return self._lookup_surface(name)
        elif category == "labor":
            return self._lookup_process(name)
        return None

    def resolve_feature_calibrated_part(
        self,
        texts: list[str],
        material: str | None,
        surface_treatment: str | None,
        calculated_reference_total: float | None = None,
    ) -> QuoteItem | None:
        """Estimate a whole-part price from drawing features, never identifiers."""
        prediction = self._feature_calibration.predict(
            texts=texts,
            material=material,
            surface_treatment=surface_treatment,
        )
        if prediction is None:
            return None
        reference = (
            f"；分项报价合计={calculated_reference_total:.2f}元（校准模型不覆盖该合计）"
            if calculated_reference_total is not None
            else ""
        )
        domain_note = "；特征超出训练范围" if prediction.out_of_domain else ""
        return QuoteItem(
            line_id=f"CAL-{uuid.uuid4().hex[:6]}",
            category="other",
            name="图纸特征校准估价",
            quantity=1,
            unit="件",
            unit_price=prediction.amount,
            amount=prediction.amount,
            source=PriceSource.E,
            rule_id="FEATURE_CALIBRATION_MODEL",
            evidence=(
                f"材料={prediction.material}；外形尺寸={prediction.dimensions_raw}；"
                f"表面处理类别={prediction.surface_family}；"
                f"特征校准模型={prediction.model_version}；训练样本={prediction.training_count}；"
                f"留一法WAPE={prediction.validation_wape_pct:.2f}%{domain_note}{reference}"
            ),
            confidence=QuoteConfidence.LOW,
            note=(
                "仅按图纸材料、尺寸和表面处理估算整件参考金额；"
                "不使用料号或文件名，不是正式价格且不计入正式合计。"
            ),
            quote_price_source="E",
            price_version_id=prediction.model_version,
            origin_price_source="H",
            price_basis="BOM_UNIT_COST_BASIS_UNSPECIFIED",
            resolution_source="FEATURE_CALIBRATION_MODEL",
        )

    def _make_legacy_fallback(
        self, yaml_result: PriceLookupResult, name: str, category: str
    ) -> PriceLookupResult:
        """Apply legacy YAML fallback metadata, detecting DRAFT status."""
        yaml_result.fallback_reason = (
            f"{category} '{name}' not in Published Pricebook "
            f"{self._published_loader.price_version}, "
            f"using legacy YAML {self._legacy_version}"
        )
        if self._legacy_is_draft:
            yaml_result.resolution_source = "LEGACY_YAML_DRAFT"
            yaml_result.fallback_approval_status = self._legacy_status
            yaml_result.fallback_warning = True
        else:
            yaml_result.resolution_source = "LEGACY_YAML"
        return yaml_result

    def _lookup_material(self, name: str) -> PriceLookupResult | None:
        """Material price lookup: Published → Legacy YAML."""
        material_code = name
        specification = None
        unit = "kg"
        if ":" in name:
            material_code, specification = name.split(":", 1)
        elif "鋁型材" in name or "AL_PROFILE" in name.upper():
            material_code = "AL_PROFILE"
            specification = normalize_profile_spec(name)
        if material_code.upper() == "AL_PROFILE":
            unit = "m"
            specification = normalize_profile_spec(specification) or specification

        if self._published_loader.is_active:
            result = self._published_loader.lookup_material(
                material_code,
                specification=specification,
                unit=unit,
            )
            if result is not None:
                logger.debug(
                    "Material '%s' → PUBLISHED pricebook: %.2f CNY/%s",
                    name,
                    result.unit_price,
                    result.unit,
                )
                return result

        yaml_result = self._lookup_material_yaml(name)
        if yaml_result is not None:
            yaml_result = self._make_legacy_fallback(yaml_result, name, "Material")
            logger.debug(
                "Material '%s' → %s: %.2f CNY/%s",
                name,
                yaml_result.resolution_source,
                yaml_result.unit_price,
                yaml_result.unit,
            )
        return yaml_result

    def _lookup_process(self, name: str) -> PriceLookupResult | None:
        """Process price lookup: Published → Legacy YAML."""
        if self._published_loader.is_active:
            result = self._published_loader.lookup_process(name)
            if result is not None:
                return result

        yaml_result = self._lookup_process_yaml(name)
        if yaml_result is not None:
            yaml_result = self._make_legacy_fallback(yaml_result, name, "Process")
        return yaml_result

    def _lookup_surface(self, name: str) -> PriceLookupResult | None:
        """Surface price lookup: Published → Legacy YAML."""
        if self._published_loader.is_active:
            published_name = "COATING_RAL9003" if "RAL9003" in name.upper() else name
            published_unit = "m2" if published_name == "COATING_RAL9003" else "kg"
            result = self._published_loader.lookup_surface(published_name, published_unit)
            if result is not None:
                return result

        yaml_result = self._lookup_surface_yaml(name)
        if yaml_result is not None:
            yaml_result = self._make_legacy_fallback(yaml_result, name, "Surface")
        return yaml_result

    # -- Legacy YAML lookup helpers --

    def _lookup_material_yaml(self, name: str) -> PriceLookupResult | None:
        """Legacy YAML material lookup."""
        mats = self._rules.get("material", {})
        price = None
        unit = "kg"
        if name in mats:
            price = float(mats[name].get("price", 0))
            unit = mats[name].get("unit", "kg")
        else:
            key_norm = name.upper().replace("-", "").replace(" ", "")
            for key, val in mats.items():
                if key.upper().replace("-", "").replace(" ", "") == key_norm:
                    price = float(val.get("price", 0))
                    unit = val.get("unit", "kg")
                    break
                if key_norm in key.upper().replace("-", "").replace(" ", ""):
                    price = float(val.get("price", 0))
                    unit = val.get("unit", "kg")
                    break
                if key.upper().replace("-", "").replace(" ", "") in key_norm:
                    price = float(val.get("price", 0))
                    unit = val.get("unit", "kg")
                    break
        if price is not None:
            return PriceLookupResult(
                unit_price=price,
                unit=unit,
                price_version_id=self._legacy_version,
            )
        return None

    def get_material_unit(self, name: str) -> str:
        """Get the pricing unit for a material (kg or m)."""
        mats = self._rules.get("material", {})
        if name in mats:
            return mats[name].get("unit", "kg")
        for key, val in mats.items():
            if key.upper().replace("-", "").replace(" ", "") == name.upper().replace(
                "-", ""
            ).replace(" ", ""):
                return val.get("unit", "kg")
        return "kg"

    def _lookup_process_yaml(self, name: str) -> PriceLookupResult | None:
        """Legacy YAML process lookup."""
        procs = self._rules.get("process", {})
        price = None
        if name in procs:
            price = float(procs[name].get("rate", 0))
        else:
            alias = _PROCESS_ALIASES.get(name)
            if alias and alias in procs:
                price = float(procs[alias].get("rate", 0))
            else:
                for key, val in procs.items():
                    if key in name or name.upper() in key.upper():
                        price = float(val.get("rate", 0))
                        break
        if price is not None:
            return PriceLookupResult(
                unit_price=price,
                unit="hour",
                price_version_id=self._legacy_version,
            )
        return None

    def _lookup_surface_yaml(self, name: str) -> PriceLookupResult | None:
        """Legacy YAML surface lookup."""
        surfs = self._rules.get("surface", {})
        for key, val in surfs.items():
            if key in name or name in key:
                return PriceLookupResult(
                    unit_price=float(val.get("price", 0)),
                    unit=val.get("unit", "kg"),
                    price_version_id=self._legacy_version,
                )
        return None

    # -- Resolve using calculators --

    def resolve_machining(self, mq: MachiningQuotationFeature) -> list[QuoteItem]:
        items: list[QuoteItem] = []
        calculation_trace = (
            mq.material_calculation.model_dump() if mq.material_calculation is not None else None
        )
        items.append(
            calc_material(
                mq.material,
                mq.weight_kg,
                mq.material_loss_rate,
                self.lookup,
                calculation_trace=calculation_trace,
            )
        )
        has_cnc_evidence = "CNC" in mq.process_hints or mq.hole_count > 0 or mq.thread_count > 0
        if has_cnc_evidence:
            cnc_hours = estimate_cnc_hours(mq.hole_count, mq.thread_count)
            items.append(calc_machining("CNC", cnc_hours, self.lookup))
        if mq.thread_count > 0:
            items.append(calc_machining("攻牙", estimate_tap_hours(mq.thread_count), self.lookup))
        surf_item = calc_surface(
            mq.surface_treatment,
            mq.weight_kg,
            self.lookup,
            surface_area_mm2=mq.surface_area_mm2,
        )
        if surf_item:
            items.append(surf_item)
        return items

    def resolve_frame(self, fq: FrameQuotationFeature) -> list[QuoteItem]:
        items: list[QuoteItem] = []
        items.append(
            calc_frame_profile(
                fq.profile_type,
                fq.profile_length_mm,
                self.lookup,
                profile_spec=fq.profile_spec,
            )
        )
        if fq.joint_count > 0:
            items.append(calc_frame_joints(fq.joint_count, self.lookup))
        return items

    def resolve_assembly(self, aq: AssemblyQuotationFeature) -> list[QuoteItem]:
        items = [calc_assembly(aq.assembly_type, aq.estimated_hours, self.lookup)]
        if aq.component_count > 0:
            area = aq.estimated_hours * 50000
            import uuid as _uuid

            area_m2 = area / 1_000_000.0
            rate = 200.0
            amount = round(area_m2 * rate, 2)
            items.append(
                QuoteItem(
                    line_id=f"ACR-{_uuid.uuid4().hex[:6]}",
                    category="material",
                    name="亚克力/面板材料费",
                    quantity=area_m2,
                    unit="m2",
                    unit_price=rate,
                    amount=amount,
                    source=PriceSource.E,
                    rule_id="ACRYLIC_INDUSTRY",
                    evidence=(
                        f"area_m2={area_m2:.2f}, rate={rate} -> "
                        f"area x rate = {amount:.2f} CNY"
                    ),
                    confidence=QuoteConfidence.LOW,
                )
            )
        return items

    def resolve_sheet_metal(self, sq: SheetMetalQuotationFeature) -> list[QuoteItem]:
        from quotation.infrastructure.rules.calculators import make_unknown_item

        items: list[QuoteItem] = []
        if sq.cutting_length_mm > 0:
            items.append(make_unknown_item(
                "process",
                "钣金切割加工",
                "公司尚未发布钣金切割费率，需按材料、厚度、切割长度及设备确认",
                quantity=round(sq.cutting_length_mm / 1000, 3),
                unit="米",
            ))
        if sq.bend_count > 0:
            items.append(make_unknown_item(
                "process",
                "折弯加工",
                "公司尚未发布每折弯单价，需确认折弯次数、板厚和模具",
                quantity=sq.bend_count,
                unit="道",
            ))
        if not items:
            items.append(make_unknown_item(
                "process",
                "钣金加工",
                "已识别钣金件，但图纸中缺少可可靠计算的切割或折弯工程量",
                quantity=1,
                unit="项",
            ))
        return items

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        if not path.exists():
            logger.warning("Rules not found: %s", path)
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
