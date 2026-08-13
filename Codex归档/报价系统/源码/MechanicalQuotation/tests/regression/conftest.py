"""Regression test fixtures — load Golden Dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quotation.domain.bom import ParsedPart
from quotation.domain.historical import HistoricalFeature
from quotation.domain.matching import MatchResult
from quotation.infrastructure.parser.description_parser import DescriptionParser
from quotation.infrastructure.parser.dwg_matcher import DwgBomMatcher
from quotation.infrastructure.parser.historical_builder import build_historical_feature

# ---------------------------------------------------------------------------
# Golden Dataset path
# ---------------------------------------------------------------------------
GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"

# Material density reference (g/cm³)
DENSITY = {
    "S50C": 7.85, "A6061-T6": 2.70, "SPCC": 7.85,
    "SUS304": 7.93, "SKD11": 7.85, "普通鋼": 7.85,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def golden_data():
    """Load the Golden Dataset from JSON."""
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def golden_parts(golden_data):
    """Build ParsedPart list from Golden Dataset."""
    parts = []
    for item in golden_data["parts"]:
        pp = ParsedPart(
            bom_item=item["bom_item"],
            source_row=item.get("source_bom_row", 0),
            category="原材料",
            sub_type=item.get("sub_type", "加工件"),
            material=item["material"],
            part_code=item.get("part_code"),
            dimensions_raw=item.get("dimensions_raw"),
            surface_treatment=item.get("surface_treatment"),
            unit_cost=item["historical_price"],
            is_quotable=True,
        )
        parts.append(pp)
    return parts


@pytest.fixture(scope="module")
def golden_matcher(golden_parts):
    """Create DwgBomMatcher from golden parts."""
    return DwgBomMatcher(golden_parts)


@pytest.fixture(scope="module")
def golden_match_results(golden_data, golden_matcher):
    """Run matcher on all golden DWG files."""
    results = {}
    for item in golden_data["parts"]:
        dwg = item["dwg_file"]
        results[dwg] = golden_matcher.match(dwg)
    return results


@pytest.fixture(scope="module")
def golden_historical_features(golden_data, golden_parts):
    """Build HistoricalFeature for each golden part."""
    parser = DescriptionParser()
    features = {}
    for item, pp in zip(golden_data["parts"], golden_parts):
        density = DENSITY.get(pp.material or "")
        h = build_historical_feature(
            pp,
            project_name=item.get("project_name", "GCS"),
            density_g_cm3=density or None,
        )
        features[item["bom_item"]] = h
    return features
