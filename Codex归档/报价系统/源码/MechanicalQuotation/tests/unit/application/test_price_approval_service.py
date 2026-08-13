from __future__ import annotations

import json

import pytest

from quotation.application.auth_service import AuthService
from quotation.application.price_approval_service import PriceApprovalService
from quotation.application.supplier_maintenance_service import SupplierMaintenanceService
from quotation.domain.price_review import PriceReviewStatus
from quotation.domain.supplier_price import PriceStatus, SupplierPriceRecord, TargetType
from quotation.domain.user import UserRole
from quotation.infrastructure.auth.encrypted_user_store import EncryptedUserStore
from quotation.infrastructure.smb.client import SmbStorageClient
from quotation.infrastructure.supplier.price_review_repository import PriceReviewRepository
from quotation.infrastructure.supplier.repository import (
    SupplierPriceRepository,
    SupplierRepository,
)


def _context(tmp_path):
    root = tmp_path / "smb"
    storage = SmbStorageClient(root)
    storage.initialize_layout()
    snapshot_name = "company-pricebook-base.json"
    storage.write_json_atomic(
        f"prices/published/{snapshot_name}",
        {
            "price_version_id": "BASE-V1",
            "version": "1.0",
            "status": "PUBLISHED",
            "company_prices": [
                {
                    "company_price_id": "CP-OLD",
                    "target_type": "MATERIAL",
                    "canonical_code": "SUS304",
                    "specification": "3mm",
                    "unit_price": 25.0,
                    "unit": "kg",
                    "currency": "CNY",
                    "price_basis": "EXCLUDING_TAX",
                    "effective_from": "2026-01-01",
                    "origin_supplier_id": "SUP-OLD-001",
                    "origin_price_record_id": "PR-OLD",
                }
            ],
        },
    )
    storage.write_json_atomic(
        "prices/published/current-version-pointer.json",
        {"current_version": "BASE-V1", "snapshot_path": snapshot_name},
    )
    storage.write_text_atomic("prices/published/version.txt", "BASE-V1\n")

    auth = AuthService(EncryptedUserStore(tmp_path / "users.json", "approval-test-key-2026"))
    admin = auth.create_initial_admin("admin001", "AdminPass123!", "管理员")
    engineer = auth.create_user(
        admin, "engineer001", "Engineer123!", "工程师", UserRole.ENGINEER
    )
    suppliers = SupplierRepository(root / "suppliers")
    prices = SupplierPriceRepository(root / "suppliers" / "prices")
    maintenance = SupplierMaintenanceService(suppliers, prices, auth)
    supplier = maintenance.create_supplier(
        admin, supplier_id="SUP-LFAF-001", supplier_name="测试供应商"
    )
    reviews = PriceReviewRepository(root / "change-requests" / "price-reviews")
    approval = PriceApprovalService(prices, reviews, storage, auth)
    return storage, auth, admin, engineer, maintenance, supplier, approval


def _create_price(maintenance, actor, supplier_id, **overrides):
    values = {
        "supplier_id": supplier_id,
        "target_type": TargetType.MATERIAL,
        "material_code": "SUS304",
        "material_spec": "3mm",
        "unit_price": 28.5,
        "unit": "kg",
        "effective_from": "2026-08-05",
        "quote_number": "QT-20260805-001",
    }
    values.update(overrides)
    return maintenance.create_price_record(actor, **values)


def test_publishable_record_does_not_require_quote_number_or_source_file():
    record = SupplierPriceRecord(
        price_record_id="PR-NO-DOCUMENT-NUMBER",
        supplier_id="SUP-001",
        target_type=TargetType.MATERIAL,
        material_code="S50C",
        unit_price=10.0,
        unit="kg",
        effective_from="2026-08-10",
        quote_number=None,
        source_file=None,
        status=PriceStatus.PENDING_REVIEW,
    )

    PriceApprovalService._validate_publishable(record)


