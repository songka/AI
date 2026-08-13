"""Supplier domain models — Phase 4.6.2."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SupplierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"


class Supplier(BaseModel):
    supplier_id: str = Field(..., description="SUP-XXX")
    supplier_name: str
    status: SupplierStatus = SupplierStatus.ACTIVE
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    payment_terms: str | None = None
    currency: str = "CNY"
    default_tax_included: bool = False
    lead_time_days: int | None = None
    quality_rating: str | None = None  # "A"/"B"/"C"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
