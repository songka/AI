"""Atomic JSON repositories for supplier data stored in the SMB public slot."""

from __future__ import annotations

import json
from pathlib import Path

from quotation.domain.supplier import Supplier
from quotation.domain.supplier_price import SupplierPriceRecord


class SupplierRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "suppliers.json"

    def list(self) -> list[Supplier]:
        payload = self._read()
        return [Supplier.model_validate(item) for item in payload["suppliers"]]

    def get(self, supplier_id: str) -> Supplier | None:
        key = supplier_id.casefold()
        return next((item for item in self.list() if item.supplier_id.casefold() == key), None)

    def create(self, supplier: Supplier) -> Supplier:
        payload = self._read()
        suppliers = [Supplier.model_validate(item) for item in payload["suppliers"]]
        if any(
            item.supplier_id.casefold() == supplier.supplier_id.casefold()
            for item in suppliers
        ):
            raise ValueError("供应商编号已经存在")
        if any(
            item.supplier_name.casefold() == supplier.supplier_name.casefold()
            for item in suppliers
        ):
            raise ValueError("供应商名称已经存在")
        suppliers.append(supplier)
        self._write(payload, suppliers)
        return supplier

    def update(self, supplier: Supplier) -> Supplier:
        payload = self._read()
        suppliers = [Supplier.model_validate(item) for item in payload["suppliers"]]
        if not any(item.supplier_id == supplier.supplier_id for item in suppliers):
            raise KeyError(supplier.supplier_id)
        if any(
            item.supplier_id != supplier.supplier_id
            and item.supplier_name.casefold() == supplier.supplier_name.casefold()
            for item in suppliers
        ):
            raise ValueError("供应商名称已经存在")
        changed = [
            supplier if item.supplier_id == supplier.supplier_id else item
            for item in suppliers
        ]
        self._write(payload, changed)
        return supplier

    def delete(self, supplier_id: str) -> None:
        payload = self._read()
        suppliers = [Supplier.model_validate(item) for item in payload["suppliers"]]
        remaining = [item for item in suppliers if item.supplier_id != supplier_id]
        if len(remaining) == len(suppliers):
            raise KeyError(supplier_id)
        self._write(payload, remaining)

    def _read(self) -> dict:
        if not self.path.is_file():
            return {"schema_version": 1, "revision": 0, "suppliers": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return {
                "schema_version": int(payload.get("schema_version", 1)),
                "revision": int(payload.get("revision", 0)),
                "suppliers": list(payload.get("suppliers", [])),
            }
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("供应商主档格式损坏") from exc

    def _write(self, payload: dict, suppliers: list[Supplier]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        output = {
            "schema_version": 1,
            "revision": int(payload.get("revision", 0)) + 1,
            "suppliers": [item.model_dump(mode="json") for item in suppliers],
        }
        temporary = self.path.with_name(".suppliers.json.tmp")
        temporary.write_text(
            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)


class SupplierPriceRepository:
    """Append-only supplier quote records; an existing record is never overwritten."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def append(self, record: SupplierPriceRecord) -> SupplierPriceRecord:
        target = self._path(record.supplier_id, record.price_record_id)
        if target.exists():
            raise FileExistsError(f"供应商报价记录已经存在：{record.price_record_id}")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(target)
        return record

    def get(self, supplier_id: str, record_id: str) -> SupplierPriceRecord | None:
        path = self._path(supplier_id, record_id)
        if not path.is_file():
            return None
        return self._load(path)

    def list(
        self,
        *,
        supplier_id: str | None = None,
        query: str | None = None,
    ) -> list[SupplierPriceRecord]:
        base = self.root / supplier_id if supplier_id else self.root
        if not base.is_dir():
            return []
        records = [self._load(path) for path in sorted(base.rglob("PR-*.json"))]
        if query:
            needle = query.casefold()
            records = [
                item
                for item in records
                if any(
                    needle in str(value or "").casefold()
                    for value in (
                        item.price_record_id,
                        item.supplier_name,
                        item.material_code,
                        item.material_spec,
                        item.process_code,
                        item.surface_code,
                        item.quote_number,
                    )
                )
            ]
        return sorted(records, key=lambda item: item.created_at or "", reverse=True)

    def has_records(self, supplier_id: str) -> bool:
        path = self.root / supplier_id
        return path.is_dir() and next(path.glob("PR-*.json"), None) is not None

    def _path(self, supplier_id: str, record_id: str) -> Path:
        if not supplier_id or not record_id or any(
            token in supplier_id or token in record_id for token in ("/", "\\", "..")
        ):
            raise ValueError("供应商编号或报价记录编号不合法")
        return self.root / supplier_id / f"{record_id}.json"

    @staticmethod
    def _load(path: Path) -> SupplierPriceRecord:
        try:
            return SupplierPriceRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"供应商报价记录格式损坏：{path.name}") from exc
