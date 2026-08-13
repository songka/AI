"""DWG to BOM Matching Engine.

Three-level matching pipeline:
  L1: Exact match — filename number ↔ BOM item number
  L2: Semantic match — part_code + material
  L3: Feature match — dimensions + material + surface treatment
"""

from __future__ import annotations

import logging
import re

from quotation.domain.bom import ParsedPart
from quotation.domain.matching import MatchLevel, MatchReport, MatchResult
from quotation.infrastructure.parser.material_normalizer import get_canonical_name

logger = logging.getLogger("quotation.infrastructure.parser.dwg_matcher")


# ---------------------------------------------------------------------------
# Candidate extraction
# ---------------------------------------------------------------------------

def extract_candidate_from_filename(filename: str) -> str | None:
    """Extract item number candidate from DWG filename.

    UC1000005854-J003.DWG → '1000005854'
    UC1002006858_J026.DWG → '1002006858'
    UC1004001886-J036.stp.DWG → '1004001886'
    UC2020083221-W001.DWG → '2020083221'
    """
    # Remove extension
    name = filename
    for ext in (".DWG", ".dxf", ".DXF", ".stp.DWG", ".SLDPRT.PDF"):
        if name.upper().endswith(ext):
            name = name[: -len(ext)]
            break

    m = re.search(r"UC(\d+)", name, re.IGNORECASE)
    return m.group(1) if m else None


