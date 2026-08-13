"""Tests for QuotationFeature mapping (Phase 3.4)."""

from __future__ import annotations

from decimal import Decimal

import ezdxf
import pytest

from quotation.domain.geometric_feature import GeometricFeatures
from quotation.domain.manufacturing_feature import (
    AcrylicFeature,
    FrameFeature,
    ManufacturingFeatures,
    MaterialFeature,
    SheetMetalFeature,
    StructureAccessoryFeature,
    StructureAssemblyFeature,
    SurfaceTreatmentFeature,
    WeldingFeature,
)
from quotation.domain.quotation_feature import (
    AssemblyQuotationFeature,
    FrameQuotationFeature,
    MachiningQuotationFeature,
    QuotationFeatures,
)
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper


@pytest.fixture
def mapper():
    return QuotationMapper()


def _extract_from_texts(tmp_path, name, texts, lines=None):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    if lines:
        for (x1, y1, x2, y2) in lines:
            msp.add_line((x1, y1), (x2, y2))
    else:
        msp.add_line((0, 0), (100, 0)); msp.add_line((100, 0), (100, 80))
        msp.add_line((100, 80), (0, 80)); msp.add_line((0, 80), (0, 0))
    for (content, x, y, h) in texts:
        msp.add_text(content, height=h).set_placement((x, y))
    path = tmp_path / f"{name}.dxf"
    doc.saveas(str(path))
    reader = DxfReader()
    ir = reader.read(path)
    geo = GeometricExtractor().extract(ir.drawing.raw_entities)
    mfg = ManufacturingExtractor().extract(geo)
    return geo, mfg


class TestMachiningQuotation:
    """J003: S50C machined part → MachiningQuotationFeature."""

    def test_j003_maps_to_machining(self, mapper, tmp_path):
        geo, mfg = _extract_from_texts(tmp_path, "J003", [
            ("S50C", 5, 85, 5.0),
            ("表面鍍鉻", 5, 75, 4.0),
            ("6-M6", 5, 65, 4.0),
        ])
        # Add holes
        l, w = geo.bounding_box.length, geo.bounding_box.width
        for i in range(4):
            doc = ezdxf.readfile(str(tmp_path / "J003.dxf"))
            doc.modelspace().add_circle((l / 5 * (i + 1), w / 2), radius=3)
            doc.saveas(str(tmp_path / "J003.dxf"))
        # Re-extract
        reader = DxfReader()
        ir = reader.read(str(tmp_path / "J003.dxf"))
        geo2 = GeometricExtractor().extract(ir.drawing.raw_entities)
        mfg2 = ManufacturingExtractor().extract(geo2)

        qf = mapper.map(mfg2, geo2)
        assert len(qf.machining) >= 1
        mq = qf.machining[0]
        assert mq.material == "S50C"
        assert mq.surface_treatment is not None
        assert mq.hole_count >= 4
        assert "CNC" in mq.process_hints

    def test_spcc_preserves_fractional_sheet_thickness_without_rounding(self, mapper):
        from quotation.domain.geometric_feature import BoundingBox, FeatureValue

        geo = GeometricFeatures(
            bounding_box=BoundingBox(
                min_x=0,
                min_y=0,
                max_x=100,
                max_y=50,
                source="TEST",
                confidence=1.0,
            )
        )
        material = MaterialFeature(
            material_id="MAT-SPCC",
            normalized=FeatureValue(value="SPCC", source="TEST", confidence=1.0),
            confidence=1.0,
        )
        sheet = SheetMetalFeature(
            sheet_id="SHEET-SPCC",
            material="SPCC",
            thickness_mm=0.35,
            confidence=1.0,
        )
        qf = mapper.map(
            ManufacturingFeatures(material=material, sheet_metal_parts=[sheet]),
            geo,
        )

        mq = qf.machining[0]
        trace = mq.material_calculation
        assert trace is not None
        assert trace.area_mm2 == Decimal("5000")
        assert trace.thickness_mm == Decimal("0.35")
        assert trace.volume_mm3 == Decimal("1750.00")
        assert trace.density_g_cm3 == Decimal("7.85")
        assert trace.weight_kg == Decimal("0.0137375")
        assert mq.weight_kg == Decimal("0.0137375")
        assert trace.weight_source == "EXTRACTED_SHEET_THICKNESS"


