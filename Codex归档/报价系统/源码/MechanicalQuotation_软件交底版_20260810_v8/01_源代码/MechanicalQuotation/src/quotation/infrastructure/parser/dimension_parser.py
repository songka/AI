"""Dimension Parser — extracts structured dimensions from raw text.

Supported formats:
- 928*796*15          → (928, 796, 15)
- 928×796×15          → (928, 796, 15)
- 928x796x15          → (928, 796, 15)
- φ250×15             → (250, None, 15)  — circular, diameter × thickness
- Φ250*15             → (250, None, 15)
- M8                  → thread specification, not a dimension
- 40*40               → (40, 40, None)   — 2D profile
- 1300*1300*995       → (1300, 1300, 995)
- 60*70*20            → (60, 70, 20)
- 1208*103.5*2        → (1208, 103.5, 2)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class DimensionStatus(str, Enum):
    SUCCESS = "success"    # Fully parsed
    PARTIAL = "partial"    # Some values missing
    FAILED = "failed"      # Could not parse


@dataclass
class ParsedDimension:
    """Structured dimension extracted from raw text."""

    raw_text: str
    status: DimensionStatus = DimensionStatus.FAILED

    # Parsed values (all in mm)
    length: float | None = None    # X / diameter for circular parts
    width: float | None = None     # Y
    height: float | None = None    # Z / thickness

    # Metadata
    is_circular: bool = False
    is_thread: bool = False         # True for M8, M6 style specs
    thread_spec: str | None = None  # "M8", "M6×1.0"

    issues: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Thread spec: M8, M6, M12×1.5
_RE_THREAD = re.compile(r"^[Mm](\d+)(?:[×xX]([\d.]+))?$")

# Circular dimension: φ250×15, Φ250*15, φ250
_RE_CIRCULAR = re.compile(
    r"^[φΦ]?\s*(\d+(?:\.\d+)?)\s*[×xX\*]\s*(\d+(?:\.\d+)?)$"
)
_RE_CIRCULAR_SINGLE = re.compile(r"^[φΦ]\s*(\d+(?:\.\d+)?)$")

# Three dimensions: 928*796*15, 928×796×15, 928x796x15
_RE_3D = re.compile(
    r"^(\d+(?:\.\d+)?)\s*[×xX\*]\s*(\d+(?:\.\d+)?)\s*[×xX\*]\s*(\d+(?:\.\d+)?)$"
)

# Two dimensions: 40*40, 60×70
_RE_2D = re.compile(
    r"^(\d+(?:\.\d+)?)\s*[×xX\*]\s*(\d+(?:\.\d+)?)$"
)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_dimension(text: str) -> ParsedDimension:
    """Parse a raw dimension string into structured values.

    Args:
        text: Raw dimension text, e.g. "928*796*15", "φ250×15", "M8"

    Returns:
        ParsedDimension with extracted values and status.
    """
    text = text.strip()

    if not text:
        return ParsedDimension(raw_text=text, status=DimensionStatus.FAILED,
                               issues=["Empty dimension text"])

    # 0) Check for thread spec first (M8, M6×1.0)
    m = _RE_THREAD.match(text)
    if m:
        return ParsedDimension(
            raw_text=text,
            status=DimensionStatus.SUCCESS,
            is_thread=True,
            thread_spec=text.upper(),
            issues=[],
        )

    # 1) Try 3D first: A*B*C (most specific)
    m = _RE_3D.match(text)
    if m:
        return ParsedDimension(
            raw_text=text,
            status=DimensionStatus.SUCCESS,
            length=float(m.group(1)),
            width=float(m.group(2)),
            height=float(m.group(3)),
        )

    # 2) Try 2D: A*B
    m = _RE_2D.match(text)
    if m:
        return ParsedDimension(
            raw_text=text,
            status=DimensionStatus.PARTIAL,
            length=float(m.group(1)),
            width=float(m.group(2)),
            height=None,
            issues=["2D profile — height missing"],
        )

    # 3) Try circular: φ250×15
    m = _RE_CIRCULAR.match(text)
    if m:
        dia = float(m.group(1))
        thick = float(m.group(2))
        return ParsedDimension(
            raw_text=text,
            status=DimensionStatus.SUCCESS,
            length=dia,
            width=None,
            height=thick,
            is_circular=True,
        )

    # 2) Try circular single: φ250
    m = _RE_CIRCULAR_SINGLE.match(text)
    if m:
        dia = float(m.group(1))
        return ParsedDimension(
            raw_text=text,
            status=DimensionStatus.PARTIAL,
            length=dia,
            is_circular=True,
            issues=["Single circular dimension — thickness missing"],
        )

    # 4) Try single number (e.g. just "15" as thickness)
    try:
        val = float(text)
        return ParsedDimension(
            raw_text=text,
            status=DimensionStatus.PARTIAL,
            height=val,
            issues=["Single value — assumed to be thickness"],
        )
    except ValueError:
        pass

    return ParsedDimension(
        raw_text=text,
        status=DimensionStatus.FAILED,
        issues=[f"Could not parse dimension: '{text}'"],
    )
