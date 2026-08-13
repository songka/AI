"""Tests for equipment structure features (Phase 3.3)."""

from __future__ import annotations

import ezdxf
import pytest

from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.utils.normalization import normalize_profile_spec


def _make_dxf(tmp_path, name, texts, lines=None):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    if lines:
        for (x1, y1, x2, y2) in lines:
            msp.add_line((x1, y1), (x2, y2))
    else:
        msp.add_line((0, 0), (100, 0))
        msp.add_line((100, 0), (100, 80))
        msp.add_line((100, 80), (0, 80))
        msp.add_line((0, 80), (0, 0))
    for (content, x, y, h) in texts:
        msp.add_text(content, height=h).set_placement((x, y))
    path = tmp_path / f"{name}.dxf"
    doc.saveas(str(path))
    return path


@pytest.fixture
def geo_ext():
    return GeometricExtractor()


@pytest.fixture
def mfg_ext():
    return ManufacturingExtractor()


@pytest.fixture
def reader():
    return DxfReader()


class TestFrameFeature:
    def test_frame_detected(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "frame", [
            ("鋁型材 40×40", 5, 85, 5.0),
            ("1300*1300*995", 5, 75, 4.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.frames) >= 1
        assert mfg.frames[0].profile_type == "鋁型材"
        assert mfg.frames[0].profile_spec == "40x40"

    @pytest.mark.parametrize("raw", ["40*40", "40×40", "40X40", "40x40"])
    def test_profile_spec_variants_normalize_to_one_key(self, raw):
        assert normalize_profile_spec(raw) == "40x40"

    def test_frame_not_detected_without_keyword(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "noframe", [("S50C 鋼板", 5, 85, 5.0)])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.frames) == 0


class TestSheetMetalFeature:
    def test_sheet_metal_detected(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "sheet", [
            ("SPCC 鈑金件 折彎", 5, 85, 5.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.sheet_metal_parts) >= 1
        assert mfg.sheet_metal_parts[0].material == "SPCC"
        assert mfg.sheet_metal_parts[0].bend_count == 1

    def test_stainless_thin_plate_and_explicit_thickness(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "J029", [("4.材質為3mm厚度不鏽鋼；", 5, 85, 5.0)])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)

        assert len(mfg.sheet_metal_parts) == 1
        assert mfg.sheet_metal_parts[0].material == "SUS304"
        assert mfg.sheet_metal_parts[0].thickness_mm == 3.0
        assert mfg.material is not None
        assert mfg.material.normalized.value == "SUS304"

    def test_thick_machined_plate_is_not_sheet_metal(
        self, geo_ext, mfg_ext, reader, tmp_path
    ):
        path = _make_dxf(
            tmp_path,
            "A023-machined-plate",
            [("S50C", 5, 85, 5.0), ("50*28*17", 5, 75, 4.0), ("铣床加工", 5, 65, 4.0)],
        )
        imported = reader.read(path)
        geo = geo_ext.extract(imported.drawing.raw_entities)
        manufacturing = mfg_ext.extract(geo)

        assert manufacturing.sheet_metal_parts == []


class TestAcrylicFeature:
    def test_acrylic_detected(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "acrylic", [
            ("白色透明亞克力", 5, 85, 5.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.acrylic_parts) >= 1
        assert mfg.acrylic_parts[0].material == "亞克力"
        assert mfg.acrylic_parts[0].color == "白色透明"


class TestStructureAccessory:
    def test_accessory_detected(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "accessory", [
            ("合頁", 10, 85, 4.0),
            ("磁吸", 30, 85, 4.0),
            ("把手", 50, 85, 4.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.structure_accessories) >= 1
        items = mfg.structure_accessories[0].items
        assert "合頁" in items
        assert "磁吸" in items
        assert "把手" in items
        assert mfg.structure_accessories[0].category == "DOOR_HARDWARE"

    def test_corner_bracket(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "bracket", [("角碼", 10, 85, 4.0)])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.structure_accessories) >= 1
        assert mfg.structure_accessories[0].category == "FASTENER"


class TestWeldingFeature:
    def test_welding_detected(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "weld", [
            ("加強筋焊接", 5, 85, 5.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.welds) >= 1

    def test_spot_weld(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "spot", [("點焊固定", 5, 85, 4.0)])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.welds) >= 1
        assert mfg.welds[0].weld_type == "spot"


class TestStructureAssembly:
    def test_guard_assembly(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "guard", [
            ("防護圍欄", 5, 85, 5.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.structure_assemblies) >= 1
        assert mfg.structure_assemblies[0].assembly_type == "GUARD"

    def test_door_assembly(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "door", [("門組件", 5, 85, 5.0)])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        assert len(mfg.structure_assemblies) >= 1
        assert mfg.structure_assemblies[0].assembly_type == "DOOR"


class TestW001GoldenCase:
    """UC2020083221-W001: 鋁型材框架防護罩."""

    def test_w001_full_structure(self, geo_ext, mfg_ext, reader, tmp_path):
        path = _make_dxf(tmp_path, "W001", [
            ("鋁型材 40×40", 5, 200, 5.0),
            ("圖號:W001", 5, 190, 4.0),
            ("1300*1300*995", 5, 180, 4.0),
            ("白色透明亞克力", 5, 170, 4.0),
            ("防護圍欄", 5, 160, 5.0),
            ("門組件", 5, 150, 4.0),
            ("合頁", 5, 140, 3.0),
            ("磁吸", 5, 130, 3.0),
            ("把手", 5, 120, 3.0),
            ("角碼連接", 5, 110, 3.0),
            ("加強筋焊接", 5, 100, 3.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)

        # Frame
        assert len(mfg.frames) >= 1, "Frame not detected"
        assert mfg.frames[0].profile_type == "鋁型材"
        assert mfg.frames[0].profile_spec == "40x40"

        # Acrylic
        assert len(mfg.acrylic_parts) >= 1, "Acrylic not detected"
        assert mfg.acrylic_parts[0].color == "白色透明"

        # Accessories
        assert len(mfg.structure_accessories) >= 1, "Accessories not detected"
        acc_items = mfg.structure_accessories[0].items
        assert "合頁" in acc_items
        assert "磁吸" in acc_items
        assert "把手" in acc_items
        assert "角碼" in acc_items

        # Welding
        assert len(mfg.welds) >= 1, "Welding not detected"

        # Assemblies
        assert len(mfg.structure_assemblies) >= 2, "Assemblies not detected"
        types = {a.assembly_type for a in mfg.structure_assemblies}
        assert "GUARD" in types
        assert "DOOR" in types

    def test_w001_accessories_not_independent(self, geo_ext, mfg_ext, reader, tmp_path):
        """結構附件不應作為獨立外購件報價."""
        path = _make_dxf(tmp_path, "W001b", [
            ("鋁型材", 5, 85, 5.0),
            ("合頁", 10, 75, 4.0),
            ("把手", 20, 75, 4.0),
            ("防護門", 5, 65, 5.0),
        ])
        ir = reader.read(path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        # Accessories should be detected as STRUCTURE_ACCESSORY
        assert len(mfg.structure_accessories) >= 1
