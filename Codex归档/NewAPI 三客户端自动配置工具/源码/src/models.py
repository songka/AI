from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Source(str, Enum):
    API = "API probe"
    MODELS_DEV = "Models.dev"
    OFFICIAL = "Official metadata"
    MANUAL = "Manual"
    UNKNOWN = "Unknown"


class ProbeStatus(str, Enum):
    CONFIRMED = "confirmed"
    DECLARED = "declared"
    UNKNOWN = "unknown"
    FAILED = "failed"


class ProtocolResult(BaseModel):
    text: ProbeStatus = ProbeStatus.UNKNOWN
    streaming: ProbeStatus = ProbeStatus.UNKNOWN
    tools: ProbeStatus = ProbeStatus.UNKNOWN
    vision: ProbeStatus = ProbeStatus.UNKNOWN
    reasoning: ProbeStatus = ProbeStatus.UNKNOWN
    latency_ms: float | None = None
    first_token_latency_ms: float | None = None
    error: str | None = None


class ModelCapability(BaseModel):
    model_id: str
    display_name: str
    available: bool = True
    responses: ProtocolResult = Field(default_factory=ProtocolResult)
    messages: ProtocolResult = Field(default_factory=ProtocolResult)
    chat: ProtocolResult = Field(default_factory=ProtocolResult)
    reasoning_control: dict[str, ProbeStatus] = Field(default_factory=dict)
    reasoning_control_protocol: str | None = None
    reasoning_field: str | None = None
    context_declared: int | None = None
    context_verified_min: int | None = None
    context_source: Source = Source.UNKNOWN
    max_output_tokens: int | None = None
    input_modalities: list[str] = Field(default_factory=lambda: ["text"])
    output_modalities: list[str] = Field(default_factory=lambda: ["text"])
    test_time: datetime | None = None
    error: str | None = None

    # Explicit choices supplied by the user for this gateway. These are kept
    # separate from API-probe results so the UI never mislabels them as probes.
    manual_clients: list[str] = Field(default_factory=list)
    manual_vision: bool = False
    manual_reasoning: bool = False
    manual_reasoning_field: str | None = None
    manual_reasoning_levels: list[str] = Field(default_factory=list)

    @property
    def codex_compatible(self) -> bool:
        return not self.is_excluded and ("codex" in self.manual_clients or (self.responses.text is ProbeStatus.CONFIRMED and self.responses.streaming is ProbeStatus.CONFIRMED and self.responses.tools is ProbeStatus.CONFIRMED))

    @property
    def responses_supported(self) -> bool:
        return self.responses.text is ProbeStatus.CONFIRMED

    @property
    def messages_supported(self) -> bool:
        return self.messages.text is ProbeStatus.CONFIRMED

    @property
    def chat_supported(self) -> bool:
        return self.chat.text is ProbeStatus.CONFIRMED

    @property
    def streaming(self) -> bool:
        return any(x.streaming is ProbeStatus.CONFIRMED for x in (self.responses, self.messages, self.chat))

    @property
    def tools(self) -> bool:
        return any(x.tools is ProbeStatus.CONFIRMED for x in (self.responses, self.messages, self.chat))

    @property
    def vision(self) -> bool:
        return self.manual_vision or any(x.vision is ProbeStatus.CONFIRMED for x in (self.responses, self.messages, self.chat))

    @property
    def reasoning(self) -> bool:
        return self.manual_reasoning or self.reasoning_field is not None or any(x.reasoning is ProbeStatus.CONFIRMED for x in (self.responses, self.messages, self.chat))

    @property
    def claude_compatible(self) -> bool:
        # Claude Code can use a model once the real Messages route supports
        # text and streaming. Tool probing is reported separately: gateways may
        # translate tool schemas differently from our minimal test tool.
        return not self.is_excluded and not self.is_codex_alias and ("claude" in self.manual_clients or (self.messages.text is ProbeStatus.CONFIRMED and self.messages.streaming is ProbeStatus.CONFIRMED))

    @property
    def opencode_compatible(self) -> bool:
        route = self.chat if self.chat.text is ProbeStatus.CONFIRMED else self.responses
        # OpenCode only needs a usable OpenAI-compatible streaming route to
        # configure a model. Capability values are included only when known;
        # a failed minimal tool probe is not proof that agents cannot call it.
        probed = route.text is ProbeStatus.CONFIRMED and route.streaming is ProbeStatus.CONFIRMED
        return not self.is_excluded and not self.is_codex_alias and ("opencode" in self.manual_clients or probed)

    @property
    def is_codex_alias(self) -> bool:
        return self.model_id.lower() in {"gpt-5.4", "gpt-5.4-mini"}

    @property
    def is_excluded(self) -> bool:
        model_id = self.model_id.strip().lower()
        return model_id == "codex-auto-review" or model_id.startswith("codex-auto-review-")

    def client_source(self, client: str) -> str:
        return "用户确认" if client in self.manual_clients else "API 实测"

    @property
    def effective_reasoning_field(self) -> str | None:
        return self.manual_reasoning_field or self.reasoning_field

    @property
    def effective_reasoning_levels(self) -> list[str]:
        probed = [level for level, status in self.reasoning_control.items() if status is ProbeStatus.CONFIRMED]
        return probed or self.manual_reasoning_levels

    def short_context(self) -> str:
        if self.context_declared is None:
            return "Unknown"
        value = self.context_declared
        return f"{value / 1_000_000:.2g}M" if value >= 1_000_000 else f"{value // 1000}K"

    def context_summary(self) -> str:
        declared = f"声明：{self.short_context()}"
        verified = f"实测：≥{self.context_verified_min // 1000}K" if self.context_verified_min else "实测：未通过"
        return f"{declared}\n{verified}"

    def reasoning_summary(self) -> str:
        if self.manual_reasoning:
            return f"用户确认：{', '.join(self.effective_reasoning_levels)}\n字段：{self.effective_reasoning_field or 'reasoning_content'}"
        if not self.reasoning_control:
            return "未检测"
        accepted = [level for level, status in self.reasoning_control.items() if status is ProbeStatus.CONFIRMED]
        if not accepted:
            return "控制：不支持"
        field = self.reasoning_field or "未返回推理字段"
        return f"控制：{', '.join(accepted)}\n字段：{field}"


class ScanCache(BaseModel):
    gateway_url: str
    capabilities: list[ModelCapability]
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
