"""Quotation Application Service — unified entry point for UI, API, and batch.

All quotation workflows (single, batch, with/without AI) go through this service.
No pricing/formula logic is duplicated here — it delegates to the existing pipeline.
"""

from __future__ import annotations

import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Callable

from quotation.domain.quote import PriceSource, Quote, QuoteItem
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.quote_builder import QuoteBuilder

from .file_scanner import DrawingFile, FileScanner, JobBundle, MatchStatus


# ---------------------------------------------------------------------------
# Tax calculation (shared, UI-layer concern)
# ---------------------------------------------------------------------------

@dataclass
class TaxResult:
    subtotal_excluding_tax: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_including_tax: Decimal

    @classmethod
    def calculate(cls, items: list[QuoteItem], tax_rate: Decimal = Decimal("0.17")) -> TaxResult:
        subtotal = Decimal("0")
        for item in items:
            if item.source != PriceSource.U:
                subtotal += Decimal(str(item.amount))
        subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_incl = (subtotal * (Decimal("1") + tax_rate)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return cls(
            subtotal_excluding_tax=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_including_tax=total_incl,
        )


# ---------------------------------------------------------------------------
# Quote job status
# ---------------------------------------------------------------------------

class JobStatus:
    WAITING = "WAITING"
    SCANNED = "SCANNED"
    PARSING = "PARSING"
    AI_ANALYZING = "AI_ANALYZING"
    QUOTING = "QUOTING"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    PARSE_FAILED = "PARSE_FAILED"
    QUOTE_FAILED = "QUOTE_FAILED"


# ---------------------------------------------------------------------------
# Quote Job result
# ---------------------------------------------------------------------------

@dataclass
class QuoteJobResult:
    """Result of processing one job bundle through the pipeline."""

    job_id: str
    bundle: JobBundle
    status: str = JobStatus.WAITING
    quote: Quote | None = None
    tax: TaxResult | None = None
    feature_summary: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ai_used: bool = False
    ai_suggestions: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0

    @property
    def drawing_number(self) -> str:
        return self.bundle.drawing_number

    @property
    def source_files(self) -> list[str]:
        return [f.file_name for f in self.bundle.files]

    @property
    def is_complete(self) -> bool:
        return self.status == JobStatus.COMPLETE

    @property
    def cost_completion(self) -> float:
        if self.quote is None:
            return 0.0
        return self.quote.cost_completion

    @property
    def unknown_item_count(self) -> int:
        if self.quote is None:
            return 0
        return self.quote.unknown_count

    @property
    def subtotal_excluding_tax(self) -> Decimal:
        if self.tax is None:
            return Decimal("0")
        return self.tax.subtotal_excluding_tax

    @property
    def total_including_tax(self) -> Decimal:
        if self.tax is None:
            return Decimal("0")
        return self.tax.total_including_tax

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "drawing_number": self.drawing_number,
            "source_files": self.source_files,
            "status": self.status,
            "cost_completion": self.cost_completion,
            "unknown_item_count": self.unknown_item_count,
            "subtotal_excluding_tax": float(self.subtotal_excluding_tax),
            "tax_rate": 0.17,
            "tax_amount": float(self.tax.tax_amount) if self.tax else 0.0,
            "total_including_tax": float(self.total_including_tax),
            "rule_version": "1.0",
            "price_version_id": self.quote.price_version if self.quote else None,
            "ai_used": self.ai_used,
            "ai_suggestions": self.ai_suggestions,
            "items": [self._item_to_dict(i) for i in (self.quote.items if self.quote else [])],
            "warnings": self.warnings,
            "errors": self.errors,
        }

    @staticmethod
    def _item_to_dict(item: QuoteItem) -> dict[str, Any]:
        is_u = item.source == PriceSource.U
        return {
            "line_id": item.line_id,
            "category": item.category,
            "name": item.name,
            "source": item.source.value,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "amount": None if is_u else item.amount,
            "confidence": item.confidence.value,
            "status": "待確認" if is_u else "已確認",
            "resolution_source": item.resolution_source,
            "price_version_id": item.price_version_id,
            "company_price_id": item.company_price_id,
            "origin_price_record_id": item.origin_price_record_id,
            "origin_supplier_id": item.origin_supplier_id,
            "price_basis": item.price_basis,
            "fallback_warning": item.fallback_warning,
        }


