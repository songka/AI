"""BOM domain model.

Represents Bill of Materials data imported from Excel,
with structured part data parsed from description text.

Supports multiple part categories:
- 加工件 (machined parts) — quotation target
- 電控外購件 (electrical purchased parts)
- 機構外購件 (mechanical purchased parts)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# BomEntry — single BOM row
# ---------------------------------------------------------------------------

class BomEntry(BaseModel):
    """A single row from the BOM Excel file.

    Maps directly to Excel columns with source tracing.
    """

    # -- Source tracing --
    source_file: str = Field(default="", description="BOM Excel file path")
    source_sheet: str = Field(default="工作表1", description="Worksheet name")
    source_row: int = Field(default=0, ge=0, description="Excel row number (1-based)")

    # -- Identity --
    item: str = Field(..., description="Part/item number, e.g. 'UC1000005854'")
    description: str = Field(..., description="Full description text (semicolon-delimited)")

    # -- BOM structure --
    level: int = Field(default=0, ge=0, description="BOM level: 0=finished, 1=subassy, 2+=part")
    parent_item: str | None = Field(default=None, description="Parent item number for tree structure")

    # -- Type --
    item_type: str = Field(default="Purchased", description="Finished good | Subassembly | Purchased | Phantom item")
    uom: str = Field(default="ST", description="Unit of measure: ST/PCS/SET/KG/M/EA")

    # -- Quantity --
    quantity: float = Field(default=1.0, gt=0, description="Quantity per assembly")

    # -- Price (real historical data) --
    unit_cost: float = Field(default=0.0, ge=0, description="Unit cost in CNY")
    extended_cost: float = Field(default=0.0, ge=0, description="Extended cost = quantity × unit_cost")

    # -- Supplier --
    supplier: str | None = Field(default=None, description="Supplier name")

    # -- Metadata --
    bom_source_file: str | None = Field(default=None, description="Source BOM file name (deprecated, use source_file)")
    notes: str | None = Field(default=None, description="Remarks (Col J)")


# ---------------------------------------------------------------------------
# ParsedPart — structured data extracted from BOM description
# ---------------------------------------------------------------------------

class ParsedPart(BaseModel):
    """Structured part data extracted from BomEntry.description.

    Parses the semicolon-delimited BOM description format:

    Format A — 加工件:
        "原材料;加工件;S50C;J003;928*796*15;熱處理"
          seg0  seg1   seg2  seg3 seg4       seg5

    Format B — 電控外購件:
        "原材料;電控外購件;控制類;PLC擴展;擴展IO模塊;型號:AS16AP11T-A;品牌:台達"

    Format C — 機構外購件:
        "原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995"
    """

    # -- Source --
    bom_item: str = Field(..., description="Matching BomEntry.item")
    source_row: int = Field(default=0, ge=0, description="Source Excel row number")

    # -- Classification (from description segments 0-1) --
    category: str | None = Field(
        default=None, description="Top-level category (segment 0): 原材料 | 半成品"
    )
    sub_type: str | None = Field(
        default=None,
        description="Sub-type (segment 1): 加工件 | 電控外購件 | 機構外購件 | 軟體 | ...",
    )

    # -- Machined part fields (加工件, segment 2-5) --
    material: str | None = Field(default=None, description="Material, e.g. 'S50C', 'A6061-T6', 'SPCC'")
    part_code: str | None = Field(default=None, description="Part code, e.g. 'J003', 'R001'")
    dimensions_raw: str | None = Field(
        default=None, description="Raw dimension text, e.g. '928*796*15'"
    )
    surface_treatment: str | None = Field(
        default=None, description="Surface treatment, e.g. '熱處理'"
    )

    # -- Purchased part fields (外購件) --
    model_number: str | None = Field(default=None, description="Model number (外購件)")
    brand: str | None = Field(default=None, description="Brand (外購件)")
    spec: str | None = Field(default=None, description="Specification text (外購件)")

    # -- Price --
    unit_cost: float = Field(default=0.0, ge=0, description="Unit cost from BOM")
    quotation_source: str = Field(
        default="BOM",
        description="Price source: BOM | SUPPLIER | MANUAL",
    )

    # -- Quotation flags --
    is_quotable: bool = Field(
        default=False,
        description="True if this part should be auto-quoted (加工件 only)",
    )
    is_matched: bool = Field(
        default=False, description="True if matched to a DWG file"
    )

    # -- Cross-reference --
    drawing_ref: str | None = Field(
        default=None, description="Matching DWG file name"
    )
    feature_ref: str | None = Field(
        default=None, description="Matching Feature.id"
    )


# ---------------------------------------------------------------------------
# BomSheet — complete BOM
# ---------------------------------------------------------------------------

class BomSheet(BaseModel):
    """A complete BOM worksheet imported from Excel."""

    # -- Source --
    source_file: str = Field(..., description="BOM Excel file path")
    source_sheet: str = Field(default="工作表1", description="Worksheet name")
    total_rows: int = Field(default=0, ge=0, description="Total data rows")
    project_name: str | None = Field(default=None, description="Project name")

    # -- Data --
    entries: list[BomEntry] = Field(default_factory=list, description="All BOM rows")
    parsed_parts: list[ParsedPart] = Field(
        default_factory=list, description="Parsed structured parts"
    )

    # -- Classification statistics --
    machined_count: int = Field(default=0, ge=0, description="Number of 加工件 (quotation targets)")
    electrical_count: int = Field(default=0, ge=0, description="Number of 電控外購件")
    mechanical_count: int = Field(default=0, ge=0, description="Number of 機構外購件")
    subassembly_count: int = Field(default=0, ge=0, description="Number of subassemblies")

    # -- Legacy statistics (kept for backward compatibility) --
    total_cost: float = Field(default=0.0, description="Sum of all extended costs")
    part_count: int = Field(default=0, description="Number of manufactured parts")
    purchased_count: int = Field(default=0, description="Number of purchased parts")

    # -- Cross-reference --
    matched_drawings: int = Field(
        default=0, description="Parts matched to DWG files"
    )
    unmatched_drawings: int = Field(
        default=0, description="DWG files without BOM match"
    )
    matched_parts: list[ParsedPart] = Field(
        default_factory=list, description="ParsedParts that matched a DWG file"
    )
