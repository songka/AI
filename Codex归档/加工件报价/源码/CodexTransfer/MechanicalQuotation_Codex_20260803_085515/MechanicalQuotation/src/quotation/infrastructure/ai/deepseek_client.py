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
                return {
                    "configured": True,
                    "reachable": False,
                    "model": self._model,
                    "latency_ms": round(latency_ms, 1),
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            latency_ms = (time.monotonic() - t0) * 1000
            return {
                "configured": True,
                "reachable": False,
                "model": self._model,
                "latency_ms": round(latency_ms, 1),
                "error": str(e),
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

        # First attempt: with thinking disabled
        try:
            return self._send_request({**payload, "thinking": {"type": "disabled"}})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                # Retry without thinking field
                try:
                    return self._send_request(payload)
                except Exception:
                    return None
            return None
        except Exception:
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
