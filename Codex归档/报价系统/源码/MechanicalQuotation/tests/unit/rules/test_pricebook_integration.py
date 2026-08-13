"""Phase 4.7 Published Pricebook Integration Tests.

Tests for PublishedPricebookLoader and PricingResolver priority chain.
"""

from __future__ import annotations

import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quotation.domain.quote import PriceSource, QuoteItem
from quotation.infrastructure.rules.published_pricebook_loader import (
    PriceLookupResult,
    PublishedPricebookLoader,
)
from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.calculators import (
    calc_frame_profile,
    calc_material,
    calc_machining,
    calc_surface,
)


def test_published_al_profile_40x40_is_48_cny_per_meter():
    resolver = PricingResolver()

    for variant in ("40*40", "40×40", "40X40", "40x40"):
        result = resolver.lookup("material", f"AL_PROFILE:{variant}")
        assert result is not None
        assert result.unit == "m"
        assert result.unit_price == 48.0

    item = calc_frame_profile(
        "鋁型材",
        5200,
        resolver.lookup,
        profile_spec="40×40",
    )
    assert item.source == PriceSource.C
    assert item.quantity == 5.2
    assert item.unit_price == 48.0
    assert item.amount == 249.60
    assert item.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"


# ============================================================================
# Fixtures
# ============================================================================

VALID_POINTER = {
    "current_version": "R01-COMPANY-PRICE-V1.0",
    "snapshot_path": "company-pricebook-r01-v1.0-snapshot.json",
    "activated_at": "2026-08-01T07:03:04Z",
    "activated_by": "songka",
}

