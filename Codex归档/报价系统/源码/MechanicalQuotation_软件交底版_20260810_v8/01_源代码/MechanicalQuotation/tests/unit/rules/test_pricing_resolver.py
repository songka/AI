"""Tests for Pricing Resolver — J003 and W001 Quote output."""

from __future__ import annotations

import json

import ezdxf
import pytest

from quotation.domain.quotation_feature import (
    AssemblyQuotationFeature,
    FrameQuotationFeature,
    MachiningQuotationFeature,
    SheetMetalQuotationFeature,
)
from quotation.domain.quote import PriceSource, Quote, QuoteConfidence
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.pricing_resolver import PricingResolver


@pytest.fixture
def resolver():
    return PricingResolver()


@pytest.fixture
def mapper():
    return QuotationMapper()


# ============================================================================
# J003: S50C machined plate
# ============================================================================

class TestJ003Quote:
    """J003: 928×796×15 S50C plate, 4×M6, 鍍鉻 → Quote."""

    @pytest.fixture
    def j003_features(self, tmp_path):
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
        mapper = QuotationMapper()
        return mapper.map(mfg, geo), geo

    def test_resolve_machining(self, resolver, j003_features):
        qf, geo = j003_features
        assert len(qf.machining) >= 1
        items = resolver.resolve_machining(qf.machining[0])
        assert len(items) >= 2  # material + process
        # Material should be C source
        mat_items = [i for i in items if i.category == "material"]
        assert len(mat_items) >= 1
        assert mat_items[0].source == PriceSource.C
        assert mat_items[0].amount > 0

    def test_j003_full_quote(self, resolver, j003_features):
        qf, geo = j003_features
        all_items = []
        for mq in qf.machining:
            all_items.extend(resolver.resolve_machining(mq))

        quote = Quote(
            id="Q-J003",
            drawing_id="DWG-J003",
            part_number="UC1000005854",
            part_name="J003",
            material="S50C",
            items=all_items,
        )
        assert quote.total > 0
        # Material source summary should have C
        assert "C" in quote.source_summary

    def test_j003_quote_json(self, resolver, j003_features):
        qf, geo = j003_features
        all_items = []
        for mq in qf.machining:
            all_items.extend(resolver.resolve_machining(mq))
        quote = Quote(id="Q-J003", drawing_id="DWG-J003", part_number="UC1000005854",
                      part_name="J003", material="S50C", items=all_items)
        data = quote.model_dump()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        assert "S50C" in json_str
        assert "material" in json_str
        assert "C" in json_str

    def test_j003_material_price_resolved(self, resolver, j003_features):
        qf, geo = j003_features
        items = resolver.resolve_machining(qf.machining[0])
        mat = [i for i in items if i.category == "material"][0]
        assert mat.rule_id is not None
        assert "S50C" in (mat.rule_id or "")


# ============================================================================
# W001: Aluminum frame + guard
# ============================================================================

class TestW001Quote:
    """W001: 鋁型材防護罩 → Frame + Assembly Quote."""

    @pytest.fixture
    def w001_features(self, tmp_path):
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        msp.add_line((0, 0), (1300, 0)); msp.add_line((1300, 0), (1300, 1300))
        msp.add_line((1300, 1300), (0, 1300)); msp.add_line((0, 1300), (0, 0))
        msp.add_text("鋁型材 40×40", height=6).set_placement((10, 1320))
        msp.add_text("防護圍欄", height=6).set_placement((10, 1340))
        msp.add_text("門組件", height=5).set_placement((10, 1360))
        msp.add_text("合頁", height=4).set_placement((10, 1380))
        msp.add_text("磁吸", height=4).set_placement((10, 1400))
        msp.add_text("把手", height=4).set_placement((10, 1420))
        msp.add_text("角碼", height=4).set_placement((10, 1440))
        path = tmp_path / "W001.dxf"; doc.saveas(str(path))

        reader = DxfReader(); ir = reader.read(path)
        geo = GeometricExtractor().extract(ir.drawing.raw_entities)
        mfg = ManufacturingExtractor().extract(geo)
        mapper = QuotationMapper()
        return mapper.map(mfg, geo), geo

    def test_resolve_frame(self, resolver, w001_features):
        qf, geo = w001_features
        assert len(qf.frames) >= 1
        items = resolver.resolve_frame(qf.frames[0])
        assert len(items) >= 2  # profile + joints
        assert all(i.amount >= 0 for i in items)

    def test_resolve_assembly(self, resolver, w001_features):
        qf, geo = w001_features
        assert len(qf.assemblies) >= 1
        items = resolver.resolve_assembly(qf.assemblies[0])
        assert len(items) >= 1  # labor

    def test_w001_full_quote(self, resolver, w001_features):
        qf, geo = w001_features
        all_items = []
        for fq in qf.frames:
            all_items.extend(resolver.resolve_frame(fq))
        for aq in qf.assemblies:
            all_items.extend(resolver.resolve_assembly(aq))

        quote = Quote(
            id="Q-W001",
            drawing_id="DWG-W001",
            part_number="UC2020083221",
            part_name="W001",
            material="鋁型材",
            items=all_items,
        )
        assert quote.total > 0
        data = quote.model_dump()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        assert "鋁型材" in json_str
        assert quote.total > 0


