"""HTTP client for protocol-v1 external quotation Skills."""

from __future__ import annotations

import json
import subprocess
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
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def discover(self, endpoint: str) -> ExternalSkillDefinition:
        source_type, location = self._resolve_location(endpoint)
        if source_type == SkillSourceType.HTTP:
            payload = self._json_request(f"{location}/v1/capabilities", method="GET")
        else:
            payload = self._read_folder_manifest(Path(location))
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
        entrypoint = str(manifest.get("entrypoint", "")).strip()
        if not entrypoint:
            raise ValueError("文件夹 Skill 的 skill.json 缺少 entrypoint")
        executable = (folder / entrypoint).resolve()
        root = folder.resolve()
        if not executable.is_relative_to(root) or executable.suffix.casefold() != ".exe":
            raise ValueError("文件夹 Skill 的 entrypoint 必须是文件夹内的 .exe")
        if not executable.is_file():
            raise ValueError(f"Skill 执行文件不存在：{entrypoint}")
        try:
            completed = subprocess.run(
                [str(executable)],
                input=json.dumps(request_payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(root),
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"文件夹 Skill 执行失败：{exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip()[:500] or f"退出码 {completed.returncode}"
            raise RuntimeError(f"文件夹 Skill 执行失败：{detail}")
        if len(completed.stdout.encode("utf-8")) > 5 * 1024 * 1024:
            raise ValueError("外接 Skill 响应超过 5 MB 限制")
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("文件夹 Skill 返回的不是有效 UTF-8 JSON") from exc
        if not isinstance(result, dict):
            raise ValueError("外接 Skill 响应必须是 JSON 对象")
        return result

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
