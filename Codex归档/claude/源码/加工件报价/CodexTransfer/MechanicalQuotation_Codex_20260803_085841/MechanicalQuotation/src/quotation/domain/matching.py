"""DWG/BOM Matching domain models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from quotation.domain.bom import ParsedPart


class MatchLevel(str, Enum):
    LEVEL_1 = "L1"         # Exact: filename number ↔ BOM item
    LEVEL_2 = "L2"         # Semantic: part_code + material
    LEVEL_3 = "L3"         # Feature: dimensions + material + surface
    UNMATCHED = "UNMATCHED"


class MatchResult(BaseModel):
    """Result of matching one DWG file to BOM data."""

    source_dwg: str = Field(..., description="DWG filename")
    dwg_candidate: str | None = Field(
        default=None, description="Extracted candidate number from filename"
    )

    matched_part: ParsedPart | None = Field(
        default=None, description="Matched BOM ParsedPart"
    )
    matched_bom_item: str | None = Field(default=None)

    match_level: MatchLevel = MatchLevel.UNMATCHED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_by: str = Field(default="", description="What produced the match")
    evidence: str = Field(default="", description="Human-readable evidence")

    issues: list[str] = Field(default_factory=list)


class MatchReport(BaseModel):
    """Summary of DWG↔BOM matching results."""

    total_dwg: int = 0
    total_bom_parts: int = 0

    l1_matched: int = 0
    l2_matched: int = 0
    l3_matched: int = 0
    unmatched: int = 0

    results: list[MatchResult] = Field(default_factory=list)

    unmatched_dwg: list[str] = Field(default_factory=list)
    matched_dwg: list[str] = Field(default_factory=list)