def test_approve_publishes_new_snapshot_and_keeps_supplier_source_immutable(tmp_path):
    storage, _auth, admin, _engineer, maintenance, supplier, approval = _context(tmp_path)
    source = _create_price(maintenance, admin, supplier.supplier_id)
    original = source.model_dump(mode="json")

    pending = approval.list_items(admin, status="PENDING_REVIEW")
    review = approval.approve(
        admin,
        supplier_id=supplier.supplier_id,
        price_record_id=source.price_record_id,
        review_comment="已核对供应商盖章报价单",
        expected_current_version="BASE-V1",
    )

    assert pending[0]["review_status_display"] == "待审核"
    assert review.status == PriceReviewStatus.APPROVED
    assert review.previous_price_version_id == "BASE-V1"
    assert review.published_price_version_id
    assert maintenance.prices.get(supplier.supplier_id, source.price_record_id).model_dump(
        mode="json"
    ) == original

    pointer = json.loads(
        storage.resolve("prices/published/current-version-pointer.json").read_text(encoding="utf-8")
    )
    assert pointer["current_version"] == review.published_price_version_id
    snapshot = json.loads(
        storage.resolve(f"prices/published/{pointer['snapshot_path']}").read_text(encoding="utf-8")
    )
    published = next(
        item for item in snapshot["company_prices"] if item["canonical_code"] == "SUS304"
    )
    assert published["unit_price"] == 28.5
    assert published["price_basis"] == "EXCLUDING_TAX"
    assert published["origin_supplier_id"] == supplier.supplier_id
    assert published["origin_price_record_id"] == source.price_record_id
    assert len(list(storage.resolve("audit").glob("AUD-PRICE-*.json"))) == 1
    assert approval.list_items(admin, status="APPROVED")[0]["reviewed_by_name"] == "管理员"


def test_tax_included_price_is_converted_to_excluding_tax(tmp_path):
    storage, _auth, admin, _engineer, maintenance, supplier, approval = _context(tmp_path)
    source = _create_price(
        maintenance,
        admin,
        supplier.supplier_id,
        unit_price=117,
        tax_included=True,
        tax_rate=17,
    )

    review = approval.approve(
        admin, supplier_id=supplier.supplier_id, price_record_id=source.price_record_id
    )
    pointer = json.loads(
        storage.resolve("prices/published/current-version-pointer.json").read_text(encoding="utf-8")
    )
    snapshot = json.loads(
        storage.resolve(f"prices/published/{pointer['snapshot_path']}").read_text(encoding="utf-8")
    )
    published = next(
        item
        for item in snapshot["company_prices"]
        if item.get("origin_price_record_id") == source.price_record_id
    )
    assert review.status == PriceReviewStatus.APPROVED
    assert published["unit_price"] == 100.0


def test_reject_requires_reason_and_does_not_change_published_pointer(tmp_path):
    storage, _auth, admin, _engineer, maintenance, supplier, approval = _context(tmp_path)
    source = _create_price(maintenance, admin, supplier.supplier_id)
    pointer_before = storage.resolve("prices/published/current-version-pointer.json").read_bytes()

    with pytest.raises(ValueError, match="必须填写"):
        approval.reject(
            admin,
            supplier_id=supplier.supplier_id,
            price_record_id=source.price_record_id,
            review_comment="",
        )
    review = approval.reject(
        admin,
        supplier_id=supplier.supplier_id,
        price_record_id=source.price_record_id,
        review_comment="报价单缺少有效期",
    )

    assert review.status == PriceReviewStatus.REJECTED
    pointer_after = storage.resolve(
        "prices/published/current-version-pointer.json"
    ).read_bytes()
    assert pointer_after == pointer_before
    assert approval.list_items(admin, status="REJECTED")[0]["review_comment"] == "报价单缺少有效期"
    with pytest.raises(ValueError, match="已经完成审核"):
        approval.approve(
            admin, supplier_id=supplier.supplier_id, price_record_id=source.price_record_id
        )


def test_approval_allows_optional_quote_number_but_blocks_invalid_fields(tmp_path):
    _storage, _auth, admin, engineer, maintenance, supplier, approval = _context(tmp_path)
    source = _create_price(
        maintenance, admin, supplier.supplier_id, material_code="SPCC", effective_from=None
    )

    with pytest.raises(PermissionError):
        approval.list_items(engineer)
    with pytest.raises(ValueError, match="缺少生效日期"):
        approval.approve(
            admin, supplier_id=supplier.supplier_id, price_record_id=source.price_record_id
        )

    valid = _create_price(
        maintenance,
        admin,
        supplier.supplier_id,
        material_code="S50C",
        material_spec=None,
    )
    with pytest.raises(ValueError, match="版本已经变化"):
        approval.approve(
            admin,
            supplier_id=supplier.supplier_id,
            price_record_id=valid.price_record_id,
            expected_current_version="OLD-VERSION",
        )
    assert maintenance.prices.get(supplier.supplier_id, valid.price_record_id).status == (
        PriceStatus.PENDING_REVIEW
    )

    no_evidence = _create_price(
        maintenance,
        admin,
        supplier.supplier_id,
        material_code="Q235",
        material_spec=None,
        quote_number=None,
    )
    review = approval.approve(
        admin,
        supplier_id=supplier.supplier_id,
        price_record_id=no_evidence.price_record_id,
    )
    assert review.status == PriceReviewStatus.APPROVED
    assert review.source_sha256 == approval._source_hash(no_evidence)
