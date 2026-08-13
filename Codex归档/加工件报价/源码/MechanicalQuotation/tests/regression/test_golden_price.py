"""Regression: verify price data in Golden Dataset."""

from __future__ import annotations

import pytest


class TestGoldenPrice:
    """P1-P3: Price validation."""

    def test_all_prices_positive(self, golden_data):
        """P1: All parts have historical_price > 0."""
        for part in golden_data["parts"]:
            assert part["historical_price"] > 0, (
                f"{part['bom_item']}: price is {part['historical_price']}"
            )

    def test_all_price_source_is_bom(self, golden_data):
        """P2: All parts have price_source = 'BOM'."""
        for part in golden_data["parts"]:
            assert part["price_source"] == "BOM", (
                f"{part['bom_item']}: price_source={part['price_source']}"
            )

    def test_prices_in_reasonable_range(self, golden_data):
        """P3: Prices should be in reasonable range (not outliers)."""
        for part in golden_data["parts"]:
            price = part["historical_price"]
            material = part.get("material", "")
            # Rough sanity checks per material type
            if material == "S50C":
                assert 100 <= price <= 5000, f"{part['bom_item']}: S50C price {price} out of range"
            elif material == "A6061-T6":
                assert 10 <= price <= 500, f"{part['bom_item']}: A6061 price {price} out of range"
            elif material == "SPCC":
                assert 5 <= price <= 200, f"{part['bom_item']}: SPCC price {price} out of range"
            elif material == "SUS304":
                assert 5 <= price <= 500, f"{part['bom_item']}: SUS304 price {price} out of range"

    def test_known_prices_match(self, golden_data):
        """Verify specific known prices from BOM."""
        price_map = {p["bom_item"]: p["historical_price"] for p in golden_data["parts"]}
        assert price_map.get("UC1000005854") == 1425.0
        assert price_map.get("UC1002009711") == 209.0
        assert price_map.get("UC1002009712") == 61.0
        assert price_map.get("UC1002009713") == 38.0
        assert price_map.get("UC1007000773") == 14.0
        assert price_map.get("UC2020083221") == 2900.0
