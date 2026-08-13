"""Manufacturing Feature domain models — Layer 3 of CAD parsing.

Converts GeometricFeatures into manufacturing-meaningful features:
- HoleFeature: holes with diameter, count, position
- ThreadFeature: threaded holes (M3-M8) linked to hole geometry
- MaterialFeature: material from text annotations
- SurfaceTreatmentFeature: surface treatment from text
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from quotation.domain.geometric_feature import BoundingBox, FeatureValue


class HoleFeature(BaseModel):
    """A detected hole — diameter, count, position, confidence."""

    hole_id: str = Field(..., description="Unique hole ID")
    diameter: FeatureValue = Field(default_factory=FeatureValue)
    count: int = Field(default=1, ge=1)
    position_x: float | None = None
    position_y: float | None = None
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ThreadFeature(BaseModel):
    """A threaded hole — spec, size, linked hole."""

    thread_id: str = Field(..., description="Unique thread ID")
    spec: FeatureValue = Field(default_factory=FeatureValue)   # "M6"
    size: str = ""                                              # "M6"
    count: int = 1
    depth: float | None = None
    linked_hole_id: str | None = None    # Associated HoleFeature
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class MaterialFeature(BaseModel):
    """Material detected from drawing text."""

    material_id: str = Field(..., description="Unique ID")
    raw_text: FeatureValue = Field(default_factory=FeatureValue)
    normalized: FeatureValue = Field(default_factory=FeatureValue)
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SurfaceTreatmentFeature(BaseModel):
    """Surface treatment detected from drawing text."""

    surface_id: str = Field(..., description="Unique ID")
    raw_text: FeatureValue = Field(default_factory=FeatureValue)
    normalized: FeatureValue | None = None
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class StructureAssemblyFeature(BaseModel):
    """Equipment structure assembly (guard, door, frame, enclosure)."""

    assembly_id: str = Field(..., description="Unique ID")
    assembly_type: str = Field(default="GUARD", description="GUARD|DOOR|FRAME|ENCLOSURE")
    name: str = ""
    component_list: list[str] = Field(default_factory=list)
    quantity: int = 1
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FrameFeature(BaseModel):
    """Profile frame (aluminum extrusion, steel tube)."""

    frame_id: str = Field(..., description="Unique ID")
    profile_type: str | None = None    # "鋁型材" | "方通" | "角鋼"
    material: str | None = None
    total_length_mm: float = 0.0
    joint_count: int = 0
    connection_type: str | None = None  # "角碼" | "焊接" | "螺栓"
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SheetMetalFeature(BaseModel):
    """Sheet metal part."""

    sheet_id: str = Field(..., description="Unique ID")
    material: str | None = None
    thickness_mm: float = 0.0
    bend_count: int = 0
    cutting_length_mm: float = 0.0
    surface_treatment: str | None = None
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AcrylicFeature(BaseModel):
    """Transparent acrylic/PC panel."""

    acrylic_id: str = Field(..., description="Unique ID")
    material: str | None = None        # "亞克力" | "PC"
    thickness_mm: float = 0.0
    area_mm2: float = 0.0
    color: str | None = None           # "白色透明"
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class StructureAccessoryFeature(BaseModel):
    """Structural accessory — NOT an independent purchased part."""

    accessory_id: str = Field(..., description="Unique ID")
    category: str = Field(default="DOOR_HARDWARE")
    items: list[str] = Field(default_factory=list)
    quantity: int = 1
    belongs_to_assembly: str | None = None
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class WeldingFeature(BaseModel):
    """Welded joint or seam."""

    weld_id: str = Field(..., description="Unique ID")
    weld_length_mm: float = 0.0
    joint_count: int = 0
    weld_type: str | None = None       # "fillet" | "butt" | "spot"
    source_entities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ManufacturingFeatures(BaseModel):
    """Aggregate of all Layer 3 manufacturing features."""

    # -- Phase 3.1 (machined parts) --
    holes: list[HoleFeature] = Field(default_factory=list)
    threads: list[ThreadFeature] = Field(default_factory=list)
    material: MaterialFeature | None = None
    surface_treatment: SurfaceTreatmentFeature | None = None

    # -- Phase 3.3 (equipment structures) --
    structure_assemblies: list[StructureAssemblyFeature] = Field(default_factory=list)
    frames: list[FrameFeature] = Field(default_factory=list)
    sheet_metal_parts: list[SheetMetalFeature] = Field(default_factory=list)
    acrylic_parts: list[AcrylicFeature] = Field(default_factory=list)
    structure_accessories: list[StructureAccessoryFeature] = Field(default_factory=list)
    welds: list[WeldingFeature] = Field(default_factory=list)

    bounding_box_mm: BoundingBox | None = None

    @property
    def total_holes(self) -> int:
        return sum(h.count for h in self.holes)

    @property
    def total_threads(self) -> int:
        return sum(t.count for t in self.threads)
