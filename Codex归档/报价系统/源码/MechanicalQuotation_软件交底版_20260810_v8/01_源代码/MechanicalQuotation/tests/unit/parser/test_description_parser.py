"""Tests for BOM Description Parser — Description → ParsedPart."""

from __future__ import annotations

import pytest

from quotation.infrastructure.parser.description_parser import (
    DescriptionParser,
    ParseStatus,
)


@pytest.fixture
def parser():
    return DescriptionParser()


# ============================================================================
# 加工件 (Machined Parts)
# ============================================================================

class TestMachinedParts:
    def test_standard_machined(self, parser):
        """原材料;加工件;S50C;J003;928*796*15;表面鍍鉻"""
        r = parser.parse("UC1000005854", "原材料;加工件;S50C;J003;928*796*15;表面鍍鉻", source_row=158, unit_cost=1425.0)
        assert r.status == ParseStatus.SUCCESS
        pp = r.parsed_part
        assert pp.category == "原材料"
        assert pp.sub_type == "加工件"
        assert pp.material == "S50C"
        assert pp.part_code == "J003"
        assert pp.dimensions_raw == "928*796*15"
        assert pp.surface_treatment == "表面鍍鉻"
        assert pp.is_quotable is True
        assert pp.unit_cost == 1425.0
        assert pp.source_row == 158

    def test_a6061_anodize(self, parser):
        """原材料;加工件;A6061-T6;R001;φ250×15;表面噴砂陽極銀色"""
        r = parser.parse("UC1002009711", "原材料;加工件;A6061-T6;R001;φ250×15;表面噴砂陽極銀色", unit_cost=209.0)
        assert r.status == ParseStatus.SUCCESS
        pp = r.parsed_part
        assert pp.material == "A6061-T6"
        assert pp.part_code == "R001"
        assert pp.dimensions_raw == "φ250×15"
        assert pp.surface_treatment == "表面噴砂陽極銀色"

    def test_material_normalization_triggered(self, parser):
        """Unknown material triggers warning."""
        r = parser.parse("UC-TEST", "原材料;加工件;UnknownMetal99;X001;100*50*20;陽極")
        pp = r.parsed_part
        assert pp.material == "UnknownMetal99"
        mat_issues = [i for i in r.issues if i.field == "material"]
        assert len(mat_issues) >= 1  # Should warn about unknown material

    def test_missing_dimensions(self, parser):
        """加工件 without dimensions → PARTIAL."""
        r = parser.parse("UC-TEST", "原材料;加工件;S50C;J003;;熱處理")
        assert r.status == ParseStatus.PARTIAL
        pp = r.parsed_part
        assert pp.dimensions_raw is None or pp.dimensions_raw == ""

    def test_missing_material(self, parser):
        """加工件 without material → PARTIAL."""
        r = parser.parse("UC-TEST", "原材料;加工件;;J003;100*50*20")
        assert r.status == ParseStatus.PARTIAL

    def test_empty_segments(self, parser):
        """加工件 with empty segments."""
        r = parser.parse("UC-TEST", "原材料;加工件;;;100*50*20;")
        pp = r.parsed_part
        assert pp.sub_type == "加工件"
        assert pp.material is None
        assert pp.part_code is None
        assert pp.dimensions_raw == "100*50*20"


# ============================================================================
# 電控外購件 (Electrical Purchased)
# ============================================================================

class TestElectricalParts:
    def test_standard_electrical(self, parser):
        """原材料;電控外購件;控制類;PLC擴展;擴展IO模塊;型號:AS16AP11T-A;品牌:台達"""
        r = parser.parse(
            "UC3000030030",
            "原材料;電控外購件;控制類;PLC擴展;擴展IO模塊;型號:AS16AP11T-A;品牌:台達",
            unit_cost=370.8,
        )
        assert r.status == ParseStatus.SUCCESS
        pp = r.parsed_part
        assert pp.category == "原材料"
        assert pp.sub_type == "電控外購件"
        assert pp.is_quotable is False  # 外購件不報價
        assert pp.model_number == "AS16AP11T-A"
        assert pp.brand == "台達"

    def test_electrical_no_model(self, parser):
        """電控件 without model/brand."""
        r = parser.parse("UC-TEST", "原材料;電控外購件;傳感器;光電開關")
        pp = r.parsed_part
        assert pp.sub_type == "電控外購件"
        assert pp.is_quotable is False


