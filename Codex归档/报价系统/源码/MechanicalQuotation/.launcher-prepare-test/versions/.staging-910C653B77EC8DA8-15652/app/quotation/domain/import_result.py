"""CAD Import result domain model.

Tracks the outcome of importing a CAD file (DWG/DXF/PDF).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from quotation.domain.drawing import Drawing


class ImportResult(BaseModel):
    """Result of importing a single CAD file."""

    # -- Source --
    source_file: str = Field(..., description="Original file path")
    source_format: str = Field(..., description="DWG | DXF | PDF")

    # -- Status --
    import_status: str = Field(
        default="success", description="success | partial | failed"
    )

    # -- Converted file (DWG only) --
    converted_file: str | None = Field(
        default=None, description="Path to generated DXF (when source was DWG)"
    )

    # -- Drawing (when parse succeeds) --
    drawing: Drawing | None = Field(default=None)

    # -- Issues --
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # -- Timing (ms) --
    import_duration_ms: float = 0.0
    conversion_duration_ms: float = 0.0

    # -- PDF-specific --
    pdf_confidence: str | None = Field(default=None)
    ocr_text: str | None = Field(default=None)

    @property
    def is_success(self) -> bool:
        return self.import_status == "success"

    @property
    def is_partial(self) -> bool:
        return self.import_status == "partial"

    @property
    def is_failed(self) -> bool:
        return self.import_status == "failed"
