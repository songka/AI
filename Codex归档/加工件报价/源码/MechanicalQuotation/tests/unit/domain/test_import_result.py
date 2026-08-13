"""Tests for ImportResult domain model."""

from __future__ import annotations

import pytest

from quotation.domain.import_result import ImportResult


class TestImportResult:
    def test_create_success(self):
        r = ImportResult(source_file="/path/drawing.dxf", source_format="DXF", import_status="success")
        assert r.is_success
        assert not r.is_failed

    def test_create_failed(self):
        r = ImportResult(source_file="/path/broken.dwg", source_format="DWG", import_status="failed",
                         errors=["File corrupted"])
        assert r.is_failed
        assert len(r.errors) == 1

    def test_create_partial(self):
        r = ImportResult(source_file="/path/old.dwg", source_format="DWG", import_status="partial",
                         warnings=["3 entities skipped"])
        assert r.is_partial

    def test_converted_file(self):
        r = ImportResult(source_file="/path/drawing.dwg", source_format="DWG",
                         converted_file="/tmp/drawing.dxf")
        assert r.converted_file == "/tmp/drawing.dxf"

    def test_pdf_confidence(self):
        r = ImportResult(source_file="/path/scan.pdf", source_format="PDF",
                         pdf_confidence="low", ocr_text="材料: S50C")
        assert r.pdf_confidence == "low"
        assert "S50C" in (r.ocr_text or "")

    def test_defaults(self):
        r = ImportResult(source_file="test.dxf", source_format="DXF")
        assert r.import_status == "success"
        assert r.errors == []
        assert r.warnings == []
        assert r.drawing is None
        assert r.converted_file is None
        assert r.import_duration_ms == 0.0
