"""Quotation Application Service — unified entry point for UI, API, and batch.

All quotation workflows (single, batch, with/without AI) go through this service.
No pricing/formula logic is duplicated here — it delegates to the existing pipeline.
"""

from __future__ import annotations

import re
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Callable

from quotation.domain.quote import PriceSource, Quote, QuoteConfidence, QuoteItem
from quotation.application.external_skill_settings import (
    CATEGORY_NAMES_ZH,
    SkillStep,
    SkillRoutingMode,
    SkillSourceType,
    PartCategory,
)
from quotation.infrastructure.dwg.converter import DwgConversionService
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.calculators import calc_machining
from quotation.infrastructure.rules.calculators import make_unknown_item
from quotation.infrastructure.rules.quote_builder import QuoteBuilder
from quotation.infrastructure.solidworks.converter import SolidWorksConversionService

from .file_scanner import FileScanner, JobBundle
from .multi_agent_review import MultiAgentReviewOrchestrator

DEFAULT_TAX_RATE = Decimal("0.13")

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
    def calculate(cls, items: list[QuoteItem], tax_rate: Decimal = DEFAULT_TAX_RATE) -> TaxResult:
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
    DWG_CONVERTING = "DWG_CONVERTING"
    DWG_CONVERSION_FAILED = "DWG_CONVERSION_FAILED"
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
    supplementary_analysis: list[dict[str, Any]] = field(default_factory=list)
    document_texts: list[dict[str, Any]] = field(default_factory=list)
    dwg_conversion: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    batch_index: int | None = None

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
            "tax_rate": float(self.tax.tax_rate) if self.tax else float(DEFAULT_TAX_RATE),
            "tax_amount": float(self.tax.tax_amount) if self.tax else 0.0,
            "total_including_tax": float(self.total_including_tax),
            "rule_version": "1.0",
            "price_version_id": self.quote.price_version if self.quote else None,
            "ai_used": self.ai_used,
            "ai_suggestions": self.ai_suggestions,
            "supplementary_analysis": self.supplementary_analysis,
            "document_texts": self.document_texts,
            "dwg_conversion": self.dwg_conversion,
            "items": [self._item_to_dict(i) for i in (self.quote.items if self.quote else [])],
            "warnings": self.warnings,
            "errors": self.errors,
        }

    @staticmethod
    def _item_to_dict(item: QuoteItem) -> dict[str, Any]:
        is_u = item.source == PriceSource.U
        is_ai = item.source == PriceSource.AI
        return {
            "line_id": item.line_id,
            "category": item.category,
            "name": item.name,
            "name_zh": item.name,
            "source": item.source.value,
            "price_status": (
                "UNKNOWN" if is_u else "AI_REFERENCE" if is_ai else "FORMAL"
            ),
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "amount": None if is_u else item.amount,
            "confidence": item.confidence.value,
            "status": (
                "待确认"
                if is_u
                else "AI估算已计入，需人工确认"
                if is_ai
                else "已确认"
            ),
            "resolution_source": item.resolution_source,
            "price_version_id": item.price_version_id,
            "company_price_id": item.company_price_id,
            "origin_price_record_id": item.origin_price_record_id,
            "origin_supplier_id": item.origin_supplier_id,
            "price_basis": item.price_basis,
            "fallback_warning": item.fallback_warning,
            "requires_review": is_u or is_ai,
            "included_in_quotation": not is_u,
            "ai_reference": (
                {
                    "estimated_unit_price": item.ai_estimated_unit_price,
                    "estimated_amount": item.ai_estimated_amount,
                    "unit": item.ai_estimated_unit,
                    "reason_zh": item.ai_estimate_reason,
                    "confidence": item.ai_estimate_confidence,
                }
                if item.ai_estimated_unit_price is not None
                else None
            ),
        }


# ---------------------------------------------------------------------------
# Quotation Application Service
# ---------------------------------------------------------------------------


