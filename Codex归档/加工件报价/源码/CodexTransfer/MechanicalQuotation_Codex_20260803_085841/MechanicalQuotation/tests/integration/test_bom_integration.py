"""Integration tests — real GCS BOM Excel (318 rows)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quotation.infrastructure.excel.bom_reader import BomReader

# ---------------------------------------------------------------------------
# Path to the real BOM
# ---------------------------------------------------------------------------

REAL_BOM_PATH = Path("samples/drawings/GCS-雙滑台打磨設備-BOM.xlsx")


@pytest.fixture(scope="module")
def real_bom_sheet():
    """Load the real 318-row BOM once per test module."""
    if not REAL_BOM_PATH.exists():
        pytest.skip(f"Real BOM not found: {REAL_BOM_PATH}")
    reader = BomReader()
    return reader.read(REAL_BOM_PATH)


# ============================================================================
# Structural tests
# ============================================================================

class TestRealBomStructure:
    """Verify the real BOM loads correctly."""

    def test_loads_without_error(self, real_bom_sheet):
        assert real_bom_sheet is not None
        assert real_bom_sheet.total_rows > 0

    def test_row_count(self, real_bom_sheet):
        """Should have ~318 data rows (or close to it)."""
        assert real_bom_sheet.total_rows >= 300
        assert real_bom_sheet.total_rows <= 330

    def test_source_tracking(self, real_bom_sheet):
        """Every entry must have source_file, source_sheet, source_row."""
        for entry in real_bom_sheet.entries:
            assert entry.source_file != ""
            assert entry.source_sheet != ""
            assert entry.source_row > 0, f"Missing source_row for {entry.item}"

    def test_no_duplicate_source_rows(self, real_bom_sheet):
        """Source rows should be unique (one entry per Excel row)."""
        rows = [e.source_row for e in real_bom_sheet.entries]
        assert len(rows) == len(set(rows)), f"Duplicate source rows found"


# ============================================================================
# Content tests
# ============================================================================

class TestRealBomContent:
    """Verify specific known items exist."""

    def test_finished_good_exists(self, real_bom_sheet):
        items = {e.item for e in real_bom_sheet.entries}
        assert "UA0050000023" in items

    def test_known_machined_parts_exist(self, real_bom_sheet):
        """20 matched parts should be present."""
        items = {e.item for e in real_bom_sheet.entries}
        expected = [
            "UC1000005854",  # J003
            "UC1000005855",  # J005
            "UC1000005856",  # J006
            "UC1000005857",  # J007
            "UC1002006858",  # J026
            "UC1002009711",  # R001
            "UC1002009712",  # R002
            "UC1002009713",  # R003
            "UC1002009718",  # R004
            "UC1003000436",  # J001
            "UC1004001529",  # W002
            "UC1004001886",  # J036
            "UC1004001887",  # F002
            "UC1004001888",  # J050
            "UC1004001889",  # J027
            "UC1004001890",  # J035
            "UC1004001904",  # F003
            "UC1004001905",  # F001
            "UC1007000773",  # J029
            "UC2020083221",  # W001
        ]
        for item in expected:
            assert item in items, f"Expected BOM item {item} not found"

    def test_known_prices_correct(self, real_bom_sheet):
        """Verify known unit costs match the real BOM."""
        price_map = {e.item: e.unit_cost for e in real_bom_sheet.entries}
        assert price_map.get("UC1000005854") == 1425.0
        assert price_map.get("UC1002009711") == 209.0
        assert price_map.get("UC1002009712") == 61.0
        assert price_map.get("UC1002009713") == 38.0

    def test_machined_parts_have_description(self, real_bom_sheet):
        """All UC items should have semicolon-delimited descriptions."""
        uc_entries = [e for e in real_bom_sheet.entries if e.item.startswith("UC")]
        for e in uc_entries:
            assert ";" in e.description, (
                f"UC item {e.item} missing semicolons in description: {e.description[:50]}"
            )


# ============================================================================
# Classification tests
# ============================================================================

class TestRealBomClassification:
    """Verify item_type and level distribution."""

    def test_item_types_present(self, real_bom_sheet):
        types = {e.item_type for e in real_bom_sheet.entries}
        # The real BOM uses these specific strings
        expected = {"Finished good", "Subassembly", "Purchased item", "Phantom item"}
        assert types == expected, f"Unexpected item types: {types}"

    def test_levels_present(self, real_bom_sheet):
        levels = {e.level for e in real_bom_sheet.entries}
        assert 0 in levels  # Finished good
        assert 1 in levels  # Subassemblies
        assert 2 in levels  # Parts

    def test_uc_items_are_level_2(self, real_bom_sheet):
        """Most UC items should be at level 2 (leaf parts)."""
        uc_entries = [e for e in real_bom_sheet.entries if e.item.startswith("UC")]
        levels = {e.level for e in uc_entries}
        # Some may be at level 1 (sub-components)
        assert 2 in levels, f"UC items should include level 2, got: {levels}"


# ============================================================================
# Consistency tests
# ============================================================================

class TestRealBomConsistency:
    """Cross-field consistency checks."""

    def test_cost_fields_are_numeric(self, real_bom_sheet):
        """Unit cost and extended cost must be valid floats, not strings."""
        for e in real_bom_sheet.entries:
            assert isinstance(e.unit_cost, float)
            assert isinstance(e.extended_cost, float)

    def test_no_negative_costs(self, real_bom_sheet):
        for e in real_bom_sheet.entries:
            assert e.unit_cost >= 0
            assert e.extended_cost >= 0

    def test_no_empty_items(self, real_bom_sheet):
        for e in real_bom_sheet.entries:
            assert e.item, f"Empty item at row {e.source_row}"
            assert e.description, f"Empty description at row {e.source_row}"
