"""Tests for Quote domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quotation.domain.quote import PriceSource, Quote, QuoteConfidence, QuoteItem


class TestPriceSource:
    def test_all_sources(self):
        sources = {s.value for s in PriceSource}
        assert sources == {"C", "H", "E", "AI", "M", "U"}

    def test_source_c_is_company_rule(self):
        assert PriceSource.C == "C"


class TestQuoteConfidence:
    def test_levels(self):
        levels = {c.value for c in QuoteConfidence}
        assert levels == {"high", "medium", "low", "uncertain"}


class TestQuoteItem:
    def test_create(self):
        item = QuoteItem(
            line_id="item-001",
            category="material",
            name="S50C 材料費",
            quantity=86.91,
            unit="kg",
            unit_price=9.0,
            amount=782.19,
            source=PriceSource.C,
            rule_id="MAT_S50C",
            evidence="86.91kg × 9 CNY/kg = ¥782.19",
            confidence=QuoteConfidence.HIGH,
        )
        assert item.category == "material"
        assert item.amount == 782.19
        assert item.source == PriceSource.C
        assert item.confidence == QuoteConfidence.HIGH

    def test_create_unknown_source(self):
        """Item with unknown price."""
        item = QuoteItem(
            line_id="item-u01",
            category="surface",
            name="SPCC 噴塗 (價格待確認)",
            quantity=1.0,
            unit="ST",
            unit_price=0.0,
            amount=0.0,
            source=PriceSource.U,
            note="SPCC噴塗價格未設定",
        )
        assert item.source == PriceSource.U
        assert item.unit_price == 0.0

    def test_create_historical(self):
        """Item with price from historical BOM."""
        item = QuoteItem(
            line_id="item-h01",
            category="purchased",
            name="外購組件",
            quantity=1.0,
            unit="ST",
            unit_price=2900.0,
            amount=2900.0,
            source=PriceSource.H,
            bom_ref="UC2020083221",
        )
        assert item.source == PriceSource.H
        assert item.bom_ref == "UC2020083221"

    def test_provide_evidence(self):
        item = QuoteItem(
            line_id="item-001",
            category="material",
            name="材料費",
            source=PriceSource.C,
            evidence="928×796×15mm × 7.85g/cm³ = 86.9kg × 9元/kg",
        )
        assert item.evidence is not None


class TestQuote:
    def test_create_empty(self):
        q = Quote(id="q-001", drawing_id="dwg-001")
        assert q.id == "q-001"
        assert q.total == 0.0
        assert q.unknown_count == 0

    def test_create_with_items(self):
        items = [
            QuoteItem(
                line_id="1",
                category="material",
                name="S50C 材料費",
                quantity=86.91,
                unit="kg",
                unit_price=9.0,
                amount=782.19,
                source=PriceSource.C,
                rule_id="MAT_S50C",
                confidence=QuoteConfidence.HIGH,
            ),
            QuoteItem(
                line_id="2",
                category="process",
                name="CNC加工",
                quantity=2.0,
                unit="hour",
                unit_price=80.0,
                amount=160.0,
                source=PriceSource.C,
                rule_id="PROC_CNC",
                confidence=QuoteConfidence.HIGH,
            ),
            QuoteItem(
                line_id="3",
                category="surface",
                name="熱處理",
                quantity=86.91,
                unit="kg",
                unit_price=11.0,
                amount=956.01,
                source=PriceSource.C,
                rule_id="SURF_HEAT",
                confidence=QuoteConfidence.HIGH,
            ),
        ]
        q = Quote(
            id="q-001",
            drawing_id="dwg-001",
            feature_id="feat-001",
            part_number="UC1000005854",
            part_name="J003",
            material="S50C",
            items=items,
        )
        assert q.total == pytest.approx(1898.20, rel=0.01)
        assert q.subtotal_material == pytest.approx(782.19, rel=0.01)
        assert q.subtotal_process == 160.0
        assert q.subtotal_surface == pytest.approx(956.01, rel=0.01)
        assert q.unknown_count == 0
        assert q.source_summary == {"C": pytest.approx(1898.20, rel=0.01)}

    def test_mixed_sources(self):
        items = [
            QuoteItem(
                line_id="1",
                category="material",
                name="材料",
                amount=500.0,
                source=PriceSource.C,
                confidence=QuoteConfidence.HIGH,
            ),
            QuoteItem(
                line_id="2",
                category="process",
                name="加工",
                amount=200.0,
                source=PriceSource.H,
                confidence=QuoteConfidence.MEDIUM,
            ),
            QuoteItem(
                line_id="3",
                category="surface",
                name="表面處理",
                amount=100.0,
                source=PriceSource.U,
                confidence=QuoteConfidence.UNCERTAIN,
            ),
        ]
        q = Quote(id="q-002", drawing_id="dwg-002", items=items)
        assert q.total == 800.0
        assert q.source_summary == {"C": 500.0, "H": 200.0, "U": 100.0}
        assert q.unknown_count == 1

    def test_unknown_count(self):
        """All price sources that are U should be counted."""
        items = [
            QuoteItem(
                line_id="1", category="material", name="m", amount=100, source=PriceSource.U
            ),
            QuoteItem(
                line_id="2", category="surface", name="s", amount=50, source=PriceSource.U
            ),
            QuoteItem(
                line_id="3", category="process", name="p", amount=200, source=PriceSource.C
            ),
        ]
        q = Quote(id="q-003", drawing_id="dwg-003", items=items)
        assert q.unknown_count == 2

    def test_other_category(self):
        """Items not in standard 4 categories still counted in total."""
        items = [
            QuoteItem(
                line_id="1",
                category="material",
                name="材料",
                amount=100.0,
                source=PriceSource.C,
            ),
            QuoteItem(
                line_id="2",
                category="packaging",
                name="包裝費",
                amount=15.0,
                source=PriceSource.C,
            ),
        ]
        q = Quote(id="q-004", drawing_id="dwg-004", items=items)
        assert q.total == 115.0
