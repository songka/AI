"""Published Pricebook Loader — reads current version pointer, validates snapshot, builds indexes.

Responsibilities:
1. Read Current Version Pointer
2. Find and validate Published Snapshot (status=PUBLISHED, SHA256, version)
3. Load Material/Process/Surface C prices
4. Build read-only lookup indexes
5. MUST NOT read draft files as formal price sources
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from quotation.infrastructure.smb.client import cached_public_path
from quotation.utils.normalization import normalize_profile_spec

logger = logging.getLogger("quotation.infrastructure.rules.published_pricebook_loader")

BUNDLED_POINTER_PATH = Path("data/current-version-pointer.json")
DEFAULT_POINTER_PATH = BUNDLED_POINTER_PATH


# ---------------------------------------------------------------------------
# Origin type → origin_price_source mapping
# ---------------------------------------------------------------------------

_ORIGIN_TYPE_TO_SOURCE: dict[str, str] = {
    "SUPPLIER_PRICE_RECORD": "S",
    "LEGACY_INTERNAL_RATE": "I",
    "MANUAL_ADMIN_SELECTION": "M",
    "AI_SUGGESTION": "AI",
    "HISTORICAL": "H",
    "PENDING_SUPPLIER": "PENDING",
}


def _map_origin_price_source(origin_type: str | None) -> str | None:
    """Map snapshot origin_type to origin_price_source code."""
    if not origin_type:
        return None
    return _ORIGIN_TYPE_TO_SOURCE.get(origin_type, origin_type)


def _is_eligible_for_resolution(selection_policy: str | None, origin_type: str | None) -> bool:
    """Check if a price entry is eligible for automatic resolution.

    Pending Supplier entries are NOT eligible.
    MANUAL_ADMIN_SELECTION and SUPPLIER_PRICE_RECORD are eligible.
    """
    if selection_policy == "PENDING" or origin_type == "PENDING_SUPPLIER":
        return False
    return True


# ---------------------------------------------------------------------------
# Price lookup result with full trace
# ---------------------------------------------------------------------------

@dataclass
class PriceLookupResult:
    """Result of a price lookup with full traceability metadata."""
    unit_price: float
    price_version_id: str | None = None
    company_price_id: str | None = None
    origin_price_record_id: str | None = None
    origin_supplier_id: str | None = None
    origin_price_source: str | None = None
    unit: str = "kg"
    currency: str = "CNY"
    price_basis: str | None = None
    effective_from: str | None = None
    resolution_source: str = "LEGACY_YAML"
    fallback_reason: str | None = None
    fallback_approval_status: str | None = None
    fallback_warning: bool = False
    eligible_for_resolution: bool = True


# ---------------------------------------------------------------------------
# Material / Process / Surface index entries
# ---------------------------------------------------------------------------

@dataclass
class MaterialPriceEntry:
    canonical_code: str
    specification: str | None
    unit_price: float
    unit: str
    company_price_id: str
    origin_price_record_id: str | None
    origin_supplier_id: str | None
    origin_price_source: str | None
    price_basis: str | None
    effective_from: str | None
    eligible_for_resolution: bool = True


@dataclass
class ProcessPriceEntry:
    process_code: str
    unit_price: float
    unit: str
    company_price_id: str
    price_basis: str | None
    effective_from: str | None


@dataclass
class SurfacePriceEntry:
    surface_code: str
    unit_price: float
    unit: str
    pricing_mode: str  # "by_weight" | "by_area"
    company_price_id: str
    price_basis: str | None
    effective_from: str | None


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

class PublishedPricebookLoader:
    """Loads the published company pricebook and provides indexed lookups.

    Only reads snapshots with status=PUBLISHED. Draft files are rejected.
    """

    def __init__(self, pointer_path: str | Path | None = None):
        if pointer_path:
            self._pointer_path = Path(pointer_path)
        elif DEFAULT_POINTER_PATH != BUNDLED_POINTER_PATH:
            # Test and embedded callers may deliberately replace the default
            # pointer to isolate themselves from every production source.
            self._pointer_path = DEFAULT_POINTER_PATH
        else:
            self._pointer_path = cached_public_path(
                "prices/published/current-version-pointer.json", DEFAULT_POINTER_PATH
            )
        self._snapshot: dict[str, Any] | None = None
        self._price_version_id: str | None = None

        # Indexes
        self._materials: dict[str, MaterialPriceEntry] = {}
        self._processes: dict[str, ProcessPriceEntry] = {}
        self._surfaces: dict[str, SurfacePriceEntry] = {}

        # State
        self.loaded: bool = False
        self.load_error: str | None = None

        self._try_load()

    # ------------------------------------------------------------------
    # Load pipeline
    # ------------------------------------------------------------------

    def _try_load(self) -> None:
        """Best-effort load. On failure, record error and leave indexes empty."""
        try:
            pointer = self._read_pointer()
            snapshot_path = self._resolve_snapshot_path(pointer)
            self._snapshot = self._read_snapshot(snapshot_path)
            self._validate_snapshot(self._snapshot, pointer)
            self._build_indexes(self._snapshot)
            self.loaded = True
            logger.info(
                "Published pricebook loaded: %s (%d materials, %d processes, %d surfaces)",
                self._price_version_id,
                len(self._materials),
                len(self._processes),
                len(self._surfaces),
            )
        except Exception as e:
            self.load_error = str(e)
            logger.warning("Published pricebook NOT loaded: %s — will use legacy YAML fallback", e)

    def _read_pointer(self) -> dict[str, Any]:
        """Read and validate the current version pointer."""
        if not self._pointer_path.exists():
            raise FileNotFoundError(f"Current version pointer not found: {self._pointer_path}")
        try:
            with open(self._pointer_path, encoding="utf-8") as f:
                pointer = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Current version pointer is not valid JSON: {e}")

        if "current_version" not in pointer:
            raise ValueError("Current version pointer missing 'current_version' field")
        if "snapshot_path" not in pointer:
            raise ValueError("Current version pointer missing 'snapshot_path' field")
        return pointer

    def _resolve_snapshot_path(self, pointer: dict[str, Any]) -> Path:
        """Resolve the snapshot path. Tries:
        1. Absolute path
        2. Relative to pointer file's directory
        3. Relative to CWD
        """
        raw = pointer["snapshot_path"]
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate

        # Try relative to pointer directory first
        relative_to_pointer = (self._pointer_path.parent / raw).resolve()
        if relative_to_pointer.exists():
            return relative_to_pointer

        # Fall back to CWD
        relative_to_cwd = Path(raw).resolve()
        if relative_to_cwd.exists():
            return relative_to_cwd

        # Neither exists; return pointer-relative (will fail in _read_snapshot with clear error)
        return relative_to_pointer

    def _read_snapshot(self, path: Path) -> dict[str, Any]:
        """Read the snapshot JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {path}")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Snapshot is not valid JSON: {e}")

    def _validate_snapshot(self, snapshot: dict[str, Any], pointer: dict[str, Any]) -> None:
        """Validate the snapshot against the pointer and integrity rules."""
        # Status must be PUBLISHED
        status = snapshot.get("status", "")
        if status != "PUBLISHED":
            raise ValueError(f"Snapshot status is '{status}', not PUBLISHED")

        # Price version must match pointer
        expected_version = pointer["current_version"]
        actual_version = snapshot.get("price_version_id", "")
        if actual_version != expected_version:
            raise ValueError(
                f"Price version mismatch: pointer={expected_version}, snapshot={actual_version}"
            )

        # Effective date must be in the past or today
        effective_from = snapshot.get("effective_from")
        if effective_from:
            try:
                eff_date = date.fromisoformat(effective_from[:10])
                if eff_date > date.today():
                    raise ValueError(f"Snapshot effective_from is in the future: {effective_from}")
            except ValueError:
                raise ValueError(f"Invalid effective_from date: {effective_from}")

        # SHA256 verification (best-effort)
        expected_sha = snapshot.get("snapshot_sha256")
        if expected_sha:
            actual_sha = self._compute_snapshot_sha256(snapshot)
            if actual_sha != expected_sha:
                raise ValueError(
                    f"SHA256 mismatch: expected={expected_sha[:16]}..., actual={actual_sha[:16]}..."
                )

        # Must have company_prices array
        if "company_prices" not in snapshot:
            raise ValueError("Snapshot missing 'company_prices' array")

    @staticmethod
    def _compute_snapshot_sha256(snapshot: dict[str, Any]) -> str:
        """Compute SHA256 over the company_prices array (canonical JSON).

        Uses default json.dumps with sort_keys and ensure_ascii=False
        (matching the canonicalization used during publication).
        """
        prices = snapshot.get("company_prices", [])
        canonical = json.dumps(prices, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def _build_indexes(self, snapshot: dict[str, Any]) -> None:
        """Build lookup indexes from the company_prices array."""
        self._price_version_id = snapshot["price_version_id"]

        for entry in snapshot.get("company_prices", []):
            target_type = entry.get("target_type", "")
            if target_type == "MATERIAL":
                self._index_material(entry)
            elif target_type == "PROCESS":
                self._index_process(entry)
            elif target_type == "SURFACE":
                self._index_surface(entry)

    def _index_material(self, entry: dict[str, Any]) -> None:
        """Index a material price entry.

        Matching key: canonical_code + specification + unit.
        Multiple entries per canonical_code are possible (different specs).

        Pending Supplier entries are indexed (for trace) but marked
        eligible_for_resolution=False. If multiple entries exist for the
        same key, the eligible one takes priority.
        """
        code = entry.get("canonical_code", "")
        raw_spec = entry.get("specification")
        spec = normalize_profile_spec(raw_spec) or raw_spec
        unit = entry.get("unit", "kg")
        origin_type = entry.get("origin_type")
        selection_policy = entry.get("selection_policy")

        key = self._material_key(code, spec, unit)
        eligible = _is_eligible_for_resolution(selection_policy, origin_type)

        mat_entry = MaterialPriceEntry(
            canonical_code=code,
            specification=spec,
            unit_price=float(entry["unit_price"]),
            unit=unit,
            company_price_id=entry.get("company_price_id", ""),
            origin_price_record_id=entry.get("origin_price_record_id"),
            origin_supplier_id=entry.get("origin_supplier_id"),
            origin_price_source=_map_origin_price_source(origin_type),
            price_basis=entry.get("price_basis"),
            effective_from=entry.get("effective_from"),
            eligible_for_resolution=eligible,
        )

        # Only store if key is new OR existing entry is not eligible
        existing = self._materials.get(key)
        if existing is None or (not existing.eligible_for_resolution and eligible):
            self._materials[key] = mat_entry

        # Also index without spec for exact-code-only lookups
        simple_key = self._material_key(code, None, unit)
        if simple_key not in self._materials:
            self._materials[simple_key] = mat_entry

    def _index_process(self, entry: dict[str, Any]) -> None:
        """Index a process price entry. Key: process_code + unit."""
        code = entry.get("canonical_code", "")
        unit = entry.get("unit", "hour")
        key = f"{code}:{unit}"

        self._processes[key] = ProcessPriceEntry(
            process_code=code,
            unit_price=float(entry["unit_price"]),
            unit=unit,
            company_price_id=entry.get("company_price_id", ""),
            price_basis=entry.get("price_basis"),
            effective_from=entry.get("effective_from"),
        )

    def _index_surface(self, entry: dict[str, Any]) -> None:
        """Index a surface price entry. Key: surface_code + unit."""
        code = entry.get("canonical_code", "")
        unit = entry.get("unit", "kg")

        # Detect pricing mode from unit
        pricing_mode = "by_area" if unit == "m2" else "by_weight"

        key = f"{code}:{unit}"
        self._surfaces[key] = SurfacePriceEntry(
            surface_code=code,
            unit_price=float(entry["unit_price"]),
            unit=unit,
            pricing_mode=pricing_mode,
            company_price_id=entry.get("company_price_id", ""),
            price_basis=entry.get("price_basis"),
            effective_from=entry.get("effective_from"),
        )

    @staticmethod
    def _material_key(code: str, spec: str | None, unit: str) -> str:
        """Build a lookup key for material entries."""
        spec_part = f":{spec}" if spec else ""
        return f"{code}{spec_part}:{unit}"

    # ------------------------------------------------------------------
    # Public lookup API
    # ------------------------------------------------------------------

    def lookup_material(
        self, material_code: str, specification: str | None = None, unit: str = "kg"
    ) -> PriceLookupResult | None:
        """Look up a material price in the published pricebook.

        Tries in order:
        1. Exact match: code + spec + unit
        2. Code-only match: code + unit (no spec)
        3. Substring match over canonical_code

        Only returns entries where eligible_for_resolution=True.
        Pending Supplier entries are excluded from resolution.
        """
        if not self.loaded:
            return None

        specification = normalize_profile_spec(specification) or specification

        # 1. Exact code + spec
        key = self._material_key(material_code, specification, unit)
        entry = self._materials.get(key)
        if entry is not None and entry.eligible_for_resolution:
            return self._to_result(entry)

        # 2. Code-only (without spec)
        simple_key = self._material_key(material_code, None, unit)
        entry = self._materials.get(simple_key)
        if entry is not None and entry.eligible_for_resolution:
            return self._to_result(entry)

        # 3. Fuzzy match on canonical_code
        code_norm = material_code.upper().replace("-", "").replace(" ", "")
        for key, entry in self._materials.items():
            if not entry.eligible_for_resolution:
                continue
            entry_norm = entry.canonical_code.upper().replace("-", "").replace(" ", "")
            if code_norm == entry_norm:
                return self._to_result(entry)
            if code_norm in entry_norm or entry_norm in code_norm:
                return self._to_result(entry)

        return None

    def lookup_process(self, process_code: str, unit: str = "hour") -> PriceLookupResult | None:
        """Look up a process price in the published pricebook."""
        if not self.loaded:
            return None

        key = f"{process_code}:{unit}"
        if key in self._processes:
            return self._to_result(self._processes[key])

        # Normalized match
        code_norm = process_code.upper().replace(" ", "")
        for key, entry in self._processes.items():
            if entry.process_code.upper().replace(" ", "") == code_norm:
                return self._to_result(entry)

        return None

    def lookup_surface(self, surface_code: str, unit: str = "kg") -> PriceLookupResult | None:
        """Look up a surface treatment price in the published pricebook."""
        if not self.loaded:
            return None

        key = f"{surface_code}:{unit}"
        if key in self._surfaces:
            return self._to_result(self._surfaces[key])

        # Normalized match
        code_norm = surface_code.upper().replace(" ", "")
        for key, entry in self._surfaces.items():
            entry_norm = entry.surface_code.upper().replace(" ", "")
            if code_norm == entry_norm:
                return self._to_result(entry)
            # Substring match (e.g. "表面鍍鉻" contains "鍍鉻")
            if entry_norm in code_norm or code_norm in entry_norm:
                return self._to_result(entry)

        return None

    def _to_result(self, entry: MaterialPriceEntry | ProcessPriceEntry | SurfacePriceEntry) -> PriceLookupResult:
        """Convert an index entry to a PriceLookupResult."""
        kwargs: dict[str, Any] = {
            "unit_price": entry.unit_price,
            "unit": entry.unit,
            "price_version_id": self._price_version_id,
            "company_price_id": entry.company_price_id,
            "price_basis": entry.price_basis,
            "effective_from": entry.effective_from,
            "resolution_source": "PUBLISHED_COMPANY_PRICEBOOK",
        }
        if isinstance(entry, MaterialPriceEntry):
            kwargs["origin_price_record_id"] = entry.origin_price_record_id
            kwargs["origin_supplier_id"] = entry.origin_supplier_id
            kwargs["origin_price_source"] = entry.origin_price_source
            kwargs["eligible_for_resolution"] = entry.eligible_for_resolution
        return PriceLookupResult(**kwargs)

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    @property
    def price_version(self) -> str | None:
        return self._price_version_id

    @property
    def is_active(self) -> bool:
        return self.loaded and len(self._materials) > 0
