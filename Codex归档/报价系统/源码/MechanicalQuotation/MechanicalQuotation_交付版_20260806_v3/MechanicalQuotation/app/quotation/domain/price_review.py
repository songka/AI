"""Administrator decisions for immutable supplier price records."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class PriceReviewStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PriceReviewRecord(BaseModel):
    """Append-only review result; the original supplier record is never changed."""

    review_id: str
    price_record_id: str
    supplier_id: str
    status: PriceReviewStatus
    review_comment: str | None = None
    reviewed_by: str
    reviewed_by_name: str
    reviewed_at: str
    source_sha256: str
    previous_price_version_id: str | None = None
    published_price_version_id: str | None = None
    published_company_price_id: str | None = None

