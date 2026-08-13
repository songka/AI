"""HTTP transport and DeepSeek-backed folder Skills for protocol v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from quotation.application.external_skill_settings import (
    ExternalSkillDefinition,
    SkillSourceType,
    SkillStep,
)


class ExternalSkillClient:
    def __init__(
        self,
        timeout_seconds: float = 15.0,
        opener: Callable[..., Any] = urlopen,
        ai_client: Any = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self._opener = opener
        self._ai_client = ai_client

    def discover(self, endpoint: str) -> ExternalSkillDefinition:
        source_type, location = self._resolve_location(endpoint)
        if source_type == SkillSourceType.HTTP:
            payload = self._json_request(f"{location}/v1/capabilities", method="GET")
        else:
            payload = self._read_folder_manifest(Path(location))
            self._read_folder_instructions(Path(location), payload)
        if payload.get("protocol_version") != "1.0":
            raise ValueError("外接 Skill 不支持接口协议 1.0")
        return ExternalSkillDefinition(
            skill_id=payload["skill_id"],
            name_zh=payload["skill_name_zh"],
            endpoint=location,
            source_type=source_type,
            skill_version=payload["skill_version"],
            protocol_version=payload["protocol_version"],
            supported_steps=[SkillStep(item) for item in payload["supported_steps"]],
            supports_full_quotation=bool(payload["supports_full_quotation"]),
            enabled=True,
        )

    def invoke(self, endpoint: str, request_payload: dict[str, Any]) -> dict[str, Any]:
        source_type, location = self._resolve_location(endpoint)
        if source_type == SkillSourceType.FOLDER:
            return self._invoke_folder(Path(location), request_payload)
        request_id = str(request_payload.get("request_id", ""))
        return self._json_request(
            f"{location}/v1/quote",
            method="POST",
            payload=request_payload,
            headers={
                "X-Request-Id": request_id,
                "X-Skill-Protocol-Version": "1.0",
            },
        )

    def _json_request(
        self,
        url: str,
        *,
        method: str,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
        request = Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read(5 * 1024 * 1024 + 1)
        except Exception as exc:
            raise RuntimeError(f"外接 Skill 连接失败：{exc}") from exc
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError("外接 Skill 响应超过 5 MB 限制")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("外接 Skill 返回的不是有效 UTF-8 JSON") from exc
        if not isinstance(result, dict):
            raise ValueError("外接 Skill 响应必须是 JSON 对象")
        return result

    @staticmethod
    def _read_folder_manifest(folder: Path) -> dict[str, Any]:
        if not folder.is_dir():
            raise ValueError(f"Skill 文件夹不存在或无法访问：{folder}")
        manifest = folder / "skill.json"
        if not manifest.is_file():
            raise ValueError("Skill 文件夹缺少 skill.json")
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"无法读取 Skill 文件夹清单：{exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("skill.json 必须是 JSON 对象")
        return payload

    def _invoke_folder(
        self, folder: Path, request_payload: dict[str, Any]
    ) -> dict[str, Any]:
        manifest = self._read_folder_manifest(folder)
        if self._ai_client is None or not getattr(self._ai_client, "is_configured", False):
            raise RuntimeError("文件夹 Skill 需要先配置程序内置 DeepSeek")
        instructions = self._read_folder_instructions(folder, manifest)
        result = self._ai_client.invoke_quotation_skill(instructions, request_payload)
        if not isinstance(result, dict):
            raise ValueError("DeepSeek 未按文件夹 Skill 返回有效协议 JSON")
        return result

    @staticmethod
    def _read_folder_instructions(folder: Path, manifest: dict[str, Any]) -> str:
        root = folder.resolve()
        requested = [str(manifest.get("instruction_file") or "SKILL.md")]
        requested.extend(str(item) for item in manifest.get("reference_files", []))
        sections: list[str] = []
        total_bytes = 0
        for relative in requested:
            path = (folder / relative).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Skill 文档路径不能跳出 Skill 文件夹")
            if path.suffix.casefold() not in {".md", ".txt", ".json", ".yaml", ".yml"}:
                raise ValueError(f"不支持的 Skill 文档格式：{relative}")
            if not path.is_file():
                raise ValueError(f"Skill 文档不存在：{relative}")
            raw = path.read_bytes()
            total_bytes += len(raw)
            if total_bytes > 128 * 1024:
                raise ValueError("Skill 指令与参考文档合计不能超过 128 KB")
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"Skill 文档必须使用 UTF-8：{relative}") from exc
            sections.append(f"\n## 文件：{relative}\n{content.strip()}")
        return "\n".join(sections).strip()

    @classmethod
    def _resolve_location(cls, endpoint: str) -> tuple[SkillSourceType, str]:
        value = endpoint.strip()
        if value.casefold().startswith(("http://", "https://")):
            return SkillSourceType.HTTP, cls._validated_endpoint(value)
        if not value:
            raise ValueError("请输入 HTTP 地址、本地文件夹或 SMB 公共槽文件夹")
        return SkillSourceType.FOLDER, str(Path(value))

    @staticmethod
    def _validated_endpoint(endpoint: str) -> str:
        value = endpoint.strip().rstrip("/")
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Skill 地址必须是有效的 HTTP 或 HTTPS 地址")
        if parsed.username or parsed.password:
            raise ValueError("Skill 地址不能包含用户名或密码")
        return value
