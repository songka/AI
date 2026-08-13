# Supplier Management Design

Date: 2026-08-01 | Version: V1.0

---

## 一、服務層架構

```
domain/
  supplier.py          — Supplier model
  supplier_price.py    — SupplierPriceRecord (S source)
  price_book.py        — PriceBookEntry (C source), MaterialLossRule, TaxProfile
  price_selection.py   — SelectionPolicy, PriceSelectionResult

infrastructure/database/
  supplier_repository.py       — SupplierRepository (CRUD)
  supplier_price_repository.py — SupplierPriceRepository (append-only)

application/
  supplier_price_import_service.py    — Import from Excel → SupplierPriceRecord
  supplier_price_validation_service.py — Validate records before approval
  price_selection_service.py          — Select which price to use
  price_publication_service.py        — S → ChangeRequest → C
  supplier_change_request_service.py  — Change Request workflow

rules/
  price_audit.py   — Pricing source audit (read-only dry-run)
```

## 二、SMB Storage

```
SMB:/suppliers/
  suppliers.json              — Supplier master data
  prices/
    {supplier_id}/
      PR-YYYYMMDD-NNN.json    — Append-only price records
  change-requests/
    CR-SUP-YYYYMMDD-NNN.json

Local: C:\ProgramData\MechanicalQuotation\cache\supplier_cache.db (SQLite)
```

## 三、Price Selection Policy

Default: COMPANY_DEFAULT. If no C price, MANUAL.

System MUST NOT auto-select LOWEST or AVERAGE without explicit admin configuration.

## 四、QuotePriceSource (Extended)

```
C  — Company Rule (published, approved)
H  — Historical
E  — Industry Reference
S  — Supplier Quote (NEW)
AI-WEB / AI-EST / AI-HYBRID
M  — Manual
U  — Unknown
```

S can only become C through: S → ChangeRequest → Admin Review → Publish → C with origin_supplier_id traced.

## 五、Import Statuses

| Status | Meaning |
|---|---|
| PARSED | Extracted from Excel, not yet reviewed |
| PENDING_REVIEW | Awaiting admin confirmation |
| APPROVED | Confirmed by admin |
| PUBLISHED | Active in price book |
| REJECTED | Admin rejected |
| CONFLICT | Multiple values for same supplier+material |
| UNIT_CONFLICT | Unit mismatch (e.g., m2 vs kg) |
| UNKNOWN_PRICE | Cell empty or unparseable |

---

*Service implementation deferred until pricing import is approved.*
