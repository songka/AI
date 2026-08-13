"""Tests for Feature domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quotation.domain.drawing import TextEntity
from quotation.domain.feature import (
    BoundingBox,
    Dimensions,
    Feature,
    FeatureSource,
    Hole,
)


class TestBoundingBox:
    def test_create(self):
        bb = BoundingBox(min_x=0, min_y=0, min_z=0, max_x=928, max_y=796, max_z=15)
        assert bb.length == 928.0
        assert bb.width == 796.0
        assert bb.height == 15.0

    def test_default_z(self):
        bb = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=200)
        assert bb.min_z == 0.0
        assert bb.max_z == 0.0
        assert bb.height == 0.0

    def test_negative_coordinates(self):
        bb = BoundingBox(min_x=-50, min_y=-30, max_x=50, max_y=30, max_z=10)
        assert bb.length == 100.0
        assert bb.width == 60.0
        assert bb.height == 10.0


class TestDimensions:
    def test_create(self):
        d = Dimensions(length=928, width=796, height=15, raw_text="928*796*15")
        assert d.length == 928.0
        assert d.width == 796.0
        assert d.height == 15.0
        assert d.raw_text == "928*796*15"

    def test_create_without_raw(self):
        d = Dimensions(length=100, width=50, height=20)
        assert d.raw_text is None


class TestHole:
    def test_through_hole(self):
        h = Hole(diameter=6.0, center_x=50.0, center_y=100.0)
        assert h.diameter == 6.0
        assert h.depth is None  # through hole
        assert h.hole_type == "through"

    def test_blind_hole(self):
        h = Hole(
            diameter=10.0,
            center_x=200.0,
            center_y=300.0,
            depth=25.0,
            hole_type="blind",
        )
        assert h.depth == 25.0
        assert h.hole_type == "blind"

    def test_tapped_hole(self):
        h = Hole(
            diameter=5.0,
            center_x=10.0,
            center_y=20.0,
            hole_type="tapped",
            thread_spec="M6",
        )
        assert h.hole_type == "tapped"
        assert h.thread_spec == "M6"

    def test_counterbore_hole(self):
        h = Hole(
            diameter=11.0,
            center_x=50.0,
            center_y=50.0,
            depth=10.0,
            hole_type="counterbore",
        )
        assert h.hole_type == "counterbore"

    def test_zero_diameter_raises(self):
        with pytest.raises(ValidationError):
            Hole(diameter=0, center_x=0, center_y=0)

    def test_negative_diameter_raises(self):
        with pytest.raises(ValidationError):
            Hole(diameter=-5, center_x=0, center_y=0)


class TestFeatureSource:
    def test_all_sources(self):
        assert FeatureSource.CAD == "CAD"
        assert FeatureSource.BOM == "BOM"
        assert FeatureSource.BOTH == "BOTH"
        assert FeatureSource.MANUAL == "MANUAL"


class TestFeature:
    def test_create_minimal(self):
        f = Feature(id="feat-001", drawing_id="dwg-001")
        assert f.id == "feat-001"
        assert f.drawing_id == "dwg-001"
        assert f.overall_length == 0.0
        assert f.hole_count == 0
        assert f.feature_source == FeatureSource.CAD

    def test_create_full(self):
        f = Feature(
            id="feat-001",
            drawing_id="dwg-001",
            bom_ref="UC1000005854",
            bounding_box=BoundingBox(min_x=0, min_y=0, max_x=928, max_y=796, max_z=15),
            overall_length=928.0,
            overall_width=796.0,
            overall_height=15.0,
            dimensions_raw="928*796*15",
            volume_mm3=11_070_720.0,
            surface_area_mm2=1_529_376.0,
            weight_kg=86.91,
            holes=[
                Hole(diameter=6.0, center_x=50, center_y=100),
                Hole(
                    diameter=5.0,
                    center_x=200,
                    center_y=300,
                    hole_type="tapped",
                    thread_spec="M6",
                ),
            ],
            hole_count=2,
            through_holes=1,
            tapped_holes=1,
            threads=["M6"],
            contour_type="rectangular",
            material_text="S50C",
            material_normalized="S50C",
            surface_text="熱處理",
            surface_normalized="熱處理",
            tolerances=["平面度 0.05"],
            has_tight_tolerance=False,
            feature_source=FeatureSource.BOTH,
        )
        assert f.bom_ref == "UC1000005854"
        assert f.overall_length == 928.0
        assert f.volume_mm3 == 11_070_720.0
        assert f.weight_kg == 86.91
        assert len(f.holes) == 2
        assert f.hole_count == 2
        assert f.through_holes == 1
        assert f.tapped_holes == 1
        assert f.threads == ["M6"]
        assert f.contour_type == "rectangular"
        assert f.material_normalized == "S50C"
        assert f.surface_normalized == "熱處理"
        assert f.feature_source == FeatureSource.BOTH

    def test_calculate_weight_s50c(self):
        """928×796×15 mm S50C plate: V=11070720 mm³, density=7.85 g/cm³ → weight=86.905 kg"""
        f = Feature(
            id="feat-001",
            drawing_id="dwg-001",
            overall_length=928.0,
            overall_width=796.0,
            overall_height=15.0,
            volume_mm3=11_070_720.0,
        )
        weight = f.calculate_weight(density_g_cm3=7.85)
        assert weight is not None
        assert weight == pytest.approx(86.905, rel=1e-3)

    def test_calculate_weight_aluminum(self):
        """60×70×20 mm A6061: V=84000 mm³, density=2.70 g/cm³ → weight=0.227 kg"""
        f = Feature(
            id="feat-002",
            drawing_id="dwg-002",
            overall_length=60.0,
            overall_width=70.0,
            overall_height=20.0,
            volume_mm3=84_000.0,
        )
        weight = f.calculate_weight(density_g_cm3=2.70)
        assert weight is not None
        assert weight == pytest.approx(0.227, rel=1e-2)

    def test_calculate_weight_no_volume(self):
        f = Feature(id="feat-003", drawing_id="dwg-003")
        assert f.calculate_weight(density_g_cm3=7.85) is None

    def test_axisymmetric_detection(self):
        f = Feature(
            id="feat-004",
            drawing_id="dwg-004",
            contour_type="circular",
            is_axisymmetric=True,
        )
        assert f.is_axisymmetric is True

    def test_tight_tolerance(self):
        f = Feature(
            id="feat-005",
            drawing_id="dwg-005",
            tolerances=["平面度 0.01", "Ra0.8"],
            has_tight_tolerance=True,
            max_tolerance_grade="IT6",
        )
        assert f.has_tight_tolerance is True
        assert f.max_tolerance_grade == "IT6"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            Feature(id="test")  # type: ignore[call-arg] — missing drawing_id

    def test_negative_dimensions(self):
        with pytest.raises(ValidationError):
            Feature(
                id="feat-006",
                drawing_id="dwg-006",
                overall_length=-100.0,  # type: ignore[call-arg] — negative
            )
