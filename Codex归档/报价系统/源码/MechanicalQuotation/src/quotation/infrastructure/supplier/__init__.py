"""SMB-backed supplier master and immutable price records."""

from quotation.infrastructure.supplier.repository import (
    SupplierPriceRepository,
    SupplierRepository,
)

__all__ = ["SupplierRepository", "SupplierPriceRepository"]
