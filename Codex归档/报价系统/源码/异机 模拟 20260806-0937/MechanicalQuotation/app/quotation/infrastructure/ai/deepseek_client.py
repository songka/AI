"""DeepSeek API Client for AI-assisted drawing extraction."""

from __future__ import annotations

import json
import time
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

    def __init__(
        self,
        base_url: str = "http://10.97.144.27:3000/v1",
        model: str = "deepseek-v4-flash",
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        max_tokens: int = 1024,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_tokens = max_tokens

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
        """Estimate unknown costs for human review without changing formal prices."""
        if not self.is_configured or not items:
            return []
        bounded_items = items[:20]
        bounded_context = "\n".join(context or [])[:12000]
        prompt = f"""你是机械加工报价审核助手。请对待确认费用行给出人民币未税参考估价。
这些价格仅供人工审核，不能视为正式报价。不得编造精确供应商来源；信息不足时降低可信度并说明假设。

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
        prompt = f"""你是机械制造工艺审核员。根据图纸文字和几何摘要判断成本最低且足够完成零件的必要加工工艺。
只能使用以下代码：{', '.join(allowed)}。不要输出材料、表面处理、焊接或装配；没有充分依据就不要选择。
普通平面、直边、槽和常规孔可由三轴普通铣床完成时优先选择 MILL；不能仅因存在孔或螺纹就选择 CNC。
只有图纸明确要求 CNC/加工中心，或存在复杂曲面、多轴联动、高重复定位精度等普通铣床不足以完成的证据时才选择 CNC。
同一项去除加工不要同时返回 CNC 和 MILL；车削件优先 LATHE。必须在 evidence 中说明选择该设备而不是更昂贵设备的依据。
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
                hours = min(max(float(value.get("estimated_hours", 0)), 0), 100)
                confidence = min(max(float(value.get("confidence", 0)), 0), 1)
            except (TypeError, ValueError):
                continue
            if hours <= 0 or confidence < 0.6:
                continue
            seen.add(code)
            clean.append({
                "code": code,
                "process_name": allowed[code],
                "estimated_hours": round(hours, 2),
                "confidence": round(confidence, 2),
                "evidence": str(value.get("evidence") or "AI 工艺判断")[:500],
            })
        return clean

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
    ) -> str | None:
        """Send a chat request. Returns content string or None."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self._max_tokens,
        }

        request_payload = {**payload, "thinking": {"type": "disabled"}}
        for attempt in range(2):
            try:
                return self._send_request(request_payload)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400 and "thinking" in request_payload:
                    # Compatibility fallback for gateways without the thinking field.
                    request_payload = payload
                    continue
                if exc.response.status_code >= 500 and attempt == 0:
                    time.sleep(0.5)
                    continue
                return None
            except httpx.RequestError:
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                return None
            except Exception:
                return None
        return None

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
