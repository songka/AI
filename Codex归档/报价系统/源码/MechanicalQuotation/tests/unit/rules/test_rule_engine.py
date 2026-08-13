"""Tests for Rule Engine calculators and Pricing Resolver (Phase 4.1).

Uses test-specific YAML rules (tests/unit/rules/test_rules.yaml).
Isolated from production Current Version Pointer via conftest.py.
"""

from __future__ import annotations

from decimal import Decimal

import ezdxf
import pytest

from quotation.domain.quote import PriceSource, Quote, QuoteConfidence
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.calculators import (
    calc_material,
    calc_machining,
    calc_surface,
    calc_frame_profile,
    calc_frame_joints,
    calc_assembly,
    make_unknown_item,
    estimate_cnc_hours,
    CalculationEvidence,
)


# resolver fixture is provided by tests/unit/rules/conftest.py
# — uses test_rules.yaml, no published pricebook loading


# ============================================================================
# Calculator unit tests
# ============================================================================

class TestMaterialCalculator:
    def test_known_material(self, resolver):
        item = calc_material("S50C", 86.9, 0.05, resolver.lookup)
        assert item.source == PriceSource.C
        # Test YAML: S50C = 9 CNY/kg; 86.9 * 9 * 1.05 = 821.205 ≈ 821.21
        assert item.amount == pytest.approx(821.21, rel=0.01)
        assert item.evidence is not None
        assert "weight" in (item.evidence or "")

    def test_unknown_material(self, resolver):
        item = calc_material("UnknownAlloy99", 10.0, 0.05, resolver.lookup)
        assert item.source == PriceSource.U
        assert item.amount == 0.0
        assert "未定价原因" in (item.note or "")

    def test_fractional_thickness_trace_uses_decimal_until_currency_rounding(self, resolver):
        item = calc_material(
            "S50C",
            Decimal("0.0137375"),
            Decimal("0.05"),
            resolver.lookup,
            calculation_trace={
                "area_mm2": Decimal("5000"),
                "thickness_mm": Decimal("0.35"),
                "volume_mm3": Decimal("1750.00"),
                "density_g_cm3": Decimal("7.85"),
            },
        )

        assert item.quantity == pytest.approx(0.0137375)
        assert item.unit_price == 9.0
        assert item.amount == 0.13
        assert "area_mm2=5000" in (item.evidence or "")
        assert "thickness_mm=0.35" in (item.evidence or "")
        assert "volume_mm3=1750.00" in (item.evidence or "")
        assert "density_g_cm3=7.85" in (item.evidence or "")


class TestMachiningCalculator:
    def test_cnc_calculation(self, resolver):
        item = calc_machining("CNC", 0.6, resolver.lookup)
        assert item.source == PriceSource.C
        assert item.amount == pytest.approx(48.0, rel=0.01)

    def test_unknown_process(self, resolver):
        item = calc_machining("UnknownProcess99", 1.0, resolver.lookup)
        assert item.source == PriceSource.U

    def test_estimate_cnc_hours(self):
        hours = estimate_cnc_hours(4, 4)
        assert hours >= 0.5


class TestSurfaceCalculator:
    def test_known_surface(self, resolver):
        item = calc_surface("鍍鉻", 86.9, resolver.lookup)
        assert item is not None
        assert item.source == PriceSource.C
        assert item.amount == pytest.approx(434.5, rel=0.01)

    def test_unknown_surface(self, resolver):
        item = calc_surface("未知處理", 10.0, resolver.lookup)
        assert item is not None
        assert item.source == PriceSource.U


class TestFrameCalculator:
    def test_profile(self, resolver):
        item = calc_frame_profile("鋁型材40x40", 9800, resolver.lookup)
        assert item.amount >= 150.0  # 9.8m × rate (≥15/m)

    def test_joints(self, resolver):
        item = calc_frame_joints(20, resolver.lookup)
        assert item.amount == 100.0


class TestAssemblyCalculator:
    def test_assembly(self, resolver):
        item = calc_assembly("GUARD", 3.0, resolver.lookup)
        assert item.amount == 264.0


class TestUnknownItem:
    def test_has_status_info(self, resolver):
        item = make_unknown_item("material", "SPCC", "price not configured")
        assert item.source == PriceSource.U
        assert item.confidence == QuoteConfidence.UNCERTAIN
        assert item.note is not None
        assert "未定价原因" in (item.note or "")
        assert "price" in (item.note or "")

    def test_not_default_zero(self, resolver):
        """Unknown items explicitly flag themselves, not silently 0."""
        item = make_unknown_item("surface", "陽極氧化", "no price rule")
        # The amount is 0 but the source is U and there's a note
        assert item.amount == 0
        assert item.source == PriceSource.U
        assert item.note is not None

    def test_unknown_process_keeps_estimated_hours(self, resolver):
        item = calc_machining("焊接", 1.5, resolver.lookup)

        assert item.source == PriceSource.U
        assert item.quantity == 1.5
        assert item.unit == "小时"
        assert "公司尚未发布" in (item.evidence or "")