def extract_part_code_from_filename(filename: str) -> str | None:
    """Extract part code from filename.

    UC1000005854-J003.DWG → 'J003'
    UC1002009712-R002.DWG → 'R002'
    """
    name = filename
    for ext in (".DWG", ".dxf", ".DXF", ".stp.DWG", ".SLDPRT.PDF"):
        if name.upper().endswith(ext):
            name = name[: -len(ext)]
            break

    # Match trailing code: -J003, _J026, -R001, -F001, _W002, -Z018
    m = re.search(r"[-_](\w\d{3})(?:\b|$)", name, re.IGNORECASE)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class DwgBomMatcher:
    """Three-level DWG → BOM matching engine."""

    def __init__(self, bom_parts: list[ParsedPart]):
        self._bom_parts = bom_parts
        # Build lookup: numeric part → list of ParsedPart
        self._index: dict[str, list[ParsedPart]] = {}
        for pp in bom_parts:
            num_match = re.search(r"(\d{7,})", pp.bom_item)
            if num_match:
                key = num_match.group(1)
                self._index.setdefault(key, []).append(pp)

    # -- Public API --

    def match(self, dwg_filename: str) -> MatchResult:
        """Match a single DWG file through all three levels."""
        candidate = extract_candidate_from_filename(dwg_filename)

        if not candidate:
            return MatchResult(
                source_dwg=dwg_filename,
                match_level=MatchLevel.UNMATCHED,
                confidence=0.0,
                issues=["Cannot extract candidate number from filename"],
            )

        # L1: Exact match
        l1_result = self._match_l1(dwg_filename, candidate)
        if l1_result is not None:
            return l1_result

        # L2: Semantic match
        l2_result = self._match_l2(dwg_filename, candidate)
        if l2_result is not None and l2_result.confidence >= 0.6:
            return l2_result

        # L3: Feature match
        l3_result = self._match_l3(dwg_filename, candidate)
        if l3_result is not None and l3_result.confidence >= 0.7:
            return l3_result

        # Unmatched
        issues = ["No BOM match found"]
        if l3_result:
            issues.append(f"Best L3 confidence={l3_result.confidence:.2f} (below threshold)")
        elif l2_result:
            issues.append(f"Best L2 confidence={l2_result.confidence:.2f} (below threshold)")

        return MatchResult(
            source_dwg=dwg_filename,
            dwg_candidate=candidate,
            match_level=MatchLevel.UNMATCHED,
            confidence=l3_result.confidence if l3_result else (l2_result.confidence if l2_result else 0.0),
            issues=issues,
        )

    def match_all(self, dwg_filenames: list[str]) -> MatchReport:
        """Match all DWG files and produce a report."""
        results = [self.match(f) for f in dwg_filenames]
        return self._build_report(results)

    # -- Level matchers --

    def _match_l1(self, filename: str, candidate: str) -> MatchResult | None:
        """L1: Exact numeric match."""
        if candidate not in self._index:
            return None

        parts = self._index[candidate]
        if len(parts) == 1:
            pp = parts[0]
            return MatchResult(
                source_dwg=filename,
                dwg_candidate=candidate,
                matched_part=pp,
                matched_bom_item=pp.bom_item,
                match_level=MatchLevel.LEVEL_1,
                confidence=1.0,
                matched_by="exact_item_number",
                evidence=f"DWG candidate '{candidate}' exactly matches BOM item '{pp.bom_item}'",
            )
        # Multiple matches — ambiguous
        return None

    def _match_l2(self, filename: str, candidate: str) -> MatchResult | None:
        """L2: Semantic match by part_code + material."""
        part_code = extract_part_code_from_filename(filename)
        if not part_code:
            return None

        best_score = 0.0
        best_part: ParsedPart | None = None

        for pp in self._bom_parts:
            score = 0.0
            details = []

            if pp.part_code and pp.part_code.upper() == part_code.upper():
                score += 0.5
                details.append(f"part_code match: {part_code}")

            if pp.material:
                normalized = get_canonical_name(pp.material)
                if normalized:
                    score += 0.3
                    details.append(f"material known: {normalized}")
                else:
                    score += 0.1
                    details.append(f"material present: {pp.material}")

            if score > best_score:
                best_score = score
                best_part = pp

        if best_part and best_score >= 0.5:
            return MatchResult(
                source_dwg=filename,
                dwg_candidate=candidate,
                matched_part=best_part,
                matched_bom_item=best_part.bom_item,
                match_level=MatchLevel.LEVEL_2,
                confidence=best_score,
                matched_by="part_code",
                evidence=f"Part code '{part_code}' matched BOM part '{best_part.bom_item}' (score={best_score:.2f})",
            )
        return None

    def _match_l3(self, filename: str, candidate: str) -> MatchResult | None:
        """L3: Feature match — only when L1 candidate found but not in BOM.

        Requires actual feature comparison (not just field presence).
        """
        # L3 only applies when candidate was extracted but not in BOM
        if candidate in self._index:
            return None  # L1 should have matched; if not, ambiguous

        part_code = extract_part_code_from_filename(filename)
        best_score = 0.0
        best_part: ParsedPart | None = None
        best_evidence = ""

        for pp in self._bom_parts:
            score = 0.0
            details = []

            # Material comparison
            if pp.material:
                canonical = get_canonical_name(pp.material)
                if canonical:
                    score += 0.3
                    details.append(f"material: {canonical}")
                else:
                    score += 0.1
                    details.append(f"material_unknown: {pp.material}")

            # Dimensions present
            if pp.dimensions_raw:
                score += 0.15
                details.append(f"has_dimensions: {pp.dimensions_raw}")

            # Surface treatment
            if pp.surface_treatment:
                score += 0.1
                details.append(f"has_surface: {pp.surface_treatment}")

            # Part code prefix match
            if part_code and pp.part_code:
                if part_code[0].upper() == pp.part_code[0].upper():
                    score += 0.15
                    details.append(f"code_prefix: {part_code[0]}")

            if score > best_score:
                best_score = score
                best_part = pp
                best_evidence = "; ".join(details)

        if best_part and best_score >= 0.7:
            return MatchResult(
                source_dwg=filename,
                dwg_candidate=candidate,
                matched_part=best_part,
                matched_bom_item=best_part.bom_item,
                match_level=MatchLevel.LEVEL_3,
                confidence=best_score,
                matched_by="feature_similarity",
                evidence=best_evidence,
            )
        return None

    # -- Report --

    def _build_report(self, results: list[MatchResult]) -> MatchReport:
        report = MatchReport(
            total_dwg=len(results),
            total_bom_parts=len(self._bom_parts),
            results=results,
        )
        for r in results:
            match r.match_level:
                case MatchLevel.LEVEL_1:
                    report.l1_matched += 1
                    report.matched_dwg.append(r.source_dwg)
                case MatchLevel.LEVEL_2:
                    report.l2_matched += 1
                    report.matched_dwg.append(r.source_dwg)
                case MatchLevel.LEVEL_3:
                    report.l3_matched += 1
                    report.matched_dwg.append(r.source_dwg)
                case MatchLevel.UNMATCHED:
                    report.unmatched += 1
                    report.unmatched_dwg.append(r.source_dwg)
        return report
