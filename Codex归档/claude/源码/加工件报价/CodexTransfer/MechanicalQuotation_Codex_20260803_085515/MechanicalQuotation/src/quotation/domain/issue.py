"""Issue domain model.

Tracks anomalies, unknown items, and items requiring manual review
discovered during the quotation process.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IssueSeverity(str, Enum):
    """Severity level of an issue."""
    WARNING = "warning"     # Non-blocking, e.g. price deviation > 15%
    ERROR = "error"         # Blocks quotation, e.g. missing dimensions
    UNKNOWN = "unknown"     # Item cannot be priced


class IssueStatus(str, Enum):
    """Resolution status of an issue."""
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# ---------------------------------------------------------------------------
# Issue
# ---------------------------------------------------------------------------

class Issue(BaseModel):
    """An anomaly or unknown item found during quotation."""

    # -- Identity --
    id: str = Field(..., description="Unique issue ID")
    drawing_id: str | None = Field(default=None, description="Related Drawing.id")
    quote_id: str | None = Field(default=None, description="Related Quote.id")

    # -- Classification --
    severity: IssueSeverity = Field(default=IssueSeverity.WARNING)
    category: str = Field(
        ...,
        description=(
            "Issue category: material_unknown | process_unknown | surface_unknown | "
            "dimension_missing | rule_missing | price_uncertain | "
            "parse_error | no_match | ambiguous_material"
        ),
    )

    # -- Content --
    title: str = Field(..., description="Short summary")
    description: str = Field(..., description="Detailed explanation")
    raw_input: str | None = Field(
        default=None, description="Original input that triggered the issue"
    )

    # -- AI suggestion (Phase 5) --
    ai_suggestion: str | None = Field(default=None, description="AI recommendation")
    ai_confidence: float | None = Field(
        default=None, ge=0, le=1, description="AI confidence 0-1"
    )

    # -- Manual resolution --
    status: IssueStatus = Field(default=IssueStatus.OPEN)
    resolution: str | None = Field(default=None, description="Human resolution")
    resolved_by: str | None = Field(default=None)
    resolved_at: str | None = Field(default=None, description="ISO datetime")

    # -- Metadata --
    created_at: str | None = Field(default=None, description="ISO datetime")


# ---------------------------------------------------------------------------
# IssueReport — aggregate
# ---------------------------------------------------------------------------

class IssueReport(BaseModel):
    """Summary of all issues for a quotation run."""

    quote_id: str = Field(..., description="Related Quote.id")
    issues: list[Issue] = Field(default_factory=list)

    # Computed stats
    total_issues: int = Field(default=0)
    error_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    unknown_count: int = Field(default=0)
    resolved_count: int = Field(default=0)

    def model_post_init(self, __context: object) -> None:
        """Auto-compute statistics."""
        self.total_issues = len(self.issues)
        self.error_count = sum(
            1 for i in self.issues if i.severity == IssueSeverity.ERROR
        )
        self.warning_count = sum(
            1 for i in self.issues if i.severity == IssueSeverity.WARNING
        )
        self.unknown_count = sum(
            1 for i in self.issues if i.severity == IssueSeverity.UNKNOWN
        )
        self.resolved_count = sum(
            1 for i in self.issues if i.status == IssueStatus.RESOLVED
        )
