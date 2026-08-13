"""Tests for file scanner — drawing number normalization and matching."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from quotation.application.file_scanner import (
    DrawingFile,
    FileScanner,
    JobBundle,
    MatchStatus,
    normalize_drawing_number,
)


class TestNormalizeDrawingNumber:
    def test_case_insensitive(self):
        assert normalize_drawing_number("ABC-001") == normalize_drawing_number("abc-001")

    def test_whitespace_trim(self):
        assert normalize_drawing_number("  ABC-001  ") == "abc-001"

    def test_fullwidth_halfwidth(self):
        assert normalize_drawing_number("ＡＢＣ-００１") == "abc-001"

    def test_hyphen_underscore_equivalence(self):
        a = normalize_drawing_number("ABC-001")
        b = normalize_drawing_number("ABC_001")
        c = normalize_drawing_number("ABC 001")
        assert a == b == c == "abc-001"

    def test_rev_suffix_stripped(self):
        assert normalize_drawing_number("ABC-001-REV-A") == "abc-001"
        assert normalize_drawing_number("ABC-001-REV01") == "abc-001"

    def test_r_v_suffix_stripped(self):
        assert normalize_drawing_number("ABC-001-R01") == "abc-001"
        assert normalize_drawing_number("ABC-001-V1") == "abc-001"

    def test_version_suffix_stripped(self):
        assert normalize_drawing_number("ABC-001-VERSION-2") == "abc-001"


class TestDrawingFile:
    def test_from_dxf_path(self):
        df = DrawingFile.from_path(Path("/tmp/test/ABC-001.DXF"))
        assert df is not None
        assert df.drawing_number == "abc-001"
        assert df.is_geometry
        assert not df.is_pdf

    def test_from_pdf_path(self):
        df = DrawingFile.from_path(Path("/tmp/test/ABC-001.PDF"))
        assert df is not None
        assert df.drawing_number == "abc-001"
        assert not df.is_geometry
        assert df.is_pdf

    def test_temp_file_excluded(self):
        assert DrawingFile.from_path(Path("/tmp/~$temp.DXF")) is None
        assert DrawingFile.from_path(Path("/tmp/file.tmp")) is None
        assert DrawingFile.from_path(Path("/tmp/file.bak")) is None

    def test_unsupported_format(self):
        assert DrawingFile.from_path(Path("/tmp/test.txt")) is None
        assert DrawingFile.from_path(Path("/tmp/test.png")) is None

    def test_chinese_filename(self):
        df = DrawingFile.from_path(Path("/tmp/圖紙/機構件-001.DXF"))
        assert df is not None
        assert df.drawing_number is not None

    def test_space_in_path(self):
        df = DrawingFile.from_path(Path("/tmp/my drawings/ABC 001.DXF"))
        assert df is not None
        assert df.drawing_number == "abc-001"


class TestFileScanner:
    def test_scan_single_dxf_finds_pdf(self, tmp_path):
        dxf = tmp_path / "PART-001.dxf"
        pdf = tmp_path / "PART-001.pdf"
        dxf.write_text("")
        pdf.write_text("")
        scanner = FileScanner()
        bundle = scanner.scan_single_file(dxf)
        assert bundle.drawing_number == "part-001"
        assert bundle.match_status == MatchStatus.MATCHED
        assert bundle.file_count == 2
        assert bundle.geometry_source is not None

    def test_scan_single_no_match(self, tmp_path):
        dxf = tmp_path / "PART-002.dxf"
        dxf.write_text("")
        scanner = FileScanner()
        bundle = scanner.scan_single_file(dxf)
        assert bundle.match_status == MatchStatus.UNMATCHED
        assert bundle.file_count == 1

    def test_scan_directory_groups_by_number(self, tmp_path):
        (tmp_path / "A-001.dxf").write_text("")
        (tmp_path / "A-001.pdf").write_text("")
        (tmp_path / "B-002.dxf").write_text("")
        (tmp_path / "B-002.pdf").write_text("")
        scanner = FileScanner()
        bundles = scanner.scan_directory(tmp_path, recursive=False)
        assert len(bundles) == 2
        for b in bundles:
            assert b.file_count == 2
            assert b.match_status == MatchStatus.MATCHED

    def test_scan_directory_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "C-003.dxf").write_text("")
        (sub / "C-003.pdf").write_text("")
        scanner = FileScanner()
        bundles = scanner.scan_directory(tmp_path, recursive=True)
        assert len(bundles) == 1
        assert bundles[0].drawing_number == "c-003"

    def test_rev_suffix_matching(self, tmp_path):
        (tmp_path / "PART-R01.dxf").write_text("")
        (tmp_path / "PART-REV-A.pdf").write_text("")
        scanner = FileScanner()
        bundles = scanner.scan_directory(tmp_path, recursive=False)
        assert len(bundles) == 1  # both normalize to "part"

    def test_no_dwg_unsupported(self, tmp_path):
        """Bundle without geometry source should be handled gracefully."""
        (tmp_path / "NODWG.pdf").write_text("")
        scanner = FileScanner()
        bundles = scanner.scan_directory(tmp_path, recursive=False)
        assert len(bundles) == 1
        assert bundles[0].geometry_source is None
