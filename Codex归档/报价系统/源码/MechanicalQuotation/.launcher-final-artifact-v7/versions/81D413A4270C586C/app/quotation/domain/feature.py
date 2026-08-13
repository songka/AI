"""Feature domain model.

Represents structured manufacturing features extracted from a Drawing
and/or BOM: dimensions, holes, threads, material, surface treatment,
tolerances, and weight.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from quotation.domain.drawing import TextEntity


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FeatureSource(str, Enum):
    """Origin of the feature data."""
    CAD = "CAD"           # Extracted from CAD geometry
    BOM = "BOM"           # Extracted from BOM description
    BOTH = "BOTH"         # Cross-verified from CAD + BOM
    MANUAL = "MANUAL"     # Manually entered


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    """3D bounding box of the part in mm."""

    min_x: float
    min_y: float
    min_z: float = 0.0
    max_x: float
    max_y: float
    max_z: float = 0.0

    @property
    def length(self) -> float:
        """X-axis span."""
        return self.max_x - self.min_x

    @property
    def width(self) -> float:
        """Y-axis span."""
        return self.max_y - self.min_y

    @property
    def height(self) -> float:
        """Z-axis span."""
        return self.max_z - self.min_z


class Dimensions(BaseModel):
    """Structured part dimensions."""

    length: float = Field(..., description="Overall length (mm)")
    width: float = Field(..., description="Overall width (mm)")
    height: float = Field(..., description="Overall height (mm)")
    raw_text: str | None = Field(
        default=None, description="Original BOM dimension text, e.g. '928*796*15'"
    )


class Hole(BaseModel):
    """A hole feature detected in the part."""

    diameter: float = Field(..., gt=0, description="Hole diameter (mm)")
    center_x: float = Field(..., description="X coordinate of hole center")
    center_y: float = Field(..., description="Y coordinate of hole center")
    depth: float | None = Field(
        default=None, description="Depth for blind holes; None = through hole"
    )
    hole_type: str = Field(
        default="through",
        description="through | blind | tapped | counterbore | countersink",
    )
    thread_spec: str | None = Field(
        default=None, description="Thread specification, e.g. 'M6'"
    )


# ---------------------------------------------------------------------------
# Feature entity
# ---------------------------------------------------------------------------

class Feature(BaseModel):
    """Manufacturing features extracted from a part drawing.

    Combines data from CAD geometry and BOM description.
    """

    # -- Identity --
    id: str = Field(..., description="Unique identifier (UUID)")
    drawing_id: str = Field(..., description="Linked Drawing.id")
    bom_ref: str | None = Field(
        default=None, description="Matching BOM item number, e.g. 'UC1000005854'"
    )

    # -- Overall dimensions --
    bounding_box: BoundingBox | None = Field(default=None, description="3D bounding box")
    overall_length: float = Field(default=0.0, ge=0, description="Overall length (mm)")
    overall_width: float = Field(default=0.0, ge=0, description="Overall width (mm)")
    overall_height: float = Field(default=0.0, ge=0, description="Overall height (mm)")
    dimensions_raw: str | None = Field(
        default=None, description="Raw dimension text from BOM"
    )

    # -- Volume, surface area, weight --
    volume_mm3: float | None = Field(
        default=None, ge=0, description="Part volume from CAD (mm³)"
    )
    surface_area_mm2: float | None = Field(
        default=None, ge=0, description="Surface area for coating pricing (mm²)"
    )
    weight_kg: float | None = Field(
        default=None, ge=0, description="Weight = volume × density (kg)"
    )

    # -- Holes --
    holes: list[Hole] = Field(default_factory=list, description="Detected holes")
    hole_count: int = Field(default=0, ge=0, description="Total hole count")
    through_holes: int = Field(default=0, ge=0, description="Through hole count")
    blind_holes: int = Field(default=0, ge=0, description="Blind hole count")
    tapped_holes: int = Field(default=0, ge=0, description="Threaded hole count")

    # -- Threads --
    threads: list[str] = Field(
        default_factory=list, description="Thread specifications, e.g. ['M6', 'M8']"
    )

    # -- Contour --
    contour_type: str | None = Field(
        default=None, description="rectangular | circular | irregular"
    )
    is_axisymmetric: bool = Field(
        default=False, description="True for turned/lathe parts"
    )

    # -- Material (final normalized value) --
    material_text: str | None = Field(default=None, description="Raw material text")
    material_normalized: str | None = Field(
        default=None, description="Normalized material name, e.g. 'A6061-T6'"
    )

    # -- Surface treatment --
    surface_text: str | None = Field(default=None, description="Raw surface text")
    surface_normalized: str | None = Field(
        default=None, description="Normalized surface treatment name"
    )

    # -- Tolerances --
    tolerances: list[str] = Field(
        default_factory=list, description="Tolerance requirements, e.g. ['平面度 0.01']"
    )
    has_tight_tolerance: bool = Field(
        default=False, description="True if any tolerance < 0.05mm"
    )
    max_tolerance_grade: str | None = Field(
        default=None, description="Highest tolerance grade, e.g. 'IT6'"
    )

    # -- Technical requirements --
    tech_requirements: list[str] = Field(
        default_factory=list,
        description="Technical notes, e.g. ['Ra0.8', '倒角C1']",
    )
    all_texts: list[TextEntity] = Field(
        default_factory=list, description="All text entities from the drawing"
    )

    # -- Source --
    feature_source: FeatureSource = Field(
        default=FeatureSource.CAD, description="Origin of this feature data"
    )

    # -- Computation helpers --
    def calculate_weight(self, density_g_cm3: float) -> float | None:
        """Calculate weight from volume and material density.

        Args:
            density_g_cm3: Material density in g/cm³.

        Returns:
            Weight in kg, or None if volume is not available.
        """
        if self.volume_mm3 is None:
            return None
        # volume_mm3 / 1000 → cm³;  cm³ × density → g;  g / 1000 → kg
        return round((self.volume_mm3 / 1000.0) * density_g_cm3 / 1000.0, 3)
