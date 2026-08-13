# Price Review and Company Price Publication Design

Date: 2026-08-01 | Version: V1.0

## Publication Flow

```
SupplierPriceRecord (S)
  → Admin Review (price-review-r01-v1.0.xlsx)
  → CompanyPriceRecord (C)
  → CompanyPriceBookVersion (DRAFT → PENDING_APPROVAL → PUBLISHED)
```

## Company C Price = New Record (never overwrite S)

S record immutable. C record created with origin_supplier_id + origin_price_record_id trace.

## Publication Checks

1. C price must have effective_from
2. C price must have explicit price_basis (EXCLUDING/INCLUDING_TAX)
3. unit_price > 0
4. Unit must be explicit
5. Source must be traceable
6. Approver not empty
7. CONFLICT/UNIT_CONFLICT/UNKNOWN/AMBIGUOUS blocked
8. No duplicate C default for same material+spec+date range
9. Pending S not used by resolver

## Default Policy

COMPANY_DEFAULT. No auto LOWEST/AVERAGE without admin config.

## Pending S Exclusion

Pending S records must NOT enter formal quotation. Only published C prices are used.

*This design document supplements the implementation in Phase 4.6.4.*
