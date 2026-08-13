"""Tests for Issue domain model."""

from __future__ import annotations

import pytest

from quotation.domain.issue import Issue, IssueReport, IssueSeverity, IssueStatus


class TestIssueSeverity:
    def test_values(self):
        assert IssueSeverity.WARNING == "warning"
        assert IssueSeverity.ERROR == "error"
        assert IssueSeverity.UNKNOWN == "unknown"


class TestIssueStatus:
    def test_values(self):
        assert IssueStatus.OPEN == "open"
        assert IssueStatus.RESOLVED == "resolved"


class TestIssue:
    def test_create_warning(self):
        i = Issue(
            id="iss-001",
            drawing_id="dwg-001",
            severity=IssueSeverity.WARNING,
            category="price_uncertain",
            title="系統報價與歷史價格偏差 >15%",
            description="J003: 系統計算 ¥1,937 vs BOM ¥1,425 (偏差 +36%)",
            raw_input="material=S50C, weight=86.9kg",
        )
        assert i.severity == IssueSeverity.WARNING
        assert i.category == "price_uncertain"
        assert i.status == IssueStatus.OPEN
        assert i.ai_suggestion is None

    def test_create_error(self):
        i = Issue(
            id="iss-002",
            drawing_id="dwg-002",
            severity=IssueSeverity.ERROR,
            category="dimension_missing",
            title="無法提取零件尺寸",
            description="CAD 解析失敗，BOM 中也無尺寸數據",
        )
        assert i.severity == IssueSeverity.ERROR

    def test_create_with_ai_suggestion(self):
        i = Issue(
            id="iss-003",
            severity=IssueSeverity.UNKNOWN,
            category="material_unknown",
            title="無法識別材料: '6061鋁'",
            description="材料文字 '6061鋁' 未匹配任何規則",
            raw_input="6061鋁",
            ai_suggestion="可能為 A6061-T6 (鋁合金6061)，建議確認",
            ai_confidence=0.92,
        )
        assert i.ai_suggestion is not None
        assert i.ai_confidence == 0.92

    def test_resolve(self):
        i = Issue(
            id="iss-004",
            severity=IssueSeverity.WARNING,
            category="surface_unknown",
            title="未找到表面處理規則",
            description="test",
            status=IssueStatus.RESOLVED,
            resolution="確認為陽極氧化，已手動選擇 SURF_ANODIZE",
            resolved_by="工程師A",
            resolved_at="2026-08-01T10:00:00",
        )
        assert i.status == IssueStatus.RESOLVED
        assert i.resolution is not None

    def test_category_values(self):
        valid_categories = [
            "material_unknown",
            "process_unknown",
            "surface_unknown",
            "dimension_missing",
            "rule_missing",
            "price_uncertain",
            "parse_error",
            "no_match",
            "ambiguous_material",
        ]
        for cat in valid_categories:
            i = Issue(
                id=f"iss-{cat}",
                category=cat,
                title="test",
                description="test",
            )
            assert i.category == cat


class TestIssueReport:
    def test_empty(self):
        r = IssueReport(quote_id="q-001")
        assert r.total_issues == 0
        assert r.error_count == 0
        assert r.warning_count == 0

    def test_with_issues(self):
        issues = [
            Issue(
                id="iss-001",
                severity=IssueSeverity.ERROR,
                category="dimension_missing",
                title="err",
                description="err",
            ),
            Issue(
                id="iss-002",
                severity=IssueSeverity.WARNING,
                category="price_uncertain",
                title="warn",
                description="warn",
            ),
            Issue(
                id="iss-003",
                severity=IssueSeverity.WARNING,
                category="rule_missing",
                title="warn2",
                description="warn2",
            ),
            Issue(
                id="iss-004",
                severity=IssueSeverity.UNKNOWN,
                category="material_unknown",
                title="unk",
                description="unk",
            ),
        ]
        r = IssueReport(quote_id="q-001", issues=issues)
        assert r.total_issues == 4
        assert r.error_count == 1
        assert r.warning_count == 2
        assert r.unknown_count == 1
        assert r.resolved_count == 0

    def test_resolved_count(self):
        issues = [
            Issue(
                id="iss-001",
                severity=IssueSeverity.WARNING,
                category="test",
                title="t",
                description="t",
                status=IssueStatus.RESOLVED,
            ),
            Issue(
                id="iss-002",
                severity=IssueSeverity.WARNING,
                category="test",
                title="t",
                description="t",
            ),
        ]
        r = IssueReport(quote_id="q-001", issues=issues)
        assert r.resolved_count == 1
