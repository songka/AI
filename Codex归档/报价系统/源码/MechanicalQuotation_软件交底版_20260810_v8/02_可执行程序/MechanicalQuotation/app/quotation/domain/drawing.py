"""Drawing domain model.

Represents a CAD drawing file (DXF/DWG/PDF) and its metadata.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from quotation.domain.raw_entity import DrawingUnit, RawEntity


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DrawingFormat(str, Enum):
    """Source file format."""
    DXF = "DXF"
    DWG = "DWG"
    PDF = "PDF"


class ParseStatus(str, Enum):
    """CAD parse result status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

class TextEntity(BaseModel):
    """A TEXT or MTEXT entity extracted from a CAD drawing."""

    content: str = Field(..., description="Text content")
    position_x: float = Field(..., description="X coordinate")
    position_y: float = Field(..., description="Y coordinate")
    height: float = Field(..., description="Text height in drawing units")
    layer: str | None = Field(default=None, description="CAD layer name")
    entity_type: str = Field(default="TEXT", description="TEXT or MTEXT")


# ---------------------------------------------------------------------------
# Drawing entity
# ---------------------------------------------------------------------------

class Drawing(BaseModel):
    """A single CAD drawing file and its parsed metadata.

    Corresponds to one DXF/DWG/PDF file.
    """

    # -- Identity --
    id: str = Field(..., description="Unique identifier (UUID)")
    file_path: str = Field(..., description="Absolute path to the source file")
    file_name: str = Field(..., description="File name with extension")

    # -- Source --
    source_format: DrawingFormat = Field(..., description="DXF | DWG | PDF")

    # -- Drawing metadata (from title block / text extraction) --
    drawing_number: str | None = Field(
        default=None, description="Drawing number / part number, e.g. 'UC1000005854'"
    )
    part_name: str | None = Field(default=None, description="Part name")
    revision: str | None = Field(default=None, description="Drawing revision")
    material_text: str | None = Field(
        default=None, description="Raw material annotation text"
    )
    scale: str | None = Field(default=None, description="Drawing scale, e.g. '1:1'")

    # -- CAD entities --
    entity_count: int = Field(default=0, ge=0, description="Total number of CAD entities")
    entity_summary: dict[str, int] = Field(
        default_factory=dict,
        description="Entity type counts, e.g. {'LINE': 245, 'CIRCLE': 12}",
    )

    # -- Raw entities (Layer 1 CAD data) --
    raw_entities: list[RawEntity] = Field(
        default_factory=list, description="All raw CAD entities with geometry"
    )
    drawing_unit: DrawingUnit = Field(
        default=DrawingUnit.UNKNOWN, description="Drawing unit (MM/INCH/UNKNOWN)"
    )
    unit_source: str | None = Field(
        default=None, description="Where the unit was determined from"
    )

    # -- Text content --
    all_texts: list[TextEntity] = Field(
        default_factory=list, description="All TEXT/MTEXT entities"
    )
    raw_text_strings: list[str] = Field(
        default_factory=list,
        description="Plain text from all TEXT/MTEXT entities for material/tech search",
    )

    # -- Parse status --
    parse_status: ParseStatus = Field(
        default=ParseStatus.SUCCESS, description="Overall parse result"
    )
    parse_errors: list[str] = Field(default_factory=list, description="Parse error messages")
    parse_warnings: list[str] = Field(default_factory=list, description="Parse warnings")

    # -- Relations --
    feature_id: str | None = Field(default=None, description="Linked Feature.id")
