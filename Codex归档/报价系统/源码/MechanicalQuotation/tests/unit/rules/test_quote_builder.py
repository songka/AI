"""Tests for Quote Builder (Phase 4.2)."""

from __future__ import annotations

import json

import ezdxf
import pytest

from quotation.domain.quote import PriceSource, QuoteConfidence, QuoteItem, QuoteStatus
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.calculators import make_unknown_item
from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.quote_builder import QuoteBuilder


@pytest.fixture
def resolver():
    return PricingResolver()


@pytest.fixture
def builder():
    return QuoteBuilder()


# ============================================================================
# J003: Complete machined part
# ============================================================================

class TestJ003Complete:
    @pytest.fixture
    def j003_quote(self, resolver, builder, tmp_path):
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
        items = []
        for mq in qf.machining:
            items.extend(resolver.resolve_machining(mq))
        return builder.build("Q-J003", "DWG-J003", "UC1000005854", "J003", "S50C", items,
                             price_version="1.1", rule_version="1.0")

    def test_status_requires_review_while_tap_rate_is_draft(self, j003_quote):
        assert j003_quote.quotation_status == QuoteStatus.INCOMPLETE.value
        tap_item = next(item for item in j003_quote.items if item.fallback_warning)
        assert tap_item.fallback_warning is True
        assert tap_item.quote_price_source == "U"

    def test_confidence_reflects_unreviewed_tap_rate(self, j003_quote):
        assert 0.6 <= j003_quote.overall_confidence < 0.9
        assert "MEDIUM" in (j003_quote.confidence_reason or "")

    def test_has_version_info(self, j003_quote):
        assert j003_quote.price_version == "1.1"
        assert j003_quote.rule_version == "1.0"

    def test_total_matches_items(self, j003_quote):
        item_sum = sum(i.amount for i in j003_quote.items)
        assert j003_quote.total == pytest.approx(item_sum, rel=0.01)

    def test_full_json(self, j003_quote):
        data = json.dumps(j003_quote.model_dump(), ensure_ascii=False, indent=2)
        assert "INCOMPLETE" in data
        assert "S50C" in data
        assert "price_version" in data


# ============================================================================
# W001: Frame + Assembly
# ============================================================================

class TestW001Complete:
    @pytest.fixture
    def w001_quote(self, resolver, builder, tmp_path):
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
        items = []
        for fq in qf.frames:
            items.extend(resolver.resolve_frame(fq))
        for aq in qf.assemblies:
            items.extend(resolver.resolve_assembly(aq))
        return builder.build("Q-W001", "DWG-W001", "UC2020083221", "W001", "鋁型材", items)

    def test_status_complete(self, w001_quote):
        assert w001_quote.quotation_status == QuoteStatus.COMPLETE.value

    def test_confidence_medium(self, w001_quote):
        assert w001_quote.overall_confidence > 0.3
        assert w001_quote.overall_confidence <= 1.0


# ============================================================================
# Unknown Price Case
# ============================================================================

class TestUnknownCase:
    def test_unknown_makes_incomplete(self, resolver, builder):
        items = [
            make_unknown_item("material", "SPCC", "price not configured"),
            QuoteItem(line_id="CNC-1", category="process", name="CNC", amount=160,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
        ]
        q = builder.build("Q-UNK", "DWG-X", "UC-X", "X", "SPCC", items)
        assert q.quotation_status == QuoteStatus.INCOMPLETE.value
        assert q.overall_confidence <= 0.8  # penalized by unknown item
        assert q.unknown_count >= 1

    def test_all_unknown(self, resolver, builder):
        items = [
            make_unknown_item("material", "AlloyX", "no rule"),
            make_unknown_item("process", "MagicProcess", "no rule"),
        ]
        q = builder.build("Q-ALLU", "DWG-U", "UC-U", "U", None, items)
        assert q.total == 0.0
        assert q.overall_confidence == 0.0
        assert q.quotation_status == QuoteStatus.INCOMPLETE.value


# ============================================================================
# Cost Completion (Phase 4.2 fix)
# ============================================================================

class TestCostCompletion:
    """Tests for _calculate_cost_completion and its integration into Quote."""

    def test_all_known_100_percent(self, builder):
        """All items have known sources → 100%."""
        items = [
            QuoteItem(line_id="M1", category="material", name="S50C", amount=969.31,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
            QuoteItem(line_id="P1", category="process", name="CNC", amount=320,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
        ]
        q = builder.build("Q-K1", "DWG-K1", "P1", "AllKnown", "S50C", items)
        assert q.cost_completion == 100.0

    def test_one_known_one_unknown_50_percent(self, builder):
        """1 known + 1 unknown → 50%."""
        items = [
            QuoteItem(line_id="M1", category="material", name="S50C", amount=100,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
            make_unknown_item("process", "TAP", "no rule"),
        ]
        q = builder.build("Q-50", "DWG-50", "P50", "Half", "S50C", items)
        assert q.cost_completion == 50.0

    def test_two_known_one_unknown_66_67(self, builder):
        """2 known + 1 unknown → ~66.7%."""
        items = [
            QuoteItem(line_id="M1", category="material", name="S50C", amount=100,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
            QuoteItem(line_id="P1", category="process", name="CNC", amount=160,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
            make_unknown_item("surface", "SpecialCoat", "no rule"),
        ]
        q = builder.build("Q-66", "DWG-66", "P66", "TwoOfThree", "S50C", items)
        assert q.cost_completion == pytest.approx(66.7, rel=0.01)

    def test_all_unknown_0_percent(self, builder):
        """All items unknown → 0%."""
        items = [
            make_unknown_item("material", "AlloyX", "no rule"),
            make_unknown_item("process", "MagicP", "no rule"),
        ]
        q = builder.build("Q-U0", "DWG-U0", "PU0", "AllU", None, items)
        assert q.cost_completion == 0.0

    def test_empty_items_0_percent(self, builder):
        """No cost items → 0%."""
        q = builder.build("Q-EMPTY", "DWG-E", "PE", "Empty", None, [])
        assert q.cost_completion == 0.0

    def test_zero_amount_known_source_is_completed(self, builder):
        """amount=0 with known source (not U) → completed item."""
        items = [
            QuoteItem(line_id="Z1", category="purchased", name="FreeSpacer", amount=0,
                      source=PriceSource.M, confidence=QuoteConfidence.MEDIUM),
        ]
        q = builder.build("Q-ZERO", "DWG-Z", "PZ", "ZeroKnown", None, items)
        assert q.cost_completion == 100.0

    def test_quote_has_cost_completion_field(self, builder):
        """QuoteBuilder returns a Quote with cost_completion populated."""
        items = [
            QuoteItem(line_id="M1", category="material", name="S50C", amount=500,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
            make_unknown_item("process", "TAP", "no rule"),
        ]
        q = builder.build("Q-CC", "DWG-CC", "PCC", "CC", "S50C", items)
        assert hasattr(q, "cost_completion")
        assert isinstance(q.cost_completion, float)
        assert 0.0 <= q.cost_completion <= 100.0
        assert q.cost_completion == 50.0  # 1 known / 2 total
