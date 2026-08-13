"""Supplier Price Import Service — Phase 4.6.3 IMPORT_OVERLAY.

Imports pricing_source_records and supplier_master from rule packages.
Mode: IMPORT_OVERLAY — never replaces existing company C rules.
"""

from __future__ import annotations

import json, logging, uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger("quotation.application.supplier_price_import")


class SupplierPriceImportService:
    """Import pricing records from a rule package (YAML or JSON)."""

    def __init__(self):
        self._records: list[dict] = []
        self._suppliers: list[dict] = []
        self._company_rules: dict = {}
        self._stats: dict[str, int] = {}
        self._blocked: list[str] = []

    def load_package(self, package_dir: str | Path) -> dict:
        """Load a rule package directory. Returns import summary."""
        d = Path(package_dir)

        # Load JSON (primary structured source)
        json_path = d / "pricing-rules-excel-r01-v1.0.json"
        if json_path.exists():
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            self._records = data.get("pricing_source_records", [])
            self._suppliers = data.get("supplier_master", [])
            self._company_rules = data.get("active_company_rules", {})
        else:
            # Fallback: load YAML
            import yaml
            yaml_path = d / "pricing-rules-excel-r01-v1.0.yaml"
            if yaml_path.exists():
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                self._records = data.get("pricing_source_records", [])
                self._suppliers = data.get("supplier_master", [])
                self._company_rules = data.get("active_company_rules", {})

        # Compute stats
        self._stats = {
            "total_records": len(self._records),
            "suppliers": len(self._suppliers),
            "company_rules_kept": len(self._company_rules.get("material", {})),
        }

        for r in self._records:
            s = r.get("status", "UNKNOWN")
            self._stats[s] = self._stats.get(s, 0) + 1

        # Identify blocked records
        BLOCKED = {"CONFLICT", "UNIT_CONFLICT", "UNKNOWN_PRICE", "AMBIGUOUS_MATERIAL_SPEC"}
        self._blocked = [
            r.get("record_id", "?") for r in self._records
            if r.get("status") in BLOCKED
            or r.get("effective_from") is None
            or r.get("tax_inclusion_status") == "UNKNOWN"
        ]

        self._stats["blocked_from_publish"] = len(self._blocked)
        self._stats["publishable"] = self._stats["total_records"] - len(self._blocked)

        return dict(self._stats)

    @property
    def records(self) -> list[dict]:
        return self._records

    @property
    def suppliers(self) -> list[dict]:
        return self._suppliers

    @property
    def company_rules(self) -> dict:
        return self._company_rules

    @property
    def blocked_records(self) -> list[str]:
        return self._blocked

    @property
    def is_overlay_mode(self) -> bool:
        """IMPORT_OVERLAY — never replaces C rules."""
        return True

    # === Validation checks per instruction §8 ===

    def validate(self) -> list[str]:
        """Run validation checks. Returns list of failures (empty = all pass)."""
        failures = []

        # 1. Record count = 96
        if len(self._records) != 96:
            failures.append(f"Expected 96 records, got {len(self._records)}")

        # 2. Supplier master = 6
        if len(self._suppliers) != 6:
            failures.append(f"Expected 6 suppliers, got {len(self._suppliers)}")

        # 3. A6061-T6 three prices: 28/35/25
        a6061 = [r for r in self._records if r.get("canonical_material_code") == "A6061-T6"]
        prices = {r.get("unit_price") for r in a6061}
        expected = {28.0, 35.0, 25.0}
        if not expected.issubset(prices):
            failures.append(f"A6061-T6 prices {prices} missing {expected - prices}")

        # 4. PC = 60
        pc = [r for r in self._records if r.get("canonical_material_code") == "PC"]
        if 60.0 not in {r.get("unit_price") for r in pc}:
            failures.append("PC price 60 not found")

        # 5. Beryllium 180/130/220/170
        be = [r for r in self._records if "鈹銅" in str(r.get("raw_material_name", ""))]
        be_prices = {r.get("unit_price") for r in be}
        if not {180.0, 130.0, 220.0, 170.0}.issubset(be_prices):
            failures.append(f"Beryllium prices {be_prices}")

        # 6. Acrylic 30/28/25
        ac = [r for r in self._records if "亞克力" in str(r.get("raw_material_name", ""))]
        ac_prices = {r.get("unit_price") for r in ac}
        if not {30.0, 28.0, 25.0}.issubset(ac_prices):
            failures.append(f"Acrylic prices {ac_prices}")

        # 7. Aluminum profiles
        al30 = [r for r in self._records if "30x30" in str(r.get("material_spec", ""))]
        if 30.0 not in {r.get("unit_price") for r in al30}:
            failures.append("30x30 aluminum not 30/m")
        al40 = [r for r in self._records if "40x40" in str(r.get("material_spec", ""))]
        if 48.0 not in {r.get("unit_price") for r in al40}:
            failures.append("40x40 aluminum not 48/m")
        al20 = [r for r in self._records if "20x30" in str(r.get("material_spec", ""))]
        if not al20 or al20[0].get("unit_price") is not None:
            failures.append("20x30 should be UNKNOWN_PRICE (null price)")

        # 8. SUJ2 CONFLICT
        suj2 = [r for r in self._records if r.get("status") == "CONFLICT"]
        if len(suj2) < 2:
            failures.append(f"SUJ2 conflicts: {len(suj2)} < 2")

        # 9. Insulation UNIT_CONFLICT
        unit_c = [r for r in self._records if r.get("status") == "UNIT_CONFLICT"]
        if len(unit_c) < 1:
            failures.append("Missing UNIT_CONFLICT")

        # 10. JMD AMBIGUOUS_MATERIAL_SPEC
        ambig = [r for r in self._records if r.get("status") == "AMBIGUOUS_MATERIAL_SPEC"]
        if len(ambig) < 1:
            failures.append("Missing AMBIGUOUS_MATERIAL_SPEC")

        # 11. Tax: WS2 = UNKNOWN, WS1 = EXCLUDED
        ws2_tax = {r.get("tax_inclusion_status") for r in self._records if "工作表2" in str(r.get("source_sheet", ""))}
        if "UNKNOWN" not in str(ws2_tax):
            failures.append(f"WS2 tax should be UNKNOWN, got {ws2_tax}")

        # 12. No S→C without approval
        for r in self._records:
            if r.get("price_source") == "C":
                failures.append(f"{r.get('record_id')}: S should not be auto-published as C")

        # 14. Unknown = null (not 0)
        for r in self._records:
            if r.get("status") == "UNKNOWN_PRICE" and r.get("unit_price") == 0.0:
                failures.append(f"{r.get('record_id')}: unknown should be null, not 0")

        return failures
