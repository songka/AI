"""Geometric Feature domain models — Layer 2 of CAD parsing.

Groups raw CAD entities into geometric primitives:
- BoundingBox: overall part envelope
- HoleCandidate: small circles (potential holes)
- TextCluster: text annotations
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FeatureValue(BaseModel):
    """A feature measurement with source tracing and confidence."""

    value: float | str | None = None
    source: str = "UNKNOWN"       # CAD_GEOMETRY | DRAWING_TEXT | INFERRED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_entities: list[str] = Field(default_factory=list)  # RawEntity handles


class BoundingBox(BaseModel):
    """2D bounding box of the part envelope."""

    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @property
    def length(self) -> float:
        return self.max_x - self.min_x

    @property
    def width(self) -> float:
        return self.max_y - self.min_y

    source: str = "CAD_GEOMETRY"
    confidence: float = 0.98
    source_entities: list[str] = Field(default_factory=list)


class HoleCandidate(BaseModel):
    """A small-circle candidate that may be a hole."""

    center_x: float
    center_y: float
    diameter: float
    source_entity: str = ""      # RawEntity handle
    confidence: float = 0.90


class TextCluster(BaseModel):
    """A text annotation cluster."""

    content: str
    position_x: float
    position_y: float
    source_entity: str = ""


class GeometricFeatures(BaseModel):
    """Aggregate of all Layer 2 geometric features."""

    bounding_box: BoundingBox | None = None
    hole_candidates: list[HoleCandidate] = Field(default_factory=list)
    text_clusters: list[TextCluster] = Field(default_factory=list)

    @property
    def candidate_count(self) -> int:
        return len(self.hole_candidates)
