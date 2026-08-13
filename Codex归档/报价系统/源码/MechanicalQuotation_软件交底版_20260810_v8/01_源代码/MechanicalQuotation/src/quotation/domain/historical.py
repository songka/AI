"""Historical Feature domain model.

Represents a historical part record extracted from BOM + DWG data,
stored in the quotation knowledge base for similarity search.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HistoricalFeature(BaseModel):
    """A historical part record — the knowledge base unit.

    Built from BOM (price + material + surface) + DWG (geometry) data.
    Stored in quotation_history.db for similarity search in Phase 4.
    """

    # -- Identity --
    id: str = Field(..., description="Unique record ID (UUID)")

    # -- Part identifiers --
    part_no: str = Field(..., description="Part/drawing number, e.g. 'UC1000005854'")
    part_code: str | None = Field(default=None, description="Part code, e.g. 'J003'")
    part_name: str | None = Field(default=None)

    # -- Material --
    material: str | None = Field(default=None, description="Normalized material name")
    material_raw: str | None = Field(default=None, description="Original material text")

    # -- Dimensions --
    overall_length: float = Field(default=0.0, ge=0, description="mm")
    overall_width: float = Field(default=0.0, ge=0, description="mm")
    overall_height: float = Field(default=0.0, ge=0, description="mm")
    dimensions_raw: str | None = Field(default=None)

    # -- Weight --
    weight_kg: float | None = Field(default=None, ge=0)
    volume_mm3: float | None = Field(default=None, ge=0)

    # -- Features --
    hole_count: int = Field(default=0, ge=0)
    thread_specs: list[str] = Field(default_factory=list)
    contour_type: str | None = Field(default=None)

    # -- Surface treatment --
    surface_treatment: str | None = Field(default=None)
    surface_raw: str | None = Field(default=None)

    # -- Process hint --
    process_hint: str | None = Field(default=None)
    tolerance_grade: str | None = Field(default=None)

    # -- Historical price (ground truth from BOM) --
    historical_price: float = Field(default=0.0, ge=0, description="Real transaction price (CNY)")
    price_source: str = Field(default="BOM", description="BOM | MANUAL | SUPPLIER")
    price_date: str | None = Field(default=None, description="ISO date")

    # -- Source tracing --
    source_bom: str | None = Field(default=None, description="BOM file path")
    source_bom_row: int = Field(default=0, ge=0, description="BOM Excel row number")
    source_dwg: str | None = Field(default=None, description="DWG file name")
    source_pdf: str | None = Field(default=None, description="PDF file name")

    # -- Project --
    project_name: str | None = Field(default=None)

    # -- Metadata --
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
