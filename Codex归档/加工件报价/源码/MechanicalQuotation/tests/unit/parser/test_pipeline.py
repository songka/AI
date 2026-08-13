"""Full pipeline tests: BOM Description → ParsedPart → HistoricalFeature.

Uses 20 real BOM items from GCS-雙滑台打磨設備.
"""

from __future__ import annotations

import pytest

from quotation.infrastructure.parser.description_parser import DescriptionParser
from quotation.infrastructure.parser.historical_builder import build_historical_feature

# ---------------------------------------------------------------------------
# Material density reference (g/cm³)
# ---------------------------------------------------------------------------
DENSITY = {
    "S50C": 7.85,
    "A6061-T6": 2.70,
    "SPCC": 7.85,
    "SUS304": 7.93,
    "SKD11": 7.85,
    "普通鋼": 7.85,
}

# ---------------------------------------------------------------------------
# 20 real BOM descriptions from GCS-雙滑台打磨設備
# ---------------------------------------------------------------------------
REAL_BOM_ITEMS: list[dict] = [
    {"item": "UC1000005854", "desc": "原材料;加工件;S50C;J003;928*796*15;表面鍍鉻", "cost": 1425.0, "row": 53},
    {"item": "UC1000005855", "desc": "原材料;加工件;S50C;J005;1400*250*15;熱處理", "cost": 712.0, "row": 54},
    {"item": "UC1000005856", "desc": "原材料;加工件;S50C;J006;798*530*15;熱處理", "cost": 874.0, "row": 55},
    {"item": "UC1000005857", "desc": "原材料;加工件;S50C;J007;1400*250*15;熱處理", "cost": 693.0, "row": 56},
    {"item": "UC1002006858", "desc": "原材料;加工件;A6061-T6;J026;92*20*92;表面噴砂陽極銀色", "cost": 71.0, "row": 60},
    {"item": "UC1002009711", "desc": "原材料;加工件;A6061-T6;R001;φ250×15;表面噴砂陽極銀色", "cost": 209.0, "row": 70},
    {"item": "UC1002009712", "desc": "原材料;加工件;A6061-T6;R002;60*70*20;表面噴砂陽極銀色", "cost": 61.0, "row": 71},
    {"item": "UC1002009713", "desc": "原材料;加工件;A6061-T6;R003;60*30*10;表面噴砂陽極銀色", "cost": 38.0, "row": 72},
    {"item": "UC1002009718", "desc": "原材料;加工件;A6061-T6;R004;40*16*13;表面噴砂陽極銀色", "cost": 66.0, "row": 73},
    {"item": "UC1003000436", "desc": "原材料;加工件;普通鋼;J001;1400*1300*785;表面噴塗,顏色:皺紋白,RAL9003", "cost": 7000.0, "row": 80},
    {"item": "UC1004001529", "desc": "原材料;加工件;SPCC;W002;56*50*44;表面噴塗,顏色:皺紋白,RAL9003", "cost": 16.0, "row": 90},
    {"item": "UC1004001886", "desc": "原材料;加工件;SPCC;J036;1208*103.5*2;表面噴塗,顏色:皺紋白,RAL9003", "cost": 28.0, "row": 95},
    {"item": "UC1004001887", "desc": "原材料;加工件;SPCC;F002;794*200*15;表面噴塗,顏色:皺紋白,RAL9003", "cost": 38.0, "row": 100},
    {"item": "UC1004001888", "desc": "原材料;加工件;SPCC;J050;798*50*15;表面噴塗,顏色:皺紋白,RAL9003", "cost": 47.0, "row": 105},
    {"item": "UC1004001889", "desc": "原材料;加工件;SPCC;J027;1300*117.2*2;表面噴塗,顏色:皺紋白,RAL9003", "cost": 38.0, "row": 110},
    {"item": "UC1004001890", "desc": "原材料;加工件;SPCC;J035;1300*117.2*88;表面噴塗,顏色:皺紋白,RAL9003", "cost": 95.0, "row": 115},
    {"item": "UC1004001904", "desc": "原材料;加工件;SPCC;F003;818*200*21;表面噴塗,顏色:皺紋白,RAL9003", "cost": 57.0, "row": 120},
    {"item": "UC1004001905", "desc": "原材料;加工件;SPCC;F001;818*200*21;表面噴塗,顏色:皺紋白,RAL9003", "cost": 57.0, "row": 125},
    {"item": "UC1007000773", "desc": "原材料;加工件;SUS304;J029;80*90*2", "cost": 14.0, "row": 130},
    {"item": "UC2020083221", "desc": "原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995;白色透明", "cost": 2900.0, "row": 167},
]


@pytest.fixture
def parser():
    return DescriptionParser()