class QuotationApplicationService:
    """Central application service for all quotation workflows."""

    def __init__(
        self,
        ai_client: Any = None,
        dwg_conversion_service: DwgConversionService | None = None,
        solidworks_conversion_service: SolidWorksConversionService | None = None,
        external_skill_router: Any = None,
    ):
        self._ai_client = ai_client
        self._dwg_conversion_service = dwg_conversion_service or DwgConversionService()
        self._solidworks_conversion_service = (
            solidworks_conversion_service or SolidWorksConversionService()
        )
        self._scanner = FileScanner()
        self._resolver: PricingResolver | None = None
        self._external_skill_router = external_skill_router

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
        max_workers: int | None = None,
    ) -> list[QuoteJobResult]:
        """Process bundles concurrently while preserving the original result order."""
        total = len(bundles)
        if total == 0:
            return []
        if self._resolver is None:
            self._resolver = PricingResolver()
        configured = os.environ.get("MECHANICAL_QUOTATION_BATCH_WORKERS", "").strip()
        if max_workers is None and configured:
            try:
                max_workers = int(configured)
            except ValueError:
                max_workers = None
        if max_workers is None:
            max_workers = 2 if use_ai else 4
        # SolidWorks COM automation is not safely parallel across documents.
        if any(
            bundle.geometry_source is not None
            and bundle.geometry_source.extension.lower() in {".slddrw", ".sldprt"}
            for bundle in bundles
        ):
            max_workers = 1
        workers = max(1, min(int(max_workers), total, 8))
        results: list[QuoteJobResult | None] = [None] * total
        completed = 0
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="quotation-batch"
        ) as pool:
            futures = {
                pool.submit(self._process_bundle, bundle, use_ai): index
                for index, bundle in enumerate(bundles)
            }
            for future in as_completed(futures):
                index = futures[future]
                result = future.result()
                result.batch_index = index
                results[index] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, result)
        ordered = [result for result in results if result is not None]
        if use_ai and self._ai_client is not None:
            cache_stats = {
                "scope": "CURRENT_AI_CLIENT_EXACT_INPUT",
                "hits": int(getattr(self._ai_client, "cache_hits", 0)),
                "misses": int(getattr(self._ai_client, "cache_misses", 0)),
            }
            for result in ordered:
                result.ai_suggestions = dict(result.ai_suggestions or {})
                result.ai_suggestions["batch_ai_cache"] = cache_stats
        return ordered

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
        if use_ai and self._ai_client is None:
            result.warnings.append(
                "已启用 AI，但程序未读取到 DeepSeek Key；本次将使用内置规则报价。"
            )

        try:
            if self._resolver is None:
                self._resolver = PricingResolver()
            resolver = self._resolver
            external_config = None
            if self._external_skill_router is not None:
                try:
                    external_config = self._external_skill_router.load_config()
                    if (
                        external_config.mode == SkillRoutingMode.FULL_QUOTATION
                        and not external_config.category_routes
                    ):
                        selected = next(
                            (
                                skill
                                for skill in external_config.skills
                                if skill.skill_id == external_config.full_skill_id
                            ),
                            None,
                        )
                        if selected is not None and selected.source_type == SkillSourceType.HTTP:
                            external = self._external_skill_router.execute(result, external_config)
                            if self._apply_external_skill_execution(
                                result, external, require_quote=True
                            ):
                                result.processing_time_ms = (time.time() - t0) * 1000
                                return result
                except Exception as exc:
                    result.warnings.append(
                        f"整套外接 Skill 无法执行，已回退内置报价：{exc}"
                    )

            # Check if we have a supported geometry source
            geometry_file = bundle.geometry_source
            if geometry_file is None:
                result.status = JobStatus.UNSUPPORTED
                result.errors.append("找不到可用的 DWG、DXF 或 SolidWorks 图纸")
                return result

            if geometry_file.extension.lower() not in (".dxf", ".dwg", ".slddrw", ".sldprt"):
                result.status = JobStatus.UNSUPPORTED
                result.errors.append(f"不支援的幾何圖紙格式：{geometry_file.extension}")
                return result

            parse_path = geometry_file.full_path
            conversion_cleanup_service = None
            conversion_result = None
            if geometry_file.extension.lower() == ".dwg":
                result.status = JobStatus.DWG_CONVERTING
                if progress_callback:
                    progress_callback("正在將DWG轉換為DXF...", 0.05)
                conversion = self._dwg_conversion_service.convert(geometry_file.full_path)
                result.dwg_conversion = conversion.to_trace()
                result.warnings.extend(conversion.warnings)
                if not conversion.is_success or conversion.converted_file is None:
                    result.status = JobStatus.DWG_CONVERSION_FAILED
                    result.errors.append(conversion.error or "DWG轉換失敗")
                    return result
                parse_path = Path(conversion.converted_file)
                conversion_cleanup_service = self._dwg_conversion_service
                conversion_result = conversion
            elif geometry_file.extension.lower() in (".slddrw", ".sldprt"):
                result.status = JobStatus.DWG_CONVERTING
                if progress_callback:
                    progress_callback("正在通过 SOLIDWORKS 读取原生文件...", 0.05)
                conversion = self._solidworks_conversion_service.convert(
                    geometry_file.full_path
                )
                result.dwg_conversion = conversion.to_trace()
                if not conversion.is_success or conversion.converted_file is None:
                    result.status = JobStatus.DWG_CONVERSION_FAILED
                    result.errors.append(conversion.error or "SOLIDWORKS 转换失败")
                    return result
                parse_path = Path(conversion.converted_file)
                conversion_cleanup_service = self._solidworks_conversion_service
                conversion_result = conversion

            if progress_callback:
                progress_callback("正在解析图纸……", 0.1)

            # Read DXF
            reader = DxfReader()
            try:
                import_result = reader.read(parse_path)
            finally:
                if conversion_cleanup_service is not None and conversion_result is not None:
                    cleanup = getattr(
                        conversion_cleanup_service, "cleanup_converted_file", None
                    )
                    if callable(cleanup):
                        try:
                            deleted = bool(cleanup(conversion_result))
                            result.dwg_conversion["converted_file_deleted"] = deleted
                            result.dwg_conversion["converted_file_retained"] = False
                            result.dwg_conversion["cleanup_status"] = (
                                "DELETED" if deleted else "ALREADY_ABSENT"
                            )
                        except Exception as exc:
                            result.dwg_conversion["converted_file_deleted"] = False
                            result.dwg_conversion["converted_file_retained"] = True
                            result.dwg_conversion["cleanup_status"] = "FAILED"
                            result.warnings.append(f"转换中间文件清理失败：{exc}")
            drawing = import_result.drawing

            # Feature extraction
            geo_ext = GeometricExtractor()
            geo = geo_ext.extract(drawing.raw_entities)

            drawing_text_context = list(drawing.raw_text_strings)
            confirmed_dimensions = self._confirmed_part_dimensions(
                drawing_text_context
            )
            confirmed_dimension_values = (
                [float(value) for value in confirmed_dimensions.split("*")]
                if confirmed_dimensions
                else None
            )
            mfg_ext = ManufacturingExtractor()
            mfg = mfg_ext.extract(
                geo,
                dimensions_raw=confirmed_dimensions,
                allow_drawing_extent_estimates=False,
            )
            result.document_texts = self._document_text_inputs(
                geometry_file.file_name,
                drawing_text_context,
            )

            if progress_callback:
                progress_callback("正在提取加工特征……", 0.3)

            # AI assistance (if enabled and material not detected)
            ai_result = None
            if use_ai and self._ai_client is not None:
                result.ai_used = True
                result.status = JobStatus.AI_ANALYZING
                if progress_callback:
                    progress_callback("智能辅助正在分析……", 0.5)
                try:
                    ai_result = self._run_ai_extraction(bundle, mfg, drawing_text_context)
                    result.ai_suggestions = ai_result or {}
                except Exception as e:
                    result.warnings.append(f"智能辅助提取失败：{e}")

            # Quotation mapping
            mapper = QuotationMapper()
            qf = mapper.map(
                mfg,
                geo,
                dimensions_raw=confirmed_dimensions,
                allow_drawing_extent_estimates=False,
            )

            if progress_callback:
                progress_callback("正在计算报价……", 0.7)

            # Pricing
            items: list[QuoteItem] = []
            for mq in qf.machining:
                items.extend(resolver.resolve_machining(mq))
            for fq in qf.frames:
                items.extend(resolver.resolve_frame(fq))
            for sq in qf.sheet_metal:
                items.extend(resolver.resolve_sheet_metal(sq))
            for aq in qf.assemblies:
                items.extend(resolver.resolve_assembly(aq))
            if mfg.welds:
                items.append(make_unknown_item(
                    "process",
                    "焊接加工",
                    "图纸识别到焊接要求，但缺少可发布的焊接费率或可靠焊缝工程量",
                    quantity=1,
                    unit="项",
                ))

            ai_processes: list[dict[str, Any]] = []
            agent_reviews: dict[str, Any] = {}
            ai_geometry: dict[str, Any] = {}
            ai_orchestrator: MultiAgentReviewOrchestrator | None = None
            base_items_for_ai = [item.model_copy(deep=True) for item in items]
            if use_ai and self._ai_client is not None:
                try:
                    if progress_callback:
                        progress_callback("AI 正在并行理解备注与判断工艺……", 0.55)
                    process_rate_context: dict[str, dict[str, Any]] = {}
                    for process_name in ("CNC", "銑床", "車床", "磨床", "鉗工", "放電", "快絲", "慢絲"):
                        rate = resolver.lookup("process", process_name)
                        if rate is not None and rate.unit_price > 0:
                            process_rate_context[process_name] = {
                                "每小时工价": rate.unit_price,
                                "价格来源": rate.resolution_source,
                            }
                    ai_geometry = {
                        "孔数量": mfg.total_holes,
                        "螺纹数量": mfg.total_threads,
                        "钣金候选": bool(mfg.sheet_metal_parts),
                        "焊接候选": bool(mfg.welds),
                        "型材候选": bool(mfg.frames or mfg.structure_assemblies),
                        "零件规格尺寸": confirmed_dimension_values,
                        "外形尺寸": confirmed_dimension_values,
                        "图纸几何范围": (
                            [geo.bounding_box.length, geo.bounding_box.width]
                            if geo.bounding_box else None
                        ),
                        "几何实体数量": len(drawing.raw_entities),
                        "可用工艺小时费率": process_rate_context,
                    }
                    ai_orchestrator = MultiAgentReviewOrchestrator(self._ai_client)
                    agent_reviews = ai_orchestrator.analyze_before_pricing(
                        drawing_number=bundle.drawing_number,
                        texts=drawing_text_context,
                        geometry=ai_geometry,
                    )
                    ai_processes = agent_reviews["工艺规划智能体"]
                    items, ai_processes = self._apply_ai_process_suggestions(
                        base_items_for_ai,
                        ai_processes,
                        resolver,
                        drawing_text_context,
                        result.warnings,
                    )
                    if ai_processes:
                        result.ai_used = True
                        result.ai_suggestions = dict(result.ai_suggestions or {})
                        result.ai_suggestions["processes"] = ai_processes
                    result.ai_suggestions["agents"] = agent_reviews
                except Exception as exc:
                    result.warnings.append(f"智能辅助工艺判断失败：{exc}")

            calculated_itemized_total = round(
                sum(item.amount for item in items if item.source != PriceSource.U), 2
            )
            surface_treatment = (
                mfg.surface_treatment.raw_text.value if mfg.surface_treatment else None
            )
            calibrated_item = resolver.resolve_feature_calibrated_part(
                # The reference model must use the same unambiguous part size as
                # formal pricing.  Do not let another dimension string or the
                # drawing extent select a different model input.
                texts=[confirmed_dimensions] if confirmed_dimensions else [],
                material=(
                    mfg.material.normalized.value
                    if mfg.material and mfg.material.normalized
                    else None
                ),
                surface_treatment=surface_treatment,
                calculated_reference_total=calculated_itemized_total,
            )
            calibration_reference_item = calibrated_item
            unknown_before_calibration = [
                item for item in items if item.source == PriceSource.U
            ]
            if calibrated_item is not None and unknown_before_calibration:
                target = unknown_before_calibration[0]
                target.note = (
                    f"{target.note or ''} 图纸特征模型整件参考价："
                    f"{calibrated_item.amount:.2f}元；仅供审核，不计入正式总价。"
                ).strip()
                target.evidence = "；".join(
                    evidence
                    for evidence in (target.evidence, calibrated_item.evidence)
                    if evidence
                )
            if not items:
                items = [
                    QuoteItem(
                        line_id=f"U-CAL-{datetime.now(timezone.utc).strftime('%H%M%S%f')}",
                        category="other",
                        name="整件价格待确认",
                        source=PriceSource.U,
                        confidence=QuoteConfidence.UNCERTAIN,
                        note="图纸中缺少可用于特征校准的材料或整体尺寸。",
                    )
                ]

            if use_ai and self._ai_client is not None:
                unknown_items = [item for item in items if item.source == PriceSource.U]
                if unknown_items:
                    try:
                        if progress_callback:
                            progress_callback("AI 正在估算待确认价格……", 0.72)
                        estimates = self._run_ai_price_estimates(
                            bundle,
                            unknown_items,
                            drawing_text_context,
                        )
                        result.ai_suggestions = dict(result.ai_suggestions or {})
                        result.ai_suggestions["price_estimates"] = estimates
                    except Exception as exc:
                        result.warnings.append(f"智能辅助估价失败：{exc}")

            # Quote builder
            builder = QuoteBuilder()
            feat_conf = mfg.material.confidence if mfg.material else None
            quote = builder.build(
                quote_id=result.job_id,
                drawing_id=bundle.drawing_number,
                part_number=bundle.drawing_number,
                part_name=bundle.drawing_number,
                material=mfg.material.normalized.value
                if mfg.material and mfg.material.normalized
                else None,
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

            built_in_category = (
                PartCategory.WELDMENT.value
                if mfg.welds
                else PartCategory.SHEET_METAL.value
                if qf.sheet_metal
                else PartCategory.FRAME_ASSEMBLY.value
                if qf.frames or qf.assemblies
                else PartCategory.MACHINING.value
            )
            category_result = agent_reviews.get("零件分类智能体") or {}
            category_candidate = str(category_result.get("part_category") or "")
            category_confidence = float(category_result.get("confidence", 0) or 0)
            if (
                category_candidate in {item.value for item in PartCategory}
                and category_confidence >= 0.6
            ):
                selected_category = category_candidate
                category_source = (
                    "BUILTIN_CONSISTENCY_CORRECTED"
                    if category_result.get("status") == "CONSISTENCY_CORRECTED"
                    else "BUILTIN_DEEPSEEK_SKILL"
                )
                category_evidence = list(category_result.get("evidence") or [])
                if category_source == "BUILTIN_CONSISTENCY_CORRECTED":
                    result.warnings.append(
                        "零件分类与工艺规划冲突，已按制造证据完成一致性校正。"
                    )
            else:
                selected_category = built_in_category
                category_source = "BUILTIN_RULE_FALLBACK"
                category_confidence = 1.0
                category_evidence = ["AI 分类无有效结果，按几何与制造特征规则回退"]
                category_result = {
                    "part_category": selected_category,
                    "category_name": CATEGORY_NAMES_ZH[PartCategory(selected_category)],
                    "confidence": category_confidence,
                    "evidence": category_evidence,
                    "alternatives": [],
                    "status": "RULE_FALLBACK",
                }
                agent_reviews["零件分类智能体"] = category_result

            result.feature_summary = {
                "bounding_box": (
                    confirmed_dimensions.replace("*", "x") + " mm"
                    if confirmed_dimensions
                    else f"{bbox.length:.0f}x{bbox.width:.0f} mm"
                    if bbox
                    else "-"
                ),
                "drawing_extent": (
                    f"{bbox.length:.0f}x{bbox.width:.0f} mm" if bbox else "-"
                ),
                "mfg_holes": mfg.total_holes,
                "mfg_threads": mfg.total_threads,
                "frames": len(mfg.frames),
                "assemblies": len(mfg.structure_assemblies),
                "quotation_route": (
                    selected_category
                ),
                "part_category": selected_category,
                "part_category_source": category_source,
                "part_category_confidence": category_confidence,
                "part_category_evidence": category_evidence,
                "accessories": len(mfg.structure_accessories),
                "welds": len(mfg.welds),
                "weight": f"{weight_kg:.1f} kg" if weight_kg else "-",
                "weight_resolution": next(
                    (
                        mq.material_calculation.weight_source
                        for mq in qf.machining
                        if mq.material_calculation is not None
                    ),
                    "UNKNOWN",
                ),
                "material_dimensions": confirmed_dimensions or "-",
                "itemized_subtotal": f"{calculated_itemized_total:.2f} 元",
                "feature_calibration_reference": (
                    f"{calibration_reference_item.amount:.2f} 元（仅供审核，不计入正式合计）"
                    if calibration_reference_item is not None
                    else "-"
                ),
            }

            result.quote = quote
            result.tax = TaxResult.calculate(quote.items)

            if use_ai and self._ai_client is not None and agent_reviews:
                try:
                    if progress_callback:
                        progress_callback("AI 正在审核分项价格……", 0.84)
                    ai_orchestrator = ai_orchestrator or MultiAgentReviewOrchestrator(
                        self._ai_client
                    )
                    agent_reviews = ai_orchestrator.audit_after_pricing(
                        bundle.drawing_number,
                        drawing_text_context,
                        [QuoteJobResult._item_to_dict(item) for item in quote.items],
                        agent_reviews,
                    )
                    first_audit = agent_reviews.get("价格审核智能体")
                    audit_invalid = ai_orchestrator.audit_failed(first_audit)
                    audit_has_actions = ai_orchestrator.audit_requests_correction(
                        first_audit
                    )
                    if audit_invalid or audit_has_actions:
                        if progress_callback:
                            progress_callback(
                                "价格审核无有效结果，正在重跑前置 Skill……", 0.87
                            )
                        refreshed = ai_orchestrator.retry_dependencies(
                            bundle.drawing_number,
                            drawing_text_context,
                            ai_geometry,
                            requested_actions=list((first_audit or {}).get("actions") or []),
                        )
                        if refreshed:
                            retry_processes = refreshed.get("工艺规划智能体") or []
                            if retry_processes:
                                rebuilt_items, retry_processes = (
                                    self._apply_ai_process_suggestions(
                                        base_items_for_ai,
                                        retry_processes,
                                        resolver,
                                        drawing_text_context,
                                        result.warnings,
                                    )
                                )
                                current_by_line = {
                                    item.line_id: item for item in quote.items
                                }
                                items = [
                                    current_by_line.get(item.line_id, item).model_copy(
                                        deep=True
                                    )
                                    if item.category != "process"
                                    else item
                                    for item in rebuilt_items
                                ]
                                quote = builder.build(
                                    quote_id=result.job_id,
                                    drawing_id=bundle.drawing_number,
                                    part_number=bundle.drawing_number,
                                    part_name=bundle.drawing_number,
                                    material=(
                                        mfg.material.normalized.value
                                        if mfg.material and mfg.material.normalized
                                        else None
                                    ),
                                    items=items,
                                    feature_confidence=feat_conf,
                                    price_version=resolver.price_version,
                                    rule_version="1.0",
                                )
                                result.quote = quote
                                result.tax = TaxResult.calculate(quote.items)
                                ai_processes = retry_processes
                                result.ai_used = True
                                result.ai_suggestions["processes"] = retry_processes
                                result.feature_summary["itemized_subtotal"] = (
                                    f"{sum(item.amount for item in quote.items if item.source != PriceSource.U):.2f} 元"
                                )

                            retry_category = refreshed.get("零件分类智能体") or {}
                            retry_category_value = str(
                                retry_category.get("part_category") or ""
                            )
                            retry_category_confidence = float(
                                retry_category.get("confidence", 0) or 0
                            )
                            if (
                                retry_category_value
                                in {item.value for item in PartCategory}
                                and retry_category_confidence >= 0.6
                            ):
                                result.feature_summary["part_category"] = (
                                    retry_category_value
                                )
                                result.feature_summary["part_category_source"] = (
                                    "BUILTIN_CONSISTENCY_CORRECTED_RETRY"
                                    if retry_category.get("status")
                                    == "CONSISTENCY_CORRECTED"
                                    else "BUILTIN_DEEPSEEK_SKILL_RETRY"
                                )
                                result.feature_summary["part_category_confidence"] = (
                                    retry_category_confidence
                                )
                                result.feature_summary["part_category_evidence"] = list(
                                    retry_category.get("evidence") or []
                                )
                                result.feature_summary["quotation_route"] = (
                                    retry_category_value
                                )

                            agent_reviews = ai_orchestrator.audit_after_pricing(
                                bundle.drawing_number,
                                drawing_text_context,
                                [
                                    QuoteJobResult._item_to_dict(item)
                                    for item in quote.items
                                ],
                                refreshed,
                            )
                            result.ai_suggestions["dependency_retry"] = {
                                "trigger": (
                                    "PRICE_AUDIT_INVALID_RESULT"
                                    if audit_invalid
                                    else "PRICE_AUDIT_ACTIONS"
                                ),
                                "attempts": 1,
                                "requested_actions": list(
                                    (first_audit or {}).get("actions") or []
                                ),
                                "status": (
                                    "RECOVERED"
                                    if not ai_orchestrator.audit_failed(
                                        agent_reviews.get("价格审核智能体")
                                    )
                                    else "FAILED"
                                ),
                            }
                    result.ai_suggestions["agents"] = agent_reviews
                    supervisor = agent_reviews["风险汇总智能体"]
                    result.feature_summary["agent_review_summary"] = supervisor["summary"]
                    result.feature_summary["agent_review_verdict"] = supervisor["verdict"]
                except Exception as exc:
                    result.warnings.append(f"多智能体价格审核失败：{exc}")

            # Determine status
            unresolved_weldment_weight = any(
                mq.material_calculation is not None
                and mq.material_calculation.weight_source == "UNRESOLVED_WELDMENT_STRUCTURE"
                for mq in qf.machining
            )
            if unresolved_weldment_weight:
                result.status = JobStatus.REVIEW_REQUIRED
                result.warnings.append("焊接結構無法由2D圖可靠分解重量，需人工審核")
            elif quote.unknown_count == 0:
                result.status = JobStatus.COMPLETE
            elif quote.unknown_count > 0 and quote.total > 0:
                result.status = JobStatus.REVIEW_REQUIRED
            else:
                result.status = JobStatus.INCOMPLETE
            if any(item.source == PriceSource.AI for item in quote.items):
                result.status = JobStatus.REVIEW_REQUIRED
                quote.quotation_status = JobStatus.REVIEW_REQUIRED
                result.warnings.append(
                    "报价包含已计入合计的 AI 估算价格，必须醒目标注并经人工确认。"
                )
            if calibration_reference_item is not None:
                result.warnings.append(
                    "图纸特征模型只提供整件审核参考，不是正式价格且不计入合计；"
                    "正式报价按材料、加工、表面处理及其他费用逐项计算。"
                )
            if ai_processes:
                result.status = JobStatus.REVIEW_REQUIRED
                result.warnings.append(
                    "加工工艺包含 AI 判断结果，已使用公司费率形成分项，正式发布前必须人工确认。"
                )
            if agent_reviews.get("风险汇总智能体", {}).get("requires_human_review"):
                result.status = JobStatus.REVIEW_REQUIRED
                result.warnings.append("多智能体审核发现风险，请在价格发布前完成人工审核。")
            ai_error = getattr(self._ai_client, "last_error", None)
            if use_ai and ai_error:
                result.warnings.append(f"{ai_error}；后续 AI 步骤已快速回退内置规则。")
            if self._external_skill_router is not None and external_config is not None:
                category = PartCategory(result.feature_summary["part_category"])
                pre_category_execution = self._external_skill_router.execute(
                    result,
                    external_config,
                    only_steps={
                        SkillStep.DOCUMENT_UNDERSTANDING,
                        SkillStep.PART_CLASSIFICATION,
                    },
                )
                self._apply_external_part_classification(
                    result, pre_category_execution
                )
                category = PartCategory(result.feature_summary["part_category"])
                effective_route = external_config.route_for(category)
                if effective_route.mode == SkillRoutingMode.DISTRIBUTED:
                    external = self._external_skill_router.execute(
                        result,
                        external_config,
                        skip_steps={
                            SkillStep.DOCUMENT_UNDERSTANDING,
                            SkillStep.PART_CLASSIFICATION,
                        },
                    )
                    self._apply_external_skill_execution(result, external, require_quote=False)
                elif effective_route.mode == SkillRoutingMode.FULL_QUOTATION:
                    selected = next(
                        (
                            skill
                            for skill in external_config.skills
                            if skill.skill_id == effective_route.full_skill_id
                        ),
                        None,
                    )
                    if selected is not None:
                        external = self._external_skill_router.execute(
                            result,
                            external_config,
                            skip_steps={
                                SkillStep.DOCUMENT_UNDERSTANDING,
                                SkillStep.PART_CLASSIFICATION,
                            },
                        )
                        self._apply_external_skill_execution(
                            result, external, require_quote=True
                        )

        except FileNotFoundError as e:
            result.status = JobStatus.PARSE_FAILED
            result.errors.append(f"找不到文件：{e}")
        except Exception as e:
            result.status = JobStatus.QUOTE_FAILED
            result.errors.append(f"報價處理失敗：{e}")
            result.errors.append(traceback.format_exc())

        result.processing_time_ms = (time.time() - t0) * 1000
        return result

    def _apply_external_skill_execution(
        self, result: QuoteJobResult, execution: Any, *, require_quote: bool
    ) -> bool:
        """Validate external output, apply a complete quote, or retain audited step results."""

        result.warnings.extend(execution.warnings)
        if getattr(execution, "debug_trace", None):
            result.ai_suggestions = dict(result.ai_suggestions or {})
            existing_trace = list(result.ai_suggestions.get("skill_debug_trace") or [])
            merged = {
                (entry.get("step"), entry.get("provider")): entry
                for entry in existing_trace + list(execution.debug_trace)
            }
            order = {step.value: index for index, step in enumerate(SkillStep)}
            result.ai_suggestions["skill_debug_trace"] = sorted(
                merged.values(), key=lambda entry: order.get(entry.get("step"), 999)
            )
        if not execution.responses:
            return False
        result.ai_suggestions = dict(result.ai_suggestions or {})
        result.ai_suggestions["external_skills"] = execution.responses
        self._remember_external_skill_chain(result, execution.responses)
        applied = False
        partial_applied = False
        for entry in execution.responses:
            response = entry["response"]
            result.warnings.extend(response.get("warnings_zh", []))
            completed = set(response.get("completed_steps", []))
            if SkillStep.TIME_ESTIMATION.value in completed:
                partial_applied = (
                    self._apply_external_time_results(result, entry) or partial_applied
                )
            quote_payload = response.get("quotation")
            may_replace = (
                entry["execution_mode"] == SkillRoutingMode.FULL_QUOTATION.value
                or "QUOTE_ASSEMBLY" in completed
            )
            if quote_payload and may_replace:
                try:
                    quote = self._quote_from_external_payload(
                        result, quote_payload, execution.price_records
                    )
                except Exception as exc:
                    result.warnings.append(
                        f"外接 Skill 报价校验失败，保留内置报价：{exc}"
                    )
                    continue
                result.quote = quote
                result.tax = TaxResult.calculate(quote.items)
                review = response.get("review") or {}
                if quote.unknown_count:
                    result.status = JobStatus.REVIEW_REQUIRED
                elif review.get("decision") == "PASS":
                    result.status = JobStatus.COMPLETE
                else:
                    result.status = JobStatus.REVIEW_REQUIRED
                result.feature_summary = dict(result.feature_summary or {})
                result.feature_summary["external_skill"] = (
                    f"{entry['skill']['name_zh']} {entry['skill']['skill_version']}"
                )
                applied = True
        if partial_applied:
            result.tax = TaxResult.calculate(result.quote.items)
            result.status = JobStatus.REVIEW_REQUIRED
            result.warnings.append(
                "外接工时 Skill/智能体结果已按具体工艺更新报价，保留公司小时费率；发布前请人工确认。"
            )
        elif not applied and execution.responses:
            result.status = JobStatus.REVIEW_REQUIRED
            result.warnings.append("外接 Skill 已参与所选步骤，结果已保留供人工审核。")
        if require_quote and not applied:
            result.warnings.append("整套外接 Skill 未返回有效完整报价，已回退内置流程。")
        return applied

    @staticmethod
    def _apply_external_time_results(result: QuoteJobResult, entry: dict[str, Any]) -> bool:
        """Apply process-scoped hours while preserving the approved internal hourly rate."""

        if result.quote is None:
            return False
        response = entry.get("response") or {}
        raw = (response.get("step_results") or {}).get(
            SkillStep.TIME_ESTIMATION.value
        )
        if isinstance(raw, dict):
            candidates = raw.get("processes") or raw.get("time_items") or raw.get("items") or []
            if not candidates and any(key in raw for key in ("code", "process_code")):
                candidates = [raw]
        elif isinstance(raw, list):
            candidates = raw
        else:
            return False
        allowed = {str(item).upper() for item in entry.get("process_codes") or []}
        aliases = {
            "CNC": ("CNC", "加工中心", "數控", "数控"),
            "LATHE": ("車床", "车床", "車削", "车削"),
            "MILL": ("銑床", "铣床", "銑削", "铣削"),
            "GRIND": ("磨床", "磨削"),
            "FITTER": ("鉗工", "钳工"),
            "EDM": ("放電", "放电", "EDM"),
            "WIRE_CUT": ("快絲", "快丝", "線切割", "线切割"),
            "SLOW_WIRE": ("慢絲", "慢丝"),
            "LASER_CUT": ("激光", "雷射"),
            "BENDING": ("折彎", "折弯"),
            "WELDING": ("焊接", "焊工"),
            "SURFACE": ("表面處理", "表面处理"),
        }
        items = [item.model_copy(deep=True) for item in result.quote.items]
        changed = False
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            code = str(
                candidate.get("code") or candidate.get("process_code") or ""
            ).upper()
            if code not in aliases or (allowed and code not in allowed):
                continue
            try:
                hours = float(
                    candidate.get("estimated_hours")
                    if candidate.get("estimated_hours") is not None
                    else candidate.get("hours")
                )
            except (TypeError, ValueError):
                continue
            if not 0 < hours <= 200:
                continue
            for item in items:
                if item.category != "process" or not any(
                    alias.casefold() in item.name.casefold() for alias in aliases[code]
                ):
                    continue
                item.quantity = round(hours, 4)
                item.unit = "hour"
                item.amount = round(item.quantity * item.unit_price, 2)
                item.confidence = QuoteConfidence.UNCERTAIN
                item.resolution_source = "EXTERNAL_SKILL_TIME_ESTIMATION_REVIEW_REQUIRED"
                item.note = (
                    f"外接 Skill/智能体按 {code} 估算单件工时；"
                    "小时费率继续使用公司已发布价格，需人工确认。"
                )
                changed = True
        if changed:
            payload = result.quote.model_dump(mode="python")
            payload["items"] = [item.model_dump(mode="python") for item in items]
            result.quote = Quote.model_validate(payload)
        return changed

    def _apply_external_part_classification(
        self, result: QuoteJobResult, execution: Any
    ) -> bool:
        """Apply a validated global classification before category-specific routing."""
        result.warnings.extend(execution.warnings)
        if getattr(execution, "debug_trace", None):
            result.ai_suggestions = dict(result.ai_suggestions or {})
            result.ai_suggestions["skill_debug_trace"] = list(execution.debug_trace)
        if execution.responses:
            self._remember_external_skill_chain(result, execution.responses)
        for entry in execution.responses:
            response = entry.get("response") or {}
            step_result = (response.get("step_results") or {}).get(
                SkillStep.PART_CLASSIFICATION.value
            )
            if not isinstance(step_result, dict):
                continue
            category = str(step_result.get("part_category") or "").upper()
            try:
                confidence = float(step_result.get("confidence", 0))
            except (TypeError, ValueError):
                confidence = 0.0
            if category not in {item.value for item in PartCategory} or confidence < 0.6:
                result.warnings.append(
                    "外接零件分类 Skill 结果无效或可信度低于 0.6，已保留内置分类。"
                )
                continue
            process_context = list(
                (result.ai_suggestions or {}).get("processes") or []
            )
            if result.feature_summary.get("part_category") == "MACHINING":
                process_context.append({"code": "MACHINING"})
            reconciled = MultiAgentReviewOrchestrator._reconcile_category(
                {
                    "part_category": category,
                    "confidence": confidence,
                    "evidence": list(step_result.get("evidence") or []),
                },
                process_context,
                [
                    str(item.get("text") or "")
                    for item in result.document_texts
                    if isinstance(item, dict)
                ],
            )
            applied_category = str(reconciled.get("part_category") or category)
            corrected = applied_category != category
            result.feature_summary["part_category"] = applied_category
            result.feature_summary["quotation_route"] = applied_category
            result.feature_summary["part_category_source"] = (
                "EXTERNAL_SKILL_CONSISTENCY_CORRECTED"
                if corrected
                else "EXTERNAL_SKILL"
            )
            result.feature_summary["part_category_confidence"] = float(
                reconciled.get("confidence", confidence)
            )
            result.feature_summary["part_category_evidence"] = list(
                reconciled.get("evidence") or []
            )
            if corrected:
                result.warnings.append(
                    "外接零件分类与工艺及图纸证据冲突，已执行一致性校正，"
                    "板状加工件不会按钣金件路由。"
                )
            result.ai_suggestions = dict(result.ai_suggestions or {})
            result.ai_suggestions["external_part_classification"] = entry
            return True
        return False

    @staticmethod
    def _remember_external_skill_chain(
        result: QuoteJobResult, responses: list[dict[str, Any]]
    ) -> None:
        """Persist compact upstream Skill outputs for later dependency phases."""
        result.ai_suggestions = dict(result.ai_suggestions or {})
        chain = list(result.ai_suggestions.get("external_skill_chain") or [])
        for entry in responses:
            response = entry.get("response") or {}
            skill = entry.get("skill") or {}
            chain.append(
                {
                    "skill_id": skill.get("skill_id") or response.get("skill_id"),
                    "skill_version": skill.get("skill_version")
                    or response.get("skill_version"),
                    "completed_steps": list(response.get("completed_steps") or []),
                    "step_results": dict(response.get("step_results") or {}),
                    "quotation": response.get("quotation"),
                    "review": response.get("review"),
                }
            )
        result.ai_suggestions["external_skill_chain"] = chain[-12:]

    @staticmethod
    def _quote_from_external_payload(
        result: QuoteJobResult,
        payload: dict[str, Any],
        price_records: dict[str, dict[str, Any]],
    ) -> Quote:
        items: list[QuoteItem] = []
        for raw in payload.get("items", []):
            source_code = raw.get("source")
            confidence_value = float(raw.get("confidence", 0))
            confidence = (
                QuoteConfidence.HIGH
                if confidence_value >= 0.85
                else QuoteConfidence.MEDIUM
                if confidence_value >= 0.6
                else QuoteConfidence.UNCERTAIN
            )
            evidence = "；".join(
                str(item.get("description_zh", ""))
                for item in raw.get("evidence", [])
                if item.get("description_zh")
            )
            if source_code == "C":
                company_price_id = raw.get("company_price_id")
                record = price_records.get(company_price_id)
                if record is None:
                    raise ValueError(f"费用行 {raw.get('line_id')} 未引用有效公司正式价格")
                if abs(float(raw.get("unit_price", 0)) - float(record["unit_price"])) > 0.001:
                    raise ValueError(f"费用行 {raw.get('line_id')} 擅自修改公司正式单价")
                quantity = float(raw.get("quantity", 0))
                unit_price = float(record["unit_price"])
                item = QuoteItem(
                    line_id=str(raw["line_id"]),
                    category=str(raw["category"]),
                    name=str(raw["name_zh"]),
                    quantity=quantity,
                    unit=str(raw["unit"]),
                    unit_price=unit_price,
                    amount=round(quantity * unit_price, 2),
                    source=PriceSource.C,
                    confidence=confidence,
                    evidence=evidence,
                    company_price_id=company_price_id,
                    price_version_id=record.get("price_version_id"),
                    origin_supplier_id=record.get("origin_supplier_id"),
                    origin_price_record_id=record.get("origin_price_record_id"),
                    price_basis=record.get("price_basis"),
                    resolution_source="EXTERNAL_SKILL_VALIDATED_COMPANY_PRICE",
                )
            elif source_code in {"AI", "U"}:
                reference = raw.get("ai_reference") or {}
                estimated_unit_price = float(reference.get("estimated_unit_price") or 0)
                quantity = float(raw.get("quantity", 0))
                include_ai = estimated_unit_price > 0 and quantity > 0
                item = QuoteItem(
                    line_id=str(raw["line_id"]),
                    category=str(raw["category"]),
                    name=str(raw["name_zh"]),
                    quantity=float(raw.get("quantity", 0)),
                    unit=str(raw.get("unit", "ST")),
                    unit_price=estimated_unit_price if include_ai else 0,
                    amount=round(quantity * estimated_unit_price, 2) if include_ai else 0,
                    source=PriceSource.AI if include_ai else PriceSource.U,
                    confidence=QuoteConfidence.UNCERTAIN,
                    evidence=evidence,
                    note=(
                        "外接 Skill 的 AI 估算已计入报价合计，必须人工确认；"
                        + str(raw.get("review_reason_zh") or "尚未成为公司核准价格")
                        if include_ai
                        else str(raw.get("review_reason_zh") or "外接 Skill 价格待确认")
                    ),
                    ai_estimated_unit_price=reference.get("estimated_unit_price"),
                    ai_estimated_amount=reference.get("estimated_amount"),
                    ai_estimated_unit=reference.get("unit"),
                    ai_estimate_reason=reference.get("reason_zh"),
                    ai_estimate_confidence=reference.get("confidence"),
                    quote_price_source="AI" if include_ai else "U",
                    resolution_source=(
                        "EXTERNAL_SKILL_AI_INCLUDED_REVIEW_REQUIRED"
                        if include_ai
                        else "EXTERNAL_SKILL_UNKNOWN"
                    ),
                )
            else:
                raise ValueError("外接 Skill 不得直接生成未经本系统验证的正式价格来源")
            items.append(item)
        if not items:
            raise ValueError("外接 Skill 没有返回报价分项")
        previous = result.quote
        return QuoteBuilder().build(
            quote_id=result.job_id,
            drawing_id=result.drawing_number,
            part_number=result.drawing_number,
            part_name=(previous.part_name if previous else result.drawing_number),
            material=payload.get("material_code") or (previous.material if previous else None),
            items=items,
            price_version=next(
                (item.price_version_id for item in items if item.price_version_id), None
            ),
            rule_version="external-skill-protocol-1.0",
        )

    # ------------------------------------------------------------------
    # AI extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_ai_process_suggestions(
        base_items: list[QuoteItem],
        suggestions: list[dict[str, Any]],
        resolver: PricingResolver,
        drawing_texts: list[str],
        warnings: list[str],
    ) -> tuple[list[QuoteItem], list[dict[str, Any]]]:
        """Apply AI processes deterministically so a dependency retry can rebuild prices."""
        items = [item.model_copy(deep=True) for item in base_items]
        processes = [dict(process) for process in suggestions if isinstance(process, dict)]
        process_names = {
            process.get("process_name") for process in processes if process.get("process_name")
        }
        explicit_cnc = any(
            re.search(r"(?i)(?<![A-Z])CNC(?![A-Z])|数控|數控|加工中心", text)
            for text in drawing_texts
        )
        if explicit_cnc and "銑床" in process_names:
            processes = [
                process for process in processes if process.get("process_name") != "銑床"
            ]
            warnings.append(
                "图纸文字明确要求 CNC/数控/加工中心，未采用相冲突的普通铣床替代建议。"
            )
        elif "CNC" in process_names and "銑床" in process_names:
            alternatives = {
                process["process_name"]: process
                for process in processes
                if process.get("process_name") in {"CNC", "銑床"}
            }
            evaluated: dict[str, float] = {}
            for process_name, process in alternatives.items():
                rate = resolver.lookup("process", process_name)
                if rate is not None and rate.unit_price > 0:
                    evaluated[process_name] = round(
                        float(process.get("estimated_hours", 0)) * rate.unit_price, 2
                    )
            if len(evaluated) == 2:
                selected_name = min(evaluated, key=evaluated.get)
                rejected_name = "銑床" if selected_name == "CNC" else "CNC"
                processes = [
                    process
                    for process in processes
                    if process.get("process_name") != rejected_name
                ]
                if selected_name == "銑床":
                    items = [
                        item
                        for item in items
                        if not (
                            item.category == "process" and item.name.startswith("CNC ")
                        )
                    ]
                warnings.append(
                    "AI 给出 CNC/铣床可行工时后，系统按工时×工价比较："
                    f"CNC {evaluated['CNC']:.2f}元、铣床 {evaluated['銑床']:.2f}元；"
                    f"采用成本较低的{selected_name}，发布前请人工确认工时与可制造性。"
                )
        elif (
            process_names.intersection({"銑床", "車床"})
            and "CNC" not in process_names
            and not explicit_cnc
        ):
            original_count = len(items)
            items = [
                item
                for item in items
                if not (item.category == "process" and item.name.startswith("CNC "))
            ]
            if len(items) < original_count:
                selected = next(
                    process
                    for process in processes
                    if process.get("process_name") in {"銑床", "車床"}
                )
                selected_rate = resolver.lookup("process", selected["process_name"])
                selected_cost = (
                    float(selected.get("estimated_hours", 0)) * selected_rate.unit_price
                    if selected_rate is not None
                    else 0
                )
                warnings.append(
                    (
                        "AI 判断普通铣床足以完成当前加工，"
                        if selected["process_name"] == "銑床"
                        else f"AI 判断{selected['process_name']}足以完成当前加工，"
                    )
                    + "已撤销仅因孔位自动产生的通用 CNC 项；"
                    f"候选工时×工价约 {selected_cost:.2f} 元，正式发布前请人工确认。"
                )
        existing = {item.name for item in items if item.category == "process"}
        for process in processes:
            adjustment = process.get("hours_adjustment")
            if isinstance(adjustment, dict):
                warnings.append(
                    f"AI 对{process.get('process_name') or process.get('code')}估算 "
                    f"{adjustment.get('ai_hours')} 小时，超过当前单件图纸的合理范围；"
                    f"已按 {adjustment.get('accepted_hours')} 小时计价。"
                    f"原因：{adjustment.get('reason')}。"
                )
            process_name = str(process.get("process_name") or "")
            if not process_name or any(process_name in name for name in existing):
                continue
            item = calc_machining(
                process_name,
                float(process.get("estimated_hours", 0)),
                resolver.lookup,
            )
            item.confidence = QuoteConfidence.UNCERTAIN
            item.note = (
                f"AI 判断工艺，可信度 {float(process.get('confidence', 0)):.0%}；"
                "采用公司已发布小时费率计算，发布前必须人工确认。"
            )
            item.evidence = (
                f"{item.evidence or ''}；AI工艺依据={process.get('evidence') or '未提供'}"
            ).strip("；")
            item.resolution_source = "AI_PROCESS_CLASSIFICATION"
            items.append(item)
            existing.add(item.name)
        return items, processes

    @staticmethod
    def _confirmed_part_dimensions(drawing_texts: list[str]) -> str | None:
        """Return an unambiguous, explicit 3-axis stock-size note.

        Individual drawing dimensions and the overall DXF bounding box are not
        stock dimensions.  Only a complete standalone ``L*W*H`` text is
        accepted.  Multiple different candidates are deliberately rejected so
        that the operator reviews the drawing instead of receiving a guessed
        material weight.
        """
        from quotation.infrastructure.parser.dimension_parser import parse_dimension

        pattern = re.compile(
            r"^\s*(\d+(?:\.\d+)?)\s*[*×xX]\s*"
            r"(\d+(?:\.\d+)?)\s*[*×xX]\s*"
            r"(\d+(?:\.\d+)?)\s*(?:mm)?\s*$",
            re.IGNORECASE,
        )
        candidates: dict[tuple[float, float, float], str] = {}
        for value in drawing_texts:
            text = str(value).strip()
            match = pattern.fullmatch(text)
            if match is None:
                continue
            canonical = "*".join(match.groups())
            parsed = parse_dimension(canonical)
            dimensions = (parsed.length, parsed.width, parsed.height)
            if any(number is None or number <= 0 for number in dimensions):
                continue
            key = tuple(float(number) for number in dimensions)
            candidates[key] = canonical
        if len(candidates) != 1:
            return None
        return next(iter(candidates.values()))

    @staticmethod
    def _document_text_inputs(
        geometry_file_name: str | None,
        drawing_texts: list[str],
    ) -> list[dict[str, Any]]:
        """Preserve note source and confidence for note-understanding Agents."""

        values: list[dict[str, Any]] = []
        for text in drawing_texts[:200]:
            if str(text).strip():
                values.append(
                    {
                        "text": str(text).strip(),
                        "source_file_name": geometry_file_name,
                        "source_kind": "DRAWING_VECTOR_TEXT",
                        "page": None,
                        "entity_id": None,
                        "confidence": 1.0,
                    }
                )
        return values[:200]

    def _run_ai_extraction(
        self,
        bundle: JobBundle,
        mfg: Any,
        drawing_text_context: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Run DeepSeek-assisted extraction for missing fields."""
        if self._ai_client is None:
            return None

        # Collect context for AI
        text_context = list(drawing_text_context or [])

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

    def _run_ai_price_estimates(
        self,
        bundle: JobBundle,
        unknown_items: list[QuoteItem],
        context: list[str],
    ) -> list[dict[str, Any]]:
        """Promote valid AI estimates into the quote with mandatory review labels."""
        if self._ai_client is None:
            return []
        payload = [
            {
                "line_id": item.line_id,
                "category": item.category,
                "name": item.name,
                "known_quantity": item.quantity,
                "known_unit": item.unit,
                "unpriced_reason": item.note,
            }
            for item in unknown_items
        ]
        estimates = self._ai_client.estimate_unknown_costs(
            drawing_number=bundle.drawing_number,
            items=payload,
            context=context,
        )
        by_line = {estimate["line_id"]: estimate for estimate in estimates}
        for item in unknown_items:
            estimate = by_line.get(item.line_id)
            if not estimate:
                continue
            item.ai_estimated_unit_price = estimate["unit_price"]
            item.ai_estimated_amount = estimate["amount"]
            item.ai_estimated_unit = estimate["unit"]
            item.ai_estimate_reason = estimate["reason"]
            item.ai_estimate_confidence = estimate["confidence"]
            quantity = float(estimate.get("quantity") or item.quantity or 1)
            if estimate["unit_price"] <= 0 or quantity <= 0:
                continue
            item.quantity = quantity
            item.unit = estimate["unit"]
            item.unit_price = estimate["unit_price"]
            item.amount = round(quantity * estimate["unit_price"], 2)
            item.source = PriceSource.AI
            item.quote_price_source = "AI"
            item.resolution_source = "AI_ESTIMATE_INCLUDED_REVIEW_REQUIRED"
            item.confidence = QuoteConfidence.UNCERTAIN
            item.note = (
                "AI估算价格已计入本次报价合计，尚未成为公司核准价格，必须人工确认；"
                f"{estimate['reason']}"
            )
        return estimates

    # ------------------------------------------------------------------
    # AI health check
    # ------------------------------------------------------------------

    def check_ai_health(self) -> dict[str, Any]:
        """Check AI connectivity."""
        if self._ai_client is None:
            return {"configured": False, "reachable": False, "error": "智能辅助尚未配置"}
        try:
            return self._ai_client.health_check()
        except Exception as e:
            return {"configured": True, "reachable": False, "error": str(e)}
