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

from quotation.domain.quote import PriceSource, Quote, QuoteConfidence, QuoteItem
from quotation.application.external_skill_settings import (
    SkillRoutingMode,
    SkillSourceType,
)
from quotation.infrastructure.dwg.converter import DwgConversionService
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.pdf.reader import PdfReader
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
            if self._resolver is None:
                self._resolver = PricingResolver()
            resolver = self._resolver
            external_config = None
            if self._external_skill_router is not None:
                try:
                    external_config = self._external_skill_router.load_config()
                    if external_config.mode == SkillRoutingMode.FULL_QUOTATION:
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
                pdf_text_context = self._analyze_supplementary_pdfs(bundle, result)
                result.document_texts = self._document_text_inputs(
                    None, [], result.supplementary_analysis
                )
                calibrated_item = resolver.resolve_feature_calibrated_part(
                    texts=pdf_text_context,
                    material=None,
                    surface_treatment=None,
                )
                if calibrated_item is not None:
                    unresolved_item = QuoteItem(
                        line_id=f"U-PDF-{datetime.now(timezone.utc).strftime('%H%M%S%f')}",
                        category="other",
                        name="缺少二维几何，无法生成分项报价",
                        source=PriceSource.U,
                        confidence=QuoteConfidence.UNCERTAIN,
                        note=(
                            f"整件模型参考价为 {calibrated_item.amount:.2f} 元，仅供人工审核；"
                            "没有材料、加工和表面处理分项依据，不计入正式总价。"
                        ),
                        evidence=calibrated_item.evidence,
                    )
                    quote = QuoteBuilder().build(
                        quote_id=result.job_id,
                        drawing_id=bundle.drawing_number,
                        part_number=bundle.drawing_number,
                        part_name=bundle.drawing_number,
                        material=None,
                        items=[unresolved_item],
                        price_version=resolver.price_version,
                        rule_version="1.2",
                    )
                    result.quote = quote
                    result.tax = TaxResult.calculate(quote.items)
                    result.feature_summary = {
                        "quotation_route": "UNITEMIZED_PDF_REFERENCE",
                        "itemized_subtotal": "0.00 元",
                        "feature_calibration_reference": (
                            f"{calibrated_item.amount:.2f} 元（仅供审核，不计入正式合计）"
                        ),
                    }
                    result.status = JobStatus.REVIEW_REQUIRED
                    result.warnings.append(
                        "未找到DWG/DXF几何图，不能生成材料、加工、表面处理分项；"
                        "整件模型金额仅供人工参考，不是正式价格，也不计入正式总价。"
                    )
                    if (
                        self._external_skill_router is not None
                        and external_config is not None
                        and external_config.mode == SkillRoutingMode.FULL_QUOTATION
                    ):
                        selected = next(
                            (
                                skill
                                for skill in external_config.skills
                                if skill.skill_id == external_config.full_skill_id
                            ),
                            None,
                        )
                        if (
                            selected is not None
                            and selected.source_type == SkillSourceType.FOLDER
                        ):
                            external = self._external_skill_router.execute(
                                result, external_config
                            )
                            self._apply_external_skill_execution(
                                result, external, require_quote=True
                            )
                    result.processing_time_ms = (time.time() - t0) * 1000
                    return result
                result.status = JobStatus.UNSUPPORTED
                result.errors.append("找不到可用的DWG或DXF幾何圖紙")
                return result

            if geometry_file.extension.lower() not in (".dxf", ".dwg", ".slddrw", ".sldprt"):
                result.status = JobStatus.UNSUPPORTED
                result.errors.append(f"不支援的幾何圖紙格式：{geometry_file.extension}")
                return result

            parse_path = geometry_file.full_path
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

            if progress_callback:
                progress_callback("正在解析图纸……", 0.1)

            # Read DXF
            reader = DxfReader()
            import_result = reader.read(parse_path)
            drawing = import_result.drawing

            # Feature extraction
            geo_ext = GeometricExtractor()
            geo = geo_ext.extract(drawing.raw_entities)

            mfg_ext = ManufacturingExtractor()
            mfg = mfg_ext.extract(geo)

            pdf_text_context = self._analyze_supplementary_pdfs(bundle, result)
            result.document_texts = self._document_text_inputs(
                geometry_file.file_name,
                list(drawing.raw_text_strings),
                result.supplementary_analysis,
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
                    ai_result = self._run_ai_extraction(bundle, mfg, pdf_text_context)
                    result.ai_suggestions = ai_result or {}
                except Exception as e:
                    result.warnings.append(f"智能辅助提取失败：{e}")

            # Quotation mapping
            mapper = QuotationMapper()
            qf = mapper.map(mfg, geo)

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
            if use_ai and self._ai_client is not None:
                try:
                    agent_reviews = MultiAgentReviewOrchestrator(
                        self._ai_client
                    ).analyze_before_pricing(
                        drawing_number=bundle.drawing_number,
                        texts=list(drawing.raw_text_strings) + pdf_text_context,
                        geometry={
                            "孔数量": mfg.total_holes,
                            "螺纹数量": mfg.total_threads,
                            "钣金候选": bool(mfg.sheet_metal_parts),
                            "焊接候选": bool(mfg.welds),
                            "外形尺寸": (
                                [geo.bounding_box.length, geo.bounding_box.width]
                                if geo.bounding_box else None
                            ),
                        },
                    )
                    ai_processes = agent_reviews["工艺规划智能体"]
                    ai_process_names = {
                        process["process_name"] for process in ai_processes
                    }
                    drawing_texts = list(drawing.raw_text_strings) + pdf_text_context
                    explicit_cnc = any(
                        re.search(r"(?i)(?<![A-Z])CNC(?![A-Z])|数控|數控|加工中心", text)
                        for text in drawing_texts
                    )
                    if explicit_cnc and "銑床" in ai_process_names:
                        ai_processes = [
                            process
                            for process in ai_processes
                            if process["process_name"] != "銑床"
                        ]
                        result.warnings.append(
                            "图纸文字明确要求 CNC/数控/加工中心，未采用相冲突的普通铣床替代建议。"
                        )
                    elif "CNC" in ai_process_names and "銑床" in ai_process_names:
                        ai_processes = [
                            process
                            for process in ai_processes
                            if process["process_name"] != "銑床"
                        ]
                    elif (
                        ai_process_names.intersection({"銑床", "車床"})
                        and "CNC" not in ai_process_names
                        and not explicit_cnc
                    ):
                        original_count = len(items)
                        items = [
                            item
                            for item in items
                            if not (
                                item.category == "process"
                                and item.name.startswith("CNC ")
                            )
                        ]
                        if len(items) < original_count:
                            result.warnings.append(
                                "AI 判断普通铣床足以完成当前加工，已撤销仅因孔位自动产生的通用 CNC 项；正式发布前请人工确认。"
                            )
                    existing = {item.name for item in items if item.category == "process"}
                    for process in ai_processes:
                        process_name = process["process_name"]
                        if any(process_name in name for name in existing):
                            continue
                        item = calc_machining(
                            process_name,
                            process["estimated_hours"],
                            resolver.lookup,
                        )
                        item.confidence = QuoteConfidence.UNCERTAIN
                        item.note = (
                            f"AI 判断工艺，可信度 {process['confidence']:.0%}；"
                            "采用公司已发布小时费率计算，发布前必须人工确认。"
                        )
                        item.evidence = (
                            f"{item.evidence or ''}；AI工艺依据={process['evidence']}"
                        ).strip("；")
                        item.resolution_source = "AI_PROCESS_CLASSIFICATION"
                        items.append(item)
                        existing.add(item.name)
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
                texts=list(drawing.raw_text_strings) + pdf_text_context,
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
                        estimates = self._run_ai_price_estimates(
                            bundle,
                            unknown_items,
                            list(drawing.raw_text_strings) + pdf_text_context,
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

            result.feature_summary = {
                "bounding_box": f"{bbox.length:.0f}x{bbox.width:.0f} mm" if bbox else "-",
                "mfg_holes": mfg.total_holes,
                "mfg_threads": mfg.total_threads,
                "frames": len(mfg.frames),
                "assemblies": len(mfg.structure_assemblies),
                "quotation_route": (
                    "SHEET_METAL" if qf.sheet_metal else "MACHINING"
                ),
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
                    agent_reviews = MultiAgentReviewOrchestrator(
                        self._ai_client
                    ).audit_after_pricing(
                        bundle.drawing_number,
                        list(drawing.raw_text_strings) + pdf_text_context,
                        [QuoteJobResult._item_to_dict(item) for item in quote.items],
                        agent_reviews,
                    )
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
            if self._external_skill_router is not None and external_config is not None:
                if external_config.mode == SkillRoutingMode.DISTRIBUTED:
                    external = self._external_skill_router.execute(result, external_config)
                    self._apply_external_skill_execution(result, external, require_quote=False)
                elif external_config.mode == SkillRoutingMode.FULL_QUOTATION:
                    selected = next(
                        (
                            skill
                            for skill in external_config.skills
                            if skill.skill_id == external_config.full_skill_id
                        ),
                        None,
                    )
                    if selected is not None and selected.source_type == SkillSourceType.FOLDER:
                        external = self._external_skill_router.execute(result, external_config)
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
        if not execution.responses:
            return False
        result.ai_suggestions = dict(result.ai_suggestions or {})
        result.ai_suggestions["external_skills"] = execution.responses
        applied = False
        for entry in execution.responses:
            response = entry["response"]
            result.warnings.extend(response.get("warnings_zh", []))
            completed = set(response.get("completed_steps", []))
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
        if not applied and execution.responses:
            result.status = JobStatus.REVIEW_REQUIRED
            result.warnings.append("外接 Skill 已参与所选步骤，结果已保留供人工审核。")
        if require_quote and not applied:
            result.warnings.append("整套外接 Skill 未返回有效完整报价，已回退内置流程。")
        return applied

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
                item = QuoteItem(
                    line_id=str(raw["line_id"]),
                    category=str(raw["category"]),
                    name=str(raw["name_zh"]),
                    quantity=float(raw.get("quantity", 0)),
                    unit=str(raw.get("unit", "ST")),
                    unit_price=0,
                    amount=0,
                    source=PriceSource.U,
                    confidence=QuoteConfidence.UNCERTAIN,
                    evidence=evidence,
                    note=str(raw.get("review_reason_zh") or "外接 Skill 参考价待人工确认"),
                    ai_estimated_unit_price=reference.get("estimated_unit_price"),
                    ai_estimated_amount=reference.get("estimated_amount"),
                    ai_estimated_unit=reference.get("unit"),
                    ai_estimate_reason=reference.get("reason_zh"),
                    ai_estimate_confidence=reference.get("confidence"),
                    resolution_source="EXTERNAL_SKILL_AI_REFERENCE",
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

    def _analyze_supplementary_pdfs(
        self,
        bundle: JobBundle,
        result: QuoteJobResult,
    ) -> list[str]:
        """Parse paired PDFs and return bounded text context for optional AI."""
        contexts: list[str] = []
        reader = PdfReader()
        for source in bundle.pdf_sources:
            imported = reader.read(source.full_path)
            drawing = imported.drawing
            texts = list(drawing.raw_text_strings) if drawing is not None else []
            result.supplementary_analysis.append(
                {
                    "file_name": source.file_name,
                    "status": imported.import_status,
                    "pdf_confidence": imported.pdf_confidence,
                    "text_count": len(texts),
                    "text_items": texts[:200],
                    "errors": list(imported.errors),
                }
            )
            if imported.is_failed:
                detail = "；".join(imported.errors) or "未知錯誤"
                result.warnings.append(f"PDF輔助解析失敗（{source.file_name}）：{detail}")
                continue
            content = "\n".join(texts).strip()
            contexts.append(f"[PDF] {source.file_name}\n{content}"[:12000])
        return contexts

    @staticmethod
    def _document_text_inputs(
        geometry_file_name: str | None,
        drawing_texts: list[str],
        supplementary_analysis: list[dict[str, Any]],
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
        for analysis in supplementary_analysis:
            raw_confidence = analysis.get("pdf_confidence")
            confidence = (
                {"high": 0.95, "medium": 0.75, "low": 0.5}.get(
                    str(raw_confidence).casefold(), 0.5
                )
                if not isinstance(raw_confidence, (int, float))
                else float(raw_confidence)
            )
            source_kind = "PDF_TEXT_OR_OCR"
            for text in analysis.get("text_items", [])[:200]:
                if str(text).strip():
                    values.append(
                        {
                            "text": str(text).strip(),
                            "source_file_name": analysis.get("file_name"),
                            "source_kind": source_kind,
                            "page": None,
                            "entity_id": None,
                            "confidence": min(max(confidence, 0.0), 1.0),
                        }
                    )
        return values[:400]

    def _run_ai_extraction(
        self,
        bundle: JobBundle,
        mfg: Any,
        pdf_text_context: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Run DeepSeek-assisted extraction for missing fields."""
        if self._ai_client is None:
            return None

        # Collect context for AI
        text_context = list(pdf_text_context or [])

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
        """Attach reference-only AI estimates to unknown items."""
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
