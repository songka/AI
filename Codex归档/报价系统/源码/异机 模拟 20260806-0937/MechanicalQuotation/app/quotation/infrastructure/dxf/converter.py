"""Backward-compatible imports for the DWG conversion subsystem."""

from quotation.infrastructure.dwg.converter import (
    ConversionStatus,
    ConverterHealth,
    DwgConversionResult,
    DwgConversionService,
    DwgConverter,
    DwgConverterAdapter,
    DwgConverterLocator,
    OdaDwgConverter,
)

__all__ = [
    "ConversionStatus",
    "ConverterHealth",
    "DwgConversionResult",
    "DwgConversionService",
    "DwgConverter",
    "DwgConverterAdapter",
    "DwgConverterLocator",
    "OdaDwgConverter",
]