class TestCalculationEvidence:
    def test_evidence_string(self):
        ev = CalculationEvidence(
            formula="weight × price",
            input_values={"weight": 86.9, "price": 9.0},
            result=782.1,
        )
        s = ev.to_string()
        assert "weight=86.9" in s
        assert "price=9.0" in s
        assert "weight × price" in s
        assert "782.1" in s


# ============================================================================
# J003 + W001 full pipeline
# ============================================================================

class TestJ003FullRuleEngine:
    @pytest.fixture
    def j003_items(self, resolver, tmp_path):
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        msp.add_line((0, 0), (928, 0)); msp.add_line((928, 0), (928, 796))
        msp.add_line((928, 796), (0, 796)); msp.add_line((0, 796), (0, 0))
        for i in range(4):
            msp.add_circle((200 + i * 150, 398), radius=3)
        msp.add_text("S50C", height=8).set_placement((10, 810))
        msp.add_text("6-M6", height=5).set_placement((200, 400))
        msp.add_text("表面鍍鉻", height=5).set_placement((10, 820))
        path = tmp_path / "J003.dxf"; doc.saveas(str(path))
        reader = DxfReader(); ir = reader.read(path)
        geo = GeometricExtractor().extract(ir.drawing.raw_entities)
        mfg = ManufacturingExtractor().extract(geo)
        qf = QuotationMapper().map(mfg, geo)
        all_items = []
        for mq in qf.machining:
            all_items.extend(resolver.resolve_machining(mq))
        return all_items

    def test_four_items(self, j003_items):
        # material + CNC + TAP + surface = 4 items
        assert len(j003_items) >= 4

    def test_all_sources_c(self, j003_items):
        # Known material/process/surface should all be C
        non_u = [i for i in j003_items if i.source != PriceSource.U]
        for item in non_u:
            assert item.source == PriceSource.C

    def test_all_have_evidence(self, j003_items):
        for item in j003_items:
            assert item.evidence is not None, f"Missing evidence for {item.name}"

    def test_total_quote(self, j003_items):
        q = Quote(id="Q-J003", drawing_id="DWG-J003", part_number="UC1000005854",
                  part_name="J003", material="S50C", items=j003_items)
        assert q.total > 1000
        assert q.unknown_count == 0


class TestW001FullRuleEngine:
    @pytest.fixture
    def w001_items(self, resolver, tmp_path):
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        msp.add_line((0, 0), (1300, 0)); msp.add_line((1300, 0), (1300, 1300))
        msp.add_line((1300, 1300), (0, 1300)); msp.add_line((0, 1300), (0, 0))
        msp.add_text("鋁型材 40×40", height=6).set_placement((10, 1320))
        msp.add_text("防護圍欄", height=6).set_placement((10, 1340))
        msp.add_text("門組件", height=5).set_placement((10, 1360))
        msp.add_text("合頁", height=4).set_placement((10, 1380))
        msp.add_text("角碼", height=4).set_placement((10, 1420))
        path = tmp_path / "W001.dxf"; doc.saveas(str(path))
        reader = DxfReader(); ir = reader.read(path)
        geo = GeometricExtractor().extract(ir.drawing.raw_entities)
        mfg = ManufacturingExtractor().extract(geo)
        qf = QuotationMapper().map(mfg, geo)
        all_items = []
        for fq in qf.frames:
            all_items.extend(resolver.resolve_frame(fq))
        for aq in qf.assemblies:
            all_items.extend(resolver.resolve_assembly(aq))
        return all_items

    def test_frame_items(self, w001_items):
        # profile + joints + assembly labor
        assert len(w001_items) >= 3

    def test_industry_sources(self, w001_items):
        sources = {i.source for i in w001_items}
        assert PriceSource.E in sources  # Frame uses industry rates

    def test_total_quote(self, w001_items):
        q = Quote(id="Q-W001", drawing_id="DWG-W001", part_number="UC2020083221",
                  part_name="W001", material="鋁型材", items=w001_items)
        assert q.total > 200  # Frame profile + joints + assembly
        assert q.unknown_count == 0


class TestUnknownMaterialCase:
    def test_unknown_material_produces_u_item(self, resolver):
        from quotation.domain.quotation_feature import MachiningQuotationFeature
        mq = MachiningQuotationFeature(feature_id="test", material="UnknownAlloy99", weight_kg=10.0,
                                       process_hints=["CNC"], hole_count=2)
        items = resolver.resolve_machining(mq)
        mat = [i for i in items if i.category == "material"][0]
        assert mat.source == PriceSource.U
        assert mat.note is not None
        # CNC should still work
        cnc = [i for i in items if i.category == "process"]
        assert len(cnc) >= 1
        assert cnc[0].source == PriceSource.C
