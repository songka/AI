from __future__ import annotations

import openpyxl
import pytest

from quotation.application.auth_service import AuthService
from quotation.application.supplier_maintenance_service import SupplierMaintenanceService
from quotation.domain.supplier import SupplierStatus
from quotation.domain.supplier_price import PriceStatus, TargetType
from quotation.infrastructure.auth.encrypted_user_store import EncryptedUserStore
from quotation.infrastructure.supplier.repository import (
    SupplierPriceRepository,
    SupplierRepository,
)


def _context(tmp_path):
    auth = AuthService(EncryptedUserStore(tmp_path / "users.json", "supplier-test-key-2026"))
    admin = auth.create_initial_admin("admin001", "AdminPass123!", "管理员")
    suppliers = SupplierRepository(tmp_path / "smb" / "suppliers")
    prices = SupplierPriceRepository(tmp_path / "smb" / "suppliers" / "prices")
    return auth, admin, SupplierMaintenanceService(suppliers, prices, auth)


def test_supplier_master_crud_is_atomic_and_searchable(tmp_path):
    _auth, admin, service = _context(tmp_path)
    supplier = service.create_supplier(
        admin,
        supplier_id="SUP-LFAF-001",
        supplier_name="东莞测试材料",
        contact_person="张三",
        currency="CNY",
    )

    assert service.get_supplier(admin, supplier.supplier_id).supplier_name == "东莞测试材料"
    assert service.list_suppliers(admin, query="测试")[0].supplier_id == "SUP-LFAF-001"
    changed = service.update_supplier(
        admin, supplier.supplier_id, {"phone": "13800000000", "quality_rating": "A"}
    )
    assert changed.phone == "13800000000"
    assert changed.quality_rating == "A"
    assert not (tmp_path / "smb" / "suppliers" / ".suppliers.json.tmp").exists()

    inactive = service.set_supplier_status(admin, supplier.supplier_id, SupplierStatus.INACTIVE)
    assert inactive.status == SupplierStatus.INACTIVE
    service.delete_supplier(admin, supplier.supplier_id)
    assert service.list_suppliers(admin) == []


def test_supplier_price_is_append_only_and_unknown_is_never_zero(tmp_path):
    _auth, admin, service = _context(tmp_path)
    supplier = service.create_supplier(
        admin, supplier_id="SUP-LFAF-001", supplier_name="东莞测试材料"
    )
    record = service.create_price_record(
        admin,
        supplier_id=supplier.supplier_id,
        target_type=TargetType.MATERIAL,
        material_code="SUS304",
        material_spec="3mm",
        unit_price=28.5,
        unit="kg",
        effective_from="2026-08-04",
        quote_number="QT-001",
    )

    assert record.status == PriceStatus.PENDING_REVIEW
    assert record.created_by == admin.user_id
    assert service.list_price_records(admin, supplier_id=supplier.supplier_id)[0] == record
    with pytest.raises(FileExistsError):
        service.prices.append(record)
    with pytest.raises(ValueError, match="未知价格不能填写为 0"):
        service.create_price_record(
            admin,
            supplier_id=supplier.supplier_id,
            target_type=TargetType.MATERIAL,
            material_code="SPCC",
            unit_price=0,
            unit="kg",
        )


def test_cannot_delete_supplier_with_price_history(tmp_path):
    _auth, admin, service = _context(tmp_path)
    supplier = service.create_supplier(
        admin, supplier_id="SUP-LFAF-001", supplier_name="东莞测试材料"
    )
    service.create_price_record(
        admin,
        supplier_id=supplier.supplier_id,
        target_type=TargetType.PROCESS,
        process_code="CNC",
        unit_price=90,
        unit="hour",
        effective_from="2026-08-04",
    )

    with pytest.raises(ValueError, match="历史报价"):
        service.delete_supplier(admin, supplier.supplier_id)


def test_price_maintenance_requires_permission(tmp_path):
    auth, admin, service = _context(tmp_path)
    viewer = auth.create_user(admin, "viewer001", "ViewerPass123!", "查看者")

    with pytest.raises(PermissionError):
        service.create_supplier(viewer, supplier_id="SUP-X-001", supplier_name="无权限")


def test_import_price_excel_supports_chinese_headers_and_row_errors(tmp_path):
    _auth, admin, service = _context(tmp_path)
    service.create_supplier(admin, supplier_id="SUP-LFAF-001", supplier_name="测试供应商")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "供应商报价"
    sheet.append(["供应商编号", "价格类型", "材料代码", "规格", "未税单价", "单位", "生效日期"])
    sheet.append(["SUP-LFAF-001", "MATERIAL", "SUS304", "3mm", 28.5, "kg", "2026-08-04"])
    sheet.append(["SUP-NOT-FOUND", "MATERIAL", "SPCC", "2mm", 8.5, "kg", "2026-08-04"])
    source = tmp_path / "供应商报价.xlsx"
    workbook.save(source)

    result = service.import_price_excel(admin, str(source))

    assert result["导入成功"] == 1
    assert result["导入失败"] == 1
    record = service.list_price_records(admin)[0]
    assert record.source_file == "供应商报价.xlsx"
    assert record.source_sheet == "供应商报价"
    assert record.source_cell == "E2"