# ---------------------------------------------------------------------------
# Quotation Application Service
# ---------------------------------------------------------------------------

class QuotationApplicationService:
    """Central application service for all quotation workflows."""

    def __init__(self, ai_client: Any = None):
        self._ai_client = ai_client
        self._scanner = FileScanner()
        self._resolver: PricingResolver | None = None

    # ------------------------------------------------------------------
    # Single-file quote
    # ------------------------------------------------------------------

    def quote_single_file(
        self,
        file_path: str | Path,
        use_ai: bool = False,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> QuoteJobResult:
        """Quote a single drawing file, auto-matching related files."""
        file_path = Path(file_path)
        bundle = self._scanner.scan_single_file(file_path)
        return self._process_bundle(bundle, use_ai, progress_callback)

    # ------------------------------------------------------------------
    # Batch quote
    # ------------------------------------------------------------------

    def scan_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
    ) -> list[JobBundle]:
        """Scan a directory and return matched job bundles."""
        return self._scanner.scan_directory(Path(directory), recursive=recursive)

    def quote_batch(
        self,
        bundles: list[JobBundle],
        use_ai: bool = False,
        progress_callback: Callable[[int, int, QuoteJobResult], None] | None = None,
    ) -> list[QuoteJobResult]:
        """Process multiple job bundles."""
        results: list[QuoteJobResult] = []
        total = len(bundles)
        for i, bundle in enumerate(bundles):
            result = self._process_bundle(bundle, use_ai)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total, result)
        return results

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _process_bundle(
        self,
        bundle: JobBundle,
        use_ai: bool = False,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> QuoteJobResult:
        """Run the full pipeline on a job bundle."""
        import time
        t0 = time.time()

        result = QuoteJobResult(
            job_id=f"JOB-{bundle.drawing_number}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            bundle=bundle,
            status=JobStatus.PARSING,
        )

        try:
            # Check if we have a supported geometry source
            geometry_file = bundle.geometry_source
            if geometry_file is None:
                result.status = JobStatus.UNSUPPORTED
                result.errors.append("No DWG or DXF geometry source found")
                return result

            if geometry_file.extension.lower() not in ('.dxf', '.dwg'):
                result.status = JobStatus.UNSUPPORTED
                result.errors.append(f"Unsupported geometry format: {geometry_file.extension}")
                return result

            # If it's a DWG, we can't process it (no DWG support yet)
            if geometry_file.extension.lower() == '.dwg':
                result.status = JobStatus.UNSUPPORTED
                result.errors.append("DWG format not yet supported — convert to DXF first")
                return result

            if progress_callback:
                progress_callback("Parsing CAD file...", 0.1)

            # Read DXF
            reader = DxfReader()
            import_result = reader.read(geometry_file.full_path)
            drawing = import_result.drawing

            # Feature extraction
            geo_ext = GeometricExtractor()
            geo = geo_ext.extract(drawing.raw_entities)

            mfg_ext = ManufacturingExtractor()
            mfg = mfg_ext.extract(geo)

            if progress_callback:
                progress_callback("Extracting features...", 0.3)

            # AI assistance (if enabled and material not detected)
            ai_result = None
            if use_ai and self._ai_client is not None:
                result.ai_used = True
                result.status = JobStatus.AI_ANALYZING
                if progress_callback:
                    progress_callback("AI analyzing...", 0.5)
                try:
                    ai_result = self._run_ai_extraction(bundle, mfg)
                    result.ai_suggestions = ai_result or {}
                except Exception as e:
                    result.warnings.append(f"AI extraction failed: {e}")

            # Quotation mapping
            mapper = QuotationMapper()
            qf = mapper.map(mfg, geo)

            if progress_callback:
                progress_callback("Calculating prices...", 0.7)

            # Pricing
            if self._resolver is None:
                self._resolver = PricingResolver()
            resolver = self._resolver

            items: list[QuoteItem] = []
            for mq in qf.machining:
                items.extend(resolver.resolve_machining(mq))
            for fq in qf.frames:
                items.extend(resolver.resolve_frame(fq))
            for aq in qf.assemblies:
                items.extend(resolver.resolve_assembly(aq))

            # Quote builder
            builder = QuoteBuilder()
            feat_conf = mfg.material.confidence if mfg.material else None
            quote = builder.build(
                quote_id=result.job_id,
                drawing_id=bundle.drawing_number,
                part_number=bundle.drawing_number,
                part_name=bundle.drawing_number,
                material=mfg.material.normalized.value if mfg.material and mfg.material.normalized else None,
                items=items,
                feature_confidence=feat_conf,
                price_version=resolver.price_version,
                rule_version="1.0",
            )

            # Feature summary
            bbox = geo.bounding_box
            weight_kg = None
            for item in quote.items:
                if item.category == "material" and item.evidence:
                    m = re.search(r"weight_kg=([\d.]+)", item.evidence)
                    if m:
                        weight_kg = float(m.group(1))
                        break

            result.feature_summary = {
                "bounding_box": f"{bbox.length:.0f}x{bbox.width:.0f} mm" if bbox else "-",
                "mfg_holes": mfg.total_holes,
                "mfg_threads": mfg.total_threads,
                "frames": len(mfg.frames),
                "assemblies": len(mfg.structure_assemblies),
                "accessories": len(mfg.structure_accessories),
                "welds": len(mfg.welds),
                "weight": f"{weight_kg:.1f} kg" if weight_kg else "-",
            }

            result.quote = quote
            result.tax = TaxResult.calculate(quote.items)

            # Determine status
            if quote.unknown_count == 0:
                result.status = JobStatus.COMPLETE
            elif quote.unknown_count > 0 and quote.total > 0:
                result.status = JobStatus.REVIEW_REQUIRED
            else:
                result.status = JobStatus.INCOMPLETE

        except FileNotFoundError as e:
            result.status = JobStatus.PARSE_FAILED
            result.errors.append(f"File not found: {e}")
        except Exception as e:
            result.status = JobStatus.QUOTE_FAILED
            result.errors.append(f"{e}")
            result.errors.append(traceback.format_exc())

        result.processing_time_ms = (time.time() - t0) * 1000
        return result

    # ------------------------------------------------------------------
    # AI extraction
    # ------------------------------------------------------------------

    def _run_ai_extraction(self, bundle: JobBundle, mfg: Any) -> dict[str, Any] | None:
        """Run DeepSeek-assisted extraction for missing fields."""
        if self._ai_client is None:
            return None

        # Collect context for AI
        text_context: list[str] = []
        for f in bundle.files:
            if f.extension.lower() == '.pdf':
                text_context.append(f"[PDF] {f.file_name}")

        # Determine what's missing
        missing: list[str] = []
        if mfg.material is None or mfg.material.normalized is None:
            missing.append("material")
        if mfg.surface_treatment is None:
            missing.append("surface_treatment")

        if not missing:
            return None

        try:
            raw = self._ai_client.extract_features(
                drawing_number=bundle.drawing_number,
                texts=text_context,
                missing_fields=missing,
            )
            return raw
        except Exception:
            return None

    # ------------------------------------------------------------------
    # AI health check
    # ------------------------------------------------------------------

    def check_ai_health(self) -> dict[str, Any]:
        """Check AI connectivity."""
        if self._ai_client is None:
            return {"configured": False, "reachable": False, "error": "AI client not configured"}
        try:
            return self._ai_client.health_check()
        except Exception as e:
            return {"configured": True, "reachable": False, "error": str(e)}