# ============================================================================
# Sheet metal routing: no unsupported CNC setup charge
# ============================================================================

class TestSheetMetalRouting:
    def test_zero_hole_sheet_has_no_cnc_charge(self, resolver):
        mq = MachiningQuotationFeature(
            feature_id="J029",
            material="SUS304",
            weight_kg=0.48,
            process_hints=["SHEET_METAL"],
            hole_count=0,
            thread_count=0,
        )
        items = resolver.resolve_machining(mq)

        assert any(item.category == "material" for item in items)
        assert not any(item.category == "process" and "CNC" in item.name for item in items)

    def test_hole_evidence_still_routes_to_cnc(self, resolver):
        mq = MachiningQuotationFeature(
            feature_id="plate-with-hole",
            material="SUS304",
            weight_kg=0.48,
            process_hints=["SHEET_METAL", "CNC"],
            hole_count=1,
        )
        items = resolver.resolve_machining(mq)
        assert any(item.category == "process" and "CNC" in item.name for item in items)

    def test_sheet_metal_processes_are_explicit_unknown_items(self, resolver):
        feature = SheetMetalQuotationFeature(
            feature_id="sheet",
            material="SUS304",
            thickness_mm=3,
            cutting_length_mm=2400,
            bend_count=2,
        )

        items = resolver.resolve_sheet_metal(feature)

        assert [item.name for item in items] == [
            "钣金切割加工（未定价）",
            "折弯加工（未定价）",
        ]
        assert all(item.source == PriceSource.U for item in items)
        assert items[0].quantity == 2.4
        assert items[0].unit == "米"
        assert items[1].quantity == 2
        assert items[1].unit == "道"

    def test_thread_process_uses_chinese_name_and_remains_unpriced(self, resolver):
        feature = MachiningQuotationFeature(
            feature_id="thread",
            material="S50C",
            weight_kg=1,
            thread_count=2,
        )

        items = resolver.resolve_machining(feature)
        tapping = next(item for item in items if "攻牙" in item.name)

        assert tapping.name == "攻牙 加工費"
        assert tapping.source == PriceSource.U
        assert tapping.fallback_warning is True

    def test_zero_frame_joints_do_not_create_formal_zero_line(self, resolver):
        feature = FrameQuotationFeature(
            feature_id="frame",
            profile_type="鋁型材",
            profile_length_mm=1000,
            joint_count=0,
        )

        items = resolver.resolve_frame(feature)

        assert len(items) == 1
        assert items[0].name.endswith("材料費")

    def test_unknown_assembly_hours_are_not_formal_zero_price(self, resolver):
        feature = AssemblyQuotationFeature(
            feature_id="assembly",
            assembly_type="FRAME",
            estimated_hours=0,
        )

        item = resolver.resolve_assembly(feature)[0]

        assert item.source == PriceSource.U
        assert item.name == "FRAME 人工費（未定价）"
        assert item.quantity == 1
        assert item.unit == "项"


# ============================================================================
# Source tracking tests
# ============================================================================

class TestSourceTracking:
    def test_c_source_for_known_material(self, resolver):
        mq = MachiningQuotationFeature(feature_id="test", material="S50C", weight_kg=10.0)
        items = resolver.resolve_machining(mq)
        mat = [i for i in items if i.category == "material"][0]
        assert mat.source == PriceSource.C

    def test_u_source_for_unknown_material(self, resolver):
        mq = MachiningQuotationFeature(feature_id="test", material="UnknownAlloy99", weight_kg=10.0)
        items = resolver.resolve_machining(mq)
        mat = [i for i in items if i.category == "material"][0]
        assert mat.source == PriceSource.U

    def test_e_source_for_frame(self, resolver):
        fq = FrameQuotationFeature(feature_id="test", profile_type="鋁型材", profile_length_mm=5000, joint_count=10)
        items = resolver.resolve_frame(fq)
        # Frame profile uses industry estimate (E)
        sources = {i.source for i in items}
        assert PriceSource.E in sources

    def test_all_items_have_confidence(self, resolver):
        mq = MachiningQuotationFeature(feature_id="test", material="S50C", weight_kg=10.0,
                                       process_hints=["CNC"], surface_treatment="鍍鉻")
        items = resolver.resolve_machining(mq)
        for item in items:
            assert item.confidence is not None
            assert item.confidence in (QuoteConfidence.HIGH, QuoteConfidence.MEDIUM,
                                       QuoteConfidence.LOW, QuoteConfidence.UNCERTAIN)

    def test_evidence_field_populated(self, resolver):
        mq = MachiningQuotationFeature(feature_id="test", material="S50C", weight_kg=86.9)
        items = resolver.resolve_machining(mq)
        mat = [i for i in items if i.category == "material"][0]
        assert mat.evidence is not None
        assert "86.9" in (mat.evidence or "")
