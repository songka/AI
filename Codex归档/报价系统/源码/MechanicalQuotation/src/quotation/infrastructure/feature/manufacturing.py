"""Manufacturing Feature Extractor — GeometricFeatures → ManufacturingFeatures (Layer 3).

Converts geometric primitives into manufacturing-meaningful features:
- HoleFeature: grouped hole candidates by diameter
- ThreadFeature: M3-M8 specs from text, linked to nearby circles
- MaterialFeature: material from text → normalization
- SurfaceTreatmentFeature: surface treatment from text
"""

from __future__ import annotations

import logging
import math
import re
import uuid

from quotation.domain.geometric_feature import (
    FeatureValue,
    GeometricFeatures,
    HoleCandidate,
    TextCluster,
)
from quotation.domain.manufacturing_feature import (
    AcrylicFeature,
    FrameFeature,
    HoleFeature,
    ManufacturingFeatures,
    MaterialFeature,
    SheetMetalFeature,
    StructureAccessoryFeature,
    StructureAssemblyFeature,
    SurfaceTreatmentFeature,
    ThreadFeature,
    WeldingFeature,
)
from quotation.infrastructure.parser.material_normalizer import normalize_material
from quotation.utils.normalization import normalize_profile_spec

logger = logging.getLogger("quotation.infrastructure.feature.manufacturing")

# Diameter tolerance for grouping holes (mm)
HOLE_GROUP_TOLERANCE_MM = 0.5

# Max distance from thread text to associated circle (mm)
THREAD_CIRCLE_MAX_DISTANCE_MM = 50.0

# Thread spec patterns
THREAD_PATTERN = re.compile(r"M([34568])(?:\D|$)")
THREAD_PATTERN_COUNTED = re.compile(r"(\d+)\s*[-xX×]\s*M([34568])")

# Surface treatment keywords
SURFACE_KEYWORDS = [
    "熱處理",
    "热处理",
    "heat treatment",
    "陽極",
    "阳极",
    "anodize",
    "anodizing",
    "鍍鉻",
    "镀铬",
    "chrome",
    "鍍鎳",
    "镀镍",
    "nickel",
    "發黑",
    "发黑",
    "black oxide",
    "噴塗",
    "喷涂",
    "painting",
    "coating",
    "噴砂",
    "喷砂",
    "sandblast",
    "電鍍",
    "电镀",
    "plating",
    "氮化",
    "nitriding",
    "滲碳",
    "渗碳",
    "carburizing",
    "RAL",
    "透明",
    "白色",
    "陽極",
    "阳极",
    "表面",
    "顏色",
    "颜色",
]

# Material keywords for detection priority
MATERIAL_KEYWORDS = [
    "方通",
    "方管",
    "矩形管",
    "S50C",
    "SKD11",
    "SKD61",
    "SUS304",
    "SUS316",
    "SPCC",
    "A6061",
    "AL6061",
    "6061",
    "6061-T6",
    "A5052",
    "SS400",
    "Q235",
    "45#",
    "45鋼",
    "普通鋼",
    "普通钢",
    "鋁",
    "铝",
    "銅",
    "铜",
    "不鏽鋼",
    "不锈钢",
]


