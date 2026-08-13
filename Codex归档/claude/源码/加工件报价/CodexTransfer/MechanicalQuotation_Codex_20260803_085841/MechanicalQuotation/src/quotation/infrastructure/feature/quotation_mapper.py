"""Quotation Mapper — ManufacturingFeatures → QuotationFeatures (Layer 4).

Converts manufacturing features into cost-calculation descriptions.
No prices — only WHAT to calculate.
"""

from __future__ import annotations

import uuid

from quotation.domain.geometric_feature import GeometricFeatures
from quotation.domain.manufacturing_feature import ManufacturingFeatures
from quotation.domain.quotation_feature import (
    AssemblyQuotationFeature,
    FrameQuotationFeature,
    MachiningQuotationFeature,
    QuotationFeatures,
    SheetMetalQuotationFeature,
)


class QuotationMapper:
    """Map ManufacturingFeatures to QuotationFeatures."""

    def map(self, mfg: ManufacturingFeatures, geo: GeometricFeatures) -> QuotationFeatures:
        """Main mapping pipeline."""
        machining = self._map_machining(mfg, geo)
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
    def _estimate_weight(bbox, material: str | None, dims_raw: str | None = None) -> tuple[float, str, float]:
        """Estimate weight with type-aware routing."""
        density_map = {"S50C": 7.85, "A6061-T6": 2.70, "SPCC": 7.85,
                       "SUS304": 7.93, "SKD11": 7.85, "普通鋼": 7.85}
        density = density_map.get(material or "", 7.85)

        # SPCC sheet metal: always use 2mm nominal thickness
        if material == "SPCC":
            l = bbox.length if bbox else 100
            w = bbox.width if bbox else 50
            thickness = 2.0
            vol = l * w * thickness
            weight = round(vol * density / 1_000_000, 3)
            return weight, "MATERIAL_SPEC_THICKNESS", 0.85

        # BOM dimensions with explicit thickness
        if dims_raw:
            from quotation.infrastructure.parser.dimension_parser import parse_dimension
            dims = parse_dimension(dims_raw)
            l = dims.length or (bbox.length if bbox else 100)
            w = dims.width or (bbox.width if bbox else 50)
            h = dims.height or 15
            vol = l * w * h
            weight = round(vol * density / 1_000_000, 3)
            if weight > 0.001:
                return weight, "BOM_CONFIRMED_DIMENSION", 0.90

        # BoundingBox estimate (last resort)
        if bbox:
            smaller = min(bbox.length, bbox.width)
            thickness = max(smaller * 0.02, 2.0)
            if smaller < 100:
                thickness = max(smaller * 0.03, 1.0)
            vol = bbox.length * bbox.width * thickness
            weight = round(vol * density / 1_000_000, 3)
            return weight, "BBOX_ESTIMATE", 0.40

        return 1.0, "UNKNOWN", 0.10

    def _map_machining(self, mfg: ManufacturingFeatures, geo: GeometricFeatures) -> list[MachiningQuotationFeature]:
        if not mfg.material:
            return []

        hints = []
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
        weight, weight_source, weight_conf = self._estimate_weight(bbox, mfg.material.normalized.value if mfg.material and mfg.material.normalized.value else None)

        surface_area = 2 * (bbox.length * bbox.width) if bbox else 0

        return [MachiningQuotationFeature(
            feature_id=f"MQ-{uuid.uuid4().hex[:6]}",
            source_part=mfg.material.material_id if mfg.material else None,
            material=mfg.material.normalized.value if mfg.material and mfg.material.normalized.value else None,
            weight_kg=weight,
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
