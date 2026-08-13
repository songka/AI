"""Tests for Drawing domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quotation.domain.drawing import Drawing, DrawingFormat, ParseStatus, TextEntity


class TestDrawingFormat:
    def test_all_formats(self):
        assert DrawingFormat.DXF == "DXF"
        assert DrawingFormat.DWG == "DWG"
        assert DrawingFormat.PDF == "PDF"

    def test_format_values(self):
        assert {f.value for f in DrawingFormat} == {"DXF", "DWG", "PDF"}


class TestParseStatus:
    def test_all_statuses(self):
        assert ParseStatus.SUCCESS == "success"
        assert ParseStatus.PARTIAL == "partial"
        assert ParseStatus.FAILED == "failed"


class TestTextEntity:
    def test_create_minimal(self):
        t = TextEntity(content="S50C", position_x=100.0, position_y=200.0, height=5.0)
        assert t.content == "S50C"
        assert t.position_x == 100.0
        assert t.layer is None

    def test_create_with_layer(self):
        t = TextEntity(
            content="NOTE", position_x=0.0, position_y=0.0, height=3.5, layer="TEXT"
        )
        assert t.layer == "TEXT"
        assert t.entity_type == "TEXT"

    def test_create_mtext(self):
        t = TextEntity(
            content="熱處理 HRC58-62",
            position_x=50.0,
            position_y=100.0,
            height=4.0,
            entity_type="MTEXT",
        )
        assert t.entity_type == "MTEXT"


class TestDrawing:
    def test_create_minimal(self):
        d = Drawing(
            id="dwg-001",
            file_path="/path/to/UC1000005854-J003.DWG",
            file_name="UC1000005854-J003.DWG",
            source_format=DrawingFormat.DWG,
        )
        assert d.id == "dwg-001"
        assert d.source_format == DrawingFormat.DWG
        assert d.entity_count == 0
        assert d.parse_status == ParseStatus.SUCCESS
        assert d.all_texts == []
        assert d.parse_errors == []

    def test_create_full(self):
        d = Drawing(
            id="dwg-001",
            file_path="/path/to/drawing.dxf",
            file_name="drawing.dxf",
            source_format=DrawingFormat.DXF,
            drawing_number="UC1000005854",
            part_name="J003",
            revision="A",
            material_text="S50C",
            scale="1:1",
            entity_count=269,
            entity_summary={"LINE": 245, "CIRCLE": 12, "TEXT": 3},
            all_texts=[
                TextEntity(content="S50C", position_x=100.0, position_y=50.0, height=5.0)
            ],
            raw_text_strings=["S50C", "熱處理"],
            parse_status=ParseStatus.SUCCESS,
            parse_warnings=["Layer 'HIDDEN' has no entities"],
        )
        assert d.drawing_number == "UC1000005854"
        assert d.part_name == "J003"
        assert d.material_text == "S50C"
        assert d.revision == "A"
        assert d.scale == "1:1"
        assert d.entity_count == 269
        assert d.entity_summary["LINE"] == 245
        assert len(d.all_texts) == 1
        assert d.raw_text_strings == ["S50C", "熱處理"]
        assert d.parse_warnings == ["Layer 'HIDDEN' has no entities"]

    def test_create_failed_parse(self):
        d = Drawing(
            id="dwg-002",
            file_path="/path/to/broken.dwg",
            file_name="broken.dwg",
            source_format=DrawingFormat.DWG,
            parse_status=ParseStatus.FAILED,
            parse_errors=["Unsupported DWG version", "CRC checksum mismatch"],
        )
        assert d.parse_status == ParseStatus.FAILED
        assert len(d.parse_errors) == 2

    def test_create_partial_parse(self):
        d = Drawing(
            id="dwg-003",
            file_path="/path/to/partial.dxf",
            file_name="partial.dxf",
            source_format=DrawingFormat.DXF,
            parse_status=ParseStatus.PARTIAL,
            parse_warnings=["3 entities of unknown type skipped"],
        )
        assert d.parse_status == ParseStatus.PARTIAL

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            Drawing(id="test")  # type: ignore[call-arg] — missing file_path, file_name, source_format

    def test_invalid_source_format(self):
        with pytest.raises(ValidationError):
            Drawing(
                id="test",
                file_path="/f.dxf",
                file_name="f.dxf",
                source_format="INVALID",  # type: ignore[arg-type]
            )

    def test_feature_id_relation(self):
        d = Drawing(
            id="dwg-001",
            file_path="/f.dxf",
            file_name="f.dxf",
            source_format=DrawingFormat.DXF,
            feature_id="feat-001",
        )
        assert d.feature_id == "feat-001"

    def test_pdf_format(self):
        d = Drawing(
            id="pdf-001",
            file_path="/f.pdf",
            file_name="f.pdf",
            source_format=DrawingFormat.PDF,
        )
        assert d.source_format == DrawingFormat.PDF
