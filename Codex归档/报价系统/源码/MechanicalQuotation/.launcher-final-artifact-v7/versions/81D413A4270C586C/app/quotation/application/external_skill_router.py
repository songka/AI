"""Execute configured external quotation Skills with built-in fallback."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quotation.application.external_skill_settings import (
    STEP_NAMES_ZH,
    ExternalSkillDefinition,
    ExternalSkillRoutingConfig,
    ExternalSkillSettingsStore,
    PartCategory,
    SkillRoutingMode,
    SkillStep,
)
from quotation.infrastructure.external_skill.client import ExternalSkillClient
from quotation.infrastructure.rules.published_pricebook_loader import PublishedPricebookLoader


@dataclass
class ExternalSkillExecution:
    responses: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    price_records: dict[str, dict[str, Any]] = field(default_factory=dict)
    debug_trace: list[dict[str, Any]] = field(default_factory=list)


class ExternalSkillRouter:
    def __init__(
        self,
        store: ExternalSkillSettingsStore,
        client: ExternalSkillClient | None = None,
        pricebook_loader: PublishedPricebookLoader | None = None,
        ai_client: Any = None,
        debug_enabled: bool = False,
    ) -> None:
        self.store = store
        self.client = client or ExternalSkillClient(timeout_seconds=60, ai_client=ai_client)
        self.pricebook_loader = pricebook_loader or PublishedPricebookLoader()
        self.debug_enabled = debug_enabled

    def load_config(self) -> ExternalSkillRoutingConfig:
        return self.store.load()

    def execute(
        self,
        result: Any,
        config: ExternalSkillRoutingConfig | None = None,
    ) -> ExternalSkillExecution:
        execution = ExternalSkillExecution()
        try:
            config = config or self.store.load()
            debug_mode = config.debug_mode or self.debug_enabled
            category = self._part_category(result)
            calls = self._calls(config, category)
            if not calls and not debug_mode:
                return execution
            pricebook = self._pricebook_payload()
            execution.price_records = {
                item["company_price_id"]: item for item in pricebook["records"]
            }
            for skill, steps, mode in calls:
                payload = self._request_payload(result, skill, steps, mode, pricebook)
                started = time.perf_counter()
                try:
                    response = self.client.invoke(skill.endpoint, payload)
                    self._validate_response(payload, skill, steps, response)
                    execution.responses.append(
                        {
                            "skill": skill.model_dump(mode="json"),
                            "selected_steps": [step.value for step in steps],
                            "execution_mode": mode.value,
                            "response": response,
                        }
                    )
                    if debug_mode:
                        elapsed = round((time.perf_counter() - started) * 1000, 1)
                        for step in steps:
                            execution.debug_trace.append({
                                "step": step.value,
                                "step_name_zh": STEP_NAMES_ZH[step],
                                "provider": skill.name_zh,
                                "provider_type": skill.source_type.value,
                                "status": "成功",
                                "duration_ms": elapsed,
                                "input": payload,
                                "output": response,
                                "validation": self._debug_validation(payload, steps, response),
                            })
                except Exception as exc:
                    execution.warnings.append(
                        f"外接 Skill“{skill.name_zh}”执行失败，已回退内置结果：{exc}"
                    )
                    if debug_mode:
                        elapsed = round((time.perf_counter() - started) * 1000, 1)
                        for step in steps:
                            execution.debug_trace.append({
                                "step": step.value,
                                "step_name_zh": STEP_NAMES_ZH[step],
                                "provider": skill.name_zh,
                                "provider_type": skill.source_type.value,
                                "status": "失败并回退内置系统",
                                "duration_ms": elapsed,
                                "input": payload,
                                "output": {"error_zh": str(exc)},
                                "validation": {
                                    "input_ok": True,
                                    "output_ok": False,
                                    "issues_zh": [str(exc)],
                                },
                            })
            if debug_mode:
                traced = {entry["step"] for entry in execution.debug_trace}
                for step in SkillStep:
                    if step.value in traced:
                        continue
                    execution.debug_trace.append(self._built_in_debug_entry(result, step))
                order = {step.value: index for index, step in enumerate(SkillStep)}
                execution.debug_trace.sort(key=lambda entry: order[entry["step"]])
        except Exception as exc:
            execution.warnings.append(f"外接 Skill 路由读取失败，已使用内置报价：{exc}")
        return execution

    @staticmethod
    def _built_in_debug_entry(result: Any, step: SkillStep) -> dict[str, Any]:
        quote = result.quote
        agents = (result.ai_suggestions or {}).get("agents", {})
        outputs = {
            SkillStep.DOCUMENT_UNDERSTANDING: agents.get("备注理解智能体") or {
                "document_texts": result.document_texts,
            },
            SkillStep.FEATURE_EXTRACTION: result.feature_summary,
            SkillStep.MATERIAL_CLASSIFICATION: {"material": quote.material if quote else None},
            SkillStep.PROCESS_PLANNING: agents.get("工艺规划智能体") or [],
            SkillStep.TIME_ESTIMATION: [
                result._item_to_dict(item)
                for item in (quote.items if quote else [])
                if item.category == "process"
            ],
            SkillStep.LINE_ITEM_PRICING: [
                result._item_to_dict(item) for item in (quote.items if quote else [])
            ],
            SkillStep.UNKNOWN_ESTIMATION: (result.ai_suggestions or {}).get(
                "price_estimates", []
            ),
            SkillStep.PRICE_AUDIT: agents.get("价格审核智能体") or {},
            SkillStep.REVIEW_RECOMMENDATION: {
                "requires_review": getattr(result.status, "value", result.status)
                == "REVIEW_REQUIRED",
                "warnings": result.warnings,
            },
            SkillStep.QUOTE_ASSEMBLY: {
                "subtotal_excluding_tax": getattr(
                    result,
                    "subtotal_excluding_tax",
                    getattr(quote, "subtotal_excluding_tax", None),
                ),
                "tax_amount": (
                    result.tax.tax_amount
                    if getattr(result, "tax", None)
                    else getattr(quote, "tax_amount", None)
                ),
                "total_including_tax": getattr(
                    result,
                    "total_including_tax",
                    getattr(quote, "total_including_tax", None),
                ),
                "status": result.status,
            },
        }
        return {
            "step": step.value,
            "step_name_zh": STEP_NAMES_ZH[step],
            "provider": "内置系统",
            "provider_type": "BUILTIN",
            "status": "完成",
            "duration_ms": None,
            "input": {
                "drawing_number": result.drawing_number,
                "part_category": result.feature_summary.get("part_category"),
                "document_texts": result.document_texts,
                "previous_context": result.feature_summary,
            },
            "output": outputs[step],
            "validation": {
                "input_ok": True,
                "output_ok": True,
                "issues_zh": [],
            },
        }

    @staticmethod
    def _debug_validation(
        payload: dict[str, Any], steps: list[SkillStep], response: dict[str, Any]
    ) -> dict[str, Any]:
        issues: list[str] = []
        required_inputs = {
            "request_id", "protocol_version", "selected_steps", "drawing_package",
            "built_in_context", "published_pricebook",
        }
        missing = sorted(required_inputs - payload.keys())
        if missing:
            issues.append("输入缺少字段：" + "、".join(missing))
        completed = set(response.get("completed_steps", []))
        selected = {step.value for step in steps}
        if not completed:
            issues.append("输出没有声明已完成步骤")
        if not completed.issubset(selected):
            issues.append("输出包含未授权步骤")
        if response.get("request_id") != payload.get("request_id"):
            issues.append("输出 request_id 与输入不一致")
        if response.get("protocol_version") != payload.get("protocol_version"):
            issues.append("输出协议版本与输入不一致")
        quotation = response.get("quotation")
        if quotation is not None and not isinstance(quotation, dict):
            issues.append("quotation 必须是 JSON 对象")
        if isinstance(quotation, dict):
            for item in quotation.get("items", []):
                if not isinstance(item, dict):
                    issues.append("报价分项必须是 JSON 对象")
                    continue
                source = item.get("source")
                if source in {"H", "E"}:
                    issues.append("禁止使用历史整件价格或行业整件估价")
                if source == "C" and not item.get("company_price_id"):
                    issues.append("公司核准价缺少 company_price_id")
                if source == "AI" and (
                    item.get("price_status") != "AI_REFERENCE"
                    or item.get("requires_review") is not True
                    or item.get("included_in_quotation", True) is not True
                ):
                    issues.append("AI估价缺少待审或计入报价标记")
        return {
            "input_ok": not missing,
            "output_ok": not issues,
            "issues_zh": issues,
        }

    @staticmethod
    def _calls(
        config: ExternalSkillRoutingConfig,
        category: PartCategory | None = None,
    ):
        skills = {item.skill_id: item for item in config.skills if item.enabled}
        route = config.route_for(category)
        if route.mode == SkillRoutingMode.FULL_QUOTATION:
            skill = skills.get(route.full_skill_id or "")
            return (
                [(skill, list(SkillStep), SkillRoutingMode.FULL_QUOTATION)]
                if skill is not None
                else []
            )
        grouped: dict[str, list[SkillStep]] = {}
        for step in SkillStep:
            provider = config.provider_for(step, category)
            if provider != "builtin":
                grouped.setdefault(provider, []).append(step)
        return [
            (skills[skill_id], steps, SkillRoutingMode.DISTRIBUTED)
            for skill_id, steps in grouped.items()
            if skill_id in skills
        ]

    @staticmethod
    def _part_category(result: Any) -> PartCategory | None:
        value = str(getattr(result, "feature_summary", {}).get("part_category") or "")
        try:
            return PartCategory(value)
        except ValueError:
            return None

    def _pricebook_payload(self) -> dict[str, Any]:
        snapshot = self.pricebook_loader._snapshot  # validated, read-only snapshot
        if not snapshot:
            raise ValueError("公司正式价格表不可用")
        return {
            "price_version_id": snapshot["price_version_id"],
            "published_at": snapshot.get("approved_at") or snapshot.get("created_at"),
            "records_sha256": snapshot["snapshot_sha256"],
            "records": list(snapshot["company_prices"]),
        }

    @staticmethod
    def _request_payload(
        result: Any,
        skill: ExternalSkillDefinition,
        steps: list[SkillStep],
        mode: SkillRoutingMode,
        pricebook: dict[str, Any],
    ) -> dict[str, Any]:
        files = []
        for item in result.bundle.files:
            path = Path(item.full_path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append(
                {
                    "file_id": digest[:16],
                    "file_name": item.file_name,
                    "file_type": item.extension.lstrip(".").upper(),
                    "sha256": digest,
                    "size_bytes": path.stat().st_size,
                    "local_uri": str(path.resolve()),
                    "content_base64": None,
                }
            )
        primary = result.bundle.geometry_source
        primary_path = Path(primary.full_path) if primary is not None else None
        primary_id = next(
            (
                item["file_id"]
                for item in files
                if primary_path is not None
                and Path(item["local_uri"]).resolve() == primary_path.resolve()
            ),
            files[0]["file_id"],
        )
        file_ids_by_name = {item["file_name"].casefold(): item["file_id"] for item in files}
        extracted_texts = []
        note_inputs = []
        for item in list(getattr(result, "document_texts", []))[:400]:
            if not isinstance(item, dict) or not str(item.get("text", "")).strip():
                continue
            source_name = str(item.get("source_file_name") or "")
            source_id = file_ids_by_name.get(source_name.casefold(), primary_id)
            extracted_texts.append(
                {
                    "text": str(item["text"])[:4000],
                    "source_file_id": source_id,
                    "page": item.get("page"),
                    "entity_id": item.get("entity_id"),
                    "confidence": float(item.get("confidence", 0.5)),
                }
            )
            note_inputs.append(
                {
                    "source_file_id": source_id,
                    "source_file_name": source_name,
                    "source_kind": item.get("source_kind"),
                    "text": str(item["text"])[:4000],
                    "confidence": float(item.get("confidence", 0.5)),
                }
            )
        request_id = f"{result.job_id}-{skill.skill_id}"
        return {
            "request_id": request_id,
            "protocol_version": "1.0",
            "execution_mode": (
                "FULL_QUOTATION"
                if mode == SkillRoutingMode.FULL_QUOTATION
                else "PARTIAL_STEPS"
            ),
            "selected_steps": [step.value for step in steps],
            "locale": "zh-CN",
            "currency": "CNY",
            "quote_policy": {
                "prohibit_part_number_matching": True,
                "formal_price_requires_published_record": True,
                "ai_estimate_requires_review": True,
                "prefer_lowest_cost_capable_process": True,
                "tax_rate": 0.13,
                "require_evidence": True,
            },
            "drawing_package": {
                "drawing_number": result.drawing_number,
                "part_name": result.quote.part_name if result.quote else None,
                "quantity": result.quote.quantity if result.quote else 1,
                "primary_file": primary_id,
                "files": files,
                "extracted_texts": extracted_texts,
            },
            "built_in_context": {
                "part_category": result.feature_summary.get("part_category"),
                "material": result.quote.material if result.quote else None,
                "manufacturing_features": result.feature_summary,
                "existing_quote_items": [
                    result._item_to_dict(item) for item in (result.quote.items if result.quote else [])
                ],
                "notes": list(result.warnings),
                "note_inputs": note_inputs,
                "note_understanding": (result.ai_suggestions or {})
                .get("agents", {})
                .get("备注理解智能体"),
            },
            "published_pricebook": pricebook,
        }

    @staticmethod
    def _validate_response(payload, skill, steps, response) -> None:
        if response.get("request_id") != payload["request_id"]:
            raise ValueError("响应 request_id 不一致")
        if response.get("protocol_version") != "1.0":
            raise ValueError("响应协议版本不是 1.0")
        if response.get("skill_id") != skill.skill_id:
            raise ValueError("响应 Skill ID 不一致")
        completed = set(response.get("completed_steps", []))
        selected = {step.value for step in steps}
        if not completed.issubset(selected):
            raise ValueError("Skill 返回了未授权步骤")


def build_external_skill_router(
    settings: dict, *, ai_client: Any = None, debug_enabled: bool = False
) -> ExternalSkillRouter:
    store = ExternalSkillSettingsStore(
        Path(settings["smb_root"]) / "data" / "external-skill-routing.json",
        Path(settings["smb_cache_dir"]) / "data" / "external-skill-routing.json",
        sync_enabled=True,
    )
    return ExternalSkillRouter(store, ai_client=ai_client, debug_enabled=debug_enabled)
