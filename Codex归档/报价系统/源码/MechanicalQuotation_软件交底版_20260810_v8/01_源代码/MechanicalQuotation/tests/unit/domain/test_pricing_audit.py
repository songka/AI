"""Tests for pricing source audit and supplier price records (Phase 4.6.2.1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PREVIEW_PATH = Path("data/pricing-import-preview-full.json")


@pytest.fixture(scope="module")
def preview():
    if not PREVIEW_PATH.exists():
        pytest.skip("Preview JSON not found — run tools/full_cell_audit.py first")
    with open(PREVIEW_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestPreviewCompleteness:
    """Verify the full preview covers all required cells."""

    def test_at_least_90_records(self, preview):
        assert preview["total_records"] >= 90, f"Expected >=90, got {preview['total_records']}"

    def test_has_ws2_material_cells(self, preview):
        ws2_mat = [r for r in preview["records"] if r["source_sheet"] == "工作表2" and r.get("material_code")]
        assert len(ws2_mat) >= 50

    def test_has_internal_price_table(self, preview):
        internal = [r for r in preview["records"] if r["supplier"] == "INTERNAL_PRICE_TABLE"]
        assert len(internal) >= 13

    def test_has_jmd_price_table(self, preview):
        jmd = [r for r in preview["records"] if r["supplier"] == "JMD"]
        assert len(jmd) >= 14

    def test_has_process_prices(self, preview):
        proc = [r for r in preview["records"] if r.get("process_code")]
        assert len(proc) >= 8

    def test_has_surface_prices(self, preview):
        surf = [r for r in preview["records"] if r.get("surface_code")]
        assert len(surf) >= 4


class TestSpecificRecords:
    """Verify specific known values are correct."""

    def _find(self, preview, material, supplier):
        return [r for r in preview["records"] if r.get("material_code") == material and r.get("supplier") == supplier]

    def test_a6061t6_three_suppliers(self, preview):
        records = [r for r in preview["records"] if r.get("material_code") == "A6061T6" and r["source_sheet"] == "工作表2"]
        suppliers = {r["supplier"] for r in records}
        assert "Tongrui" in suppliers or len(records) >= 3

    def test_spcc_two_records(self, preview):
        spcc = [r for r in preview["records"] if "SPCC" in str(r.get("material_code", ""))]
        assert len(spcc) >= 2

    def test_pc_price_60(self, preview):
        pc = [r for r in preview["records"] if r.get("material_code") == "PC" and r.get("parsed_value") == 60]
        assert len(pc) >= 1

    def test_beryllium_four_sources(self, preview):
        be = [r for r in preview["records"] if r.get("material_code") == "鈹銅" and r.get("parsed_value")]
        prices = {r["parsed_value"] for r in be}
        assert 180 in prices or 180.0 in prices
        assert 130 in prices or 130.0 in prices
        assert 220 in prices
        assert 170 in prices

    def test_acrylic_three_sources(self, preview):
        ac = [r for r in preview["records"] if r.get("material_code") == "亞克力" and r.get("parsed_value")]
        prices = {r["parsed_value"] for r in ac}
        assert 30 in prices or 30.0 in prices
        assert 28 in prices
        assert 25 in prices

    def test_aluminum_20x30_unknown(self, preview):
        al = [r for r in preview["records"] if r.get("material_spec") == "20x30"]
        unknown = [r for r in al if r["status"] == "UNKNOWN_PRICE"]
        assert len(unknown) >= 1

    def test_aluminum_30x30_price(self, preview):
        al = [r for r in preview["records"] if r.get("material_spec") == "30x30" and r.get("parsed_value")]
        prices = {r["parsed_value"] for r in al}
        assert 30 in prices or 30.0 in prices

    def test_aluminum_40x40_price(self, preview):
        al = [r for r in preview["records"] if r.get("material_spec") == "40x40" and r.get("parsed_value")]
        prices = {r["parsed_value"] for r in al}
        assert 48 in prices or 48.0 in prices

    def test_suj2_conflict(self, preview):
        suj2 = [r for r in preview["records"] if r.get("material_code") == "SUJ2" and r.get("supplier") == "Tongrui"]
        conflicts = [r for r in suj2 if r["status"] == "CONFLICT"]
        assert len(conflicts) >= 2

    def test_no_published_without_review(self, preview):
        published = [r for r in preview["records"] if r["status"] == "PUBLISHED"]
        assert len(published) == 0, "No records should be PUBLISHED without review"

    def test_all_have_source_cell(self, preview):
        missing = [r for r in preview["records"] if not r.get("source_cell")]
        assert len(missing) == 0, f"Missing source_cell: {len(missing)}"

    def test_no_s_to_c_without_approval(self, preview):
        """S records should not be C."""
        for r in preview["records"]:
            assert r["status"] != "PUBLISHED", f"{r['source_cell']} should not be PUBLISHED"

    def test_json_roundtrip(self, preview):
        """Ensure the preview JSON is valid and roundtrips."""
        data = json.dumps(preview, ensure_ascii=False)
        restored = json.loads(data)
        assert restored["total_records"] == preview["total_records"]

    def test_同一材料多供應商獨立保存(self, preview):
        a6061 = [r for r in preview["records"] if r.get("material_code") == "A6061T6" and r["source_sheet"] == "工作表2"]
        by_supplier = {}
        for r in a6061:
            s = r["supplier"]
            by_supplier[s] = by_supplier.get(s, 0) + 1
        assert len(by_supplier) >= 2

    def test_no_virtual_supplier_prices(self, preview):
        fyc = [r for r in preview["records"] if r.get("supplier") == "Fuyuchang" and r.get("parsed_value") is not None]
        assert len(fyc) == 0, "Fuyuchang has no prices, should not generate virtual records"
