from __future__ import annotations

import asyncio
import base64
import json
import random
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from io import BytesIO
from typing import Any, AsyncIterator

import httpx
from PIL import Image, ImageDraw, ImageFont

from .models import ModelCapability, ProbeStatus, ProtocolResult, Source


# This is an internal review model, not a user-selectable client model. Keep it
# out of scanning as well as configuration so cached results cannot reintroduce it.
EXCLUDED_MODEL_IDS = {"codex-auto-review"}


def is_excluded_model(model_id: str) -> bool:
    normalized = model_id.strip().lower()
    return normalized in EXCLUDED_MODEL_IDS or normalized.startswith("codex-auto-review-")


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def display_name(model_id: str) -> str:
    return model_id.replace("-", " ").replace("_", " ").title()


def _has_text(payload: Any) -> bool:
    def strings(value: Any, meaningful_key: bool = False) -> list[str]:
        if isinstance(value, dict):
            return [s for key, child in value.items() for s in strings(child, key in {"text", "content", "output_text"})]
        if isinstance(value, list):
            return [s for child in value for s in strings(child, meaningful_key)]
        return [value.strip()] if meaningful_key and isinstance(value, str) else []
    return any(value for value in strings(payload))


def _reasoning_field(payload: Any) -> str | None:
    raw = json.dumps(payload, ensure_ascii=False)
    for field in ("reasoning_content", "reasoning_text", "thinking", "reasoning"):
        if f'"{field}"' in raw:
            return field
    return None


def _tool_called(payload: Any) -> bool:
    raw = json.dumps(payload, ensure_ascii=False)
    return "get_test_code" in raw and any(key in raw for key in ("tool_call", "function_call", "tool_use"))


def make_image() -> tuple[str, str]:
    code = f"{random.randint(0, 9999):04d}"
    image = Image.new("RGB", (520, 240), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=72)
    box = draw.textbbox((0, 0), code, font=font)
    draw.text(((520 - (box[2] - box[0])) / 2, (240 - (box[3] - box[1])) / 2), code, fill="black", font=font)
    stream = BytesIO(); image.save(stream, format="PNG")
    return code, base64.b64encode(stream.getvalue()).decode()


