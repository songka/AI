"""Execute configured external quotation Skills with built-in fallback."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quotation.application.external_skill_settings import (
    BUILTIN_AGENTS,
    AgentDefinition,
    AgentSourceType,
    STEP_NAMES_ZH,
    ExternalSkillDefinition,
    ExternalSkillRoutingConfig,
    ExternalSkillSettingsStore,
    PartCategory,
    ProcessCode,
    PROCESS_ROUTABLE_STEPS,
    PRE_CATEGORY_STEPS,
    SkillRoutingMode,
    SkillSourceType,
    SkillStep,
    StepRoute,
)
from quotation.infrastructure.external_skill.client import ExternalSkillClient
from quotation.infrastructure.rules.published_pricebook_loader import PublishedPricebookLoader


@dataclass
class ExternalSkillExecution:
    responses: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    price_records: dict[str, dict[str, Any]] = field(default_factory=dict)
    debug_trace: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RoutedProviderCall:
    skill: ExternalSkillDefinition
    steps: list[SkillStep]
    mode: SkillRoutingMode
    process_codes: list[ProcessCode] = field(default_factory=list)
    agent: AgentDefinition | None = None
    direct_agent: bool = False


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
        *,
        only_steps: set[SkillStep] | None = None,
        skip_steps: set[SkillStep] | None = None,
    ) -> ExternalSkillExecution:
        execution = ExternalSkillExecution()
        try:
            config = config or self.store.load()
            debug_mode = config.debug_mode or self.debug_enabled
            category = self._part_category(result)
            calls = self._route_calls(
                config,
                category,
                process_codes=self._detected_processes(result),
                only_steps=only_steps,
                skip_steps=skip_steps,
            )
            if not calls and not debug_mode:
                return execution
            pricebook = self._pricebook_payload()
            execution.price_records = {
                item["company_price_id"]: item for item in pricebook["records"]
            }
            prior_skill_results: list[dict[str, Any]] = list(
                (getattr(result, "ai_suggestions", {}) or {}).get(
                    "external_skill_chain", []
                )
            )
            for call in calls:
                skill, steps, mode = call.skill, call.steps, call.mode
                payload = self._request_payload(
                    result,
                    skill,
                    steps,
                    mode,
                    pricebook,
                    prior_skill_results=prior_skill_results,
                    process_codes=call.process_codes,
                    target_agent=call.agent,
                )
                started = time.perf_counter()
                try:
                    invoke_skill = getattr(self.client, "invoke_skill", None)
                    uses_external_agent = (
                        call.agent is not None
                        and call.agent.source_type != AgentSourceType.BUILTIN
                    )
                    if uses_external_agent:
                        response = self.client.invoke_agent(call.agent, payload)
                        if not call.direct_agent:
                            response["agent_id"] = call.agent.agent_id
                            response["skill_id"] = skill.skill_id
                            response.setdefault("skill_version", skill.skill_version)
                    else:
                        response = (
                            invoke_skill(skill, payload)
                            if callable(invoke_skill)
                            else self.client.invoke(skill.endpoint, payload)
                        )
                    self._validate_response(payload, skill, steps, response)
                    execution.responses.append(
                        {
                            "skill": skill.model_dump(mode="json"),
                            "selected_steps": [step.value for step in steps],
                            "execution_mode": mode.value,
                            "process_codes": [item.value for item in call.process_codes],
                            "agent": (
                                call.agent.model_dump(mode="json") if call.agent else None
                            ),
                            "response": response,
                        }
                    )
                    prior_skill_results.append(
                        {
                            "skill_id": skill.skill_id,
                            "skill_version": skill.skill_version,
                            "completed_steps": list(response.get("completed_steps") or []),
                            "step_results": dict(response.get("step_results") or {}),
                            "quotation": response.get("quotation"),
                            "review": response.get("review"),
                        }
                    )
                    if debug_mode:
                        elapsed = round((time.perf_counter() - started) * 1000, 1)
                        for step in steps:
                            execution.debug_trace.append({
                                "step": step.value,
                                "step_name_zh": STEP_NAMES_ZH[step],
                                "provider": skill.name_zh,
                                "provider_type": (
                                    "EXTERNAL_AGENT" if call.direct_agent else skill.source_type.value
                                ),
                                "agent": call.agent.name_zh if call.agent else None,
                                "process_codes": [item.value for item in call.process_codes],
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
                                "provider_type": (
                                    "EXTERNAL_AGENT" if call.direct_agent else skill.source_type.value
                                ),
                                "agent": call.agent.name_zh if call.agent else None,
                                "process_codes": [item.value for item in call.process_codes],
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
                debug_steps = list(only_steps) if only_steps is not None else list(SkillStep)
                for step in debug_steps:
                    if skip_steps and step in skip_steps:
                        continue
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
            SkillStep.PART_CLASSIFICATION: agents.get("零件分类智能体") or {
                "part_category": result.feature_summary.get("part_category"),
                "source": result.feature_summary.get("part_category_source", "BUILTIN_RULE"),
                "confidence": result.feature_summary.get("part_category_confidence", 1.0),
                "evidence": result.feature_summary.get("part_category_evidence", []),
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
        ai_steps = {
            SkillStep.DOCUMENT_UNDERSTANDING,
            SkillStep.PART_CLASSIFICATION,
            SkillStep.PROCESS_PLANNING,
            SkillStep.PRICE_AUDIT,
        }
        provider = "内置 DeepSeek Skill" if step in ai_steps else "内置规则引擎"
        agent_keys = {
            SkillStep.DOCUMENT_UNDERSTANDING: "备注理解智能体",
            SkillStep.PART_CLASSIFICATION: "零件分类智能体",
            SkillStep.PROCESS_PLANNING: "工艺规划智能体",
            SkillStep.PRICE_AUDIT: "价格审核智能体",
        }
        if step in agent_keys and agent_keys[step] not in agents:
            provider = "内置规则引擎"
        if step == SkillStep.TIME_ESTIMATION and any(
            item.get("resolution_source") == "AI_PROCESS_CLASSIFICATION"
            for item in outputs[step]
        ):
            provider = "内置 DeepSeek Skill（AI估工时）"
        if step == SkillStep.UNKNOWN_ESTIMATION and outputs[step]:
            provider = "内置 DeepSeek Skill（AI参考估价）"
        status = "完成"
        if step == SkillStep.DOCUMENT_UNDERSTANDING and (
            outputs[step].get("confidence", 0) == 0
            and "失败" in str(outputs[step].get("summary", ""))
        ):
            status = "失败并回退"
        elif step == SkillStep.PART_CLASSIFICATION:
            if outputs[step].get("status") != "SUCCESS":
                provider = "内置规则引擎"
                status = "AI分类失败，规则回退"
        elif step == SkillStep.PRICE_AUDIT and (
            outputs[step].get("confidence", 0) == 0
            and "价格审核未返回有效结果" in outputs[step].get("issues", [])
        ):
            status = "失败并回退"
        return {
            "step": step.value,
            "step_name_zh": STEP_NAMES_ZH[step],
            "provider": provider,
            "provider_type": "BUILTIN",
            "status": status,
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
        *,
        only_steps: set[SkillStep] | None = None,
        skip_steps: set[SkillStep] | None = None,
    ):
        return [
            (call.skill, call.steps, call.mode)
            for call in ExternalSkillRouter._route_calls(
                config,
                category,
                only_steps=only_steps,
                skip_steps=skip_steps,
            )
        ]

    @staticmethod
    def _route_calls(
        config: ExternalSkillRoutingConfig,
        category: PartCategory | None = None,
        *,
        process_codes: set[ProcessCode] | None = None,
        only_steps: set[SkillStep] | None = None,
        skip_steps: set[SkillStep] | None = None,
    ) -> list[RoutedProviderCall]:
        skills = {item.skill_id: item for item in config.skills if item.enabled}
        agents = {
            item.agent_id: item
            for item in (*BUILTIN_AGENTS, *config.agents)
            if item.enabled
        }
        grouped: dict[
            tuple[int, str, SkillRoutingMode, str | None, bool],
            dict[str, Any],
        ] = {}
        phase_by_step = {
            SkillStep.DOCUMENT_UNDERSTANDING: 0,
            SkillStep.PART_CLASSIFICATION: 0,
            SkillStep.FEATURE_EXTRACTION: 1,
            SkillStep.MATERIAL_CLASSIFICATION: 1,
            SkillStep.PROCESS_PLANNING: 2,
            SkillStep.TIME_ESTIMATION: 2,
            SkillStep.LINE_ITEM_PRICING: 3,
            SkillStep.UNKNOWN_ESTIMATION: 3,
            SkillStep.QUOTE_ASSEMBLY: 3,
            SkillStep.PRICE_AUDIT: 4,
            SkillStep.REVIEW_RECOMMENDATION: 4,
        }
        for step in SkillStep:
            if only_steps is not None and step not in only_steps:
                continue
            if skip_steps and step in skip_steps:
                continue
            category_route = (
                config.route_for(None)
                if step in PRE_CATEGORY_STEPS
                else config.route_for(category)
            )
            if category_route.mode == SkillRoutingMode.FULL_QUOTATION:
                provider_routes = [(StepRoute(provider=category_route.full_skill_id or "builtin"), None)]
                mode = SkillRoutingMode.FULL_QUOTATION
            else:
                mode = SkillRoutingMode.DISTRIBUTED
                provider_routes = []
                if (
                    step in PROCESS_ROUTABLE_STEPS
                    and category is not None
                    and process_codes
                ):
                    provider_routes.extend(
                        (config.route_for_process(step, category, process), process)
                        for process in sorted(process_codes, key=lambda item: item.value)
                    )
                else:
                    provider_routes.append(
                        (category_route.step_routes.get(step, StepRoute()), None)
                    )
            for route, process in provider_routes:
                provider = route.provider
                if provider == "builtin":
                    agent = agents.get(route.agent_id or "")
                    if agent is None or agent.source_type == AgentSourceType.BUILTIN:
                        continue
                    skill = ExternalSkillRouter._agent_as_skill(agent)
                    direct_agent = True
                    provider = agent.agent_id
                else:
                    skill = skills.get(provider)
                    direct_agent = skill is None and provider in agents
                    agent = agents.get(provider) if direct_agent else None
                    if skill is None and agent is not None:
                        if agent.source_type == AgentSourceType.BUILTIN:
                            continue
                        skill = ExternalSkillRouter._agent_as_skill(agent)
                if skill is None or step not in skill.supported_steps:
                    continue
                agent_id = route.agent_id or skill.step_agent_routes.get(step)
                if agent_id:
                    agent = agents.get(agent_id)
                phase = 0 if mode == SkillRoutingMode.FULL_QUOTATION else phase_by_step[step]
                key = (phase, provider, mode, agent.agent_id if agent else None, direct_agent)
                bucket = grouped.setdefault(
                    key, {"skill": skill, "steps": [], "processes": set(), "agent": agent}
                )
                if step not in bucket["steps"]:
                    bucket["steps"].append(step)
                if process is not None:
                    bucket["processes"].add(process)
        calls = []
        for key, bucket in sorted(
            grouped.items(),
            key=lambda item: (
                item[0][0], item[0][1], item[0][2].value, item[0][3] or ""
            ),
        ):
            calls.append(
                RoutedProviderCall(
                    skill=bucket["skill"],
                    steps=bucket["steps"],
                    mode=key[2],
                    process_codes=sorted(bucket["processes"], key=lambda item: item.value),
                    agent=bucket["agent"],
                    direct_agent=key[4],
                )
            )
        return calls

    @staticmethod
    def _agent_as_skill(agent: AgentDefinition) -> ExternalSkillDefinition:
        return ExternalSkillDefinition(
            skill_id=agent.agent_id,
            name_zh=agent.name_zh,
            endpoint=agent.endpoint,
            source_type=(
                SkillSourceType.HTTP
                if agent.source_type == AgentSourceType.HTTP
                else SkillSourceType.FOLDER
            ),
            skill_version=agent.agent_version,
            supported_steps=agent.supported_steps,
            supported_processes=agent.supported_processes,
        )

    @staticmethod
    def _detected_processes(result: Any) -> set[ProcessCode]:
        detected: set[ProcessCode] = set()
        for item in (getattr(result, "ai_suggestions", {}) or {}).get("processes", []):
            try:
                detected.add(ProcessCode(str(item.get("code") or "").upper()))
            except (ValueError, AttributeError):
                continue
        aliases = {
            "CNC": ProcessCode.CNC,
            "加工中心": ProcessCode.CNC,
            "車床": ProcessCode.LATHE,
            "车床": ProcessCode.LATHE,
            "銑床": ProcessCode.MILL,
            "铣床": ProcessCode.MILL,
            "磨床": ProcessCode.GRIND,
            "鉗工": ProcessCode.FITTER,
            "钳工": ProcessCode.FITTER,
            "放電": ProcessCode.EDM,
            "放电": ProcessCode.EDM,
            "快絲": ProcessCode.WIRE_CUT,
            "快丝": ProcessCode.WIRE_CUT,
            "慢絲": ProcessCode.SLOW_WIRE,
            "慢丝": ProcessCode.SLOW_WIRE,
            "焊": ProcessCode.WELDING,
            "折弯": ProcessCode.BENDING,
            "折彎": ProcessCode.BENDING,
            "激光": ProcessCode.LASER_CUT,
            "雷射": ProcessCode.LASER_CUT,
            "表面处理": ProcessCode.SURFACE,
            "表面處理": ProcessCode.SURFACE,
        }
        quote = getattr(result, "quote", None)
        for item in getattr(quote, "items", []) or []:
            name = str(getattr(item, "name", ""))
            for token, code in aliases.items():
                if token in name:
                    detected.add(code)
        return detected

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
        prior_skill_results: list[dict[str, Any]] | None = None,
        process_codes: list[ProcessCode] | None = None,
        target_agent: AgentDefinition | None = None,
    ) -> dict[str, Any]:
        price_sensitive_steps = {
            SkillStep.PROCESS_PLANNING,
            SkillStep.TIME_ESTIMATION,
            SkillStep.LINE_ITEM_PRICING,
            SkillStep.UNKNOWN_ESTIMATION,
            SkillStep.QUOTE_ASSEMBLY,
            SkillStep.PRICE_AUDIT,
            SkillStep.REVIEW_RECOMMENDATION,
        }
        effective_pricebook = pricebook
        if not any(step in price_sensitive_steps for step in steps):
            effective_pricebook = {
                key: value for key, value in pricebook.items() if key != "records"
            }
            effective_pricebook["records"] = []
            effective_pricebook["records_omitted_for_non_pricing_step"] = True
        manufacturing_features = dict(result.feature_summary or {})
        if SkillStep.PART_CLASSIFICATION in steps:
            for key in (
                "part_category",
                "part_category_source",
                "part_category_confidence",
                "part_category_evidence",
            ):
                manufacturing_features.pop(key, None)
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
            "target_skill": {
                "skill_id": skill.skill_id,
                "skill_version": skill.skill_version,
                "skill_name_zh": skill.name_zh,
            },
            "target_agent": (
                {
                    "agent_id": target_agent.agent_id,
                    "agent_version": target_agent.agent_version,
                    "agent_name_zh": target_agent.name_zh,
                    "source_type": target_agent.source_type.value,
                }
                if target_agent else None
            ),
            "selected_processes": [item.value for item in (process_codes or [])],
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
                "part_category": (
                    None
                    if SkillStep.PART_CLASSIFICATION in steps
                    else result.feature_summary.get("part_category")
                ),
                "material": result.quote.material if result.quote else None,
                "manufacturing_features": manufacturing_features,
                "existing_quote_items": [
                    result._item_to_dict(item) for item in (result.quote.items if result.quote else [])
                ],
                "notes": list(result.warnings),
                "note_inputs": note_inputs,
                "note_understanding": (result.ai_suggestions or {})
                .get("agents", {})
                .get("备注理解智能体"),
                "prior_skill_results": list(prior_skill_results or []),
            },
            "published_pricebook": effective_pricebook,
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
        if SkillStep.PART_CLASSIFICATION.value in completed:
            classification = (response.get("step_results") or {}).get(
                SkillStep.PART_CLASSIFICATION.value
            )
            if not isinstance(classification, dict):
                raise ValueError("零件分类步骤缺少结构化结果")
            category = str(classification.get("part_category") or "").upper()
            if category not in {item.value for item in PartCategory}:
                raise ValueError("零件分类结果不是允许的四类之一")
            try:
                confidence = float(classification.get("confidence", 0))
            except (TypeError, ValueError) as exc:
                raise ValueError("零件分类可信度不是有效数字") from exc
            if not 0 <= confidence <= 1:
                raise ValueError("零件分类可信度必须在 0 到 1 之间")


def build_external_skill_router(
    settings: dict, *, ai_client: Any = None, debug_enabled: bool = False
) -> ExternalSkillRouter:
    store = ExternalSkillSettingsStore(
        Path(settings["smb_root"]) / "data" / "external-skill-routing.json",
        Path(settings["smb_cache_dir"]) / "data" / "external-skill-routing.json",
        sync_enabled=True,
    )
    return ExternalSkillRouter(store, ai_client=ai_client, debug_enabled=debug_enabled)
