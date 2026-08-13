"""Tests for HistoricalFeature builder — ParsedPart → HistoricalFeature."""

from __future__ import annotations

import pytest

from quotation.domain.bom import ParsedPart
from quotation.infrastructure.parser.historical_builder import build_historical_feature


class TestBuildHistoricalFeature:
    def test_build_s50c_plate(self):
        """J003: 928×796×15 S50C plate with heat treatment."""
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
            is_quotable=True,
        )
        h = build_historical_feature(p, project_name="GCS", density_g_cm3=7.85)

        assert h.part_no == "UC1000005854"
        assert h.part_code == "J003"
        assert h.material == "S50C"
        assert h.overall_length == 928.0
        assert h.overall_width == 796.0
        assert h.overall_height == 15.0
        assert h.surface_treatment == "熱處理"
        assert h.historical_price == 1425.0
        assert h.project_name == "GCS"
        assert h.source_bom_row == 158
        # Weight: 928*796*15 = 11,070,720 mm³ → 86.905 kg
        assert h.weight_kg is not None
        assert h.weight_kg == pytest.approx(86.905, rel=0.01)
        # Process hint
        assert "CNC" in (h.process_hint or "")
        assert "熱處理" in (h.process_hint or "")

    def test_build_a6061_circular(self):
        """R001: φ250×15 A6061."""
        p = ParsedPart(
            bom_item="UC1002009711",
            source_row=120,
            category="原材料",
            sub_type="加工件",
            material="A6061-T6",
            part_code="R001",
            dimensions_raw="φ250×15",
            surface_treatment="陽極氧化",
            unit_cost=209.0,
        )
        h = build_historical_feature(p, density_g_cm3=2.70)

        assert h.material == "A6061-T6"
        assert h.overall_length == 250.0  # diameter
        assert h.overall_height == 15.0  # thickness
        assert h.surface_treatment == "陽極氧化"
        assert "CNC" in (h.process_hint or "")
        assert "陽極" in (h.process_hint or "")

    def test_build_spcc_part(self):
        """W002: SPCC sheet metal."""
        p = ParsedPart(
            bom_item="UC1004001529",
            source_row=200,
            category="原材料",
            sub_type="加工件",
            material="SPCC",
            part_code="W002",
            dimensions_raw="56*50*44",
            surface_treatment="噴塗(RAL9003)",
            unit_cost=16.0,
        )
        h = build_historical_feature(p, density_g_cm3=7.85)

        assert h.material == "SPCC"
        assert h.overall_length == 56.0
        assert h.overall_width == 50.0
        assert h.overall_height == 44.0
        # Process hint for SPCC → sheet metal
        assert "鈑金" in (h.process_hint or "")

    def test_build_without_dimensions(self):
        """Part with no dimension text."""
        p = ParsedPart(
            bom_item="UC1002006858",
            source_row=130,
            category="原材料",
            sub_type="加工件",
            material="A6061-T6",
            unit_cost=71.0,
        )
        h = build_historical_feature(p)
        assert h.overall_length == 0.0
        assert h.weight_kg is None
        assert h.historical_price == 71.0

    def test_build_minimal(self):
        p = ParsedPart(bom_item="UC-TEST", source_row=1)
        h = build_historical_feature(p)
        assert h.part_no == "UC-TEST"
        assert h.material is None
        assert h.historical_price == 0.0

    def test_build_without_density(self):
        """No density → no weight calculation."""
        p = ParsedPart(
            bom_item="UC-TEST",
            source_row=1,
            dimensions_raw="100*50*20",
        )
        h = build_historical_feature(p, density_g_cm3=None)
        assert h.overall_length == 100.0
        assert h.volume_mm3 is not None  # Volume still calculable
        assert h.weight_kg is None  # But no density → no weight
