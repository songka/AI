from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from packaging.version import InvalidVersion, Version

from .models import ModelCapability
from .storage import create_backup, opencode_config_path
from .api import is_excluded_model


def _eligible(models: Iterable[ModelCapability], target: str) -> list[ModelCapability]:
    eligible = [m for m in models if not is_excluded_model(m.model_id) and getattr(m, f"{target}_compatible")]
    return eligible


def _set_user_environment(name: str, value: str) -> None:
    if os.name != "nt":
        os.environ[name] = value
        return
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
    try: winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
    finally: winreg.CloseKey(key)


@dataclass
class Preview:
    title: str
    text: str


class Configurator:
    def __init__(self, gateway_url: str, token: str, models: list[ModelCapability]):
        self.gateway_url, self.token = gateway_url.rstrip("/"), token
        # Defense in depth: never configure internal review models even if a
        # stale window/cache passed one into this object.
        self.models = [model for model in models if not is_excluded_model(model.model_id)]

    def preview(self, targets: set[str]) -> Preview:
        chunks: list[str] = []
        if "codex" in targets:
            entries = _eligible(self.models, "codex")
            chunks.append("Codex\n  条件：Responses 的文本、流式、工具调用均实测通过。\n"
                          f"  通过：{len(entries)} 个\n  " + (", ".join(x.model_id for x in entries) or "无"))
        if "claude" in targets:
            entries = _eligible(self.models, "claude")
            chunks.append("Claude Code\n  条件：Messages 的文本和流式均实测通过；工具调用结果单独标注，不阻止配置。排除 Codex 映射模型。\n"
                          f"  通过：{len(entries)} 个\n  " + (", ".join(x.model_id for x in entries) or "无"))
        if "opencode" in targets:
            entries = _eligible(self.models, "opencode")
            chunks.append("OpenCode\n  条件：Chat（优先）或 Responses 的文本和流式均实测通过；工具、上下文和输出限制会按实际已知值生成。\n"
                          f"  通过：{len(entries)} 个\n  " + (", ".join(x.model_id for x in entries) or "无"))
        return Preview("配置预览（不会写入）", "\n\n".join(chunks) or "尚未选择配置目标。")

    def apply(self, targets: set[str]) -> list[str]:
        backup = create_backup()
        results: list[str] = [f"已创建配置备份：{backup}"]
        if "codex" in targets: results.append(self._write_codex())
        if "claude" in targets: results.append(self._write_claude())
        if "opencode" in targets: results.append(self._write_opencode())
        return results

    def _write_codex(self) -> str:
        models = _eligible(self.models, "codex")
        if not models: return "Codex：跳过，没有兼容模型。"
        try:
            import tomlkit
            path = Path.home() / ".codex" / "config.toml"; path.parent.mkdir(parents=True, exist_ok=True)
            doc = tomlkit.parse(path.read_text(encoding="utf-8")) if path.exists() else tomlkit.document()
            providers = doc.setdefault("model_providers", tomlkit.table())
            provider = tomlkit.table(); provider.add("name", "NewAPI"); provider.add("base_url", f"{self.gateway_url}/v1"); provider.add("env_key", "NEWAPI_API_KEY")
            providers["newapi"] = provider
            if "model_provider" not in doc: doc["model_provider"] = "newapi"
            path.write_text(tomlkit.dumps(doc), encoding="utf-8")
            _set_user_environment("NEWAPI_API_KEY", self.token)
            return f"Codex：已配置 {path}"
        except Exception as exc: return f"Codex：配置失败：{exc}"

    def _write_claude(self) -> str:
        models = _eligible(self.models, "claude")
        if not models: return "Claude Code：跳过，没有兼容模型。"
        path = Path.home() / ".claude" / "settings.json"
        try:
            existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            if not isinstance(existing, dict):
                return "Claude Code：配置失败，settings.json 顶层必须是 JSON 对象。"
            environment = existing.get("env", {})
            if not isinstance(environment, dict):
                return "Claude Code：配置失败，settings.json 中的 env 必须是 JSON 对象。"
            # Base URL and model choices are safe to keep in settings. The
            # authentication token remains only in the user environment.
            environment.update({"ANTHROPIC_BASE_URL": self.gateway_url, "ANTHROPIC_MODEL": models[0].model_id, "ANTHROPIC_SMALL_FAST_MODEL": models[0].model_id})
            existing["env"] = environment
            existing["availableModels"] = [model.model_id for model in models]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError) as exc:
            return f"Claude Code：配置失败：无法读取或合并 {path}：{exc}"
        _set_user_environment("ANTHROPIC_BASE_URL", self.gateway_url)
        _set_user_environment("ANTHROPIC_AUTH_TOKEN", self.token)
        _set_user_environment("ANTHROPIC_MODEL", models[0].model_id)
        _set_user_environment("ANTHROPIC_SMALL_FAST_MODEL", models[0].model_id)
        # Do not set global thinking-disabling variables: capability varies by model.
        return f"Claude Code：已合并 {path}，认证令牌已写入当前用户环境变量。"

    def _write_opencode(self) -> str:
        models = _eligible(self.models, "opencode")
        if not models: return "OpenCode：跳过，没有兼容模型。"
        generated = opencode_config_path()
        adapter = OpenCodeV2Adapter() if self._opencode_major_version() >= 2 else OpenCodeV1Adapter()
        data = adapter.build(self.gateway_url, models, self._opencode_model)
        try:
            existing = json.loads(generated.read_text(encoding="utf-8")) if generated.exists() else {}
            if not isinstance(existing, dict):
                return "OpenCode：配置失败，opencode.json 顶层必须是 JSON 对象。"
            # Preserve all user configuration; overwrite only the NewAPI
            # provider section managed by this application.
            root_key = adapter.key
            providers = existing.get(root_key, {})
            if not isinstance(providers, dict):
                return f"OpenCode：配置失败，{root_key} 必须是 JSON 对象。"
            providers["newapi"] = data[root_key]["newapi"]
            existing[root_key] = providers
            existing.setdefault("$schema", "https://opencode.ai/config.json")
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError) as exc:
            return f"OpenCode：配置失败：无法读取或合并 {generated}：{exc}"
        _set_user_environment("NEWAPI_API_KEY", self.token)
        # Standard global config does not need OPENCODE_CONFIG. Do not delete a
        # user-owned custom override, because it may point to unrelated work.
        verified = self._verify_opencode(generated)
        return f"OpenCode（{adapter.name}）：已合并官方全局配置 {generated}{verified}"

    def _opencode_major_version(self) -> int:
        """Use the local CLI when present; stable V1 remains the safe fallback."""
        try:
            output = subprocess.run(["opencode", "--version"], capture_output=True, text=True, timeout=5, check=False).stdout.strip()
            value = Version(output.lstrip("v").split()[0])
            return value.major
        except (OSError, subprocess.SubprocessError, InvalidVersion, IndexError):
            return 1

    def _verify_opencode(self, config: Path) -> str:
        try:
            env = {**os.environ, "OPENCODE_CONFIG": str(config)}
            check = subprocess.run(["opencode", "debug", "config"], env=env, capture_output=True, text=True, timeout=15, check=False)
            return "\nOpenCode 配置验证通过。" if check.returncode == 0 else "\n配置已保存；本机 OpenCode CLI 不可用或未通过验证。"
        except (OSError, subprocess.SubprocessError):
            return "\n配置已保存；未找到 OpenCode CLI，无法验证。"

    def _opencode_model(self, model: ModelCapability) -> dict:
        route = model.chat if model.chat.text.value == "confirmed" else model.responses
        input_modalities = list(model.input_modalities)
        # A successful vision probe is the authoritative gateway result. The
        # Models.dev record may be unavailable/stale and default to text only.
        if model.vision and "image" not in input_modalities:
            input_modalities.append("image")
        if not model.vision:
            input_modalities = [item for item in input_modalities if item != "image"] or ["text"]
        # False is an explicit known-negative. For a failed/unknown minimal
        # probe, omit tools so OpenCode can use its provider default instead of
        # receiving a misleading permanent prohibition.
        capabilities = {"input": input_modalities, "output": model.output_modalities}
        if route.tools.value == "confirmed":
            capabilities["tools"] = True
        item = {"modelID": model.model_id, "name": model.display_name, "capabilities": capabilities}
        # Do not invent limits when user-confirmed routing lacks metadata. An
        # omitted field is safer than an inaccurate fixed value.
        limits = {key: value for key, value in {"context": model.context_declared, "output": model.max_output_tokens}.items() if value is not None}
        if limits:
            item["limit"] = limits
        if model.reasoning_field: item["compatibility"] = {"reasoningField": model.reasoning_field}
        levels = [level for level, status in model.reasoning_control.items() if status.value == "confirmed"]
        # OpenCode schema expects a map keyed by variant ID, not the array form
        # used by some older examples. The map's values are variant settings.
        if levels:
            item["variants"] = {level: {"reasoningEffort": level} for level in levels}
        return item


class OpenCodeConfigAdapter:
    name = "unknown"
    key = "provider"

    def build(self, gateway_url: str, models: list[ModelCapability], model_builder) -> dict:
        provider = {"newapi": {"npm": "@ai-sdk/openai-compatible", "name": "NewAPI", "options": {"baseURL": f"{gateway_url}/v1", "apiKey": "{env:NEWAPI_API_KEY}"}, "models": {m.model_id: model_builder(m) for m in models}}}
        return {"$schema": "https://opencode.ai/config.json", self.key: provider}


class OpenCodeV1Adapter(OpenCodeConfigAdapter):
    name = "V1 适配器"
    key = "provider"


class OpenCodeV2Adapter(OpenCodeConfigAdapter):
    name = "V2 适配器"
    key = "providers"
