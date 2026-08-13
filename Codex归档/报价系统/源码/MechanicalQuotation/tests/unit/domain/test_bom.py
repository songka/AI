"""Tests for BOM domain model — Phase 2.0.1 extended."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quotation.domain.bom import BomEntry, BomSheet, ParsedPart


# ============================================================================
# BomEntry tests
# ============================================================================

class TestBomEntry:
    # -- Existing tests (Phase 1) —

    def test_create_minimal(self):
        e = BomEntry(item="UC1000005854", description="S50C plate")
        assert e.item == "UC1000005854"
        assert e.description == "S50C plate"
        assert e.level == 0
        assert e.quantity == 1.0
        assert e.unit_cost == 0.0
        assert e.extended_cost == 0.0

    def test_create_real_data(self):
        """Real BOM data: UC1000005854-J003."""
        e = BomEntry(
            item="UC1000005854",
            description="原材料;加工件;S50C;J003;928*796*15;熱處理",
            level=2,
            parent_item="UB100D000654",
            item_type="Purchased item",
            uom="EA",
            quantity=1.0,
            unit_cost=1425.0,
            extended_cost=1425.0,
            bom_source_file="GCS-雙滑台打磨設備-BOM.xlsx",
        )
        assert e.item == "UC1000005854"
        assert e.level == 2
        assert e.parent_item == "UB100D000654"
        assert e.unit_cost == 1425.0
        assert e.extended_cost == 1425.0
        assert "S50C" in e.description

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            BomEntry(item="test")  # type: ignore[call-arg] — missing description

    def test_negative_quantity(self):
        with pytest.raises(ValidationError):
            BomEntry(item="X", description="desc", quantity=-1.0)

    def test_supplier(self):
        e = BomEntry(
            item="UC1000005854",
            description="test",
            supplier="XX精密加工廠",
        )
        assert e.supplier == "XX精密加工廠"

    # -- New tests (Phase 2.0.1) —

    def test_source_tracking(self):
        """BomEntry must track source file, sheet, and row."""
        e = BomEntry(
            item="UC1000005854",
            description="test",
            source_file="GCS-雙滑台打磨設備-BOM.xlsx",
            source_sheet="工作表1",
            source_row=158,
        )
        assert e.source_file == "GCS-雙滑台打磨設備-BOM.xlsx"
        assert e.source_sheet == "工作表1"
        assert e.source_row == 158

    def test_source_defaults(self):
        """source_file/sheet/row have sensible defaults."""
        e = BomEntry(item="X", description="test")
        assert e.source_file == ""
        assert e.source_sheet == "工作表1"
        assert e.source_row == 0

    def test_notes_field(self):
        """Col J 備註 should be preserved."""
        e = BomEntry(item="X", description="test", notes="急件，需3天內交貨")
        assert e.notes == "急件，需3天內交貨"


# ============================================================================
# ParsedPart tests
# ============================================================================

class TestParsedPart:
    # -- Existing tests (Phase 1, updated for semantic change) —

    def test_create_machined_part(self):
        """加工件: category=原材料, sub_type=加工件."""
        p = ParsedPart(
            bom_item="UC1000005854",
            source_row=158,
            category="原材料",
            sub_type="加工件",
            material="S50C",
            part_code="J003",
            dimensions_raw="928*796*15",
            surface_treatment="熱處理",
            unit_cost=1425.0,
            drawing_ref="UC1000005854-J003.DWG",
            is_quotable=True,
            is_matched=True,
        )
        assert p.category == "原材料"
        assert p.sub_type == "加工件"
        assert p.material == "S50C"
        assert p.part_code == "J003"
        assert p.dimensions_raw == "928*796*15"
        assert p.surface_treatment == "熱處理"
        assert p.drawing_ref == "UC1000005854-J003.DWG"
        assert p.is_quotable is True
        assert p.is_matched is True

    def test_create_minimal(self):
        p = ParsedPart(bom_item="UC1000005854")
        assert p.bom_item == "UC1000005854"
        assert p.material is None
        assert p.part_code is None
        assert p.sub_type is None
        assert p.category is None
        assert p.unit_cost == 0.0
        assert p.is_quotable is False
        assert p.is_matched is False

    def test_feature_ref(self):
        p = ParsedPart(bom_item="UC1000005854", feature_ref="feat-001")
        assert p.feature_ref == "feat-001"

    # -- New tests (Phase 2.0.1) —

    def test_electrical_purchased_part(self):
        """電控外購件: different fields populated."""
        p = ParsedPart(
            bom_item="UC3000030030",
            source_row=100,
            category="原材料",
            sub_type="電控外購件",
            model_number="AS16AP11T-A",
            brand="台達",
            spec="擴展IO模塊",
            unit_cost=370.8,
            is_quotable=False,  # 外購件不用系統報價
        )
        assert p.sub_type == "電控外購件"
        assert p.model_number == "AS16AP11T-A"
        assert p.brand == "台達"
        assert p.spec == "擴展IO模塊"
        assert p.is_quotable is False

    def test_mechanical_purchased_part(self):
        """機構外購件."""
        p = ParsedPart(
            bom_item="UC2020083221",
            source_row=200,
            category="原材料",
            sub_type="機構外購件",
            material="鋁型材",
            dimensions_raw="40*40",
            spec="1300*1300*995",
            unit_cost=2900.0,
            quotation_source="SUPPLIER",
        )
        assert p.sub_type == "機構外購件"
        assert p.quotation_source == "SUPPLIER"

    def test_quotation_source_default(self):
        p = ParsedPart(bom_item="UC1000005854")
        assert p.quotation_source == "BOM"

    def test_source_row_tracking(self):
        p = ParsedPart(bom_item="UC1000005854", source_row=158)
        assert p.source_row == 158


# ============================================================================
# BomSheet tests
# ============================================================================

class TestBomSheet:
    # -- Existing tests (Phase 1) —

    def test_create_empty(self):
        sheet = BomSheet(source_file="test.xlsx")
        assert sheet.source_file == "test.xlsx"
        assert sheet.total_rows == 0
        assert sheet.total_cost == 0.0
        assert sheet.entries == []

    def test_create_with_entries(self):
        entries = [
            BomEntry(item="UC1000005854", description="S50C;J003", unit_cost=1425.0),
            BomEntry(item="UC1002009711", description="A6061;R001", unit_cost=209.0),
        ]
        sheet = BomSheet(
            source_file="BOM.xlsx",
            source_sheet="工作表1",
            total_rows=2,
            project_name="GCS-雙滑台打磨設備",
            entries=entries,
            part_count=2,
            matched_drawings=2,
        )
        assert len(sheet.entries) == 2
        assert sheet.project_name == "GCS-雙滑台打磨設備"
        assert sheet.matched_drawings == 2
        assert sheet.unmatched_drawings == 0

    def test_parsed_parts(self):
        parts = [
            ParsedPart(bom_item="UC1000005854", material="S50C", part_code="J003"),
            ParsedPart(bom_item="UC1002009711", material="A6061-T6", part_code="R001"),
        ]
        sheet = BomSheet(
            source_file="BOM.xlsx",
            total_rows=2,
            parsed_parts=parts,
        )
        assert len(sheet.parsed_parts) == 2
        assert sheet.parsed_parts[0].material == "S50C"

    # -- New tests (Phase 2.0.1) —

    def test_classification_counts(self):
        """BomSheet tracks counts per sub_type."""
        sheet = BomSheet(
            source_file="BOM.xlsx",
            total_rows=3,
            machined_count=82,
            electrical_count=140,
            mechanical_count=66,
            subassembly_count=28,
        )
        assert sheet.machined_count == 82
        assert sheet.electrical_count == 140
        assert sheet.mechanical_count == 66
        assert sheet.subassembly_count == 28

    def test_matched_parts_list(self):
        """BomSheet stores matched ParsedParts separately."""
        matched = [
            ParsedPart(
                bom_item="UC1000005854",
                sub_type="加工件",
                material="S50C",
                is_matched=True,
                drawing_ref="UC1000005854-J003.DWG",
            ),
            ParsedPart(
                bom_item="UC1002009711",
                sub_type="加工件",
                material="A6061-T6",
                is_matched=True,
                drawing_ref="UC1002009711-R001.DWG",
            ),
        ]
        sheet = BomSheet(
            source_file="BOM.xlsx",
            total_rows=2,
            matched_parts=matched,
            matched_drawings=2,
        )
        assert len(sheet.matched_parts) == 2
        assert sheet.matched_parts[0].is_matched is True
        assert sheet.matched_parts[0].drawing_ref == "UC1000005854-J003.DWG"

    def test_source_sheet_tracking(self):
        sheet = BomSheet(source_file="BOM.xlsx", source_sheet="工作表1")
        assert sheet.source_sheet == "工作表1"
