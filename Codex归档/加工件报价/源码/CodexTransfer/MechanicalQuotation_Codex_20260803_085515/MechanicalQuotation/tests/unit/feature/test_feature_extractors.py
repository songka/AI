"""Tests for Geometric and Manufacturing Feature Extractors."""

from __future__ import annotations

import pytest
import ezdxf

from quotation.domain.manufacturing_feature import (
    HoleFeature,
    ManufacturingFeatures,
    MaterialFeature,
    SurfaceTreatmentFeature,
    ThreadFeature,
)
from quotation.domain.raw_entity import (
    CircleGeometry,
    EntityType,
    LineGeometry,
    RawEntity,
    TextGeometry,
)
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def geo_extractor():
    return GeometricExtractor()


@pytest.fixture
def mfg_extractor():
    return ManufacturingExtractor()


def _make_dxf_with_features(tmp_path, lines, circles, texts, mtexts=None):
    """Helper: create a DXF with specific geometry."""
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for (x1, y1, x2, y2) in lines:
        msp.add_line((x1, y1), (x2, y2))
    for (cx, cy, r) in circles:
        msp.add_circle((cx, cy), radius=r)
    for (content, x, y, h) in texts:
        msp.add_text(content, height=h).set_placement((x, y))
    if mtexts:
        for (content, x, y) in mtexts:
            msp.add_mtext(content).set_placement((x, y))
    path = tmp_path / "test.dxf"
    doc.saveas(str(path))
    return path


# ============================================================================
# Geometric Extractor Tests
# ============================================================================

class TestGeometricExtractor:
    def test_bounding_box(self, geo_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 50), (100, 50, 0, 50), (0, 50, 0, 0)],
            circles=[(50, 25, 5)],
            texts=[],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        assert geo.bounding_box is not None
        assert geo.bounding_box.length == 100.0
        assert geo.bounding_box.width == 50.0

    def test_hole_candidates(self, geo_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 50), (100, 50, 0, 50), (0, 50, 0, 0)],
            circles=[(50, 25, 3), (80, 40, 4)],
            texts=[],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        assert geo.candidate_count == 2

    def test_large_circle_excluded(self, geo_extractor, tmp_path):
        """Diameter > 30mm should NOT be a hole candidate."""
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 80), (100, 80, 0, 80), (0, 80, 0, 0)],
            circles=[(50, 40, 25)],  # diameter=50mm — too large
            texts=[],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        assert geo.candidate_count == 0

    def test_text_extraction(self, geo_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 50, 0), (50, 0, 50, 30), (50, 30, 0, 30), (0, 30, 0, 0)],
            circles=[],
            texts=[("S50C", 10, 15, 5.0), ("熱處理", 25, 20, 4.0)],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        assert len(geo.text_clusters) == 2
        contents = {t.content for t in geo.text_clusters}
        assert "S50C" in contents
        assert "熱處理" in contents


# ============================================================================
# Manufacturing Extractor Tests
# ============================================================================

class TestManufacturingExtractor:
    def test_hole_grouping(self, geo_extractor, mfg_extractor, tmp_path):
        """4 identical circles → 1 hole group with count=4."""
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 100), (100, 100, 0, 100), (0, 100, 0, 0)],
            circles=[(10, 10, 3), (90, 10, 3), (10, 90, 3), (90, 90, 3)],
            texts=[],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert len(mfg.holes) == 1
        assert mfg.holes[0].count == 4
        assert mfg.holes[0].diameter.value == pytest.approx(6.0, rel=0.01)

    def test_different_hole_groups(self, geo_extractor, mfg_extractor, tmp_path):
        """Different diameter circles → separate hole groups."""
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 100), (100, 100, 0, 100), (0, 100, 0, 0)],
            circles=[(10, 10, 3), (90, 10, 6)],
            texts=[],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert len(mfg.holes) >= 2

    def test_thread_extraction_m6(self, geo_extractor, mfg_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 100), (100, 100, 0, 100), (0, 100, 0, 0)],
            circles=[(50, 50, 3)],
            texts=[("6-M6", 55, 55, 5.0)],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert len(mfg.threads) == 1
        assert mfg.threads[0].spec.value == "M6"
        assert mfg.threads[0].count == 6
        assert mfg.threads[0].linked_hole_id is not None

    def test_thread_m3_m4_m5_m8(self, geo_extractor, mfg_extractor, tmp_path):
        for size in ["M3", "M4", "M5", "M8"]:
            path = _make_dxf_with_features(
                tmp_path,
                lines=[(0, 0, 50, 0), (50, 0, 50, 30), (50, 30, 0, 30), (0, 30, 0, 0)],
                circles=[(25, 15, 2)],
                texts=[(size, 30, 20, 4.0)],
            )
            reader = DxfReader()
            result = reader.read(path)
            geo = geo_extractor.extract(result.drawing.raw_entities)
            mfg = mfg_extractor.extract(geo)
            assert len(mfg.threads) >= 1, f"Failed for {size}"
            assert mfg.threads[0].spec.value == size, f"Wrong spec for {size}"

    def test_material_extraction(self, geo_extractor, mfg_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 50, 0), (50, 0, 50, 30), (50, 30, 0, 30), (0, 30, 0, 0)],
            circles=[],
            texts=[("S50C", 10, 15, 5.0)],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert mfg.material is not None
        assert mfg.material.raw_text.value == "S50C"
        assert mfg.material.normalized.value == "S50C"

    def test_surface_treatment_extraction(self, geo_extractor, mfg_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 50, 0), (50, 0, 50, 30), (50, 30, 0, 30), (0, 30, 0, 0)],
            circles=[],
            texts=[("熱處理 HRC58-62", 10, 15, 5.0)],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert mfg.surface_treatment is not None
        assert "熱處理" in (mfg.surface_treatment.raw_text.value or "")

    def test_no_material_when_absent(self, geo_extractor, mfg_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 50), (100, 50, 0, 50), (0, 50, 0, 0)],
            circles=[(50, 25, 5)],
            texts=[("NOTE", 50, 25, 3.0)],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert mfg.material is None

    def test_all_features_have_source(self, geo_extractor, mfg_extractor, tmp_path):
        path = _make_dxf_with_features(
            tmp_path,
            lines=[(0, 0, 100, 0), (100, 0, 100, 80), (100, 80, 0, 80), (0, 80, 0, 0)],
            circles=[(50, 40, 4)],
            texts=[("S50C", 10, 70, 5.0), ("M6", 55, 45, 4.0)],
        )
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)

        # Every feature should have source info
        for hole in mfg.holes:
            assert hole.diameter.source in ("CAD_GEOMETRY", "UNKNOWN")
            assert hole.diameter.confidence > 0
        assert mfg.material.raw_text.source == "DRAWING_TEXT"
        for thread in mfg.threads:
            assert thread.spec.source == "DRAWING_TEXT"

    def test_empty_drawing(self, geo_extractor, mfg_extractor, tmp_path):
        doc = ezdxf.new()
        path = tmp_path / "empty.dxf"
        doc.saveas(str(path))
        reader = DxfReader()
        result = reader.read(path)
        geo = geo_extractor.extract(result.drawing.raw_entities)
        mfg = mfg_extractor.extract(geo)
        assert mfg.total_holes == 0
        assert mfg.total_threads == 0
        assert mfg.material is None
