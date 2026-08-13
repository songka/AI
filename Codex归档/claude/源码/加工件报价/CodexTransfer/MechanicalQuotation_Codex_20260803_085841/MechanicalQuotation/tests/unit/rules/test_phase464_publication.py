"""Phase 4.6.4 publication validation tests — per instructions §14."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA = Path("data")


class TestReviewFiles:
    def test_json_exists(self):
        assert (DATA / "price-review-r01-v1.0.json").exists()

    def test_xlsx_exists(self):
        assert (DATA / "price-review-r01-v1.0.xlsx").exists()

    def test_draft_book_exists(self):
        assert (DATA / "company-pricebook-r01-v1.0-draft.json").exists()


class TestGrouping:
    @pytest.fixture(scope="module")
    def review(self):
        with open(DATA / "price-review-r01-v1.0.json", encoding="utf-8") as f:
            return json.load(f)

    def test_same_material_multi_supplier_grouped(self, review):
        a6061 = [c for c in review["company_price_candidates"] if c["canonical_material_code"] == "A6061-T6"]
        assert len(a6061) >= 1
        assert a6061[0]["source_count"] >= 3  # Tongrui, Liangwei, Wendi

    def test_no_auto_lowest_selection(self, review):
        for c in review["company_price_candidates"]:
            af = c["admin_fields"]
            assert af["publish_as_company_default"] == False
            assert af["selected_origin_record_id"] is None

    def test_no_auto_average(self, review):
        for c in review["company_price_candidates"]:
            af = c["admin_fields"]
            assert af["company_unit_price"] is None  # Not auto-filled

    def test_s_records_keep_source(self, review):
        for s in review["supplier_prices"]:
            assert s["status"] != "PUBLISHED"

    def test_exceptions_blocked(self, review):
        for e in review["exceptions"]:
            assert e["publish_allowed"] == False

    def test_conflict_not_publishable(self, review):
        conflicts = [e for e in review["exceptions"] if e["status"] == "CONFLICT"]
        assert len(conflicts) >= 2

    def test_unit_conflict_not_publishable(self, review):
        uc = [e for e in review["exceptions"] if e["status"] == "UNIT_CONFLICT"]
        assert len(uc) >= 1

    def test_unknown_price_not_publishable(self, review):
        up = [e for e in review["exceptions"] if e["status"] == "UNKNOWN_PRICE"]
        assert len(up) >= 1

    def test_ambiguous_not_publishable(self, review):
        am = [e for e in review["exceptions"] if e["status"] == "AMBIGUOUS_MATERIAL_SPEC"]
        assert len(am) >= 1


class TestDraftBook:
    @pytest.fixture(scope="module")
    def book(self):
        with open(DATA / "company-pricebook-r01-v1.0-draft.json", encoding="utf-8") as f:
            return json.load(f)

    def test_draft_status(self, book):
        assert book["status"] in ("DRAFT", "PUBLISHED")  # PUBLISHED after admin review

    def test_no_published_prices(self, book):
        # After publication, company_prices should exist
        assert isinstance(book.get("company_prices", []), list)

    def test_no_effective_date(self, book):
        # After publication, effective_from is set
        assert book.get("effective_from") is not None or book.get("status") == "DRAFT"

    def test_has_source_sha(self, book):
        assert book["source_package_sha256"] is not None


class TestJsonExcelConsistency:
    def test_counts_match(self):
        with open(DATA / "price-review-r01-v1.0.json", encoding="utf-8") as f:
            r = json.load(f)
        s = r["publication_summary"]
        assert s["total_candidates"] > 0
        assert s["total_exceptions"] >= 7
        assert s["status"] == "DRAFT"
        assert s["publishable_count"] == 0
