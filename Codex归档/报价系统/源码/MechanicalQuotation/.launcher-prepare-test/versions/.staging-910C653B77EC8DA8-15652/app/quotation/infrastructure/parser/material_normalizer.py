"""Material Name Normalizer.

Unifies variant material name spellings to a standard form.

Examples:
    SUS304  → SUS304
    304     → SUS304
    SUS-304 → SUS304
    AL6061  → A6061-T6
    6061    → A6061-T6
    6061-T6 → A6061-T6
    S50C    → S50C
    skd11   → SKD11
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Normalization table
# ---------------------------------------------------------------------------

# Ordered from most-specific to least-specific to avoid false matches.
# Format: (canonical_name, [aliases...])
_MATERIAL_ALIASES: list[tuple[str, list[str]]] = [
    ("方通", ["方通", "方管", "矩形管", "square tube"]),
    (
        "A6061-T6",
        [
            "A6061-T6",
            "A6061T6",
            "AL6061-T6",
            "AL6061T6",
            "6061-T6",
            "6061T6",
            "AL6061",
            "6061",
            "6061鋁",
            "鋁6061",
        ],
    ),
    (
        "SUS304",
        [
            "SUS304",
            "SUS-304",
            "SUS 304",
            "304",
            "304SS",
            "304不鏽鋼",
            "不鏽鋼304",
            "不鏽鋼",
            "不锈钢",
            "stainless steel",
            "stainless",
        ],
    ),
    (
        "SUS316",
        [
            "SUS316",
            "SUS-316",
            "SUS 316",
            "316",
            "316L",
        ],
    ),
    (
        "S50C",
        [
            "S50C",
            "S-50C",
            "S 50C",
            "50C",
            "s50c",
        ],
    ),
    (
        "SKD11",
        [
            "SKD11",
            "SKD-11",
            "SKD 11",
        ],
    ),
    (
        "SKD61",
        [
            "SKD61",
            "SKD-61",
            "SKD 61",
        ],
    ),
    (
        "SPCC",
        [
            "SPCC",
            "SPCC-SD",
            "冷軋鋼板",
            "冷轧钢板",
        ],
    ),
    (
        "普通鋼",
        [
            "普通鋼",
            "普通钢",
            "普通",
            "SS400",
            "Q235",
            "A3鋼",
        ],
    ),
    (
        "鋁型材",
        [
            "鋁型材",
            "铝型材",
            "鋁擠型",
            "铝挤型",
        ],
    ),
]

# Build lookup: lowercased alias → canonical name
_LOOKUP: dict[str, str] = {}
for canonical, aliases in _MATERIAL_ALIASES:
    for alias in aliases:
        key = alias.lower().replace("-", "").replace(" ", "")
        if key not in _LOOKUP:
            _LOOKUP[key] = canonical


@dataclass
class NormalizationResult:
    """Result of material name normalization."""

    original: str
    normalized: str | None = None
    confidence: float = 0.0  # 0.0 - 1.0
    matched_by: str = ""  # Which alias matched
    note: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_material(text: str) -> NormalizationResult:
    """Normalize a material name to its canonical form.

    Args:
        text: Raw material name from BOM or CAD text.

    Returns:
        NormalizationResult with canonical name and confidence.
    """
    if not text or not text.strip():
        return NormalizationResult(
            original=text,
            normalized=None,
            confidence=0.0,
            note="Empty input",
        )

    original = text.strip()

    # Exact match (case-insensitive, punctuation-normalized)
    key = original.lower().replace("-", "").replace(" ", "")
    if key in _LOOKUP:
        return NormalizationResult(
            original=original,
            normalized=_LOOKUP[key],
            confidence=0.95,
            matched_by=key,
        )

    # Partial match — check if any alias is contained in the input
    for canonical, aliases in _MATERIAL_ALIASES:
        for alias in aliases:
            alias_key = alias.lower().replace("-", "").replace(" ", "")
            if alias_key in key and len(alias_key) >= 3:
                return NormalizationResult(
                    original=original,
                    normalized=canonical,
                    confidence=0.7,
                    matched_by=alias,
                    note=f"Partial match via '{alias}'",
                )

    # Known material categories
    category_hints = {
        "鋁": "可能是鋁合金（需確認具體牌號）",
        "钢": "可能是鋼材（需確認具體牌號）",
        "鋼": "可能是鋼材（需確認具體牌號）",
        "鐵": "可能是鐵材（需確認具體牌號）",
    }
    for hint_char, msg in category_hints.items():
        if hint_char in original:
            return NormalizationResult(
                original=original,
                normalized=None,
                confidence=0.3,
                note=msg,
            )

    return NormalizationResult(
        original=original,
        normalized=None,
        confidence=0.0,
        note=f"Unknown material: '{original}'",
    )


def get_canonical_name(material_name: str) -> str | None:
    """Convenience: return canonical name or None."""
    result = normalize_material(material_name)
    return result.normalized
