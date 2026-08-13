"""Quotation Mapper — ManufacturingFeatures → QuotationFeatures (Layer 4).

Converts manufacturing features into cost-calculation descriptions.
No prices — only WHAT to calculate.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from quotation.domain.geometric_feature import GeometricFeatures
from quotation.domain.manufacturing_feature import ManufacturingFeatures
from quotation.domain.quotation_feature import (
    AssemblyQuotationFeature,
    FrameQuotationFeature,
    MachiningQuotationFeature,
    MaterialCalculationTrace,
    QuotationFeatures,
    SheetMetalQuotationFeature,
)


class QuotationMapper:
    """Map ManufacturingFeatures to QuotationFeatures."""

    def map(
        self,
        mfg: ManufacturingFeatures,
        geo: GeometricFeatures,
        *,
        dimensions_raw: str | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> QuotationFeatures:
        """Main mapping pipeline."""
        machining = self._map_machining(
            mfg,
            geo,
            dimensions_raw=dimensions_raw,
            allow_drawing_extent_estimates=allow_drawing_extent_estimates,
        )
        frames = self._map_frames(mfg, geo)
        sheet_metal = self._map_sheet_metal(mfg, geo)
        assemblies = self._map_assemblies(mfg)

        return QuotationFeatures(
            machining=machining,
            frames=frames,
            sheet_metal=sheet_metal,
            assemblies=assemblies,
        )

    # -- Machining --

    @staticmethod
    def _estimate_weight(
        bbox,
        material: str | None,
        dims_raw: str | None = None,
        explicit_thickness_mm: float | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> tuple[MaterialCalculationTrace, float]:
        """Estimate weight with type-aware routing."""
        density_map = {
            "S50C": Decimal("7.85"),
            "A6061-T6": Decimal("2.70"),
            "SPCC": Decimal("7.85"),
            "SUS304": Decimal("7.93"),
            "SKD11": Decimal("7.85"),
            "普通鋼": Decimal("7.85"),
        }
        density = density_map.get(material or "", Decimal("7.85"))

        def trace(length, width, thickness, source: str) -> MaterialCalculationTrace:
            area = Decimal(str(length)) * Decimal(str(width))
            thickness_decimal = Decimal(str(thickness))
            volume = area * thickness_decimal
            weight = volume * density / Decimal("1000000")
            return MaterialCalculationTrace(
                area_mm2=area,
                thickness_mm=thickness_decimal,
                volume_mm3=volume,
                density_g_cm3=density,
                weight_kg=weight,
                weight_source=source,
            )

        # Sheet metal thickness must come from extracted evidence. Never replace
        # a fractional value (for example 0.35 mm) with a 2 mm nominal default.
        if explicit_thickness_mm and explicit_thickness_mm > 0:
            if dims_raw:
                from quotation.infrastructure.parser.dimension_parser import parse_dimension

                dims = parse_dimension(dims_raw)
                if dims.length and dims.width:
                    return (
                        trace(
                            dims.length,
                            dims.width,
                            explicit_thickness_mm,
                            "CONFIRMED_SHEET_DIMENSION_AND_THICKNESS",
                        ),
                        0.90,
                    )
            if allow_drawing_extent_estimates and bbox:
                return (
                    trace(
                        bbox.length,
                        bbox.width,
                        explicit_thickness_mm,
                        "EXTRACTED_SHEET_THICKNESS",
                    ),
                    0.40,
                )
            return MaterialCalculationTrace(
                weight_kg=Decimal("0"),
                density_g_cm3=density,
                thickness_mm=Decimal(str(explicit_thickness_mm)),
                weight_source="MISSING_CONFIRMED_SHEET_DIMENSION",
            ), 0.10

        # Explicit, complete part dimensions from a trusted drawing/BOM field.
        if dims_raw:
            from quotation.infrastructure.parser.dimension_parser import parse_dimension
            dims = parse_dimension(dims_raw)
            l = dims.length or (bbox.length if bbox else 100)
            w = dims.width or (bbox.width if bbox else 50)
            h = dims.height or 15
            calculation = trace(l, w, h, "CONFIRMED_PART_DIMENSION")
            if calculation.weight_kg > Decimal("0.001"):
                return calculation, 0.90

        # A 2D drawing bounding box often includes projected views, title blocks,
        # borders and notes.  It is therefore not a defensible solid-part volume.
        # Missing stock dimensions must remain unresolved instead of silently
        # turning the whole sheet into material weight.
        return MaterialCalculationTrace(
            weight_kg=Decimal("0"),
            density_g_cm3=density,
            weight_source="MISSING_CONFIRMED_DIMENSION",
        ), 0.10

    def _map_machining(
        self,
        mfg: ManufacturingFeatures,
        geo: GeometricFeatures,
        *,
        dimensions_raw: str | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> list[MachiningQuotationFeature]:
        unresolved_weldment = bool(
            mfg.welds
            and any(assembly.assembly_type == "FRAME" for assembly in mfg.structure_assemblies)
        )
        if not mfg.material and not unresolved_weldment:
            return []

        hints = []
        if mfg.sheet_metal_parts:
            hints.append("SHEET_METAL")
        if mfg.holes:
            hints.append("CNC")
        if mfg.threads:
            hints.append("TAP")
        if mfg.surface_treatment:
            surf = mfg.surface_treatment.raw_text.value or ""
            if "熱" in str(surf):
                hints.append("HEAT_TREAT")
            if "鍍" in str(surf):
                hints.append("PLATING")

        # Weight estimation (BOM dims > BBox estimate)
        bbox = geo.bounding_box
        material = (
            mfg.material.normalized.value
            if mfg.material and mfg.material.normalized.value
            else None
        )
        sheet_thickness = next(
            (
                part.thickness_mm
                for part in mfg.sheet_metal_parts
                if part.material == material and part.thickness_mm > 0
            ),
            None,
        )
        if unresolved_weldment:
            material_calculation = MaterialCalculationTrace(
                weight_source="UNRESOLVED_WELDMENT_STRUCTURE",
            )
            weight_conf = 0.0
        else:
            material_calculation, weight_conf = self._estimate_weight(
                bbox,
                material,
                dims_raw=dimensions_raw,
                explicit_thickness_mm=sheet_thickness,
                allow_drawing_extent_estimates=allow_drawing_extent_estimates,
            )

        surface_area = 0.0
        if dimensions_raw:
            from quotation.infrastructure.parser.dimension_parser import parse_dimension

            dimensions = parse_dimension(dimensions_raw)
            if dimensions.length and dimensions.width and dimensions.height:
                length, width, height = (
                    dimensions.length,
                    dimensions.width,
                    dimensions.height,
                )
                surface_area = 2 * (
                    length * width + length * height + width * height
                )
        elif allow_drawing_extent_estimates and bbox:
            surface_area = 2 * (bbox.length * bbox.width)

        return [MachiningQuotationFeature(
            feature_id=f"MQ-{uuid.uuid4().hex[:6]}",
            source_part=mfg.material.material_id if mfg.material else None,
            material=material,
            weight_kg=material_calculation.weight_kg,
            material_calculation=material_calculation,
            process_hints=hints,
            hole_count=mfg.total_holes,
            thread_count=mfg.total_threads,
            surface_treatment=mfg.surface_treatment.raw_text.value if mfg.surface_treatment else None,
            surface_area_mm2=surface_area,
            surface_mode="by_weight" if mfg.surface_treatment and any(kw in str(mfg.surface_treatment.raw_text.value or "").lower() for kw in ("熱", "heat")) else "by_area",
            confidence=mfg.material.confidence if mfg.material else 0.0,
        )]

    # -- Frames --

    def _map_frames(self, mfg: ManufacturingFeatures, geo: GeometricFeatures) -> list[FrameQuotationFeature]:
        results = []
        for f in mfg.frames:
            # Find matching assembly
            source_asm = None
            if mfg.structure_assemblies and len(mfg.structure_assemblies) == 1:
                source_asm = mfg.structure_assemblies[0].assembly_id
            results.append(FrameQuotationFeature(
                feature_id=f"FQ-{uuid.uuid4().hex[:6]}",
                source_assembly=source_asm,
                profile_type=f.profile_type,
                profile_spec=f.profile_spec,
                profile_length_mm=f.total_length_mm,
                joint_count=f.joint_count,
                connection_type=f.connection_type,
                confidence=f.confidence,
            ))
        return results

    # -- Sheet Metal --

    def _map_sheet_metal(self, mfg: ManufacturingFeatures, geo: GeometricFeatures) -> list[SheetMetalQuotationFeature]:
        return [
            SheetMetalQuotationFeature(
                feature_id=f"SQ-{uuid.uuid4().hex[:6]}",
                source_part=s.source_part if hasattr(s, 'source_part') else None,
                material=s.material,
                thickness_mm=s.thickness_mm,
                cutting_length_mm=s.cutting_length_mm,
                bend_count=s.bend_count,
                surface_treatment=s.surface_treatment,
                confidence=s.confidence,
            )
            for s in mfg.sheet_metal_parts
        ]

    # -- Assemblies --

    def _map_assemblies(self, mfg: ManufacturingFeatures) -> list[AssemblyQuotationFeature]:
        results = []
        for a in mfg.structure_assemblies:
            # Count accessories belonging to this assembly
            comp_count = len(mfg.structure_accessories[0].items) if mfg.structure_accessories else 0
            results.append(AssemblyQuotationFeature(
                feature_id=f"AQ-{uuid.uuid4().hex[:6]}",
                source_assembly=a.assembly_id,
                assembly_type=a.assembly_type,
                component_count=comp_count,
                operation="組裝",
                estimated_hours=comp_count * 0.5,
                confidence=a.confidence,
            ))
        return results
