"""Price Selection Policy — controls which price to use."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from quotation.domain.supplier_price import SupplierPriceRecord


class SelectionPolicy(str, Enum):
    MANUAL = "MANUAL"
    COMPANY_DEFAULT = "COMPANY_DEFAULT"
    SPECIFIED_SUPPLIER = "SPECIFIED_SUPPLIER"
    LATEST_EFFECTIVE = "LATEST_EFFECTIVE"
    LOWEST_PRICE = "LOWEST_PRICE"
    AVERAGE_PRICE = "AVERAGE_PRICE"


class PriceSelectionResult(BaseModel):
    candidate_prices: list[SupplierPriceRecord] = Field(default_factory=list)
    selected_price: float | None = None
    selected_supplier: str | None = None
    selection_policy: SelectionPolicy = SelectionPolicy.COMPANY_DEFAULT
    selection_reason: str = ""
    effective_date: str | None = None


# Default policy: COMPANY_DEFAULT. If no company price, MANUAL.
# System MUST NOT auto-select LOWEST or AVERAGE without explicit config.
