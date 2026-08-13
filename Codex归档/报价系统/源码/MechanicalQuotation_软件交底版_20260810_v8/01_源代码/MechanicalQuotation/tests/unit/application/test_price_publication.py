from quotation.application.price_publication import (
    build_current_version_pointer,
    build_supplier_provenance_index,
    origin_supplier_id_for,
    prepare_published_pricebook,
)


def test_supplier_provenance_is_preserved_from_selected_source_record():
    index = build_supplier_provenance_index(
        [
            {"record_id": "PR-001", "supplier_id": "SUP-TONGRUI"},
            {"record_id": "PR-002", "supplier_id": None},
        ]
    )

    assert origin_supplier_id_for("PR-001", index) == "SUP-TONGRUI"
    assert origin_supplier_id_for("PR-002", index) is None


def test_supplier_provenance_does_not_guess_for_unknown_source_record():
    index = build_supplier_provenance_index([])

    assert origin_supplier_id_for("PR-UNKNOWN", index) is None


def test_blank_source_records_are_ignored():
    index = build_supplier_provenance_index(
        [{"record_id": "", "supplier_id": "SUP-SHOULD-NOT-APPEAR"}]
    )

    assert index == {}


def test_reviewed_draft_is_promoted_with_integrity_and_provenance():
    draft = {
        "status": "DRAFT",
        "blocking_errors": 0,
        "notes": "reviewed",
        "company_prices": [
            {
                "company_price_id": "CP-1",
                "target_type": "MATERIAL",
                "canonical_code": "S50C",
                "specification": None,
                "unit_price": 10,
                "unit": "kg",
                "price_basis": "EXCLUDING_TAX",
                "origin_price_record_id": "PR-1",
                "origin_supplier_id": None,
                "price_version_id": "DRAFT",
            },
            {
                "company_price_id": "CP-RAL",
                "target_type": "SURFACE",
                "canonical_code": "COATING_RAL9003",
                "specification": None,
                "unit_price": 25,
                "unit": "m2",
                "price_basis": "EXCLUDING_TAX",
                "origin_price_record_id": None,
                "origin_supplier_id": None,
                "price_version_id": "DRAFT",
            },
        ],
    }
    package = {
        "pricing_source_records": [
            {"record_id": "PR-1", "supplier_id": "SUP-TONGRUI"}
        ]
    }

    published = prepare_published_pricebook(
        draft,
        package,
        price_version_id="R01-COMPANY-PRICE-V1.1",
        version="1.1.0",
        approved_by="admin",
        approved_at="2026-08-03T00:00:00+00:00",
    )
    pointer = build_current_version_pointer(
        published,
        snapshot_path="company-pricebook-r01-v1.1-snapshot.json",
        activated_by="admin",
        activated_at="2026-08-03T00:00:00+00:00",
    )

    assert published["status"] == "PUBLISHED"
    assert published["record_count"] == 2
    assert published["company_prices"][0]["origin_supplier_id"] == "SUP-TONGRUI"
    assert all(
        p["price_version_id"] == "R01-COMPANY-PRICE-V1.1"
        for p in published["company_prices"]
    )
    assert len(published["snapshot_sha256"]) == 64
    assert pointer["current_version"] == "R01-COMPANY-PRICE-V1.1"


def test_non_draft_cannot_be_republished():
    try:
        prepare_published_pricebook(
            {"status": "PUBLISHED"},
            {},
            price_version_id="V2",
            version="2.0.0",
            approved_by="admin",
            approved_at="2026-08-03T00:00:00+00:00",
        )
    except ValueError as exc:
        assert "DRAFT" in str(exc)
    else:
        raise AssertionError("publishing a non-draft must fail")