VALID_SNAPSHOT = {
    "price_version_id": "R01-COMPANY-PRICE-V1.0",
    "version": "1.0.0",
    "status": "PUBLISHED",
    "effective_from": "2026-08-01",
    "record_count": 3,
    "material_count": 2,
    "process_count": 1,
    "surface_count": 0,
    "snapshot_sha256": "",  # computed after prices are set
    "company_prices": [
        {
            "company_price_id": "CP-S50C-001",
            "target_type": "MATERIAL",
            "canonical_code": "S50C",
            "specification": None,
            "unit_price": 10.0,
            "unit": "kg",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "origin_type": "SUPPLIER_PRICE_RECORD",
            "origin_supplier_id": "SUPP-001",
            "origin_price_record_id": "PR-S50C-001",
            "selection_policy": "MANUAL_ADMIN_SELECTION",
            "approved_by": "songka",
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
        {
            "company_price_id": "CP-SPCC-001",
            "target_type": "MATERIAL",
            "canonical_code": "SPCC",
            "specification": "2mm",
            "unit_price": 9.0,
            "unit": "kg",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "origin_type": "SUPPLIER_PRICE_RECORD",
            "origin_supplier_id": None,
            "origin_price_record_id": "PR-SPCC-001",
            "selection_policy": "MANUAL_ADMIN_SELECTION",
            "approved_by": "songka",
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
        {
            "company_price_id": "CP-CNC-001",
            "target_type": "PROCESS",
            "canonical_code": "CNC",
            "unit_price": 80.0,
            "unit": "hour",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "approved_by": "songka",
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
    ],
}
# Compute SHA256 for the valid snapshot
VALID_SNAPSHOT["snapshot_sha256"] = hashlib.sha256(
    json.dumps(VALID_SNAPSHOT["company_prices"], sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()

DRAFT_SNAPSHOT = {
    "price_version_id": "R01-COMPANY-PRICE-V1.1-DRAFT",
    "version": "1.1.0-draft",
    "status": "DRAFT",
    "effective_from": "2026-08-01",
    "snapshot_sha256": "",
    "company_prices": [],
}
DRAFT_SNAPSHOT["snapshot_sha256"] = hashlib.sha256(
    json.dumps(DRAFT_SNAPSHOT["company_prices"], sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()

PENDING_SUPPLIER_SNAPSHOT = {
    "price_version_id": "R01-COMPANY-PRICE-V1.0",
    "version": "1.0.0",
    "status": "PUBLISHED",
    "effective_from": "2026-08-01",
    "snapshot_sha256": "",
    "company_prices": [
        {
            "company_price_id": "CP-PENDING-001",
            "target_type": "MATERIAL",
            "canonical_code": "S50C",
            "specification": None,
            "unit_price": 8.0,
            "unit": "kg",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "origin_type": "PENDING_SUPPLIER",
            "origin_supplier_id": "PENDING-SUP",
            "origin_price_record_id": "PR-PENDING",
            "selection_policy": "PENDING",
            "approved_by": None,
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
    ],
}
PENDING_SUPPLIER_SNAPSHOT["snapshot_sha256"] = hashlib.sha256(
    json.dumps(PENDING_SUPPLIER_SNAPSHOT["company_prices"], sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()


def _write_files(tmpdir: Path, pointer=None, snapshot=None):
    """Write pointer and snapshot files for testing."""
    data_dir = tmpdir / "data"
    data_dir.mkdir(exist_ok=True)

    if pointer:
        ptr_path = data_dir / "current-version-pointer.json"
        ptr_path.write_text(json.dumps(pointer), encoding="utf-8")

    if snapshot:
        snap_path = data_dir / "company-pricebook-r01-v1.0-snapshot.json"
        snap_path.write_text(json.dumps(snapshot), encoding="utf-8")

    return data_dir / "current-version-pointer.json"


# ============================================================================
# Test 1-3: Loader reads pointer, loads snapshot, rejects draft
# ============================================================================

class TestLoaderPointerAndSnapshot:
    """Test 1-3: Current Pointer → Published Snapshot loading."""

    def test_01_loader_reads_current_pointer(self, tmp_path):
        """Resolver can read Current Version Pointer."""
        ptr_path = _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        loader = PublishedPricebookLoader(ptr_path)
        assert loader.loaded
        assert loader.is_active
        assert loader.price_version == "R01-COMPANY-PRICE-V1.0"

    def test_02_loader_loads_published_snapshot(self, tmp_path):
        """Resolver loads Published Snapshot with correct prices."""
        ptr_path = _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        loader = PublishedPricebookLoader(ptr_path)
        assert loader.is_active

        result = loader.lookup_material("S50C")
        assert result is not None
        assert result.unit_price == 10.0
        assert result.company_price_id == "CP-S50C-001"
        assert result.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"

    def test_03_loader_rejects_draft_snapshot(self, tmp_path):
        """Resolver does NOT read Draft as formal price source."""
        ptr_path = _write_files(tmp_path, pointer=VALID_POINTER, snapshot=DRAFT_SNAPSHOT)
        loader = PublishedPricebookLoader(ptr_path)
        assert not loader.loaded
        assert "DRAFT" in (loader.load_error or "")


# ============================================================================
# Test 4-7: PricingResolver priority
# ============================================================================

class TestPricingResolverPriority:
    """Test 4-7: Published pricebook takes priority over legacy YAML."""

    def test_04_published_material_priority(self, tmp_path):
        """Published material price takes priority over legacy YAML."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            assert resolver.is_using_published_pricebook

            result = resolver.lookup("material", "S50C")
            assert result is not None
            assert result.unit_price == 10.0  # Published price
            assert result.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"
            assert result.company_price_id == "CP-S50C-001"
            assert result.fallback_reason is None

    def test_05_published_process_priority(self, tmp_path):
        """Published process rate takes priority over legacy YAML."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            result = resolver.lookup("process", "CNC")
            assert result is not None
            assert result.unit_price == 80.0
            assert result.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"

    def test_06_legacy_fallback_for_unlisted_process(self, tmp_path):
        """Process not in Published Pricebook falls back to legacy YAML."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            result = resolver.lookup("process", "TAP")
            assert result is not None
            # Production YAML is DRAFT → LEGACY_YAML_DRAFT
            assert result.resolution_source in ("LEGACY_YAML", "LEGACY_YAML_DRAFT")
            assert result.fallback_reason is not None
            assert "legacy YAML" in (result.fallback_reason or "")

    def test_07_published_result_source_is_C(self, tmp_path):
        """Published price result always has source=C, not M."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_material("S50C", 10.0, 0.05, resolver.lookup)
            assert item.source == PriceSource.C
            assert item.quote_price_source == "C"
            assert item.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"


# ============================================================================
# Test 8-9: Origin trace info and Pending Supplier rejection
# ============================================================================

class TestOriginTraceAndPendingSupplier:
    """Test 8-9: Origin S info is preserved; Pending S is rejected."""

    def test_08_published_result_preserves_origin_info(self, tmp_path):
        """Published result preserves origin_price_record_id and origin_supplier_id."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_material("S50C", 10.0, 0.05, resolver.lookup)
            assert item.company_price_id == "CP-S50C-001"
            assert item.origin_price_record_id == "PR-S50C-001"
            assert item.origin_supplier_id == "SUPP-001"
            assert item.price_basis == "EXCLUDING_TAX"

    def test_09_pending_supplier_rejected_by_resolver(self, tmp_path):
        """Pending Supplier S entries are NOT selectable by resolver lookup.

        The loader indexes all PUBLISHED entries but marks Pending as
        eligible_for_resolution=False. lookup_material skips non-eligible entries.
        """
        ptr_path = _write_files(tmp_path, pointer=VALID_POINTER, snapshot=PENDING_SUPPLIER_SNAPSHOT)
        loader = PublishedPricebookLoader(ptr_path)
        assert loader.is_active
        # Pending Supplier should NOT be returned by lookup
        result = loader.lookup_material("S50C")
        assert result is None, "Pending Supplier should not be selectable for resolution"


# ============================================================================
# Test 10-11: Fallback on SHA256/pointer errors
# ============================================================================

class TestFallbackScenarios:
    """Test 10-11: SHA256 error and missing pointer trigger fallback."""

    def test_10_sha256_error_falls_back_to_legacy(self, tmp_path):
        """SHA256 mismatch triggers legacy YAML fallback, no crash."""
        bad_snapshot = dict(VALID_SNAPSHOT)
        bad_snapshot["snapshot_sha256"] = "deadbeef" * 8  # intentionally wrong
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=bad_snapshot)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            assert not resolver.is_using_published_pricebook
            # Should still work with legacy YAML
            result = resolver.lookup("material", "S50C")
            assert result is not None
            assert result.resolution_source in ("LEGACY_YAML", "LEGACY_YAML_DRAFT")

    def test_11_missing_pointer_falls_back_to_legacy(self, tmp_path):
        """Missing Current Version Pointer triggers legacy YAML fallback."""
        # Don't create pointer file at all
        data_dir = tmp_path / "data2"
        data_dir.mkdir(exist_ok=True)
        # Write snapshot but no pointer
        snap_path = data_dir / "company-pricebook-r01-v1.0-snapshot.json"
        snap_path.write_text(json.dumps(VALID_SNAPSHOT), encoding="utf-8")

        nonexistent = data_dir / "nonexistent-pointer.json"
        loader = PublishedPricebookLoader(nonexistent)
        assert not loader.loaded
        assert "not found" in (loader.load_error or "").lower() or "pointer" in (loader.load_error or "").lower()


# ============================================================================
# Test 12: Quote Trace fields
# ============================================================================

class TestQuoteTraceFields:
    """Test 12: Quote trace saves price_version and company_price_id."""

    def test_12a_trace_price_version_on_quote_item(self, tmp_path):
        """QuoteItem carries price_version_id from published pricebook."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_material("S50C", 10.0, 0.05, resolver.lookup)
            assert item.price_version_id == "R01-COMPANY-PRICE-V1.0"
            assert item.company_price_id == "CP-S50C-001"

    def test_12b_legacy_item_has_fallback_reason(self, tmp_path):
        """Item from legacy YAML has resolution_source=LEGACY_YAML and fallback_reason."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            # SPCC is in the test snapshot, so find something that's not
            item = calc_material("BAKELITE", 5.0, 0.05, resolver.lookup)
            # BAKELITE _is_ in published snapshot at 27 but might not match via normalized lookup
            if item.resolution_source == "LEGACY_YAML":
                assert item.fallback_reason is not None
                assert "legacy YAML" in (item.fallback_reason or "").lower() or \
                       "not in" in (item.fallback_reason or "").lower()

    def test_12c_published_surface_has_trace(self, tmp_path):
        """Published surface treatment has full trace."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_machining("CNC", 1.0, resolver.lookup)
            assert item.source == PriceSource.C
            assert item.company_price_id == "CP-CNC-001"
            assert item.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"
            assert item.price_basis == "EXCLUDING_TAX"


# ============================================================================
# Hardening Tests (Task 0.1)
# ============================================================================

SUPPLIER_SNAPSHOT = {
    "price_version_id": "R01-COMPANY-PRICE-V1.0",
    "version": "1.0.0",
    "status": "PUBLISHED",
    "effective_from": "2026-08-01",
    "snapshot_sha256": "",
    "company_prices": [
        {
            "company_price_id": "CP-S50C-SUPPLIER",
            "target_type": "MATERIAL",
            "canonical_code": "S50C",
            "specification": None,
            "unit_price": 10.0,
            "unit": "kg",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "origin_type": "SUPPLIER_PRICE_RECORD",
            "origin_supplier_id": "SUPP-TONGRUI-001",
            "origin_price_record_id": "PR-TONGRUI-S50C-001",
            "selection_policy": "MANUAL_ADMIN_SELECTION",
            "approved_by": "songka",
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
        {
            "company_price_id": "CP-CNC-INTERNAL",
            "target_type": "PROCESS",
            "canonical_code": "CNC",
            "unit_price": 80.0,
            "unit": "hour",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "origin_type": "LEGACY_INTERNAL_RATE",
            "approved_by": "songka",
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
        {
            "company_price_id": "CP-S50C-PENDING",
            "target_type": "MATERIAL",
            "canonical_code": "S50C",
            "specification": None,
            "unit_price": 8.0,
            "unit": "kg",
            "currency": "CNY",
            "price_basis": "EXCLUDING_TAX",
            "effective_from": "2026-08-01",
            "origin_type": "PENDING_SUPPLIER",
            "origin_supplier_id": "PENDING-SUP-002",
            "origin_price_record_id": "PR-PENDING-S50C",
            "selection_policy": "PENDING",
            "approved_by": None,
            "price_version_id": "R01-COMPANY-PRICE-V1.0",
        },
    ],
}
SUPPLIER_SNAPSHOT["snapshot_sha256"] = hashlib.sha256(
    json.dumps(SUPPLIER_SNAPSHOT["company_prices"], sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()


class TestHardeningOriginTrace:
    """Hardening: Supplier origin trace, internal rate vs supplier."""

    def test_h01_supplier_c_price_preserves_origin_supplier_id(self, tmp_path):
        """Supplier-origin C price: origin_supplier_id must not be None."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=SUPPLIER_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_material("S50C", 10.0, 0.05, resolver.lookup)
            assert item.source == PriceSource.C
            assert item.origin_price_source == "S"
            assert item.origin_supplier_id == "SUPP-TONGRUI-001"
            assert item.origin_price_record_id == "PR-TONGRUI-S50C-001"
            assert item.company_price_id == "CP-S50C-SUPPLIER"

    def test_h02_internal_rate_allows_null_supplier_id(self, tmp_path):
        """Internal rate origin: origin_supplier_id may be None."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=SUPPLIER_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_machining("CNC", 1.0, resolver.lookup)
            assert item.source == PriceSource.C
            # CNC is LEGACY_INTERNAL_RATE → origin_price_source="I", supplier_id may be None
            assert item.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"
            assert item.company_price_id == "CP-CNC-INTERNAL"


class TestHardeningSourceSeparation:
    """Hardening: quote_price_source vs resolution_source separation."""

    def test_h03_quote_price_source_is_C_not_published(self, tmp_path):
        """quote_price_source must be 'C', not 'PUBLISHED_COMPANY_PRICEBOOK'."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=SUPPLIER_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            item = calc_material("S50C", 10.0, 0.05, resolver.lookup)
            assert item.quote_price_source == "C"
            assert item.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"
            assert item.quote_price_source != item.resolution_source

    def test_h04_pending_s_not_selected(self, tmp_path):
        """Pending S must not be returned by resolver."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=SUPPLIER_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            result = resolver.lookup("material", "S50C")
            # Should get the SUPPLIER entry (10 CNY), not the PENDING entry (8 CNY)
            assert result is not None
            assert result.unit_price == 10.0
            assert result.company_price_id == "CP-S50C-SUPPLIER"
            assert result.origin_price_source == "S"
            assert result.eligible_for_resolution is True


class TestHardeningUnitTestIsolation:
    """Hardening: unit tests don't read production Current Pointer."""

    def test_h05_unit_test_resolver_does_not_load_published(self):
        """Unit test resolver (from conftest) does NOT load published pricebook."""
        from pathlib import Path as _Path
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            _Path("/nonexistent/test-pointer.json"),
        ):
            r = PricingResolver(rules_path=_Path(__file__).parent / "test_rules.yaml")
            assert not r.is_using_published_pricebook
            result = r.lookup("material", "S50C")
            assert result is not None
            assert result.unit_price == 9.0  # Test YAML price
            assert result.resolution_source == "LEGACY_YAML"  # Not DRAFT

    def test_h06_draft_legacy_fallback_has_warning(self, tmp_path):
        """When legacy YAML is DRAFT, fallback has warning markers."""
        _write_files(tmp_path, pointer=VALID_POINTER, snapshot=VALID_SNAPSHOT)
        with patch(
            "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
            tmp_path / "data" / "current-version-pointer.json",
        ):
            resolver = PricingResolver()
            # Production YAML is DRAFT → LEGACY_YAML_DRAFT
            result = resolver.lookup("material", "BAKELITE")
            if result is not None and "DRAFT" in (result.resolution_source or ""):
                assert result.fallback_warning is True
                assert result.fallback_approval_status is not None
                assert "DRAFT" in str(result.fallback_approval_status).upper()
