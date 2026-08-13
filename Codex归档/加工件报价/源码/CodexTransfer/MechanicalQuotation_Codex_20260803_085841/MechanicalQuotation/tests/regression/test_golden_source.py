"""Regression: verify source tracing and data chain completeness."""

from __future__ import annotations

import pytest


class TestGoldenSource:
    """S1-S4: Source tracing validation."""

    def test_all_source_bom_row_valid(self, golden_data):
        """S1-S2: All parts have valid source_bom_row."""
        for part in golden_data["parts"]:
            assert part["source_bom_row"] > 0, (
                f"{part['bom_item']}: source_bom_row={part['source_bom_row']}"
            )
            assert isinstance(part["source_bom_row"], int)

    def test_all_have_dwg_file(self, golden_data):
        """Every part must reference a DWG file."""
        for part in golden_data["parts"]:
            assert part["dwg_file"] is not None
            assert ".DWG" in part["dwg_file"].upper()

    def test_all_have_project_name(self, golden_data):
        """Every part should belong to a project."""
        for part in golden_data["parts"]:
            assert part.get("project_name") == "GCS"

    def test_all_surface_treatment_documented(self, golden_data):
        """Surface treatment should be documented (even if None)."""
        for part in golden_data["parts"]:
            # 'surface_treatment' key must exist (can be None)
            assert "surface_treatment" in part, (
                f"{part['bom_item']}: missing surface_treatment key"
            )

    def test_data_chain_dwg_to_price(self, golden_data):
        """S4: Complete chain DWG → BOM → price."""
        for part in golden_data["parts"]:
            # Every required field must be present
            required = [
                "dwg_file", "bom_item", "material", "dimensions_raw",
                "historical_price", "price_source", "source_bom_row",
                "match_level", "project_name",
            ]
            for field in required:
                assert field in part, f"{part.get('bom_item', '?')}: missing field '{field}'"

    def test_historical_features_complete(self, golden_historical_features):
        """HistoricalFeature built from golden data must have all source fields."""
        for bom_item, hf in golden_historical_features.items():
            assert hf.part_no == bom_item
            assert hf.historical_price > 0
            assert hf.project_name == "GCS"

    def test_golden_count(self, golden_data):
        """Must have exactly 20 parts."""
        assert golden_data["total_parts"] == 20
        assert len(golden_data["parts"]) == 20

    def test_golden_version(self, golden_data):
        """Golden dataset must have version info."""
        assert golden_data["version"] == "1.0"
        assert golden_data["created_at"] is not None
