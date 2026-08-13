"""DeepSeek API Client for AI-assisted drawing extraction."""

from __future__ import annotations

import json
import hashlib
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class AIExtractionResult:
    """Structured result from DeepSeek feature extraction."""
    drawing_number: str | None = None
    material_candidate: str | None = None
    surface_treatment_candidate: str | None = None
    heat_treatment_candidate: str | None = None
    thickness_candidate: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "drawing_number": self.drawing_number,
            "material_candidate": self.material_candidate,
            "surface_treatment_candidate": self.surface_treatment_candidate,
            "heat_treatment_candidate": self.heat_treatment_candidate,
            "thickness_candidate": self.thickness_candidate,
            "missing_fields": self.missing_fields,
            "warnings": self.warnings,
            "confidence": self.confidence,
        }


class DeepSeekClient:
    """Shared DeepSeek API client for UI and API usage.

    Uses the internal LAN API. API key loaded via SecretLocator.
    """

    _cache_limit = 256

    def __init__(
        self,
        base_url: str = "http://10.97.144.27:3000/v1",
        model: str = "deepseek-v4-flash",
        api_key: str | None = None,
        timeout_seconds: float = 20.0,
        max_tokens: int = 1024,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_tokens = max_tokens
        self._circuit_open_until = 0.0
        self.last_error: str | None = None
        self.cache_hits = 0
        self.cache_misses = 0
        # Per-client cache avoids sharing drawing content across users/API keys.
        self._response_cache: OrderedDict[str, str] = OrderedDict()
        self._cache_lock = threading.RLock()

    @property
    def is_configured(self) -> bool:
        return self._api_key is not None and len(self._api_key.strip()) > 0

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Check API connectivity. Returns health status without exposing key."""
        if not self.is_configured:
            return {"configured": False, "reachable": False, "error": "API key not configured"}

        t0 = time.monotonic()
        last_error = "未知连接错误"
        for attempt in range(2):
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(
                        f"{self._base_url}/models",
                        headers=self._headers(),
                    )
                latency_ms = (time.monotonic() - t0) * 1000
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id", "") for m in data.get("data", [])]
                    model_found = any(self._model in m for m in models)
                    return {
                        "configured": True,
                        "reachable": True,
                        "model": self._model,
                        "model_found": model_found,
                        "latency_ms": round(latency_ms, 1),
                        "error": None,
                    }
                last_error = f"HTTP {resp.status_code}"
                if resp.status_code >= 500 and attempt == 0:
                    time.sleep(0.5)
                    continue
                break
            except httpx.TimeoutException:
                self.last_error = f"AI服务响应超时（{self._timeout:g}秒）"
                self._circuit_open_until = time.monotonic() + 30.0
                return None
            except httpx.RequestError as exc:
                last_error = str(exc)
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                break
            except Exception as exc:
                last_error = str(exc)
                break
        latency_ms = (time.monotonic() - t0) * 1000
        return {
            "configured": True,
            "reachable": False,
            "model": self._model,
            "latency_ms": round(latency_ms, 1),
            "error": last_error,
        }

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def extract_features(
        self,
        drawing_number: str,
        texts: list[str],
        missing_fields: list[str],
    ) -> dict[str, Any] | None:
        """Extract drawing features using DeepSeek.

        Only called when deterministic parser lacks data.
        Returns structured JSON or None on failure.
        """
        if not self.is_configured:
            return None

        prompt = self._build_extraction_prompt(drawing_number, texts, missing_fields)

        content = self._chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        if content is None:
            return None

        return self._parse_extraction_response(content)

    def estimate_unknown_costs(
        self,
        drawing_number: str,
        items: list[dict[str, Any]],
        context: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Estimate unknown costs for inclusion in a review-required quotation."""
        if not self.is_configured or not items:
            return []
        bounded_items = items[:20]
        bounded_context = "\n".join(context or [])[:12000]
        prompt = f"""你是机械加工报价审核助手。请对待确认费用行给出人民币未税参考估价。
这些价格会作为“AI估算、需人工确认”的分项计入本次报价合计，但不能冒充公司核准价格。
不得编造精确供应商来源；信息不足时降低可信度并说明假设。

图号：{drawing_number}
图纸文字：
{bounded_context or "（无额外文字）"}

待确认费用行：
{json.dumps(bounded_items, ensure_ascii=False)}

只返回合法 JSON 对象，不要输出其他文字：
{{"estimates":[{{"line_id":"费用行编号","unit_price":数字,"quantity":数字,"unit":"中文计价单位","amount":数字,"reason":"中文估价依据和假设","confidence":0到1}}]}}
amount 应等于 unit_price × quantity；无法合理估计的费用行也必须返回，价格填 0 并解释原因。"""
        content = self._chat([{"role": "user", "content": prompt}], temperature=0.2)
        if content is None:
            return []
        parsed = self._parse_json_object(content)
        estimates = parsed.get("estimates", []) if parsed else []
        allowed_ids = {str(item.get("line_id")) for item in bounded_items}
        clean: list[dict[str, Any]] = []
        for estimate in estimates if isinstance(estimates, list) else []:
            if not isinstance(estimate, dict) or str(estimate.get("line_id")) not in allowed_ids:
                continue
            try:
                unit_price = max(float(estimate.get("unit_price", 0)), 0.0)
                quantity = max(float(estimate.get("quantity", 0)), 0.0)
                amount = max(float(estimate.get("amount", unit_price * quantity)), 0.0)
                confidence = min(max(float(estimate.get("confidence", 0)), 0.0), 1.0)
            except (TypeError, ValueError):
                continue
            clean.append({
                "line_id": str(estimate["line_id"]),
                "unit_price": round(unit_price, 2),
                "quantity": quantity,
                "unit": str(estimate.get("unit") or "项")[:20],
                "amount": round(amount, 2),
                "reason": str(estimate.get("reason") or "信息不足，仅供人工参考")[:500],
                "confidence": round(confidence, 2),
            })
        return clean

    def classify_processes(
        self,
        drawing_number: str,
        texts: list[str],
        geometry_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Judge manufacturing processes using a strict auditable whitelist."""
        if not self.is_configured:
            return []
        allowed = {
            "CNC": "CNC",
            "LATHE": "車床",
            "MILL": "銑床",
            "GRIND": "磨床",
            "FITTER": "鉗工",
            "EDM": "放電",
            "WIRE_CUT": "快絲",
            "SLOW_WIRE": "慢絲",
        }
        context = "\n".join(texts)[:12000]
        prompt = f"""你是机械制造工艺审核员。根据图纸文字、几何摘要和其中的可用工艺小时费率，逐项检查全部候选工艺，判断成本最低且足够完成零件的必要加工工艺。
只能使用以下代码：{', '.join(allowed)}。不要输出材料、表面处理、焊接或装配；没有充分依据就不要选择。
普通平面、直边、槽和常规孔可由三轴普通铣床完成时优先选择 MILL；不能仅因存在孔或螺纹就选择 CNC。
只有图纸明确要求 CNC/加工中心，或存在复杂曲面、多轴联动、高重复定位精度等普通铣床不足以完成的证据时才选择 CNC。
若 CNC 与 MILL 都能满足要求，应分别估算实际工时并同时返回两个候选，让系统按“工时×已发布小时工价”选择较低成本；不得只比较小时费率。
存在轴、套、回转体、同心圆柱面或明确车削要求时优先 LATHE；不要把回转体默认交给铣床。
存在高精度尺寸、平面度/圆度、较低 Ra 或明确磨削要求时检查 GRIND；普通粗加工不要选磨床。
存在深窄腔、内尖角、硬料精密型腔或明确放电要求时检查 EDM。
存在贯穿异形轮廓、精密直壁割形或明确线切割要求时检查 WIRE_CUT；高精度、低粗糙度要求时检查 SLOW_WIRE。
只有图纸明确要求去毛刺、修配、钻铰或人工装配配合时才检查 FITTER。
必须在 evidence 中列出“装夹/准备、实际加工、辅助处理”三部分工时；禁止把等待、排队或整批准备时间全部计入单件。
工时按图纸中的 1 件估算，除非输入明确给出其它数量。必须在 evidence 中说明可制造性、工时构成，以及选择或保留候选设备的依据。
图纸已有螺纹时系统会单独计算攻牙；不要仅因螺纹再返回 FITTER，除非还有去毛刺、修配等额外钳工作业证据。
图号：{drawing_number}
图纸文字：{context or '（无）'}
几何摘要：{json.dumps(geometry_summary, ensure_ascii=False)}
只返回 JSON：{{"processes":[{{"code":"CNC","estimated_hours":1.0,"confidence":0.8,"evidence":"中文依据"}}]}}
estimated_hours 必须为正数；confidence 低于 0.6 的工艺不要返回。"""
        content = self._chat([{"role": "user", "content": prompt}], temperature=0.1)
        parsed = self._parse_json_object(content) if content else None
        values = parsed.get("processes", []) if parsed else []
        clean: list[dict[str, Any]] = []
        seen: set[str] = set()
        for value in values if isinstance(values, list) else []:
            if not isinstance(value, dict):
                continue
            code = str(value.get("code", "")).upper()
            if code not in allowed or code in seen:
                continue
            try:
                raw_hours = min(max(float(value.get("estimated_hours", 0)), 0), 100)
                confidence = min(max(float(value.get("confidence", 0)), 0), 1)
            except (TypeError, ValueError):
                continue
            if raw_hours <= 0 or confidence < 0.6:
                continue
            hour_limit = self._simple_part_hour_limit(code, texts, geometry_summary)
            hours = min(raw_hours, hour_limit) if hour_limit is not None else raw_hours
            seen.add(code)
            process = {
                "code": code,
                "process_name": allowed[code],
                "estimated_hours": round(hours, 2),
                "confidence": round(confidence, 2),
                "evidence": str(value.get("evidence") or "AI 工艺判断")[:500],
            }
            if hours < raw_hours:
                process["hours_adjustment"] = {
                    "ai_hours": round(raw_hours, 2),
                    "accepted_hours": round(hours, 2),
                    "reason": "图纸未提供复杂工艺依据，按单件尺寸、孔/螺纹和几何复杂度上限校正",
                }
            clean.append(process)
        return clean

    @staticmethod
    def _simple_part_hour_limit(
        code: str,
        texts: list[str],
        geometry_summary: dict[str, Any],
    ) -> float | None:
        """Bound unsupported AI hours for a geometrically simple single part."""
        context = " ".join(str(text) for text in texts).lower()
        explicit_patterns = {
            "CNC": r"cnc|数控|數控|加工中心|多轴|多軸|曲面",
            "LATHE": r"车削|車削|车床|車床|回转体|回轉體|轴类|軸類|套筒",
            "MILL": r"铣削|銑削|铣床|銑床|深腔|复杂轮廓|複雜輪廓",
            "GRIND": r"磨削|磨床|平面度|圆度|圓度|ra\s*[0-1](?:\.|。)",
            "FITTER": r"钳工|鉗工|去毛刺|修配|铰孔|鉸孔",
            "EDM": r"edm|放电|放電|电火花|電火花|内尖角|內尖角",
            "WIRE_CUT": r"线切割|線切割|快丝|快絲|wire\s*cut",
            "SLOW_WIRE": r"慢丝|慢絲|精密线切割|精密線切割",
        }
        if re.search(explicit_patterns.get(code, r"$^"), context, re.IGNORECASE):
            return None
        try:
            holes = max(float(geometry_summary.get("孔数量", 0) or 0), 0)
            threads = max(float(geometry_summary.get("螺纹数量", 0) or 0), 0)
            entities = max(float(geometry_summary.get("几何实体数量", 0) or 0), 0)
            dimensions = geometry_summary.get("外形尺寸") or []
            span = max((float(value) for value in dimensions), default=0)
        except (TypeError, ValueError):
            return 1.5
        baseline = (
            0.5
            + holes * 0.08
            + threads * 0.05
            + min(span / 1000.0, 0.75)
            + min(entities / 200.0, 0.75)
        )
        return round(min(max(baseline * 1.75, 1.0), 3.0), 2)

    def classify_part_category(
        self,
        drawing_number: str,
        texts: list[str],
        geometry_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Classify the part before category-specific Skill routing."""
        if not self.is_configured:
            return {
                "part_category": None,
                "category_name": None,
                "confidence": 0.0,
                "evidence": [],
                "alternatives": [],
                "status": "NOT_CONFIGURED",
            }
        allowed = {
            "MACHINING": "加工件",
            "SHEET_METAL": "钣金件",
            "WELDMENT": "焊接件",
            "FRAME_ASSEMBLY": "型材组装件",
        }
        context = "\n".join(texts)[:12000] or "（无）"
        prompt = f"""你是机械报价系统的零件类别分类 Skill。只能在以下四类中选择一类：
MACHINING 加工件；SHEET_METAL 钣金件；WELDMENT 焊接件；FRAME_ASSEMBLY 型材组装件。
必须依据图纸文字与几何摘要分类，不得使用图号、文件名或历史价格猜测。
优先级不是固定的；请根据零件的主要制造形态判断，并在证据不足时降低可信度。
板状、矩形或存在厚度尺寸不等于钣金件；由铣床、CNC、车床、磨床等去除材料成形的板块零件属于 MACHINING。
只有存在折弯、冲压、钣金展开、激光下料等薄板成形证据时，才可选择 SHEET_METAL。
“图纸几何范围”包含视图和图框，不能当成零件外形尺寸；优先使用“零件规格尺寸”。
图号：{drawing_number}
图纸文字：{context}
几何摘要：{json.dumps(geometry_summary, ensure_ascii=False)}
只返回 JSON：{{"part_category":"MACHINING","confidence":0.8,"evidence":["中文依据"],"alternatives":["SHEET_METAL"]}}"""
        content = self._chat([{"role": "user", "content": prompt}], temperature=0.1)
        value = self._parse_json_object(content) if content else None
        category = str((value or {}).get("part_category") or "").upper()
        if category not in allowed:
            return {
                "part_category": None,
                "category_name": None,
                "confidence": 0.0,
                "evidence": [],
                "alternatives": [],
                "status": "INVALID_RESULT",
            }
        try:
            confidence = min(max(float(value.get("confidence", 0)), 0), 1)
        except (TypeError, ValueError):
            confidence = 0.0
        alternatives = [
            str(item).upper()
            for item in value.get("alternatives", [])[:3]
            if str(item).upper() in allowed and str(item).upper() != category
        ]
        return {
            "part_category": category,
            "category_name": allowed[category],
            "confidence": confidence,
            "evidence": [str(item)[:300] for item in value.get("evidence", [])[:10]],
            "alternatives": alternatives,
            "status": "SUCCESS",
        }

    def begin_controlled_retry(self) -> bool:
        """Allow one orchestrator-controlled retry without waiting for the circuit timer."""
        if not self.is_configured:
            return False
        self._circuit_open_until = 0.0
        self.last_error = None
        return True

    def analyze_drawing_notes(
        self, drawing_number: str, texts: list[str]
    ) -> dict[str, Any]:
        """Interpret drawing notes without changing formal quote fields."""
        if not self.is_configured:
            return {"summary": "未配置人工智能", "requirements": [], "risks": [], "confidence": 0.0}
        context = "\n".join(texts)[:12000] or "（无）"
        prompt = f"""你是机械图纸备注理解智能体。归纳材料、热处理、表面处理、公差、粗糙度、数量和特殊要求。
图号：{drawing_number}
图纸文字：{context}
只返回 JSON：{{"summary":"中文摘要","requirements":["明确要求"],"risks":["歧义或缺失"],"confidence":0到1}}。不得猜测未出现的要求。"""
        content = self._chat([{"role": "user", "content": prompt}], temperature=0.1)
        value = self._parse_json_object(content) if content else None
        if not value:
            return {"summary": "备注理解失败", "requirements": [], "risks": ["智能体未返回有效结果"], "confidence": 0.0}
        return {
            "summary": str(value.get("summary") or "无明确备注")[:500],
            "requirements": [str(v)[:200] for v in value.get("requirements", [])[:20]],
            "risks": [str(v)[:200] for v in value.get("risks", [])[:20]],
            "confidence": min(max(float(value.get("confidence", 0)), 0), 1),
        }

    def audit_itemized_quote(
        self, drawing_number: str, texts: list[str], items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Audit price completeness and anomalies; never rewrite prices."""
        if not self.is_configured:
            return {"verdict": "REVIEW", "issues": ["未配置人工智能"], "actions": [], "confidence": 0.0}
        context = "\n".join(texts)[:8000] or "（无）"
        prompt = f"""你是机械报价价格审核智能体。检查遗漏工艺、重复计费、数量/单位异常、工时异常及备注与费用不一致。
不得修改单价，不得把整件模型参考价当正式价格。
本次报价对象默认为 1 件零件；材料费用行的 quantity 若以 kg 为单位，表示制造 1 件零件所需的材料重量，
不是零件件数，不能把“3.1 kg 材料重量”误判成“3.1 件”。只有图纸明确标注净重且与计算重量冲突时才报告重量问题。
actions 只填写可以通过重新理解备注、重判工艺、重估工时或重新计价执行的具体动作；纯人工确认写入 issues，不要伪装成自动动作。
图号：{drawing_number}
备注：{context}
分项：{json.dumps(items[:40], ensure_ascii=False)}
只返回 JSON：{{"verdict":"PASS或REVIEW或BLOCK","issues":["问题"],"actions":["建议"],"confidence":0到1}}。"""
        content = self._chat([{"role": "user", "content": prompt}], temperature=0.1)
        value = self._parse_json_object(content) if content else None
        if not value:
            return {"verdict": "REVIEW", "issues": ["价格审核未返回有效结果"], "actions": [], "confidence": 0.0}
        verdict = str(value.get("verdict", "REVIEW")).upper()
        if verdict not in {"PASS", "REVIEW", "BLOCK"}:
            verdict = "REVIEW"
        return {
            "verdict": verdict,
            "issues": [str(v)[:300] for v in value.get("issues", [])[:20]],
            "actions": [str(v)[:300] for v in value.get("actions", [])[:20]],
            "confidence": min(max(float(value.get("confidence", 0)), 0), 1),
        }

    def invoke_quotation_skill(
        self,
        skill_instructions: str,
        request_payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Run a local/SMB document Skill through the program's DeepSeek client."""

        if not self.is_configured:
            return None
        instructions = skill_instructions.strip()[:131072]
        request_json = json.dumps(request_payload, ensure_ascii=False)[:131072]
        system_prompt = f"""你是机械加工报价系统中的受控报价 Agent。
下面是管理员选定的 Skill 指令和参考文档。你必须遵守它们，但不得绕过系统安全规则：
- 禁止使用 UC 料号、图号或文件名匹配价格；
- 正式公司价格只能引用输入 published_pricebook 中存在的 company_price_id，单价必须一致；
- AI 估价可计入本次报价合计，但必须标记为 AI、要求人工确认，且不得冒充公司核准价格；
- 响应 skill_id 与 skill_version 必须逐字复制请求 target_skill 中的值，不得使用示例值或自行改写；
- 只执行 selected_steps，所有业务文字使用中文，并提供可审核证据；
- 不得输出密钥、密码、令牌或 reasoning_content。

{instructions}"""
        user_prompt = f"""以下 JSON 是用户选择的图纸资料、内置解析结果、既有报价分项和正式价格表。
请按外接报价 Skill 协议 1.0 返回一个合法 JSON 对象。至少包含 request_id、protocol_version、
skill_id、completed_steps、step_results、review、execution_trace；整套报价模式还必须包含 quotation。
不要输出 Markdown 或 JSON 以外的文字。

{request_json}"""
        for _attempt in range(2):
            content = self._chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=max(self._max_tokens, 4096),
            )
            parsed = self._parse_json_object(content) if content else None
            if parsed is not None:
                return parsed
            user_prompt += "\n上一次响应不是合法协议 JSON，请严格只返回一个完整 JSON 对象。"
        return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key or ''}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _build_extraction_prompt(
        self, drawing_number: str, texts: list[str], missing_fields: list[str],
    ) -> str:
        context = "\n".join(texts) if texts else "(no text context available)"
        fields_str = ", ".join(missing_fields)
        return f"""You are a mechanical drawing analysis assistant. Extract the following fields from the drawing information.

Drawing number: {drawing_number}
Text context from drawing:
{context}

Missing fields to extract: {fields_str}

Return ONLY a valid JSON object with these fields:
{{
  "drawing_number": string or null,
  "material_candidate": string or null,
  "surface_treatment_candidate": string or null,
  "heat_treatment_candidate": string or null,
  "thickness_candidate": string or null,
  "missing_fields": ["list of fields that could not be determined"],
  "warnings": ["any issues found"],
  "confidence": number from 0.0 to 1.0
}}

Do NOT include any text outside the JSON. Use Chinese for material/treatment names if applicable."""

    def _chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> str | None:
        """Send a chat request. Returns content string or None."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        cacheable = temperature <= 0.1
        cache_key = hashlib.sha256(
            json.dumps(
                {
                    "schema": 1,
                    "base_url": self._base_url,
                    **payload,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if cacheable:
            with self._cache_lock:
                cached = self._response_cache.get(cache_key)
                if cached is not None:
                    self._response_cache.move_to_end(cache_key)
                    self.cache_hits += 1
                    self.last_error = None
                    return cached
                self.cache_misses += 1
        if time.monotonic() < self._circuit_open_until:
            return None

        request_payload = {**payload, "thinking": {"type": "disabled"}}
        for attempt in range(2):
            try:
                content = self._send_request(request_payload)
                self._circuit_open_until = 0.0
                self.last_error = None
                if cacheable and content and self._parse_json_object(content) is not None:
                    with self._cache_lock:
                        self._response_cache[cache_key] = content
                        self._response_cache.move_to_end(cache_key)
                        while len(self._response_cache) > self._cache_limit:
                            self._response_cache.popitem(last=False)
                return content
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400 and "thinking" in request_payload:
                    # Compatibility fallback for gateways without the thinking field.
                    request_payload = payload
                    continue
                if exc.response.status_code >= 500 and attempt == 0:
                    time.sleep(0.5)
                    continue
                self.last_error = f"AI服务返回 HTTP {exc.response.status_code}"
                self._circuit_open_until = time.monotonic() + 30.0
                return None
            except httpx.RequestError as exc:
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                self.last_error = f"AI服务连接失败：{exc}"
                self._circuit_open_until = time.monotonic() + 30.0
                return None
            except Exception as exc:
                self.last_error = f"AI调用失败：{exc}"
                self._circuit_open_until = time.monotonic() + 30.0
                return None
        return None

    def clear_response_cache(self) -> None:
        """Clear this client's exact-input cache (primarily for tests/admin tools)."""
        with self._cache_lock:
            self._response_cache.clear()

    def _send_request(self, payload: dict[str, Any]) -> str | None:
        """Send a single request and extract message.content."""
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data.get("choices", [{}])[0]
        finish_reason = choice.get("finish_reason", "")
        message = choice.get("message", {})

        # NEVER expose reasoning_content
        content = message.get("content", "")

        if finish_reason == "length":
            # Content was truncated
            if not content or not content.strip():
                return None

        if not content or not content.strip():
            return None

        return content

    def _parse_extraction_response(self, content: str) -> dict[str, Any] | None:
        """Parse AI JSON response into structured dict."""
        try:
            # Try direct JSON parse
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if m:
                try:
                    result = json.loads(m.group(1))
                except json.JSONDecodeError:
                    return None
            else:
                # Try to find any JSON object
                m = re.search(r'\{.*\}', content, re.DOTALL)
                if m:
                    try:
                        result = json.loads(m.group(0))
                    except json.JSONDecodeError:
                        return None
                else:
                    return None

        return {
            "drawing_number": result.get("drawing_number"),
            "material_candidate": result.get("material_candidate"),
            "surface_treatment_candidate": result.get("surface_treatment_candidate"),
            "heat_treatment_candidate": result.get("heat_treatment_candidate"),
            "thickness_candidate": result.get("thickness_candidate"),
            "missing_fields": result.get("missing_fields", []),
            "warnings": result.get("warnings", []),
            "confidence": float(result.get("confidence", 0.0)),
        }

    @staticmethod
    def _parse_json_object(content: str) -> dict[str, Any] | None:
        """Parse a JSON object, tolerating a Markdown code fence."""
        try:
            value = json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if not match:
                match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                return None
            try:
                value = json.loads(match.group(1) if match.lastindex else match.group(0))
            except json.JSONDecodeError:
                return None
        return value if isinstance(value, dict) else None
