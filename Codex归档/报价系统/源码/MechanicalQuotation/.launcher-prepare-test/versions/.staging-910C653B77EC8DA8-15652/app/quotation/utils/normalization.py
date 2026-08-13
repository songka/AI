"""Shared normalization helpers for quotation identifiers."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


_PROFILE_SPEC = re.compile(r"(\d+(?:\.\d+)?)\s*[*×xX]\s*(\d+(?:\.\d+)?)")


def normalize_profile_spec(value: str | None) -> str | None:
    """Return profile dimensions as canonical ``widthxheight`` text."""
    if not value:
        return None
    match = _PROFILE_SPEC.search(value)
    if match is None:
        return None

    def canonical(number: str) -> str:
        try:
            parsed = Decimal(number)
        except InvalidOperation:
            return number
        return format(parsed.normalize(), "f")

    return f"{canonical(match.group(1))}x{canonical(match.group(2))}"
