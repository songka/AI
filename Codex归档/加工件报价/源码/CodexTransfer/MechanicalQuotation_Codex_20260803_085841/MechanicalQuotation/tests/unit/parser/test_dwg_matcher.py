"""Tests for DWG/BOM Matcher."""

from __future__ import annotations

import pytest

from quotation.domain.bom import ParsedPart
from quotation.domain.matching import MatchLevel
from quotation.infrastructure.parser.dwg_matcher import (
    DwgBomMatcher,
    extract_candidate_from_filename,
    extract_part_code_from_filename,
)


# ============================================================================
# Candidate Extraction Tests
# ============================================================================

class TestCandidateExtraction:
    def test_standard_dash(self):
        assert extract_candidate_from_filename("UC1000005854-J003.DWG") == "1000005854"

    def test_underscore(self):
        assert extract_candidate_from_filename("UC1002006858_J026.DWG") == "1002006858"

    def test_stp_dot_dwg(self):
        assert extract_candidate_from_filename("UC1004001886-J036.stp.DWG") == "1004001886"

    def test_w_series(self):
        assert extract_candidate_from_filename("UC2020083221-W001.DWG") == "2020083221"

    def test_z_series(self):
        assert extract_candidate_from_filename("UC1002009714-Z018.DWG") == "1002009714"

    def test_no_uc_prefix(self):
        assert extract_candidate_from_filename("Drawing1.DWG") is None

    def test_lowercase(self):
        assert extract_candidate_from_filename("uc1000005854-j003.dwg") == "1000005854"


class TestPartCodeExtraction:
    def test_j_series(self):
        assert extract_part_code_from_filename("UC1000005854-J003.DWG") == "J003"

    def test_r_series(self):
        assert extract_part_code_from_filename("UC1002009712-R002.DWG") == "R002"

    def test_f_series(self):
        assert extract_part_code_from_filename("UC1004001905-F001.DWG") == "F001"

    def test_w_series(self):
        assert extract_part_code_from_filename("UC1004001529_W002.DWG") == "W002"

    def test_z_series(self):
        assert extract_part_code_from_filename("UC1002009714-Z018.DWG") == "Z018"

    def test_no_code(self):
        assert extract_part_code_from_filename("drawing.DWG") is None


# ============================================================================
# Fixtures — 20 matched + 9 unmatched BOM parts
# ============================================================================

@pytest.fixture
def bom_parts():
    """Real BOM parts from GCS-雙滑台打磨設備."""
    data = [
        ("UC1000005854", "S50C", "J003", "928*796*15", "表面鍍鉻"),
        ("UC1000005855", "S50C", "J005", "1400*250*15", "熱處理"),
        ("UC1000005856", "S50C", "J006", "798*530*15", "熱處理"),
        ("UC1000005857", "S50C", "J007", "1400*250*15", "熱處理"),
        ("UC1002006858", "A6061-T6", None, None, "表面噴砂陽極銀色"),
        ("UC1002009711", "A6061-T6", "R001", "φ250×15", "表面噴砂陽極銀色"),
        ("UC1002009712", "A6061-T6", "R002", "60*70*20", "表面噴砂陽極銀色"),
        ("UC1002009713", "A6061-T6", "R003", "60*30*10", "表面噴砂陽極銀色"),
        ("UC1002009718", "A6061-T6", "R004", "40*16*13", "表面噴砂陽極銀色"),
        ("UC1003000436", "普通鋼", "J001", "1400*1300*785", "表面噴塗,RAL9003"),
        ("UC1004001529", "SPCC", "W002", "56*50*44", "表面噴塗,RAL9003"),
        ("UC1004001886", "SPCC", "J036", "1208*103.5*2", "表面噴塗,RAL9003"),
        ("UC1004001887", "SPCC", "F002", "794*200*15", "表面噴塗,RAL9003"),
        ("UC1004001888", "SPCC", "J050", "798*50*15", "表面噴塗,RAL9003"),
        ("UC1004001889", "SPCC", "J027", "1300*117.2*2", "表面噴塗,RAL9003"),
        ("UC1004001890", "SPCC", "J035", "1300*117.2*88", "表面噴塗,RAL9003"),
        ("UC1004001904", "SPCC", "F003", "818*200*21", "表面噴塗,RAL9003"),
        ("UC1004001905", "SPCC", "F001", "818*200*21", "表面噴塗,RAL9003"),
        ("UC1007000773", "SUS304", "J029", "80*90*2", None),
        ("UC2020083221", "鋁型材", None, "40*40", "白色透明"),
    ]
    return [
        ParsedPart(
            bom_item=item,
            sub_type="加工件" if item != "UC2020083221" else "機構外購件",
            material=mat,
            part_code=code,
            dimensions_raw=dims,
            surface_treatment=surf,
            unit_cost=100.0,
            is_quotable=(item != "UC2020083221"),
        )
        for item, mat, code, dims, surf in data
    ]


