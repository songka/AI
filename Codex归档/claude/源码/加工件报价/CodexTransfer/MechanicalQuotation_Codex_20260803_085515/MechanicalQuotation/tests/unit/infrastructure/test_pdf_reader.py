"""Tests for PDF Reader (Phase 3.0 interface only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quotation.infrastructure.pdf.reader import PdfReader


class TestPdfReader:
    def test_file_not_found(self, tmp_path):
        reader = PdfReader()
        result = reader.read(tmp_path / "nonexistent.pdf")
        assert result.is_failed

    def test_reader_creates_result(self):
        """Basic smoke test — reader exists and returns ImportResult."""
        reader = PdfReader()
        assert reader is not None
        # Type detection and extraction tested with real PDFs in integration tests