class TestFrameQuotation:
    """W001: Frame → FrameQuotationFeature."""

    def test_frame_maps_to_quotation(self, mapper, tmp_path):
        geo, mfg = _extract_from_texts(tmp_path, "W001_frame", [
            ("鋁型材 40×40", 5, 85, 5.0),
            ("防護圍欄", 5, 75, 5.0),
        ])
        qf = mapper.map(mfg, geo)
        assert len(qf.frames) >= 1
        fq = qf.frames[0]
        assert fq.profile_type == "鋁型材"
        assert isinstance(fq, FrameQuotationFeature)


class TestAssemblyQuotation:
    """W001: Assembly → AssemblyQuotationFeature."""

    def test_assembly_maps_to_quotation(self, mapper, tmp_path):
        geo, mfg = _extract_from_texts(tmp_path, "W001_asm", [
            ("防護門組件", 5, 85, 5.0),
            ("合頁", 5, 75, 3.0),
            ("把手", 5, 65, 3.0),
        ])
        qf = mapper.map(mfg, geo)
        assert len(qf.assemblies) >= 1
        aq = qf.assemblies[0]
        assert aq.assembly_type in ("GUARD", "DOOR")
        assert isinstance(aq, AssemblyQuotationFeature)

    def test_weldment_structure_does_not_use_solid_bbox_weight(self, mapper):
        from quotation.domain.geometric_feature import BoundingBox, FeatureValue

        geo = GeometricFeatures(
            bounding_box=BoundingBox(
                min_x=0,
                min_y=0,
                max_x=1400,
                max_y=1300,
                source="TEST",
                confidence=1.0,
            )
        )
        material = MaterialFeature(
            material_id="MAT-STEEL",
            normalized=FeatureValue(value="普通鋼", source="TEST", confidence=1.0),
            confidence=1.0,
        )
        assembly = StructureAssemblyFeature(
            assembly_id="ASM-J001",
            assembly_type="FRAME",
            name="焊接機架",
            confidence=1.0,
        )
        weld = WeldingFeature(weld_id="WELD-J001", confidence=1.0)

        qf = mapper.map(
            ManufacturingFeatures(
                material=material,
                structure_assemblies=[assembly],
                welds=[weld],
            ),
            geo,
        )

        mq = qf.machining[0]
        assert mq.weight_kg == Decimal("0")
        assert mq.material_calculation is not None
        assert mq.material_calculation.weight_source == "UNRESOLVED_WELDMENT_STRUCTURE"


class TestQuotationFeaturesAggregate:
    def test_no_prices_in_quotation_features(self):
        """QuotationFeature must not contain any price fields."""
        mq = MachiningQuotationFeature(feature_id="test", material="S50C")
        data = mq.model_dump()
        assert "price" not in data
        assert "amount" not in data
        assert "cost" not in data

    def test_total_features_count(self, mapper, tmp_path):
        geo, mfg = _extract_from_texts(tmp_path, "multi", [
            ("S50C", 5, 85, 5.0),
            ("鋁型材", 5, 75, 5.0),
            ("防護罩", 5, 65, 5.0),
        ])
        qf = mapper.map(mfg, geo)
        assert qf.total_features >= 1

    def test_empty_manufacturing_produces_empty_quotation(self, mapper):
        empty_mfg = ManufacturingFeatures()
        empty_geo = GeometricFeatures()
        qf = mapper.map(empty_mfg, empty_geo)
        assert qf.total_features == 0
        assert qf.machining == []
        assert qf.frames == []
        assert qf.assemblies == []


