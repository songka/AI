"""Serialization utilities for domain models.

Handles JSON serialization/deserialization with type preservation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class QuotationEncoder(json.JSONEncoder):
    """Custom JSON encoder for quotation domain objects."""

    def default(self, obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize a domain object to JSON string."""
    return json.dumps(obj, cls=QuotationEncoder, ensure_ascii=False, indent=indent)


def to_json_file(obj: Any, file_path: str | Path) -> None:
    """Write a domain object to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(obj), encoding="utf-8")


def from_json_file(file_path: str | Path) -> dict[str, Any]:
    """Read JSON from a file."""
    return json.loads(Path(file_path).read_text(encoding="utf-8"))
