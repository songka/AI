"""Raw CAD Entity domain models.

Layer 1 of the CAD parsing hierarchy — direct representation of CAD entities
extracted from DXF/DWG files, before any manufacturing interpretation.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Drawing Unit
# ---------------------------------------------------------------------------

class DrawingUnit(str, Enum):
    MM = "MM"
    INCH = "INCH"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Entity Type
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    LINE = "LINE"
    CIRCLE = "CIRCLE"
    ARC = "ARC"
    POLYLINE = "POLYLINE"
    LWPOLYLINE = "LWPOLYLINE"
    TEXT = "TEXT"
    MTEXT = "MTEXT"
    INSERT = "INSERT"
    DIMENSION = "DIMENSION"
    HATCH = "HATCH"
    POINT = "POINT"
    ELLIPSE = "ELLIPSE"
    SPLINE = "SPLINE"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Geometry value objects
# ---------------------------------------------------------------------------

class LineGeometry(BaseModel):
    """LINE entity geometry."""
    start_x: float
    start_y: float
    start_z: float = 0.0
    end_x: float
    end_y: float
    end_z: float = 0.0

    @property
    def length(self) -> float:
        return ((self.end_x - self.start_x) ** 2 + (self.end_y - self.start_y) ** 2) ** 0.5


class CircleGeometry(BaseModel):
    """CIRCLE entity geometry."""
    center_x: float
    center_y: float
    center_z: float = 0.0
    radius: float

    @property
    def diameter(self) -> float:
        return self.radius * 2


class ArcGeometry(BaseModel):
    """ARC entity geometry."""
    center_x: float
    center_y: float
    center_z: float = 0.0
    radius: float
    start_angle: float       # degrees
    end_angle: float         # degrees

    @property
    def angle_span(self) -> float:
        span = self.end_angle - self.start_angle
        return span + 360 if span < 0 else span


class PolylineGeometry(BaseModel):
    """POLYLINE / LWPOLYLINE geometry."""
    vertices: list[list[float]] = Field(default_factory=list)  # [[x,y,z], ...]
    is_closed: bool = False
    vertex_count: int = 0


class TextGeometry(BaseModel):
    """TEXT / MTEXT geometry."""
    content: str
    position_x: float
    position_y: float
    position_z: float = 0.0
    height: float
    rotation: float = 0.0
    width_factor: float = 1.0


class InsertGeometry(BaseModel):
    """INSERT (block reference) geometry."""
    block_name: str
    position_x: float
    position_y: float
    position_z: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0


# ---------------------------------------------------------------------------
# Raw Entity
# ---------------------------------------------------------------------------

Geometry = (
    LineGeometry | CircleGeometry | ArcGeometry | PolylineGeometry |
    TextGeometry | InsertGeometry | None
)


class RawEntity(BaseModel):
    """Raw CAD entity — direct representation from DXF/DWG.

    Layer 1 of the CAD parsing hierarchy.
    No manufacturing interpretation — pure geometry.
    """

    # -- Identity --
    entity_type: EntityType = Field(..., description="DXF entity type")
    handle: str | None = Field(default=None, description="DXF handle (unique ID)")

    # -- Geometry --
    geometry: Geometry = Field(default=None, description="Entity-specific geometry")

    # -- CAD metadata --
    layer: str | None = Field(default=None, description="CAD layer name")
    color: int | None = Field(default=None, description="DXF color index (ACI)")

    # -- Source --
    source_file: str | None = Field(default=None, description="Source file path")