class TestConfirmedStockDimensions:
    def test_machining_weight_uses_explicit_dimensions_not_drawing_bbox(self, mapper):
        from quotation.domain.geometric_feature import BoundingBox, FeatureValue

        geo = GeometricFeatures(
            bounding_box=BoundingBox(
                min_x=0,
                min_y=0,
                max_x=375,
                max_y=239,
                source="TEST_DRAWING_SHEET",
                confidence=1.0,
            )
        )
        material = MaterialFeature(
            material_id="MAT-A023",
            normalized=FeatureValue(value="S50C", source="TEST", confidence=1.0),
            confidence=1.0,
        )

        qf = mapper.map(
            ManufacturingFeatures(material=material),
            geo,
            dimensions_raw="50*28*17",
        )

        machining = qf.machining[0]
        assert machining.weight_kg == Decimal("0.186830")
        assert machining.material_calculation is not None
        assert machining.material_calculation.weight_source == "CONFIRMED_PART_DIMENSION"

    def test_drawing_bbox_is_not_used_as_solid_weight(self, mapper):
        from quotation.domain.geometric_feature import BoundingBox, FeatureValue

        geo = GeometricFeatures(
            bounding_box=BoundingBox(
                min_x=0,
                min_y=0,
                max_x=375,
                max_y=239,
                source="TEST_DRAWING_SHEET",
                confidence=1.0,
            )
        )
        material = MaterialFeature(
            material_id="MAT-NO-DIMS",
            normalized=FeatureValue(value="S50C", source="TEST", confidence=1.0),
            confidence=1.0,
        )

        qf = mapper.map(ManufacturingFeatures(material=material), geo)

        machining = qf.machining[0]
        assert machining.weight_kg == Decimal("0")
        assert machining.material_calculation is not None
        assert machining.material_calculation.weight_source == "MISSING_CONFIRMED_DIMENSION"


class TestJ003W001FullPipeline:
    """End-to-end: J003 machined + W001 equipment."""

    def test_j003_full_chain(self, mapper, tmp_path):
        """J003: RawEntity → ... → MachiningQuotationFeature."""
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        msp.add_line((0, 0), (928, 0)); msp.add_line((928, 0), (928, 796))
        msp.add_line((928, 796), (0, 796)); msp.add_line((0, 796), (0, 0))
        for i in range(4):
            msp.add_circle((200 + i * 150, 398), radius=3)
        msp.add_text("S50C", height=8).set_placement((10, 810))
        msp.add_text("6-M6", height=5).set_placement((200, 400))
        msp.add_text("表面鍍鉻", height=5).set_placement((10, 820))
        path = tmp_path / "J003_full.dxf"; doc.saveas(str(path))

        reader = DxfReader(); ir = reader.read(path)
        geo = GeometricExtractor().extract(ir.drawing.raw_entities)
        mfg = ManufacturingExtractor().extract(geo)
        qf = mapper.map(mfg, geo)

        assert len(qf.machining) >= 1
        mq = qf.machining[0]
        assert mq.material == "S50C"
        assert mq.hole_count == 4
        assert mq.thread_count >= 1
        assert "CNC" in mq.process_hints

    def test_w001_full_chain(self, mapper, tmp_path):
        """W001: Equipment structure features mapped."""
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        msp.add_line((0, 0), (1300, 0)); msp.add_line((1300, 0), (1300, 1300))
        msp.add_line((1300, 1300), (0, 1300)); msp.add_line((0, 1300), (0, 0))
        msp.add_text("鋁型材 40×40", height=6).set_placement((10, 1320))
        msp.add_text("防護圍欄", height=6).set_placement((10, 1340))
        msp.add_text("門組件", height=5).set_placement((10, 1360))
        msp.add_text("白色透明亞克力", height=4).set_placement((10, 1380))
        msp.add_text("合頁", height=4).set_placement((10, 1400))
        msp.add_text("磁吸", height=4).set_placement((10, 1420))
        msp.add_text("把手", height=4).set_placement((10, 1440))
        msp.add_text("角碼", height=4).set_placement((10, 1460))
        msp.add_text("加強筋焊接", height=4).set_placement((10, 1480))
        path = tmp_path / "W001_full.dxf"; doc.saveas(str(path))

        reader = DxfReader(); ir = reader.read(path)
        geo = GeometricExtractor().extract(ir.drawing.raw_entities)
        mfg = ManufacturingExtractor().extract(geo)
        qf = mapper.map(mfg, geo)

        assert len(qf.frames) >= 1, "Frame not mapped"
        assert len(qf.assemblies) >= 2, "Assemblies not mapped"
        assert qf.total_features >= 3
