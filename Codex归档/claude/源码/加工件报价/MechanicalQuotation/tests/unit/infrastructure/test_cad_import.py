"""Tests for DXF Reader and DWG Converter."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import ezdxf

from quotation.infrastructure.dxf.converter import DwgConverter
from quotation.infrastructure.dxf.reader import DxfReader


# ============================================================================
# DXF Reader Tests (using generated DXF)
# ============================================================================

class TestDxfReader:
    @pytest.fixture
    def simple_dxf(self, tmp_path):
        """Generate a simple DXF with LINE, CIRCLE, TEXT."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 0))
        msp.add_line((100, 0), (100, 50))
        msp.add_line((100, 50), (0, 50))
        msp.add_line((0, 50), (0, 0))
        msp.add_circle((50, 25), radius=5)
        msp.add_text("S50C", height=5.0).set_placement((10, 30))
        path = tmp_path / "test.dxf"
        doc.saveas(str(path))
        return path

    def test_read_basic_dxf(self, simple_dxf):
        reader = DxfReader()
        result = reader.read(simple_dxf)
        assert result.is_success
        assert result.drawing is not None
        assert result.drawing.entity_count >= 6
        assert result.drawing.parse_status == "success"

    def test_entity_summary(self, simple_dxf):
        reader = DxfReader()
        result = reader.read(simple_dxf)
        summary = result.drawing.entity_summary
        assert summary.get("LINE", 0) >= 4
        assert summary.get("CIRCLE", 0) >= 1
        assert summary.get("TEXT", 0) >= 1

    def test_text_extraction(self, simple_dxf):
        reader = DxfReader()
        result = reader.read(simple_dxf)
        texts = result.drawing.raw_text_strings
        assert "S50C" in texts

    def test_file_not_found(self, tmp_path):
        reader = DxfReader()
        result = reader.read(tmp_path / "nonexistent.dxf")
        assert result.is_failed
        assert len(result.errors) > 0

    def test_empty_dxf(self, tmp_path):
        doc = ezdxf.new()
        path = tmp_path / "empty.dxf"
        doc.saveas(str(path))
        reader = DxfReader()
        result = reader.read(path)
        assert result.is_partial  # empty entities → partial
        assert "no entities" in str(result.warnings).lower()

    def test_corrupted_dxf(self, tmp_path):
        path = tmp_path / "corrupt.dxf"
        path.write_text("NOT A VALID DXF FILE\nGARBAGE DATA")
        reader = DxfReader()
        result = reader.read(path)
        assert result.is_failed

    def test_import_duration_recorded(self, simple_dxf):
        reader = DxfReader()
        result = reader.read(simple_dxf)
        assert result.import_duration_ms > 0

    def test_drawing_format_is_dxf(self, simple_dxf):
        reader = DxfReader()
        result = reader.read(simple_dxf)
        assert result.drawing.source_format == "DXF"


# ============================================================================
# DWG Converter Tests
# ============================================================================

class TestDwgConverter:
    def test_converter_availability(self):
        """Check if ODA is available without failing."""
        converter = DwgConverter()
        # Just verify it doesn't crash
        assert isinstance(converter.is_available, bool)

    def test_convert_nonexistent_file(self, tmp_path):
        converter = DwgConverter()
        result = converter.convert(tmp_path / "nonexistent.dwg")
        assert result.is_failed

    def test_convert_invalid_file(self, tmp_path):
        path = tmp_path / "not_a_dwg.dwg"
        path.write_text("not a DWG file")
        converter = DwgConverter()
        result = converter.convert(path)
        # Should fail (not a valid DWG, or ODA not installed)
        assert not result.is_success

    def test_real_dwg_if_oda_available(self):
        """Try to convert a real DWG file if ODA is installed."""
        converter = DwgConverter()
        if not converter.is_available:
            pytest.skip("ODA File Converter not installed")

        real_dwg = Path("samples/drawings/UC1000005854-J003.DWG")
        if not real_dwg.exists():
            pytest.skip("Real DWG sample not found")

        result = converter.convert(real_dwg)
        # If ODA is available and DWG is valid, should succeed
        assert result.is_success
        assert result.converted_file is not None
        assert Path(result.converted_file).exists()

    def test_full_dwg_to_dxf_flow(self):
        """Full DWG→DXF→Drawing flow if ODA available."""
        converter = DwgConverter()
        if not converter.is_available:
            pytest.skip("ODA File Converter not installed")

        real_dwg = Path("samples/drawings/UC1000005854-J003.DWG")
        if not real_dwg.exists():
            pytest.skip("Real DWG sample not found")

        # Convert DWG → DXF
        conv_result = converter.convert(real_dwg)
        assert conv_result.is_success

        # Read DXF → Drawing
        reader = DxfReader()
        read_result = reader.read(conv_result.converted_file)
        assert read_result.is_success
        assert read_result.drawing is not None
        assert read_result.drawing.entity_count > 0