# ============================================================================
# 機構外購件 (Mechanical Purchased)
# ============================================================================

class TestMechanicalParts:
    def test_standard_mechanical(self, parser):
        """原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995;白色透明"""
        r = parser.parse(
            "UC2020083221",
            "原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995;白色透明",
            unit_cost=2900.0,
        )
        assert r.status == ParseStatus.SUCCESS
        pp = r.parsed_part
        assert pp.sub_type == "機構外購件"
        assert pp.is_quotable is False
        assert pp.material == "鋁型材"
        assert pp.part_code == "W001"
        assert pp.dimensions_raw == "40*40"

    def test_mechanical_with_brand(self, parser):
        """機構外購件 with brand."""
        r = parser.parse("UC-TEST", "原材料;機構外購件;氣缸;型號:CDM2B20-50;品牌:SMC")
        pp = r.parsed_part
        assert pp.model_number == "CDM2B20-50"
        assert pp.brand == "SMC"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    def test_empty_description(self, parser):
        r = parser.parse("UC-TEST", "")
        assert r.status == ParseStatus.FAILED

    def test_single_segment(self, parser):
        """Only one segment."""
        r = parser.parse("UC-TEST", "原材料")
        assert r.status == ParseStatus.FAILED

    def test_two_segments(self, parser):
        r = parser.parse("UC-TEST", "原材料;加工件")
        pp = r.parsed_part
        assert pp.category == "原材料"
        assert pp.sub_type == "加工件"
        assert r.status == ParseStatus.PARTIAL  # missing material + dims

    def test_extra_segments(self, parser):
        """More than 6 segments — extra should be handled."""
        r = parser.parse("UC-TEST", "原材料;加工件;S50C;J003;100*50*20;熱處理;備註1;備註2;備註3")
        pp = r.parsed_part
        assert pp.surface_treatment == "熱處理"
        assert r.status == ParseStatus.SUCCESS

    def test_whitespace_handling(self, parser):
        """Segments with leading/trailing whitespace."""
        r = parser.parse("UC-TEST", " 原材料 ; 加工件 ; S50C ; J003 ; 100*50*20 ; 熱處理 ")
        pp = r.parsed_part
        assert pp.material == "S50C"
        assert pp.dimensions_raw == "100*50*20"

    def test_unknown_sub_type(self, parser):
        """Sub-type that doesn't match any known category."""
        r = parser.parse("UC-TEST", "原材料;未知類型;XXX;YYY")
        pp = r.parsed_part
        assert pp.sub_type == "未知類型"
        assert pp.is_quotable is False  # Default: not quotable

    def test_chinese_description(self, parser):
        """All-Chinese description without English."""
        r = parser.parse("UC-TEST", "原材料;加工件;普通鋼;底板;1400*1300*785;表面噴塗,顏色:皺紋白,RAL9003")
        pp = r.parsed_part
        assert pp.material == "普通鋼"
        assert pp.dimensions_raw == "1400*1300*785"
        assert "RAL9003" in (pp.surface_treatment or "")

    def test_spcc_sheet_metal(self, parser):
        """SPCC sheet metal part."""
        r = parser.parse("UC1004001529", "原材料;加工件;SPCC;W002;56*50*44;表面噴塗,顏色:皺紋白,RAL9003", unit_cost=16.0)
        pp = r.parsed_part
        assert pp.material == "SPCC"
        assert pp.part_code == "W002"
        assert pp.is_quotable is True


# ============================================================================
# Parse Status
# ============================================================================

class TestParseStatus:
    def test_success(self, parser):
        r = parser.parse("UC-TEST", "原材料;加工件;S50C;J003;100*50*20;熱處理")
        assert r.status == ParseStatus.SUCCESS

    def test_partial_missing_material(self, parser):
        r = parser.parse("UC-TEST", "原材料;加工件;;J003;100*50*20;熱處理")
        assert r.status == ParseStatus.PARTIAL

    def test_partial_missing_dims(self, parser):
        r = parser.parse("UC-TEST", "原材料;加工件;S50C;J003;;熱處理")
        assert r.status == ParseStatus.PARTIAL

    def test_failed_empty(self, parser):
        r = parser.parse("UC-TEST", "")
        assert r.status == ParseStatus.FAILED

    def test_failed_one_segment(self, parser):
        r = parser.parse("UC-TEST", "原材料")
        assert r.status == ParseStatus.FAILED