class NewAPI:
    def __init__(self, base_url: str, token: str, timeout: float = 35.0):
        self.base_url = normalize_url(base_url)
        self.headers = {"Authorization": f"Bearer {token}"}
        self.client = httpx.AsyncClient(timeout=timeout, headers=self.headers)

    async def close(self) -> None:
        await self.client.aclose()

    async def models(self) -> list[str]:
        response = await self.client.get(f"{self.base_url}/v1/models")
        response.raise_for_status()
        data = response.json().get("data", [])
        return [str(item["id"]) for item in data if isinstance(item, dict) and item.get("id") and not is_excluded_model(str(item["id"]))]

    async def request(self, route: str, body: dict[str, Any]) -> tuple[dict[str, Any], float]:
        start = time.perf_counter()
        headers = {"anthropic-version": "2023-06-01"} if route == "/v1/messages" else None
        response = await self.client.post(f"{self.base_url}{route}", json=body, headers=headers)
        response.raise_for_status()
        return response.json(), (time.perf_counter() - start) * 1000

    async def stream(self, route: str, body: dict[str, Any]) -> tuple[list[str], float | None]:
        started = time.perf_counter(); first = None; events: list[str] = []
        headers = {"anthropic-version": "2023-06-01"} if route == "/v1/messages" else None
        async with self.client.stream("POST", f"{self.base_url}{route}", json=body, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                if first is None:
                    first = (time.perf_counter() - started) * 1000
                events.append(line)
        return events, first


class MetadataResolver:
    URL = "https://models.dev/api.json"

    async def resolve(self, model_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self.URL)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return {}
        candidates = self._walk(data)
        exact = next((x for x in candidates if x.get("id") == model_id), None)
        if exact:
            return exact
        canonical = model_id.lower().replace("-latest", "")
        return next((x for x in candidates if str(x.get("id", "")).lower() == canonical), {})

    def _walk(self, obj: Any) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if isinstance(obj, dict):
            models = obj.get("models")
            if isinstance(models, dict):
                for model_id, model in models.items():
                    if isinstance(model, dict):
                        found.append({"id": model_id, **model})
            if "id" in obj and ("limit" in obj or "modalities" in obj):
                found.append(obj)
            for value in obj.values(): found.extend(self._walk(value))
        elif isinstance(obj, list):
            for value in obj: found.extend(self._walk(value))
        return found


def _response_body(model: str, stream: bool = False, tools: bool = False, image: str | None = None, reasoning: str | None = None) -> dict[str, Any]:
    content: list[dict[str, str]] = [{"type": "input_text", "text": "Only reply: OK"}]
    if image: content = [{"type": "input_text", "text": "Read the 4-digit number in the image. Reply only with the digits."}, {"type": "input_image", "image_url": f"data:image/png;base64,{image}"}]
    body: dict[str, Any] = {"model": model, "input": [{"role": "user", "content": content}], "stream": stream, "max_output_tokens": 32}
    if reasoning: body["reasoning"] = {"effort": reasoning}
    if tools:
        body["tools"] = [{"type": "function", "name": "get_test_code", "description": "Return test code", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}]
        body["input"] = "You must call get_test_code with code TEST123. Do not answer directly."
    return body


def _chat_body(model: str, stream: bool = False, tools: bool = False, image: str | None = None, reasoning: str | None = None) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "user", "content": "Only reply: OK"}
    if image: message["content"] = [{"type": "text", "text": "Read the 4-digit number in the image. Reply only with the digits."}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}}]
    if tools: message["content"] = "You must call get_test_code with code TEST123. Do not answer directly."
    body: dict[str, Any] = {"model": model, "messages": [message], "stream": stream, "max_tokens": 32}
    if reasoning: body["reasoning_effort"] = reasoning
    if tools: body["tools"] = [{"type": "function", "function": {"name": "get_test_code", "description": "Return test code", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]
    return body


def _messages_body(model: str, stream: bool = False, tools: bool = False, image: str | None = None) -> dict[str, Any]:
    content: Any = "Only reply: OK"
    if image: content = [{"type": "text", "text": "Read the 4-digit number in the image. Reply only with the digits."}, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image}}]
    if tools: content = "You must call get_test_code with code TEST123. Do not answer directly."
    body: dict[str, Any] = {"model": model, "max_tokens": 32, "messages": [{"role": "user", "content": content}], "stream": stream}
    if tools: body["tools"] = [{"name": "get_test_code", "description": "Return test code", "input_schema": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}]
    return body


def _context_body(route: str, model: str, tokens: int = 8192) -> dict[str, Any]:
    # A deliberately simple, countable payload. This records a verified lower
    # bound, never an asserted maximum context window.
    prompt = ("x " * tokens) + "\nReply only: OK"
    if route == "/v1/responses":
        return {"model": model, "input": prompt, "max_output_tokens": 1}
    if route == "/v1/chat/completions":
        return {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1}
    return {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1}


def _usage_input_tokens(payload: Any) -> int | None:
    if not isinstance(payload, dict):
        return None
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    for field in ("input_tokens", "prompt_tokens"):
        value = usage.get(field)
        if isinstance(value, int) and value > 0:
            return value
    return None


