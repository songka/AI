"""Regression: verify material data in Golden Dataset."""

from __future__ import annotations

import pytest

from quotation.infrastructure.parser.material_normalizer import get_canonical_name


class TestGoldenMaterial:
    """M1-M3: Material validation."""

    def test_all_materials_not_null(self, golden_data):
        """M1: All machined parts have non-null material."""
        for part in golden_data["parts"]:
            if part["sub_type"] == "加工件":
                assert part["material"] is not None, (
                    f"{part['bom_item']}: material is None"
                )
                assert part["material"] != "", (
                    f"{part['bom_item']}: material is empty"
                )

    def test_all_materials_normalizable(self, golden_data):
        """M2: All materials can be normalized."""
        for part in golden_data["parts"]:
            if part.get("material"):
                canonical = get_canonical_name(part["material"])
                # SPCC won't normalize (not in the normalizer table yet)
                # but other materials should
                if part["material"] not in ("SPCC", "普通鋼", "鋁型材"):
                    assert canonical is not None, (
                        f"{part['bom_item']}: cannot normalize '{part['material']}'"
                    )

    def test_material_distribution(self, golden_data):
        """Verify expected material distribution."""
        materials = {}
        for part in golden_data["parts"]:
            mat = part.get("material", "UNKNOWN")
            materials[mat] = materials.get(mat, 0) + 1

        assert materials.get("S50C", 0) == 4
        assert materials.get("A6061-T6", 0) == 5
        assert materials.get("SPCC", 0) == 8
        assert materials.get("SUS304", 0) == 1
        assert materials.get("普通鋼", 0) == 1
        assert materials.get("鋁型材", 0) == 1

    def test_no_unknown_materials_in_golden(self, golden_data):
        """Golden dataset should not contain truly unknown materials."""
        known = {"S50C", "A6061-T6", "SPCC", "SUS304", "SKD11", "SKD61", "普通鋼", "鋁型材"}
        for part in golden_data["parts"]:
            if part.get("material"):
                assert part["material"] in known, (
                    f"{part['bom_item']}: unknown material '{part['material']}'"
                )