# ============================================================================
# Full Pipeline Tests
# ============================================================================

class TestFullPipeline:
    """BOM Description → ParsedPart → HistoricalFeature."""

    @pytest.mark.parametrize("bom", REAL_BOM_ITEMS)
    def test_parse_all_20_items(self, parser, bom):
        """Every real BOM item must parse without FAILED status."""
        r = parser.parse(bom["item"], bom["desc"], source_row=bom["row"], unit_cost=bom["cost"])
        assert r.status != "failed", f"{bom['item']}: {r.status}"
        assert r.parsed_part.bom_item == bom["item"]

    @pytest.mark.parametrize("bom", REAL_BOM_ITEMS)
    def test_build_historical_all_20(self, parser, bom):
        """Every real BOM item must produce a valid HistoricalFeature."""
        r = parser.parse(bom["item"], bom["desc"], source_row=bom["row"], unit_cost=bom["cost"])
        density = DENSITY.get(r.parsed_part.material or "")
        h = build_historical_feature(r.parsed_part, project_name="GCS", density_g_cm3=density or None)
        assert h.part_no == bom["item"]
        assert h.historical_price == bom["cost"]
        assert h.project_name == "GCS"

    def test_pipeline_s50c(self, parser):
        """End-to-end: S50C J003."""
        r = parser.parse("UC1000005854", "原材料;加工件;S50C;J003;928*796*15;表面鍍鉻", source_row=53, unit_cost=1425.0)
        h = build_historical_feature(r.parsed_part, project_name="GCS", density_g_cm3=7.85)
        assert h.material == "S50C"
        assert h.overall_length == 928.0
        assert h.weight_kg == pytest.approx(86.905, rel=0.01)
        assert h.historical_price == 1425.0
        assert "CNC" in (h.process_hint or "")

    def test_pipeline_a6061(self, parser):
        """End-to-end: A6061-T6 R002."""
        r = parser.parse("UC1002009712", "原材料;加工件;A6061-T6;R002;60*70*20;表面噴砂陽極銀色", unit_cost=61.0)
        h = build_historical_feature(r.parsed_part, density_g_cm3=2.70)
        assert h.material == "A6061-T6"
        assert h.overall_length == 60.0
        assert h.overall_width == 70.0
        assert h.overall_height == 20.0
        # 60*70*20 = 84000 mm³, density 2.70 → 0.227 kg
        assert h.weight_kg == pytest.approx(0.227, rel=0.01)

    def test_pipeline_spcc(self, parser):
        """End-to-end: SPCC F001."""
        r = parser.parse("UC1004001905", "原材料;加工件;SPCC;F001;818*200*21;表面噴塗,顏色:皺紋白,RAL9003", unit_cost=57.0)
        h = build_historical_feature(r.parsed_part, density_g_cm3=7.85)
        assert h.material == "SPCC"
        # 818*200*21 = 3435600 mm³, density 7.85 → 26.97 kg
        assert h.weight_kg == pytest.approx(26.97, rel=0.01)
        assert "鈑金" in (h.process_hint or "")

    def test_pipeline_mechanical_purchased(self, parser):
        """機構外購件: is_quotable=False, price preserved as-is."""
        r = parser.parse("UC2020083221", "原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995;白色透明", unit_cost=2900.0)
        pp = r.parsed_part
        assert pp.is_quotable is False
        h = build_historical_feature(pp, project_name="GCS")
        assert h.historical_price == 2900.0
        assert h.part_code == "W001"


# ============================================================================
# 20-Item Batch Statistics
# ============================================================================

class TestBatchStatistics:
    def test_all_20_machined_parts_quotable(self, parser):
        """All 加工件 should have is_quotable=True."""
        machined = [b for b in REAL_BOM_ITEMS if "加工件" in b["desc"]]
        assert len(machined) == 19  # 19 machined + 1 機構外購件

        for bom in machined:
            r = parser.parse(bom["item"], bom["desc"])
            assert r.parsed_part.is_quotable is True, f"{bom['item']}: is_quotable should be True"

    def test_material_distribution(self, parser):
        """Verify material distribution in 20 items."""
        materials = {}
        for bom in REAL_BOM_ITEMS:
            r = parser.parse(bom["item"], bom["desc"])
            mat = r.parsed_part.material or "UNKNOWN"
            materials[mat] = materials.get(mat, 0) + 1
        assert "S50C" in materials
        assert "A6061-T6" in materials
        assert "SPCC" in materials
        assert "SUS304" in materials

    def test_all_have_cost(self, parser):
        """All 20 items have unit_cost > 0."""
        for bom in REAL_BOM_ITEMS:
            assert bom["cost"] > 0, f"{bom['item']}: cost should be > 0"
