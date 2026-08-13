"""BOM Description Parser.

Parses semicolon-delimited BOM description strings into structured ParsedPart objects.

Format:
    segment0;segment1;segment2;segment3;segment4;segment5;...

Typical patterns:
    加工件: 原材料;加工件;S50C;J003;928*796*15;表面鍍鉻
    電控件: 原材料;電控外購件;控制類;PLC擴展;擴展IO模塊;型號:AS16AP11T-A;品牌:台達
    機構件: 原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from quotation.domain.bom import ParsedPart
from quotation.infrastructure.parser.dimension_parser import (
    DimensionStatus,
    parse_dimension,
)
from quotation.infrastructure.parser.material_normalizer import normalize_material


# ---------------------------------------------------------------------------
# Parse status
# ---------------------------------------------------------------------------

class ParseStatus(str, Enum):
    SUCCESS = "success"    # All expected fields present
    PARTIAL = "partial"    # Some fields missing
    FAILED = "failed"      # Cannot parse at all


@dataclass
class ParseIssue:
    """A single issue found during parsing."""
    severity: str        # "warning" | "error"
    field: str           # Which field is affected
    message: str


@dataclass
class DescriptionParseResult:
    """Complete result of parsing a BOM description."""

    # The populated ParsedPart (domain model)
    parsed_part: ParsedPart

    # Parse status
    status: ParseStatus = ParseStatus.SUCCESS

    # Issues found
    issues: list[ParseIssue] = field(default_factory=list)

    # Raw segments for debugging
    raw_segments: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Known sub-types and which kind they map to
_MACHINED_SUBTYPES = {"加工件"}
_ELECTRICAL_SUBTYPES = {"電控外購件", "电控外购件"}
_MECHANICAL_SUBTYPES = {"機構外購件", "机构外购件", "機加件"}


class DescriptionParser:
    """Parses BOM description text into structured ParsedPart objects.

    Usage:
        parser = DescriptionParser()
        result = parser.parse(bom_entry)
        # result.parsed_part → ParsedPart domain model
        # result.status → ParseStatus
        # result.issues → list of ParseIssue
    """

    def __init__(self, separator: str = ";"):
        self._separator = separator

    # -- Public API --

    def parse(
        self,
        bom_item: str,
        description: str,
        source_row: int = 0,
        unit_cost: float = 0.0,
    ) -> DescriptionParseResult:
        """Parse a single BOM description string.

        Args:
            bom_item: The BomEntry.item identifier.
            description: The full semicolon-delimited description.
            source_row: Source Excel row for tracing.
            unit_cost: Unit cost from BOM.

        Returns:
            DescriptionParseResult with populated ParsedPart and status.
        """
        issues: list[ParseIssue] = []

        # Split into segments
        segments = [s.strip() for s in description.split(self._separator)]

        # Build ParsedPart with defaults
        pp = ParsedPart(
            bom_item=bom_item,
            source_row=source_row,
            unit_cost=unit_cost,
        )

        # Parse category (segment 0)
        if len(segments) > 0 and segments[0]:
            pp.category = segments[0]
        else:
            issues.append(ParseIssue("warning", "category", "Missing category (segment 0)"))

        # Parse sub_type (segment 1) — determines is_quotable
        if len(segments) > 1 and segments[1]:
            pp.sub_type = segments[1]
            pp = self._classify_part(pp, segments[1])
        else:
            issues.append(ParseIssue("warning", "sub_type", "Missing sub_type (segment 1)"))

        # Parse material or type-category (segment 2)
        if len(segments) > 2 and segments[2]:
            pp = self._parse_material_field(pp, segments[2], issues)

        # Parse part code (segment 3)
        if len(segments) > 3 and segments[3]:
            pp = self._parse_code_field(pp, segments[3], issues)

        # Parse dimensions (segment 4)
        if len(segments) > 4 and segments[4]:
            pp = self._parse_dimension_field(pp, segments[4], issues)

        # Parse surface/brand/notes (segment 5+)
        if len(segments) > 5:
            pp = self._parse_tail_segments(pp, segments[5:], issues)

        # Determine overall status
        if not pp.category and not pp.sub_type:
            status = ParseStatus.FAILED
        elif not pp.sub_type:
            status = ParseStatus.FAILED  # Only category without sub_type → FAILED
        elif not pp.category:
            status = ParseStatus.PARTIAL  # Has sub_type but no category
        elif not pp.material and pp.sub_type in _MACHINED_SUBTYPES:
            status = ParseStatus.PARTIAL
        elif not pp.dimensions_raw and pp.sub_type in _MACHINED_SUBTYPES:
            status = ParseStatus.PARTIAL
        elif any(i.severity == "error" for i in issues):
            status = ParseStatus.PARTIAL
        else:
            status = ParseStatus.SUCCESS

        return DescriptionParseResult(
            parsed_part=pp,
            status=status,
            issues=issues,
            raw_segments=segments,
        )

    # -- Segment parsers --

    def _classify_part(self, pp: ParsedPart, sub_type: str) -> ParsedPart:
        """Determine is_quotable based on sub_type."""
        if sub_type in _MACHINED_SUBTYPES:
            pp.is_quotable = True
        elif sub_type in _ELECTRICAL_SUBTYPES or sub_type in _MECHANICAL_SUBTYPES:
            pp.is_quotable = False
        # Unknown sub_type → not quotable by default
        return pp

    def _parse_material_field(
        self, pp: ParsedPart, raw: str, issues: list[ParseIssue]
    ) -> ParsedPart:
        """Parse segment 2 as material (加工件) or category (外購件)."""
        if pp.sub_type in _MACHINED_SUBTYPES:
            pp.material = raw
            # Normalize
            result = normalize_material(raw)
            if result.normalized:
                if result.confidence < 0.9:
                    issues.append(ParseIssue(
                        "warning", "material",
                        f"Material '{raw}' normalized to '{result.normalized}' "
                        f"(confidence={result.confidence:.0%}): {result.note}"
                    ))
            else:
                issues.append(ParseIssue(
                    "warning", "material",
                    f"Cannot normalize material: '{raw}'. {result.note}"
                ))
        elif pp.sub_type in _ELECTRICAL_SUBTYPES:
            pp.spec = raw  # e.g. "控制類"
        elif pp.sub_type in _MECHANICAL_SUBTYPES:
            pp.material = raw  # e.g. "鋁型材"
        return pp

    def _parse_code_field(
        self, pp: ParsedPart, raw: str, issues: list[ParseIssue]
    ) -> ParsedPart:
        """Parse segment 3 as part code or sub-category."""
        if pp.sub_type in _MACHINED_SUBTYPES:
            pp.part_code = raw
        elif pp.sub_type in _ELECTRICAL_SUBTYPES:
            if pp.spec:
                pp.spec = f"{pp.spec};{raw}"
            else:
                pp.spec = raw
        elif pp.sub_type in _MECHANICAL_SUBTYPES:
            # Could be dimensions, code, or prefixed field
            if _looks_like_dimension(raw):
                pp.dimensions_raw = raw
            elif raw.startswith("圖號:") or raw.startswith("图号:"):
                pp.part_code = raw.split(":", 1)[-1].strip()
            elif raw.startswith("型號:") or raw.startswith("型号:"):
                pp.model_number = raw.split(":", 1)[-1].strip()
            elif raw.startswith("品牌:"):
                pp.brand = raw.split(":", 1)[-1].strip()
            else:
                pp.part_code = raw
        return pp

    def _parse_dimension_field(
        self, pp: ParsedPart, raw: str, issues: list[ParseIssue]
    ) -> ParsedPart:
        """Parse segment 4 as dimensions, specs, or prefixed fields."""
        if pp.sub_type in _MACHINED_SUBTYPES:
            pp.dimensions_raw = raw
            dim_result = parse_dimension(raw)
            if dim_result.status == DimensionStatus.FAILED:
                issues.append(ParseIssue(
                    "warning", "dimensions",
                    f"Cannot parse dimension: '{raw}'. {dim_result.issues}"
                ))
            elif dim_result.status == DimensionStatus.PARTIAL:
                issues.append(ParseIssue(
                    "warning", "dimensions",
                    f"Partial dimension parse: {dim_result.issues}"
                ))
        elif pp.sub_type in _ELECTRICAL_SUBTYPES:
            if raw.startswith("型號:") or raw.startswith("型号:"):
                pp.model_number = raw.split(":", 1)[-1].strip()
            elif raw.startswith("品牌:"):
                pp.brand = raw.split(":", 1)[-1].strip()
            else:
                existing = pp.spec or ""
                pp.spec = f"{existing};{raw}" if existing else raw
        elif pp.sub_type in _MECHANICAL_SUBTYPES:
            if raw.startswith("圖號:") or raw.startswith("图号:"):
                pp.part_code = raw.split(":", 1)[-1].strip()
            elif raw.startswith("型號:") or raw.startswith("型号:"):
                pp.model_number = raw.split(":", 1)[-1].strip()
            elif raw.startswith("品牌:"):
                pp.brand = raw.split(":", 1)[-1].strip()
            else:
                pp.dimensions_raw = raw
        return pp

    def _parse_tail_segments(
        self, pp: ParsedPart, segments: list[str], issues: list[ParseIssue]
    ) -> ParsedPart:
        """Parse remaining segments (5+) for surface treatment / brand / notes."""
        for seg in segments:
            if not seg:
                continue

            if pp.sub_type in _MACHINED_SUBTYPES:
                # First non-dimension tail = surface treatment
                if not pp.surface_treatment:
                    pp.surface_treatment = seg
                # Subsequent tails = extra notes (could be tolerances, etc.)
            elif pp.sub_type in _ELECTRICAL_SUBTYPES:
                if seg.startswith("型號:") or seg.startswith("型号:"):
                    pp.model_number = seg.split(":", 1)[-1].strip()
                elif seg.startswith("品牌:"):
                    pp.brand = seg.split(":", 1)[-1].strip()
                else:
                    pp.spec = f"{pp.spec};{seg}" if pp.spec else seg
            elif pp.sub_type in _MECHANICAL_SUBTYPES:
                if seg.startswith("圖號:") or seg.startswith("图号:"):
                    pp.part_code = seg.split(":", 1)[-1].strip()
                elif seg.startswith("型號:") or seg.startswith("型号:"):
                    pp.model_number = seg.split(":", 1)[-1].strip()
                elif seg.startswith("品牌:"):
                    pp.brand = seg.split(":", 1)[-1].strip()
                elif not pp.surface_treatment:
                    pp.surface_treatment = seg

        return pp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _looks_like_dimension(text: str) -> bool:
    """Check if text looks like a dimension (contains * or × or starts with φ)."""
    import re
    return bool(re.search(r"[*×xXφΦ]", text) or re.match(r"^\d+$", text))
