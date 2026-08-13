"""Historical Feature Builder.

Converts ParsedPart (from BOM) + Dimension data into HistoricalFeature
records suitable for the quotation knowledge base.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from quotation.domain.bom import ParsedPart
from quotation.domain.historical import HistoricalFeature
from quotation.infrastructure.parser.dimension_parser import parse_dimension


def build_historical_feature(
    parsed: ParsedPart,
    project_name: str | None = None,
    density_g_cm3: float | None = None,
) -> HistoricalFeature:
    """Build a HistoricalFeature from a ParsedPart.

    Args:
        parsed: Parsed BOM part data.
        project_name: Project name for grouping.
        density_g_cm3: Material density for weight estimation.

    Returns:
        A HistoricalFeature ready for database insertion.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Parse dimensions
    length, width, height = 0.0, 0.0, 0.0
    volume = None
    weight = None

    if parsed.dimensions_raw:
        dim_result = parse_dimension(parsed.dimensions_raw)
        if dim_result.length is not None:
            length = dim_result.length
        if dim_result.width is not None:
            width = dim_result.width
        if dim_result.height is not None:
            height = dim_result.height

        if dim_result.is_circular:
            # Circular: diameter × thickness
            # Approximate volume as cylinder
            if dim_result.length and dim_result.height:
                radius = dim_result.length / 2.0
                volume = 3.14159 * radius * radius * dim_result.height
        elif length > 0 and width > 0 and height > 0:
            volume = length * width * height

    # Weight from volume × density
    if volume is not None and density_g_cm3 is not None:
        weight = (volume / 1000.0) * density_g_cm3 / 1000.0  # mm³ → cm³ → g → kg

    # Process hint from material + surface
    process_hint = _build_process_hint(parsed)

    return HistoricalFeature(
        id=str(uuid.uuid4()),
        part_no=parsed.bom_item,
        part_code=parsed.part_code,
        material=parsed.material,
        material_raw=parsed.material,
        overall_length=length,
        overall_width=width,
        overall_height=height,
        dimensions_raw=parsed.dimensions_raw,
        weight_kg=round(weight, 3) if weight is not None else None,
        volume_mm3=round(volume, 1) if volume is not None else None,
        surface_treatment=parsed.surface_treatment,
        surface_raw=parsed.surface_treatment,
        process_hint=process_hint,
        historical_price=parsed.unit_cost,
        price_source=parsed.quotation_source,
        source_bom=parsed.bom_item,  # Will be enriched by caller
        source_bom_row=parsed.source_row,
        source_dwg=parsed.drawing_ref,
        project_name=project_name,
        created_at=now,
        updated_at=now,
    )


def _build_process_hint(parsed: ParsedPart) -> str | None:
    """Infer a process hint from material + surface treatment."""
    parts = []
    if parsed.material:
        mat = parsed.material.upper()
        if "AL" in mat or "A6061" in mat:
            parts.append("CNC")
        elif "SUS" in mat:
            parts.append("CNC")
        elif "S50C" in mat or "SKD" in mat:
            parts.append("CNC")
        elif "SPCC" in mat:
            parts.append("鈑金+焊接")

    if parsed.surface_treatment:
        surf = parsed.surface_treatment
        if "熱" in surf:
            parts.append("熱處理")
        elif "陽極" in surf:
            parts.append("陽極氧化")
        elif "噴塗" in surf or "噴" in surf:
            parts.append("噴塗")
        elif "鍍" in surf:
            parts.append("電鍍")
        elif "發黑" in surf:
            parts.append("發黑")

    return "+".join(parts) if parts else None
