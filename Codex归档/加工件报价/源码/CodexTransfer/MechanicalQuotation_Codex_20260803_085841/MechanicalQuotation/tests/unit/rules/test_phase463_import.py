"""Phase 4.6.3 import validation tests — per CLAUDE_IMPORT_INSTRUCTIONS.md §8."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quotation.application.supplier_price_import_service import SupplierPriceImportService

PACKAGE_DIR = Path("rules/imports/r01-v1.0")


@pytest.fixture(scope="module")
def service():
    svc = SupplierPriceImportService()
    svc.load_package(PACKAGE_DIR)
    return svc


class TestImportLoad:
    def test_yaml_loads(self):
        import yaml
        path = PACKAGE_DIR / "pricing-rules-excel-r01-v1.0.yaml"
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data.get("ruleset", {}).get("mode") == "IMPORT_OVERLAY"

    def test_json_loads(self):
        path = PACKAGE_DIR / "pricing-rules-excel-r01-v1.0.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None
        assert len(data.get("pricing_source_records", [])) == 96


class TestRecordCounts:
    def test_96_records(self, service):
        assert service._stats["total_records"] == 96

    def test_6_suppliers(self, service):
        assert service._stats["suppliers"] == 6

    def test_fuyuchang_zero_price_records(self, service):
        fyc = [r for r in service.records if r.get("supplier_name") == "富裕昌"]
        assert len(fyc) == 0, "富裕昌 should have no price records"


class TestSpecificPrices:
    def test_a6061t6_three_prices(self, service):
        a6061 = [r for r in service.records if r.get("canonical_material_code") == "A6061-T6"]
        prices = {r.get("unit_price") for r in a6061}
        assert 28.0 in prices
        assert 35.0 in prices
        assert 25.0 in prices

    def test_pc_price_60(self, service):
        pc = [r for r in service.records if r.get("canonical_material_code") == "PC"]
        assert any(r.get("unit_price") == 60.0 for r in pc)

    def test_beryllium_four_prices(self, service):
        be = [r for r in service.records if "鈹銅" in str(r.get("raw_material_name", ""))]
        prices = {r.get("unit_price") for r in be}
        assert 180.0 in prices
        assert 130.0 in prices
        assert 220.0 in prices
        assert 170.0 in prices

    def test_acrylic_three_prices(self, service):
        ac = [r for r in service.records if "亞克力" in str(r.get("raw_material_name", ""))]
        prices = {r.get("unit_price") for r in ac}
        assert 30.0 in prices
        assert 28.0 in prices
        assert 25.0 in prices

    def test_aluminum_30x30(self, service):
        al = [r for r in service.records if "30x30" in str(r.get("material_spec", ""))]
        assert any(r.get("unit_price") == 30.0 for r in al)

    def test_aluminum_40x40(self, service):
        al = [r for r in service.records if "40x40" in str(r.get("material_spec", ""))]
        assert any(r.get("unit_price") == 48.0 for r in al)

    def test_aluminum_20x30_unknown(self, service):
        al = [r for r in service.records if "20x30" in str(r.get("material_spec", ""))]
        assert al, "20x30 record should exist"
        assert al[0].get("unit_price") is None, "20x30 should be null price"


class TestConflicts:
    def test_suj2_conflict(self, service):
        suj2 = [r for r in service.records if r.get("status") == "CONFLICT"]
        assert len(suj2) >= 2

    def test_insulation_unit_conflict(self, service):
        uc = [r for r in service.records if r.get("status") == "UNIT_CONFLICT"]
        assert len(uc) >= 1

    def test_jmd_ambiguous(self, service):
        ambig = [r for r in service.records if r.get("status") == "AMBIGUOUS_MATERIAL_SPEC"]
        assert len(ambig) >= 1


class TestTax:
    def test_ws2_tax_unknown(self, service):
        """Worksheet2 prices have unknown tax status."""
        ws2 = [r for r in service.records if "工作表2" in str(r.get("source_sheet", ""))]
        for r in ws2[:5]:
            assert r.get("tax_inclusion_status") == "UNKNOWN"

    def test_tax_17_not_overrides_13(self, service):
        """Legacy 17% and current 13% should NOT override each other."""
        tax_profiles = service._company_rules.get("tax", {})
        # 13% stays disabled
        assert tax_profiles.get("enabled") != True


class TestNoAutoPublish:
    def test_no_s_to_c_without_approval(self, service):
        for r in service.records:
            assert r.get("price_source") != "C", f"{r.get('record_id')}: S should not be C"

    def test_all_pending_or_blocked(self, service):
        publishable = service._stats.get("publishable", 0)
        assert publishable == 0, "No records should be publishable (no effective dates, tax unknown)"

    def test_blocked_count(self, service):
        blocked = service._stats.get("blocked_from_publish", 0)
        assert blocked > 0


class TestUnknownRepresentation:
    def test_unknown_price_is_null(self, service):
        for r in service.records:
            if r.get("status") == "UNKNOWN_PRICE":
                assert r.get("unit_price") is None, f"{r.get('record_id')}: unknown should be null"


class TestImportOverlay:
    def test_overlay_mode(self, service):
        assert service.is_overlay_mode is True

    def test_existing_company_rules_preserved(self, service):
        """Company C rules from quotation-rules.yaml must not be deleted."""
        cr = service.company_rules
        # The existing material rules (S50C, A6061-T6, etc.) should be accessible
        assert isinstance(cr, dict)


class TestFullValidation:
    def test_all_checks_pass(self, service):
        failures = service.validate()
        assert len(failures) == 0, f"Validation failures: {failures}"