class ManufacturingExtractor:
    """Extract manufacturing features from geometric features."""

    def extract(
        self,
        geo: GeometricFeatures,
        *,
        dimensions_raw: str | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> ManufacturingFeatures:
        """Main extraction pipeline."""
        holes = self._extract_holes(geo.hole_candidates)
        threads = self._extract_threads(geo.text_clusters, geo.hole_candidates)
        material = self._extract_material(geo.text_clusters)
        surface = self._extract_surface_treatment(geo.text_clusters)

        # Phase 3.3: Equipment structure features
        trusted_dimensions = self._trusted_plan_dimensions(dimensions_raw)
        frames = self._extract_frames(
            geo, trusted_dimensions, allow_drawing_extent_estimates
        )
        sheet_metal = self._extract_sheet_metal(
            geo, trusted_dimensions, allow_drawing_extent_estimates
        )
        acrylic = self._extract_acrylic(
            geo, trusted_dimensions, allow_drawing_extent_estimates
        )
        accessories = self._extract_accessories(geo)
        welds = self._extract_welds(geo)
        assemblies = self._extract_assemblies(geo)

        return ManufacturingFeatures(
            holes=holes,
            threads=threads,
            material=material,
            surface_treatment=surface,
            frames=frames,
            sheet_metal_parts=sheet_metal,
            acrylic_parts=acrylic,
            structure_accessories=accessories,
            welds=welds,
            structure_assemblies=assemblies,
            bounding_box_mm=geo.bounding_box,
        )

    @staticmethod
    def _trusted_plan_dimensions(
        dimensions_raw: str | None,
    ) -> tuple[float, float, float] | None:
        if not dimensions_raw:
            return None
        from quotation.infrastructure.parser.dimension_parser import parse_dimension

        parsed = parse_dimension(dimensions_raw)
        if not parsed.length or not parsed.width or not parsed.height:
            return None
        return float(parsed.length), float(parsed.width), float(parsed.height)

    # -- Hole Extraction --

    def _extract_holes(self, candidates: list[HoleCandidate]) -> list[HoleFeature]:
        """Group hole candidates by diameter."""
        if not candidates:
            return []

        # Sort by diameter
        sorted_candidates = sorted(candidates, key=lambda c: c.diameter)
        groups: list[list[HoleCandidate]] = []
        current_group = [sorted_candidates[0]]

        for c in sorted_candidates[1:]:
            avg_dia = sum(h.diameter for h in current_group) / len(current_group)
            if abs(c.diameter - avg_dia) <= HOLE_GROUP_TOLERANCE_MM:
                current_group.append(c)
            else:
                groups.append(current_group)
                current_group = [c]
        groups.append(current_group)

        # Build HoleFeatures
        holes: list[HoleFeature] = []
        for i, group in enumerate(groups):
            avg_dia = sum(h.diameter for h in group) / len(group)
            first = group[0]
            handles = [h.source_entity for h in group if h.source_entity]

            holes.append(
                HoleFeature(
                    hole_id=f"HOLE-{i + 1:03d}",
                    diameter=FeatureValue(
                        value=round(avg_dia, 2),
                        source="CAD_GEOMETRY",
                        confidence=0.95,
                        source_entities=handles,
                    ),
                    count=len(group),
                    position_x=first.center_x,
                    position_y=first.center_y,
                    source_entities=handles,
                    confidence=0.95 if len(group) > 1 else 0.90,
                )
            )

        return holes

    # -- Thread Extraction --

    def _extract_threads(
        self, texts: list[TextCluster], holes: list[HoleCandidate]
    ) -> list[ThreadFeature]:
        """Find thread specs in text and link to nearby circles."""
        threads: list[ThreadFeature] = []

        for tc in texts:
            content = tc.content.strip()
            # Try counted pattern first: "6-M6"
            m = THREAD_PATTERN_COUNTED.search(content)
            if m:
                count = int(m.group(1))
                size = m.group(2)
                spec = f"M{size}"
            else:
                m = THREAD_PATTERN.search(content)
                if not m:
                    continue
                count = 1
                size = m.group(1)
                spec = f"M{size}"

            # Find nearest circle within range
            nearest_hole = self._find_nearest_circle(tc, holes)

            thread = ThreadFeature(
                thread_id=f"THR-{uuid.uuid4().hex[:6]}",
                spec=FeatureValue(
                    value=spec,
                    source="DRAWING_TEXT",
                    confidence=0.85,
                    source_entities=[tc.source_entity],
                ),
                size=spec,
                count=count,
                linked_hole_id=nearest_hole.source_entity if nearest_hole else None,
                source_entities=[tc.source_entity]
                + (
                    [nearest_hole.source_entity]
                    if nearest_hole and nearest_hole.source_entity
                    else []
                ),
                confidence=0.85 if nearest_hole else 0.60,
            )
            threads.append(thread)

        return threads

    def _find_nearest_circle(
        self, text: TextCluster, holes: list[HoleCandidate]
    ) -> HoleCandidate | None:
        """Find the nearest hole candidate to a text annotation."""
        best = None
        best_dist = THREAD_CIRCLE_MAX_DISTANCE_MM

        for h in holes:
            dist = math.hypot(
                text.position_x - h.center_x,
                text.position_y - h.center_y,
            )
            if dist < best_dist:
                best_dist = dist
                best = h

        return best

    # -- Material Extraction --

    def _extract_material(self, texts: list[TextCluster]) -> MaterialFeature | None:
        """Find material name in text annotations."""
        for tc in texts:
            content = tc.content.strip()
            for keyword in MATERIAL_KEYWORDS:
                if keyword.lower() in content.lower():
                    norm_result = normalize_material(content)
                    return MaterialFeature(
                        material_id=f"MAT-{uuid.uuid4().hex[:6]}",
                        raw_text=FeatureValue(
                            value=content,
                            source="DRAWING_TEXT",
                            confidence=0.80,
                            source_entities=[tc.source_entity],
                        ),
                        normalized=FeatureValue(
                            value=norm_result.normalized or content,
                            source="DRAWING_TEXT",
                            confidence=norm_result.confidence,
                            source_entities=[tc.source_entity],
                        ),
                        source_entities=[tc.source_entity],
                        confidence=norm_result.confidence if norm_result.normalized else 0.60,
                    )
        return None

    # -- Surface Treatment Extraction --

    def _extract_surface_treatment(
        self, texts: list[TextCluster]
    ) -> SurfaceTreatmentFeature | None:
        """Find surface treatment keywords in text."""
        for tc in texts:
            content = tc.content.strip().lower()
            for keyword in SURFACE_KEYWORDS:
                if keyword.lower() in content:
                    return SurfaceTreatmentFeature(
                        surface_id=f"SURF-{uuid.uuid4().hex[:6]}",
                        raw_text=FeatureValue(
                            value=tc.content.strip(),
                            source="DRAWING_TEXT",
                            confidence=0.75,
                            source_entities=[tc.source_entity],
                        ),
                        source_entities=[tc.source_entity],
                        confidence=0.75,
                    )
        return None

    # -- Phase 3.3: Equipment Structure Features --

    _FRAME_KW = ["型材", "鋁型材", "鋁擠型", "方通", "角鋼"]
    _SHEET_METAL_KW = [
        "SPCC",
        "鈑金",
        "板金",
        "折彎",
        "鋼板",
        "钢板",
        "不鏽鋼",
        "不锈钢",
        "厚度",
    ]
    _ACRYLIC_KW = ["亞克力", "壓克力", "PC板", "透明"]
    _ACCESSORY_KW = {
        "合頁": "DOOR_HARDWARE",
        "鉸鏈": "DOOR_HARDWARE",
        "磁吸": "DOOR_HARDWARE",
        "把手": "DOOR_HARDWARE",
        "門鎖": "DOOR_HARDWARE",
        "拉手": "DOOR_HARDWARE",
        "角碼": "FASTENER",
        "角件": "FASTENER",
    }
    _ASSEMBLY_KW = {
        "防護": "GUARD",
        "圍欄": "GUARD",
        "護罩": "GUARD",
        "機架": "FRAME",
        "框架": "FRAME",
        "門": "DOOR",
        "門組": "DOOR",
        "罩": "ENCLOSURE",
    }

    def _extract_frames(
        self,
        geo: GeometricFeatures,
        trusted_dimensions: tuple[float, float, float] | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> list[FrameFeature]:
        for tc in geo.text_clusters:
            for kw in self._FRAME_KW:
                if kw in tc.content:
                    if trusted_dimensions:
                        length = 2 * (trusted_dimensions[0] + trusted_dimensions[1])
                    elif allow_drawing_extent_estimates and geo.bounding_box:
                        length = geo.bounding_box.length * 4
                    else:
                        length = 0
                    # Count joints from accessory keywords
                    joint_count = self._estimate_joints(geo.text_clusters)
                    return [
                        FrameFeature(
                            frame_id=f"FRM-{uuid.uuid4().hex[:6]}",
                            profile_type="鋁型材" if "鋁" in tc.content else "方通",
                            profile_spec=normalize_profile_spec(tc.content),
                            total_length_mm=length,
                            joint_count=joint_count,
                            connection_type="角碼"
                            if any(
                                "角碼" in t.content or "角件" in t.content
                                for t in geo.text_clusters
                            )
                            else None,
                            source_entities=[tc.source_entity] if tc.source_entity else [],
                            confidence=0.75,
                        )
                    ]
        return []

    def _estimate_joints(self, texts: list[TextCluster]) -> int:
        """Estimate joint count from accessory and connection keywords."""
        joint_count = 0
        for tc in texts:
            if "角碼" in tc.content or "角件" in tc.content:
                joint_count += 4  # each corner bracket ≈ 4 connection points
            if "連接" in tc.content or "连接" in tc.content:
                joint_count += 2
            if "螺絲" in tc.content or "螺丝" in tc.content:
                joint_count += 2
            if "固定" in tc.content:
                joint_count += 1
        return max(joint_count, 1) if joint_count > 0 else 0  # at least 1 if keyword found, else 0

    def _extract_sheet_metal(
        self,
        geo: GeometricFeatures,
        trusted_dimensions: tuple[float, float, float] | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> list[SheetMetalFeature]:
        combined_text = "\n".join(tc.content for tc in geo.text_clusters)
        bend_count = combined_text.count("折彎") + combined_text.count("折弯")
        explicit_fabrication = bool(
            re.search(
                r"钣金|鈑金|板金|折弯|折彎|冲压|沖壓|激光切割|雷射切割|"
                r"折边|折邊|展开图|展開圖",
                combined_text,
                re.IGNORECASE,
            )
        )
        thickness_matches = re.findall(
                r"(?:厚度?|[Tt])\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:mm)?|"
                r"(\d+(?:\.\d+)?)\s*mm\s*厚",
                combined_text,
                re.IGNORECASE,
            )
        thickness_values = [
            float(value)
            for match in thickness_matches
            for value in match
            if value
        ]
        thin_sheet_stock = (
            any(
                material in combined_text
                for material in ("SPCC", "SUS304", "不鏽鋼", "不锈钢")
            )
            and bool(thickness_values)
            and min(thickness_values) <= 6.0
        )
        if not explicit_fabrication and not thin_sheet_stock:
            return []
        source_text = next(
            (
                tc
                for tc in geo.text_clusters
                if re.search(
                    r"钣金|鈑金|板金|折弯|折彎|冲压|沖壓|激光切割|雷射切割|"
                    r"折边|折邊|展开图|展開圖|SPCC|SUS304|不鏽鋼|不锈钢",
                    tc.content,
                    re.IGNORECASE,
                )
            ),
            geo.text_clusters[0] if geo.text_clusters else None,
        )
        thickness = min(thickness_values) if thickness_values else 1.5
        if "SPCC" in combined_text:
            material = "SPCC"
        elif any(
            value in combined_text for value in ("SUS304", "不鏽鋼", "不锈钢")
        ):
            material = "SUS304"
        else:
            material = None
        if trusted_dimensions:
            perimeter = 2 * (trusted_dimensions[0] + trusted_dimensions[1])
        elif allow_drawing_extent_estimates and geo.bounding_box:
            perimeter = 2 * (geo.bounding_box.length + geo.bounding_box.width)
        else:
            perimeter = 0
        return [
            SheetMetalFeature(
                sheet_id=f"SHT-{uuid.uuid4().hex[:6]}",
                material=material,
                thickness_mm=thickness,
                cutting_length_mm=perimeter,
                bend_count=bend_count,
                surface_treatment=(source_text.content.strip()[:40] if source_text else None),
                source_entities=(
                    [source_text.source_entity]
                    if source_text and source_text.source_entity
                    else []
                ),
                confidence=0.80 if thickness_values else 0.65,
            )
        ]

    def _extract_acrylic(
        self,
        geo: GeometricFeatures,
        trusted_dimensions: tuple[float, float, float] | None = None,
        allow_drawing_extent_estimates: bool = True,
    ) -> list[AcrylicFeature]:
        for tc in geo.text_clusters:
            for kw in self._ACRYLIC_KW:
                if kw in tc.content:
                    if trusted_dimensions:
                        area = trusted_dimensions[0] * trusted_dimensions[1]
                    elif allow_drawing_extent_estimates and geo.bounding_box:
                        area = geo.bounding_box.length * geo.bounding_box.width
                    else:
                        area = 0
                    return [
                        AcrylicFeature(
                            acrylic_id=f"ACR-{uuid.uuid4().hex[:6]}",
                            material="亞克力"
                            if any(k in tc.content for k in ("亞克力", "壓克力"))
                            else "PC",
                            area_mm2=area,
                            color="白色透明"
                            if "透明" in tc.content and "白" in tc.content
                            else None,
                            source_entities=[tc.source_entity] if tc.source_entity else [],
                            confidence=0.75,
                        )
                    ]
        return []

    def _extract_accessories(self, geo: GeometricFeatures) -> list[StructureAccessoryFeature]:
        items = []
        handles = []
        for tc in geo.text_clusters:
            for kw, _cat in self._ACCESSORY_KW.items():
                if kw in tc.content and kw not in items:
                    items.append(kw)
                    if tc.source_entity:
                        handles.append(tc.source_entity)
                    break
        if not items:
            return []
        return [
            StructureAccessoryFeature(
                accessory_id=f"ACC-{uuid.uuid4().hex[:6]}",
                category="DOOR_HARDWARE"
                if any(k in items for k in ("合頁", "鉸鏈", "磁吸", "把手", "門鎖", "拉手"))
                else "FASTENER",
                items=items,
                source_entities=handles,
                confidence=0.75,
            )
        ]

    def _extract_welds(self, geo: GeometricFeatures) -> list[WeldingFeature]:
        for tc in geo.text_clusters:
            if any(kw in tc.content for kw in ("焊接", "點焊", "滿焊", "加強筋")):
                return [
                    WeldingFeature(
                        weld_id=f"WELD-{uuid.uuid4().hex[:6]}",
                        weld_type="spot" if "點焊" in tc.content else "fillet",
                        source_entities=[tc.source_entity] if tc.source_entity else [],
                        confidence=0.70,
                    )
                ]
        return []

    def _extract_assemblies(self, geo: GeometricFeatures) -> list[StructureAssemblyFeature]:
        assemblies = []
        seen = set()
        for tc in geo.text_clusters:
            for kw, atype in self._ASSEMBLY_KW.items():
                if kw in tc.content and atype not in seen:
                    seen.add(atype)
                    assemblies.append(
                        StructureAssemblyFeature(
                            assembly_id=f"ASM-{uuid.uuid4().hex[:6]}",
                            assembly_type=atype,
                            name=tc.content.strip()[:40],
                            source_entities=[tc.source_entity] if tc.source_entity else [],
                            confidence=0.70,
                        )
                    )
                    break
        return assemblies