@pytest.fixture
def real_dwg_files():
    """29 real DWG filenames from the samples directory."""
    return [
        # 20 matched
        "UC1000005854-J003.DWG",
        "UC1000005855-J005.DWG",
        "UC1000005856-J006.DWG",
        "UC1000005857-J007.DWG",
        "UC1002006858_J026.DWG",
        "UC1002009711-R001.DWG",
        "UC1002009712-R002.DWG",
        "UC1002009713-R003.DWG",
        "UC1002009718-R004.DWG",
        "UC1003000436_J001.DWG",
        "UC1004001529_W002.DWG",
        "UC1004001886-J036.stp.DWG",
        "UC1004001887-F002.DWG",
        "UC1004001888-J050.DWG",
        "UC1004001889_J027.DWG",
        "UC1004001890-J035.DWG",
        "UC1004001904-F003.DWG",
        "UC1004001905-F001.DWG",
        "UC1007000773_J029.DWG",
        "UC2020083221-W001.DWG",
        # 9 Z-series (unmatched)
        "UC1002009714-Z018.DWG",
        "UC1002009715-Z016.DWG",
        "UC1002009716-Z011.DWG",
        "UC1007000774-Z020.DWG",
        "UC1008000528-Z001.DWG",
        "UC1008000529-Z019.DWG",
        "UC1008000530-Z021.DWG",
        "UC1250000084-Z024.DWG",
        "UC1300000008-Z017.DWG",
    ]


# ============================================================================
# L1 Exact Match Tests
# ============================================================================

class TestLevel1ExactMatch:
    def test_20_exact_matches(self, bom_parts, real_dwg_files):
        """All 20 known DWG files should match at L1."""
        matcher = DwgBomMatcher(bom_parts)
        matched_20 = real_dwg_files[:20]
        for dwg in matched_20:
            result = matcher.match(dwg)
            assert result.match_level == MatchLevel.LEVEL_1, (
                f"{dwg}: expected L1, got {result.match_level}"
            )
            assert result.confidence == 1.0
            assert result.matched_part is not None

    def test_j003_match(self, bom_parts):
        matcher = DwgBomMatcher(bom_parts)
        result = matcher.match("UC1000005854-J003.DWG")
        assert result.match_level == MatchLevel.LEVEL_1
        assert result.matched_bom_item == "UC1000005854"
        assert result.matched_part.material == "S50C"

    def test_r001_match(self, bom_parts):
        matcher = DwgBomMatcher(bom_parts)
        result = matcher.match("UC1002009711-R001.DWG")
        assert result.match_level == MatchLevel.LEVEL_1
        assert result.matched_bom_item == "UC1002009711"


# ============================================================================
# Z-Series Unmatched Tests
# ============================================================================

class TestZSeriesUnmatched:
    def test_all_9_z_series_unmatched(self, bom_parts, real_dwg_files):
        """All 9 Z-series DWG files must be UNMATCHED."""
        matcher = DwgBomMatcher(bom_parts)
        z_series = real_dwg_files[20:]  # Last 9
        matched_count = 0
        for dwg in z_series:
            result = matcher.match(dwg)
            if result.match_level != MatchLevel.UNMATCHED:
                matched_count += 1
        assert matched_count == 0, f"{matched_count} Z-series files were incorrectly matched"

    def test_z018_unmatched(self, bom_parts):
        matcher = DwgBomMatcher(bom_parts)
        result = matcher.match("UC1002009714-Z018.DWG")
        assert result.match_level == MatchLevel.UNMATCHED
        assert len(result.issues) > 0

    def test_z024_unmatched(self, bom_parts):
        matcher = DwgBomMatcher(bom_parts)
        result = matcher.match("UC1250000084-Z024.DWG")
        assert result.match_level == MatchLevel.UNMATCHED


# ============================================================================
# Match Report Tests
# ============================================================================

class TestMatchReport:
    def test_report_counts(self, bom_parts, real_dwg_files):
        matcher = DwgBomMatcher(bom_parts)
        report = matcher.match_all(real_dwg_files)

        assert report.total_dwg == 29
        assert report.total_bom_parts == 20
        assert report.l1_matched == 20
        assert report.unmatched == 9
        assert len(report.results) == 29

    def test_no_forced_matches(self, bom_parts, real_dwg_files):
        """All L3+ matches must have confidence >= 0.7."""
        matcher = DwgBomMatcher(bom_parts)
        report = matcher.match_all(real_dwg_files)
        for r in report.results:
            if r.match_level == MatchLevel.LEVEL_3:
                assert r.confidence >= 0.7, (
                    f"{r.source_dwg}: confidence {r.confidence} < 0.7"
                )

    def test_l1_confidence_is_1(self, bom_parts, real_dwg_files):
        matcher = DwgBomMatcher(bom_parts)
        for dwg in real_dwg_files[:20]:
            result = matcher.match(dwg)
            if result.match_level == MatchLevel.LEVEL_1:
                assert result.confidence == 1.0


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    def test_unparseable_filename(self, bom_parts):
        matcher = DwgBomMatcher(bom_parts)
        result = matcher.match("no_prefix_here.DWG")
        assert result.match_level == MatchLevel.UNMATCHED

    def test_empty_bom(self, real_dwg_files):
        matcher = DwgBomMatcher([])
        result = matcher.match(real_dwg_files[0])
        assert result.match_level == MatchLevel.UNMATCHED

    def test_duplicate_candidate(self, bom_parts):
        """When two BOM items share the same candidate number."""
        dup_parts = list(bom_parts) + [
            ParsedPart(bom_item="UC1000005854-DUP",
                       sub_type="加工件",
                       material="S50C",
                       unit_cost=999)
        ]
        matcher = DwgBomMatcher(dup_parts)
        result = matcher.match("UC1000005854-J003.DWG")
        # Ambiguous — should NOT match at L1 (multiple candidates)
        assert result.match_level != MatchLevel.LEVEL_1 or result.issues
