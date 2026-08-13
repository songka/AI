"""Initialize the SMB supplier master from the audited legacy import package."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from quotation.application.settings_service import UserSettingsService
from quotation.domain.supplier import Supplier
from quotation.infrastructure.smb.client import SmbStorageClient
from quotation.infrastructure.supplier.repository import SupplierRepository


def bootstrap_supplier_master(
    source_path: str | Path,
    smb_root: str | Path,
) -> dict:
    source = Path(source_path)
    package = json.loads(source.read_text(encoding="utf-8"))
    source_suppliers = list(package.get("supplier_master", []))
    client = SmbStorageClient(smb_root)
    client.initialize_layout()
    repository = SupplierRepository(client.resolve("suppliers"))
    if repository.path.exists():
        return {
            "状态": "已跳过",
            "原因": "供应商主档已经存在",
            "供应商数量": len(repository.list()),
        }
    now = datetime.now(timezone.utc).isoformat()
    for item in source_suppliers:
        tax_status = str(item.get("default_tax_inclusion_status") or "UNKNOWN")
        repository.create(
            Supplier(
                supplier_id=item["supplier_id"],
                supplier_name=item["supplier_name"],
                status="ACTIVE",
                contact_person=item.get("contact_person"),
                phone=item.get("phone"),
                email=item.get("email"),
                address=item.get("address"),
                payment_terms=item.get("payment_terms"),
                currency=item.get("currency") or "CNY",
                default_tax_included=(
                    True
                    if tax_status == "INCLUDED"
                    else False
                    if tax_status == "EXCLUDED"
                    else None
                ),
                lead_time_days=item.get("lead_time_days"),
                quality_rating=item.get("quality_rating"),
                notes=item.get("notes"),
                created_at=now,
                updated_at=now,
            )
        )
    return {
        "状态": "已建立",
        "供应商数量": len(source_suppliers),
        "目标": "suppliers/suppliers.json",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="建立 SMB 供应商主档（不覆盖已有资料）")
    parser.add_argument(
        "--source",
        default="rules/imports/r01-v1.0/pricing-rules-excel-r01-v1.0.json",
    )
    parser.add_argument("--smb-root", default=UserSettingsService().load()["smb_root"])
    args = parser.parse_args()
    print(
        json.dumps(
            bootstrap_supplier_master(args.source, args.smb_root),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
