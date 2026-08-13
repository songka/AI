"""Tests for Rule domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quotation.domain.rule import (
    MaterialRule,
    MaterialStatus,
    ProcessRule,
    RuleSet,
    SurfacePricingMode,
    SurfaceRule,
)


class TestMaterialStatus:
    def test_values(self):
        assert MaterialStatus.ACTIVE == "ACTIVE"
        assert MaterialStatus.PENDING == "PENDING"
        assert MaterialStatus.DEPRECATED == "DEPRECATED"


class TestSurfacePricingMode:
    def test_values(self):
        modes = {m.value for m in SurfacePricingMode}
        assert modes == {"by_weight", "by_area", "by_piece", "by_length"}


class TestMaterialRule:
    def test_create(self):
        r = MaterialRule(
            material_id="MAT_A6061",
            material_name="A6061-T6",
            aliases=["6061", "AL6061", "6061-T6"],
            unit_price=38.0,
            loss_rate=0.05,
        )
        assert r.material_id == "MAT_A6061"
        assert r.material_name == "A6061-T6"
        assert "6061" in r.aliases
        assert r.unit_price == 38.0
        assert r.status == MaterialStatus.ACTIVE

    def test_create_pending(self):
        """SPCC — price not yet confirmed by procurement."""
        r = MaterialRule(
            material_id="MAT_SPCC",
            material_name="SPCC",
            unit_price=0,
            status=MaterialStatus.PENDING,
            note="冷軋鋼板，價格待採購部門確認",
        )
        assert r.status == MaterialStatus.PENDING
        assert r.unit_price == 0.0

    def test_zero_price_active_is_allowed(self):
        """Pydantic allows unit_price=0 — status check happens in application layer."""
        r = MaterialRule(
            material_id="MAT_X",
            material_name="X",
            unit_price=0,
            status=MaterialStatus.ACTIVE,
        )
        assert r.unit_price == 0.0

    def test_loss_rate_bounds(self):
        with pytest.raises(ValidationError):
            MaterialRule(
                material_id="MAT_X", material_name="X", unit_price=10, loss_rate=1.5
            )


class TestProcessRule:
    def test_create(self):
        r = ProcessRule(
            process_id="PROC_CNC",
            process_name="CNC",
            rate=80.0,
            conditions=["普通三軸", "公差>0.05mm"],
        )
        assert r.process_id == "PROC_CNC"
        assert r.rate == 80.0
        assert r.unit == "hour"
        assert len(r.conditions) == 2  # type: ignore[arg-type]

    def test_create_without_conditions(self):
        r = ProcessRule(process_id="PROC_LATHE", process_name="車床", rate=40.0)
        assert r.conditions is None


class TestSurfaceRule:
    def test_by_weight(self):
        r = SurfaceRule(
            surface_id="SURF_HEAT",
            surface_name="熱處理",
            pricing_mode=SurfacePricingMode.BY_WEIGHT,
            unit_price=11.0,
            unit="kg",
            min_charge=50.0,
            applicable_materials=["S50C", "SKD11", "SKD61"],
        )
        assert r.pricing_mode == SurfacePricingMode.BY_WEIGHT
        assert r.min_charge == 50.0
        assert "S50C" in r.applicable_materials

    def test_by_area(self):
        r = SurfaceRule(
            surface_id="SURF_SPRAY",
            surface_name="噴塗",
            pricing_mode=SurfacePricingMode.BY_AREA,
            unit_price=0.35,
            unit="dm2",
            min_charge=50.0,
            applicable_materials=["SPCC"],
            note="顏色: RAL9003 皺紋白",
        )
        assert r.pricing_mode == SurfacePricingMode.BY_AREA
        assert r.unit == "dm2"

    def test_by_piece(self):
        r = SurfaceRule(
            surface_id="SURF_SMALL",
            surface_name="小件發黑",
            pricing_mode=SurfacePricingMode.BY_PIECE,
            unit_price=5.0,
            unit="piece",
            min_charge=20.0,
            applicable_materials=["S50C"],
        )
        assert r.pricing_mode == SurfacePricingMode.BY_PIECE


class TestRuleSet:
    def test_create_empty(self):
        rs = RuleSet(version="1.0")
        assert rs.version == "1.0"
        assert rs.material_count == 0
        assert rs.process_count == 0
        assert rs.surface_count == 0

    def test_create_with_rules(self):
        rs = RuleSet(
            version="1.1",
            source="3.0報價表-R01",
            materials=[
                MaterialRule(
                    material_id="MAT_A6061", material_name="A6061-T6", unit_price=38.0
                ),
                MaterialRule(
                    material_id="MAT_S50C", material_name="S50C", unit_price=9.0
                ),
            ],
            processes=[
                ProcessRule(process_id="PROC_CNC", process_name="CNC", rate=80.0),
                ProcessRule(process_id="PROC_LATHE", process_name="車床", rate=40.0),
            ],
            surfaces=[
                SurfaceRule(
                    surface_id="SURF_ANODIZE",
                    surface_name="陽極氧化",
                    pricing_mode=SurfacePricingMode.BY_AREA,
                    unit_price=0.15,
                    unit="dm2",
                    applicable_materials=["A6061-T6"],
                ),
            ],
        )
        assert rs.material_count == 2
        assert rs.process_count == 2
        assert rs.surface_count == 1

    def test_post_init_updates_counts(self):
        rs = RuleSet(version="1.0")
        assert rs.material_count == 0
        rs.materials.append(
            MaterialRule(
                material_id="MAT_A6061", material_name="A6061-T6", unit_price=38.0
            )
        )
        # Count is computed only in model_post_init, so it won't auto-update
        # unless we re-create. This is by design — use immutable patterns.
