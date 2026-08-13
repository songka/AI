"""Regression: verify dimension data in Golden Dataset."""

from __future__ import annotations

import pytest

from quotation.infrastructure.parser.dimension_parser import (
    DimensionStatus,
    parse_dimension,
)


class TestGoldenDimensions:
    """D1-D3: Dimension validation."""

    def test_all_machined_have_dimensions(self, golden_data):
        """D1: All machined parts have dimension text."""
        for part in golden_data["parts"]:
            if part["sub_type"] == "加工件":
                assert part["dimensions_raw"] is not None, (
                    f"{part['bom_item']}: dimensions_raw is None"
                )
                assert part["dimensions_raw"] != "", (
                    f"{part['bom_item']}: dimensions_raw is empty"
                )

    def test_all_dimensions_parsable(self, golden_data):
        """D2: Dimension Parser returns non-FAILED for all."""
        for part in golden_data["parts"]:
            if part.get("dimensions_raw"):
                result = parse_dimension(part["dimensions_raw"])
                assert result.status != DimensionStatus.FAILED, (
                    f"{part['bom_item']}: cannot parse '{part['dimensions_raw']}' — {result.issues}"
                )

    def test_all_length_positive(self, golden_data):
        """D3: Parsed length > 0 for all machined parts."""
        for part in golden_data["parts"]:
            dims = part.get("dimensions_parsed", {})
            length = dims.get("length")
            if part["sub_type"] == "加工件" and length is not None:
                assert length > 0, f"{part['bom_item']}: length={length}"

    def test_parsed_matches_raw(self, golden_data):
        """Parsed dimensions should match Golden Data."""
        for part in golden_data["parts"]:
            if part.get("dimensions_raw"):
                result = parse_dimension(part["dimensions_raw"])
                expected = part.get("dimensions_parsed", {})
                if result.length is not None and expected.get("length") is not None:
                    assert result.length == pytest.approx(expected["length"], rel=0.01), (
                        f"{part['bom_item']}: length mismatch {result.length} vs {expected['length']}"
                    )

    def test_dimension_types(self, golden_data):
        """Verify dimension types: circular vs rectangular."""
        circular_items = {"UC1002009711"}  # R001: φ250×15
        for part in golden_data["parts"]:
            if part.get("dimensions_raw"):
                result = parse_dimension(part["dimensions_raw"])
                if part["bom_item"] in circular_items:
                    assert result.is_circular is True, (
                        f"{part['bom_item']}: expected circular"
                    )
