"""Regression: verify DWG/BOM matching in Golden Dataset."""

from __future__ import annotations

import pytest

from quotation.domain.matching import MatchLevel


class TestGoldenMatching:
    """T1-T3: Matching validation."""

    def test_all_20_l1_matched(self, golden_match_results):
        """T1: All 20 golden parts match at L1."""
        unmatched = []
        for dwg, result in golden_match_results.items():
            if result.match_level != MatchLevel.LEVEL_1:
                unmatched.append(dwg)
        assert len(unmatched) == 0, (
            f"{len(unmatched)} parts not L1 matched: {unmatched}"
        )

    def test_all_candidates_extracted(self, golden_match_results):
        """T2: All DWG filenames yield valid candidates."""
        for dwg, result in golden_match_results.items():
            assert result.dwg_candidate is not None, (
                f"{dwg}: candidate extraction failed"
            )

    def test_all_confidence_1_point_0(self, golden_match_results):
        """T3: All L1 matches have confidence = 1.0."""
        for dwg, result in golden_match_results.items():
            if result.match_level == MatchLevel.LEVEL_1:
                assert result.confidence == 1.0, (
                    f"{dwg}: confidence={result.confidence}"
                )

    def test_all_matched_parts_not_null(self, golden_match_results):
        """Every match must have a non-null matched_part."""
        for dwg, result in golden_match_results.items():
            assert result.matched_part is not None, (
                f"{dwg}: matched_part is None"
            )
            assert result.matched_bom_item is not None, (
                f"{dwg}: matched_bom_item is None"
            )

    def test_exact_count(self, golden_match_results):
        """Must have exactly 20 match results."""
        assert len(golden_match_results) == 20