class CapabilityScanner:
    def __init__(self, gateway: NewAPI, log):
        self.gateway, self.log, self.metadata = gateway, log, MetadataResolver()

    async def scan_one(self, model_id: str, deep: bool = False) -> ModelCapability:
        cap = ModelCapability(model_id=model_id, display_name=display_name(model_id))
        meta = await self.metadata.resolve(model_id)
        self._apply_metadata(cap, meta)
        self.log(f"开始检测：{model_id}")
        cap.responses = await self._probe("/v1/responses", _response_body, model_id)
        cap.chat = await self._probe("/v1/chat/completions", _chat_body, model_id)
        cap.messages = await self._probe("/v1/messages", _messages_body, model_id)
        await self._probe_context(model_id, cap, deep)
        cap.reasoning_field = await self._probe_reasoning(model_id, cap)
        cap.test_time = datetime.now(timezone.utc)
        return cap

    def _apply_metadata(self, cap: ModelCapability, meta: dict[str, Any]) -> None:
        limit = meta.get("limit") or {}
        modalities = meta.get("modalities") or {}
        if isinstance(limit.get("context"), int): cap.context_declared, cap.context_source = limit["context"], Source.MODELS_DEV
        if isinstance(limit.get("output"), int): cap.max_output_tokens = limit["output"]
        if isinstance(modalities.get("input"), list): cap.input_modalities = modalities["input"]
        if isinstance(modalities.get("output"), list): cap.output_modalities = modalities["output"]

    async def _probe(self, route: str, factory, model: str) -> ProtocolResult:
        result = ProtocolResult()
        try:
            payload, latency = await self.gateway.request(route, factory(model))
            result.text, result.latency_ms = (ProbeStatus.CONFIRMED if _has_text(payload) else ProbeStatus.FAILED), latency
            field = _reasoning_field(payload)
            result.reasoning = ProbeStatus.CONFIRMED if field else ProbeStatus.UNKNOWN
        except Exception as exc:
            result.error = str(exc)[:180]; result.text = ProbeStatus.FAILED; return result
        try:
            events, first = await self.gateway.stream(route, factory(model, stream=True))
            result.streaming = ProbeStatus.CONFIRMED if events else ProbeStatus.FAILED; result.first_token_latency_ms = first
        except Exception as exc: result.streaming = ProbeStatus.FAILED; result.error = str(exc)[:180]
        try:
            payload, _ = await self.gateway.request(route, factory(model, tools=True))
            result.tools = ProbeStatus.CONFIRMED if _tool_called(payload) else ProbeStatus.FAILED
        except Exception: result.tools = ProbeStatus.FAILED
        try:
            expected, image = make_image(); payload, _ = await self.gateway.request(route, factory(model, image=image))
            result.vision = ProbeStatus.CONFIRMED if expected in json.dumps(payload) else ProbeStatus.FAILED
        except Exception: result.vision = ProbeStatus.FAILED
        return result

    async def _probe_context(self, model: str, cap: ModelCapability, deep: bool) -> None:
        stages = [8192]
        if deep:
            # The declaration is an upper bound, never a justification to send
            # more than the user has expressly requested through deep mode.
            stages += [size for size in (32768, 65536, 131072, 262144, 524288, 1048576) if cap.context_declared is None or size <= cap.context_declared]
        for route, result in (("/v1/responses", cap.responses), ("/v1/chat/completions", cap.chat), ("/v1/messages", cap.messages)):
            if result.text is not ProbeStatus.CONFIRMED:
                continue
            for size in stages:
                try:
                    payload, _ = await self.gateway.request(route, _context_body(route, model, size))
                    # A successful HTTP request alone is not proof of an input
                    # token count. Only record a numeric lower bound if the
                    # gateway returned actual usage for the prompt.
                    input_tokens = _usage_input_tokens(payload)
                    if input_tokens:
                        cap.context_verified_min = max(cap.context_verified_min or 0, input_tokens)
                        self.log(f"{model}: 上下文实测下限 ≥{cap.context_verified_min // 1000}K（{route}）")
                    else:
                        self.log(f"{model}: 上下文请求成功，但网关未返回 input_tokens，不能确认数值下限。")
                except Exception as exc:
                    self.log(f"{model}: 上下文 {size // 1000}K 未通过；已确认下限为 ≥{(cap.context_verified_min or 0) // 1000}K")
                    break
            return

    async def _probe_reasoning(self, model: str, cap: ModelCapability) -> str | None:
        field = None
        # Chat Completions is the most broadly implemented OpenAI-compatible
        # surface for reasoning_effort. Record accepted levels, not guesses.
        if cap.chat.text is not ProbeStatus.CONFIRMED:
            return None
        cap.reasoning_control_protocol = "Chat"
        for level in ("low", "medium", "high", "none", "xhigh", "max"):
            try:
                body = _chat_body(model, reasoning=level)
                body["messages"] = [{"role": "user", "content": "Calculate 17 times 29 carefully, then give only the answer."}]
                payload, _ = await self.gateway.request("/v1/chat/completions", body)
                cap.reasoning_control[level] = ProbeStatus.CONFIRMED
                found = _reasoning_field(payload)
                field = field or found
                if found:
                    cap.chat.reasoning = ProbeStatus.CONFIRMED
            except Exception:
                cap.reasoning_control[level] = ProbeStatus.FAILED
        if any(status is ProbeStatus.CONFIRMED for status in cap.reasoning_control.values()) and cap.chat.reasoning is not ProbeStatus.CONFIRMED:
            cap.chat.reasoning = ProbeStatus.DECLARED
        self.log(f"{model}: 推理控制（Chat）已接受 {', '.join(level for level, status in cap.reasoning_control.items() if status is ProbeStatus.CONFIRMED) or '无'}")
        return field
