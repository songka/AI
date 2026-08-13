"""Material domain model.

Physical material properties (density, category) — separated from pricing rules.
All prices belong in quotation-rules.yaml, never here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MaterialProperties(BaseModel):
    """Physical properties of a material.

    Density, category, and grade are physical facts — not pricing.
    Pricing rules are managed separately in quotation-rules.yaml.
    """

    name: str = Field(..., description="Standard material name, e.g. 'A6061-T6'")
    density: float = Field(..., gt=0, description="Density in g/cm³")
    category: str = Field(..., description="Material category, e.g. '鋁合金'")
    grade: str = Field(..., description="Material grade/standard, e.g. '6061-T6'")
    source_file: str = Field(
        default="material-density.yaml",
        description="Source file for this property",
    )
    note: str | None = Field(default=None, description="Additional notes")
