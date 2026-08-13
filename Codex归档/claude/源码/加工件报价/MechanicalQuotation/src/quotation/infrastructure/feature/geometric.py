"""Geometric Feature Extractor — RawEntity[] → GeometricFeatures (Layer 2).

Extracts:
- BoundingBox from LINE/POLYLINE extents
- HoleCandidates from small CIRCLE entities (diameter < 30mm)
- TextClusters from TEXT/MTEXT entities
"""

from __future__ import annotations

import logging
import re

from quotation.domain.geometric_feature import (
    BoundingBox,
    GeometricFeatures,
    HoleCandidate,
    TextCluster,
)
from quotation.domain.raw_entity import (
    CircleGeometry,
    EntityType,
    LineGeometry,
    PolylineGeometry,
    RawEntity,
    TextGeometry,
)

logger = logging.getLogger("quotation.infrastructure.feature.geometric")

# Diameter threshold: circles larger than this are contour circles, not holes
MAX_HOLE_DIAMETER_MM = 30.0


class GeometricExtractor:
    """Extract geometric features from raw CAD entities."""

    def extract(self, entities: list[RawEntity]) -> GeometricFeatures:
        """Main extraction pipeline."""
        bbox = self._extract_bounding_box(entities)
        holes = self._extract_hole_candidates(entities)
        texts = self._extract_text_clusters(entities)

        return GeometricFeatures(
            bounding_box=bbox,
            hole_candidates=holes,
            text_clusters=texts,
        )

    # -- Bounding Box --

    def _extract_bounding_box(self, entities: list[RawEntity]) -> BoundingBox | None:
        """Compute 2D bounding box from all LINE/POLYLINE vertices."""
        points: list[tuple[float, float]] = []
        handles: list[str] = []

        for e in entities:
            if e.handle:
                handles.append(e.handle)
            if e.entity_type == EntityType.LINE and isinstance(e.geometry, LineGeometry):
                points.append((e.geometry.start_x, e.geometry.start_y))
                points.append((e.geometry.end_x, e.geometry.end_y))
            elif e.entity_type in (EntityType.POLYLINE, EntityType.LWPOLYLINE) and isinstance(e.geometry, PolylineGeometry):
                for v in e.geometry.vertices:
                    if len(v) >= 2:
                        points.append((v[0], v[1]))

        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return BoundingBox(
            min_x=min(xs), min_y=min(ys),
            max_x=max(xs), max_y=max(ys),
            source_entities=handles[:20],  # Cap at 20 handles
        )

    # -- Hole Candidates --

    def _extract_hole_candidates(self, entities: list[RawEntity]) -> list[HoleCandidate]:
        """Extract small circles as hole candidates."""
        candidates: list[HoleCandidate] = []

        for e in entities:
            if e.entity_type != EntityType.CIRCLE:
                continue
            if not isinstance(e.geometry, CircleGeometry):
                continue

            dia = e.geometry.diameter
            if dia <= 0 or dia > MAX_HOLE_DIAMETER_MM:
                continue

            candidates.append(HoleCandidate(
                center_x=e.geometry.center_x,
                center_y=e.geometry.center_y,
                diameter=dia,
                source_entity=e.handle or "",
                confidence=0.90,
            ))

        return candidates

    # -- Text Clusters --

    def _extract_text_clusters(self, entities: list[RawEntity]) -> list[TextCluster]:
        """Extract text from TEXT/MTEXT entities."""
        clusters: list[TextCluster] = []

        for e in entities:
            if e.entity_type not in (EntityType.TEXT, EntityType.MTEXT):
                continue
            if not isinstance(e.geometry, TextGeometry):
                continue
            content = e.geometry.content.strip()
            if not content:
                continue

            clusters.append(TextCluster(
                content=content,
                position_x=e.geometry.position_x,
                position_y=e.geometry.position_y,
                source_entity=e.handle or "",
            ))

        return clusters
