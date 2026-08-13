"""Quotation Feature domain models — Layer 4 of CAD parsing.

Describes WHAT cost items need calculation, without prices.
Prices are computed by the Rule Engine (Phase 4).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MachiningQuotationFeature(BaseModel):
    """Machined part — what costs to calculate."""

    feature_id: str = Field(..., description="Unique ID")
    source_part: str | None = None       # BOM item

    # Material cost inputs
    material: str | None = None
    weight_kg: float = 0.0
    material_loss_rate: float = 0.05

    # Process cost inputs
    process_hints: list[str] = Field(default_factory=list)
    hole_count: int = 0
    thread_count: int = 0
    tolerance_grade: str | None = None
    setup_count: int = 1

    # Surface cost inputs
    surface_treatment: str | None = None
    surface_area_mm2: float = 0.0
    surface_mode: str = "by_weight"

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FrameQuotationFeature(BaseModel):
    """Profile frame — what costs to calculate."""

    feature_id: str = Field(..., description="Unique ID")
    source_assembly: str | None = None

    profile_type: str | None = None      # "鋁型材"
    profile_length_mm: float = 0.0
    joint_count: int = 0
    connection_type: str | None = None   # "角碼"
    assembly_factor: float = 1.15

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SheetMetalQuotationFeature(BaseModel):
    """Sheet metal part — what costs to calculate."""

    feature_id: str = Field(..., description="Unique ID")
    source_part: str | None = None

    material: str | None = None
    thickness_mm: float = 0.0
    cutting_length_mm: float = 0.0
    bend_count: int = 0
    welding_length_mm: float = 0.0
    surface_area_mm2: float = 0.0
    surface_treatment: str | None = None

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AssemblyQuotationFeature(BaseModel):
    """Assembly/labor — what costs to calculate."""

    feature_id: str = Field(..., description="Unique ID")
    source_assembly: str | None = None

    assembly_type: str | None = None     # "GUARD" | "DOOR"
    component_count: int = 0
    operation: str | None = None         # "組裝"
    labor_factor: float = 1.0
    estimated_hours: float = 0.0

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class QuotationFeatures(BaseModel):
    """Aggregate of all Layer 4 quotation features."""

    machining: list[MachiningQuotationFeature] = Field(default_factory=list)
    frames: list[FrameQuotationFeature] = Field(default_factory=list)
    sheet_metal: list[SheetMetalQuotationFeature] = Field(default_factory=list)
    assemblies: list[AssemblyQuotationFeature] = Field(default_factory=list)

    @property
    def total_features(self) -> int:
        return len(self.machining) + len(self.frames) + len(self.sheet_metal) + len(self.assemblies)
