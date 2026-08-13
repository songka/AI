"""Tests for file scanner — drawing number normalization and matching."""
from __future__ import annotations

from pathlib import Path

from quotation.application.file_scanner import (
    DrawingFile,
    FileScanner,
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
    def test_native_solidworks_files_are_geometry_sources(self, tmp_path):
        from quotation.application.file_scanner import FileScanner

        part = tmp_path / "未来零件.SLDPRT"
        part.write_bytes(b"part")
        bundle = FileScanner().scan_single_file(part)

        assert bundle.geometry_source is not None
        assert bundle.geometry_source.extension == ".sldprt"

    def test_from_dxf_path(self):
        df = DrawingFile.from_path(Path("/tmp/test/ABC-001.DXF"))
        assert df is not None
        assert df.drawing_number == "abc-001"
        assert df.is_geometry

    def test_pdf_is_not_supported(self):
        df = DrawingFile.from_path(Path("/tmp/test/ABC-001.PDF"))
        assert df is None

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
    def test_explicit_dwg_wins_over_related_solidworks_file(self, tmp_path):
        dwg = tmp_path / "PART-000.dwg"
        solidworks = tmp_path / "PART-000.sldprt"
        dwg.write_bytes(b"dwg")
        solidworks.write_bytes(b"part")

        bundle = FileScanner().scan_single_file(dwg)

        assert bundle.geometry_source is not None
        assert bundle.geometry_source.full_path == dwg.resolve()

    def test_explicit_solidworks_file_wins_over_related_dwg(self, tmp_path):
        dwg = tmp_path / "PART-000.dwg"
        solidworks = tmp_path / "PART-000.sldprt"
        dwg.write_bytes(b"dwg")
        solidworks.write_bytes(b"part")

        bundle = FileScanner().scan_single_file(solidworks)

        assert bundle.geometry_source is not None
        assert bundle.geometry_source.full_path == solidworks.resolve()

    def test_explicit_pdf_is_rejected_even_with_related_geometry(self, tmp_path):
        pdf = tmp_path / "PART-000.pdf"
        related_dwg = tmp_path / "PART-000.dwg"
        pdf.write_bytes(b"pdf")
        related_dwg.write_bytes(b"dwg")

        bundle = FileScanner().scan_single_file(pdf)

        assert bundle.geometry_source is None
        assert bundle.files == []

    def test_selected_files_group_same_name_and_use_priority(self, tmp_path):
        solidworks = tmp_path / "PART-000.sldprt"
        dwg = tmp_path / "PART-000.dwg"
        unrelated = tmp_path / "PART-000.dxf"
        solidworks.write_bytes(b"part")
        dwg.write_bytes(b"dwg")
        unrelated.write_bytes(b"dxf")

        bundles = FileScanner().scan_selected_files([solidworks, dwg])

        assert len(bundles) == 1
        assert bundles[0].geometry_source is not None
        assert bundles[0].geometry_source.full_path == dwg.resolve()
        assert unrelated.resolve() not in {item.full_path for item in bundles[0].files}

    def test_selected_single_geometry_is_used_without_directory_priority(self, tmp_path):
        selected = tmp_path / "PART-000.sldprt"
        unselected = tmp_path / "PART-000.dwg"
        selected.write_bytes(b"part")
        unselected.write_bytes(b"dwg")

        bundles = FileScanner().scan_selected_files([selected])

        assert bundles[0].geometry_source is not None
        assert bundles[0].geometry_source.full_path == selected.resolve()

    def test_directory_scan_prefers_dwg_when_multiple_geometry_formats_exist(self, tmp_path):
        (tmp_path / "PART-000.sldprt").write_bytes(b"part")
        dwg = tmp_path / "PART-000.dwg"
        dwg.write_bytes(b"dwg")

        bundles = FileScanner().scan_directory(tmp_path, recursive=False)

        assert bundles[0].geometry_source is not None
        assert bundles[0].geometry_source.full_path == dwg.resolve()

    def test_scan_single_dxf_ignores_pdf(self, tmp_path):
        dxf = tmp_path / "PART-001.dxf"
        pdf = tmp_path / "PART-001.pdf"
        dxf.write_text("")
        pdf.write_text("")
        scanner = FileScanner()
        bundle = scanner.scan_single_file(dxf)
        assert bundle.drawing_number == "part-001"
        assert bundle.match_status == MatchStatus.UNMATCHED
        assert bundle.file_count == 1
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
            assert b.file_count == 1
            assert b.match_status == MatchStatus.UNMATCHED

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
        (tmp_path / "PART-REV-A.dwg").write_text("")
        scanner = FileScanner()
        bundles = scanner.scan_directory(tmp_path, recursive=False)
        assert len(bundles) == 1  # both normalize to "part"

    def test_pdf_directory_is_ignored(self, tmp_path):
        (tmp_path / "NODWG.pdf").write_text("")
        scanner = FileScanner()
        bundles = scanner.scan_directory(tmp_path, recursive=False)
        assert bundles == []
