"""Domain layer — business data models.

No file I/O, no Excel, no AI calls allowed in this layer.
All models use Pydantic v2 for runtime type validation.
"""

from quotation.domain.bom import BomEntry, BomSheet, ParsedPart
from quotation.domain.drawing import Drawing, DrawingFormat, ParseStatus, TextEntity
from quotation.domain.feature import (
    BoundingBox,
    Dimensions,
    Feature,
    FeatureSource,
    Hole,
)
from quotation.domain.historical import HistoricalFeature
from quotation.domain.issue import Issue, IssueReport, IssueSeverity, IssueStatus
from quotation.domain.material import MaterialProperties
from quotation.domain.quote import PriceSource, Quote, QuoteConfidence, QuoteItem
from quotation.domain.rule import (
    MaterialRule,
    MaterialStatus,
    ProcessRule,
    RuleSet,
    SurfacePricingMode,
    SurfaceRule,
)

__all__ = [
    # Drawing
    "Drawing",
    "DrawingFormat",
    "ParseStatus",
    "TextEntity",
    # Feature
    "BoundingBox",
    "Dimensions",
    "Feature",
    "FeatureSource",
    "Hole",
    # BOM
    "BomEntry",
    "BomSheet",
    "ParsedPart",
    # Material
    "MaterialProperties",
    # Rule
    "MaterialRule",
    "MaterialStatus",
    "ProcessRule",
    "RuleSet",
    "SurfacePricingMode",
    "SurfaceRule",
    # Quote
    "PriceSource",
    "Quote",
    "QuoteConfidence",
    "QuoteItem",
    # Historical
    "HistoricalFeature",
    # Issue
    "Issue",
    "IssueReport",
    "IssueSeverity",
    "IssueStatus",
]
