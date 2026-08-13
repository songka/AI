"""Tests for HistoricalFeature domain model."""

from __future__ import annotations

import pytest

from quotation.domain.historical import HistoricalFeature


class TestHistoricalFeature:
    def test_create_minimal(self):
        h = HistoricalFeature(
            id="hf-001",
            part_no="UC1000005854",
        )
        assert h.id == "hf-001"
        assert h.part_no == "UC1000005854"
        assert h.overall_length == 0.0
        assert h.historical_price == 0.0
        assert h.price_source == "BOM"
        assert h.hole_count == 0

    def test_create_full(self):
        h = HistoricalFeature(
            id="hf-001",
            part_no="UC1000005854",
            part_code="J003",
            part_name="底板",
            material="S50C",
            material_raw="S50C",
            overall_length=928.0,
            overall_width=796.0,
            overall_height=15.0,
            dimensions_raw="928*796*15",
            weight_kg=86.91,
            volume_mm3=11070720.0,
            hole_count=12,
            thread_specs=["M6", "M8"],
            contour_type="rectangular",
            surface_treatment="熱處理",
            surface_raw="熱處理",
            process_hint="CNC+熱處理",
            tolerance_grade="IT7",
            historical_price=1425.0,
            price_source="BOM",
            price_date="2025-06-01",
            source_bom="GCS-BOM.xlsx",
            source_bom_row=158,
            source_dwg="UC1000005854-J003.DWG",
            project_name="GCS-雙滑台打磨設備",
            created_at="2026-08-01T10:00:00",
        )
        assert h.material == "S50C"
        assert h.overall_length == 928.0
        assert h.weight_kg == 86.91
        assert h.hole_count == 12
        assert len(h.thread_specs) == 2
        assert h.surface_treatment == "熱處理"
        assert h.historical_price == 1425.0
        assert h.source_dwg == "UC1000005854-J003.DWG"

    def test_create_a6061_part(self):
        """R001 — A6061 aluminum."""
        h = HistoricalFeature(
            id="hf-002",
            part_no="UC1002009711",
            part_code="R001",
            material="A6061-T6",
            overall_length=250.0,
            overall_height=15.0,
            volume_mm3=736310.0,
            weight_kg=1.99,
            surface_treatment="陽極氧化",
            historical_price=209.0,
            source_dwg="UC1002009711-R001.DWG",
        )
        assert h.material == "A6061-T6"
        assert h.historical_price == 209.0

    def test_create_spcc_part(self):
        """SPCC — PENDING price."""
        h = HistoricalFeature(
            id="hf-003",
            part_no="UC1004001529",
            part_code="W002",
            material="SPCC",
            overall_length=56.0,
            overall_width=50.0,
            overall_height=44.0,
            surface_treatment="噴塗(RAL9003)",
            historical_price=16.0,
            source_dwg="UC1004001529_W002.DWG",
        )
        assert h.material == "SPCC"

    def test_json_roundtrip(self):
        h = HistoricalFeature(
            id="hf-001",
            part_no="UC1000005854",
            material="S50C",
            historical_price=1425.0,
            surface_treatment="熱處理",
            thread_specs=["M6"],
        )
        json_str = h.model_dump_json()
        restored = HistoricalFeature.model_validate_json(json_str)
        assert restored.material == "S50C"
        assert restored.thread_specs == ["M6"]
