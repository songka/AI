"""Rule domain model.

Quotation rules for materials, processes, and surface treatments.
All prices come from YAML files — never hardcoded.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MaterialStatus(str, Enum):
    """Availability status of a material rule."""
    ACTIVE = "ACTIVE"           # Price confirmed and usable
    PENDING = "PENDING"         # Price not yet provided — items marked U
    DEPRECATED = "DEPRECATED"   # No longer in use


class SurfacePricingMode(str, Enum):
    """How a surface treatment is priced."""
    BY_WEIGHT = "by_weight"     # CNY/kg
    BY_AREA = "by_area"         # CNY/dm²
    BY_PIECE = "by_piece"       # CNY/piece
    BY_LENGTH = "by_length"     # CNY/m


# ---------------------------------------------------------------------------
# Material rule
# ---------------------------------------------------------------------------

class MaterialRule(BaseModel):
    """Material pricing rule — from quotation-rules.yaml."""

    material_id: str = Field(..., description="Unique rule ID, e.g. 'MAT_A6061'")
    material_name: str = Field(..., description="Standard material name, e.g. 'A6061-T6'")
    aliases: list[str] = Field(
        default_factory=list,
        description="Aliases for matching: ['6061', 'AL6061', '6061-T6']",
    )

    # -- Price --
    unit_price: float = Field(..., ge=0, description="Price per unit (0 = not yet set)")
    unit: str = Field(default="kg", description="Pricing unit")
    loss_rate: float = Field(
        default=0.05, ge=0, le=1, description="Material loss rate (0.05 = 5%)"
    )

    # -- Status --
    status: MaterialStatus = Field(
        default=MaterialStatus.ACTIVE, description="Rule availability"
    )
    note: str | None = Field(default=None)

    # -- Version --
    version: str = Field(default="1.0")
    updated_at: str | None = Field(default=None, description="ISO datetime")


# ---------------------------------------------------------------------------
# Process rule
# ---------------------------------------------------------------------------

class ProcessRule(BaseModel):
    """Machining process pricing rule."""

    process_id: str = Field(..., description="Unique rule ID, e.g. 'PROC_CNC'")
    process_name: str = Field(..., description="Process name, e.g. 'CNC'")
    rate: float = Field(..., gt=0, description="Hourly rate (CNY/h)")
    unit: str = Field(default="hour")
    conditions: list[str] | None = Field(
        default=None,
        description="Applicable conditions, e.g. ['普通三軸', '公差>0.05mm']",
    )
    version: str = Field(default="1.0")


# ---------------------------------------------------------------------------
# Surface treatment rule
# ---------------------------------------------------------------------------

class SurfaceRule(BaseModel):
    """Surface treatment pricing rule — supports multiple pricing modes."""

    surface_id: str = Field(..., description="Unique rule ID, e.g. 'SURF_ANODIZE'")
    surface_name: str = Field(..., description="Surface treatment name")
    aliases: list[str] = Field(
        default_factory=list,
        description="Aliases for matching: ['陽極', 'anodize']",
    )

    pricing_mode: SurfacePricingMode = Field(
        default=SurfacePricingMode.BY_WEIGHT,
        description="Pricing mode: by_weight | by_area | by_piece | by_length",
    )
    unit_price: float = Field(..., ge=0, description="Price per unit (0 = not yet set)")
    unit: str = Field(default="kg", description="Pricing unit")
    min_charge: float | None = Field(default=None, ge=0, description="Minimum charge (CNY)")

    applicable_materials: list[str] = Field(
        default_factory=list,
        description="Materials this treatment applies to",
    )
    note: str | None = Field(default=None)

    version: str = Field(default="1.0")


# ---------------------------------------------------------------------------
# RuleSet — aggregate root
# ---------------------------------------------------------------------------

class RuleSet(BaseModel):
    """Complete quotation rule set loaded from YAML files."""

    version: str = Field(..., description="Rule set version")
    source: str | None = Field(default=None, description="Source description")
    updated_at: str | None = Field(default=None, description="ISO datetime")

    materials: list[MaterialRule] = Field(default_factory=list)
    processes: list[ProcessRule] = Field(default_factory=list)
    surfaces: list[SurfaceRule] = Field(default_factory=list)

    # Computed counts
    material_count: int = Field(default=0, description="Number of material rules")
    process_count: int = Field(default=0, description="Number of process rules")
    surface_count: int = Field(default=0, description="Number of surface rules")

    def model_post_init(self, __context: object) -> None:
        """Update computed counts after initialization."""
        self.material_count = len(self.materials)
        self.process_count = len(self.processes)
        self.surface_count = len(self.surfaces)
