"""HTTP transport and DeepSeek-backed folder Skills for protocol v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from quotation.application.external_skill_settings import (
    AgentDefinition,
    AgentSourceType,
    ExternalSkillDefinition,
    SkillCommandCapability,
    SkillSourceType,
    SkillStep,
    SkillTaskType,
)
from quotation.application.external_skill_command import ExternalSkillCommandRunner


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
        excel_export = payload.get("excel_export") or {}
        commands = payload.get("commands") or []
        command_capabilities = [
            SkillCommandCapability.model_validate(item) for item in commands
        ]
        command_excel_export = any(
            SkillTaskType.EXCEL_EXPORT in item.task_types
            for item in command_capabilities
        )
        return ExternalSkillDefinition(
            skill_id=payload["skill_id"],
            name_zh=payload["skill_name_zh"],
            endpoint=location,
            source_type=source_type,
            skill_version=payload["skill_version"],
            protocol_version=payload["protocol_version"],
            supported_steps=[SkillStep(item) for item in payload["supported_steps"]],
            supports_full_quotation=bool(payload["supports_full_quotation"]),
            supports_excel_export=(
                bool(excel_export.get("enabled", False)) or command_excel_export
            ),
            excel_export_command=[str(item) for item in excel_export.get("command", [])],
            excel_export_timeout_seconds=int(excel_export.get("timeout_seconds", 60)),
            execution_requirements=[
                str(item) for item in excel_export.get("requirements", [])
            ],
            command_capabilities=command_capabilities,
            supported_processes=payload.get("supported_processes", []),
            step_agent_routes={
                SkillStep(step): str(agent_id)
                for step, agent_id in (payload.get("step_agent_routes") or {}).items()
            },
            enabled=True,
        )

    def discover_agent(self, endpoint: str) -> AgentDefinition:
        source_type, location = self._resolve_location(endpoint)
        if source_type == SkillSourceType.HTTP:
            payload = self._json_request(f"{location}/v1/agent-capabilities", method="GET")
            agent_source = AgentSourceType.HTTP
        else:
            payload = self._read_agent_manifest(Path(location))
            self._read_folder_instructions(Path(location), payload, default_file="AGENT.md")
            agent_source = AgentSourceType.FOLDER
        if payload.get("protocol_version") != "1.0":
            raise ValueError("外挂智能体不支持接口协议 1.0")
        return AgentDefinition(
            agent_id=payload["agent_id"],
            name_zh=payload["agent_name_zh"],
            endpoint=location,
            source_type=agent_source,
            agent_version=payload["agent_version"],
            protocol_version=payload["protocol_version"],
            supported_steps=[SkillStep(item) for item in payload["supported_steps"]],
            supported_processes=payload.get("supported_processes", []),
            description_zh=str(payload.get("description_zh") or ""),
            instruction_file=str(payload.get("instruction_file") or "AGENT.md"),
            reference_files=[str(item) for item in payload.get("reference_files", [])],
            enabled=True,
        )

    def invoke_agent(
        self, agent: AgentDefinition, request_payload: dict[str, Any]
    ) -> dict[str, Any]:
        if agent.source_type == AgentSourceType.BUILTIN:
            raise ValueError("内置智能体由主程序直接执行，不能通过外接接口调用")
        if agent.source_type == AgentSourceType.HTTP:
            return self._json_request(
                f"{agent.endpoint}/v1/quote",
                method="POST",
                payload=request_payload,
                headers={
                    "X-Request-Id": str(request_payload.get("request_id", "")),
                    "X-Skill-Protocol-Version": "1.0",
                },
            )
        folder = Path(agent.endpoint)
        manifest = self._read_agent_manifest(folder)
        if self._ai_client is None or not getattr(self._ai_client, "is_configured", False):
            raise RuntimeError("文件夹智能体需要先配置程序内置 DeepSeek")
        instructions = self._read_folder_instructions(
            folder, manifest, default_file="AGENT.md"
        )
        result = self._ai_client.invoke_quotation_skill(instructions, request_payload)
        if not isinstance(result, dict):
            raise ValueError("DeepSeek 未按外挂智能体协议返回有效 JSON")
        returned_id = str(result.get("skill_id") or result.get("agent_id") or "")
        if returned_id != agent.agent_id:
            warnings = list(result.get("warnings_zh") or [])
            warnings.append("智能体响应 ID 已按 agent.json 自动规范")
            result["warnings_zh"] = warnings
        result["skill_id"] = agent.agent_id
        result["agent_id"] = agent.agent_id
        result.setdefault("skill_version", agent.agent_version)
        return result

    def read_skill_content(self, skill: ExternalSkillDefinition) -> str:
        if skill.source_type == SkillSourceType.BUILTIN:
            return "\n\n".join(
                item
                for item in (skill.description_zh, skill.instruction_content_zh)
                if item.strip()
            )
        if skill.source_type != SkillSourceType.FOLDER:
            return "HTTP Skill 的内部提示词由远端服务管理，本机只能查看公开能力清单。"
        folder = Path(skill.endpoint)
        return self._read_folder_instructions(folder, self._read_folder_manifest(folder))

    def read_agent_content(self, agent: AgentDefinition) -> str:
        if agent.source_type == AgentSourceType.BUILTIN:
            return "\n\n".join(
                item
                for item in (agent.description_zh, agent.instruction_content_zh)
                if item.strip()
            )
        if agent.source_type == AgentSourceType.HTTP:
            return "HTTP 智能体的内部提示词由远端服务管理，本机只能查看公开能力清单。"
        folder = Path(agent.endpoint)
        return self._read_folder_instructions(
            folder, self._read_agent_manifest(folder), default_file="AGENT.md"
        )

    @staticmethod
    def list_folder_files(folder: str | Path) -> list[dict[str, Any]]:
        """Return a safe, display-only inventory including non-text assets."""
        root = Path(folder)
        if not root.is_dir():
            return []
        type_names = {
            ".md": "Markdown",
            ".txt": "文本",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".py": "Python",
            ".exe": "执行档",
            ".bat": "批处理",
            ".cmd": "批处理",
            ".ps1": "PowerShell",
            ".xlsx": "Excel 工作簿",
            ".xlsm": "Excel 工作簿",
            ".xls": "Excel 工作簿",
            ".csv": "CSV",
        }
        rows: list[dict[str, Any]] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            suffix = path.suffix.casefold()
            rows.append(
                {
                    "path": relative,
                    "type": type_names.get(suffix, suffix.lstrip(".").upper() or "文件"),
                    "size": path.stat().st_size,
                    "usage": "仅展示结构；按清单声明决定是否可执行"
                    if suffix not in {".md", ".txt", ".json", ".yaml", ".yml"}
                    else "可作为指令或参考内容读取",
                }
            )
            if len(rows) >= 2000:
                rows.append(
                    {
                        "path": "…",
                        "type": "提示",
                        "size": "—",
                        "usage": "文件超过 2000 个，仅展示前 2000 个",
                    }
                )
                break
        return rows

    def discover_group(self, folder: str | Path) -> list[ExternalSkillDefinition]:
        """Discover one Skill folder or all direct child Skill folders."""
        root = Path(folder)
        if not root.is_dir():
            raise ValueError(f"Skill 组文件夹不存在或无法访问：{root}")
        candidates = [root] if (root / "skill.json").is_file() else [
            path for path in sorted(root.iterdir())
            if path.is_dir() and (path / "skill.json").is_file()
        ]
        if not candidates:
            raise ValueError("所选文件夹及其一级子文件夹中未找到 skill.json")
        skills = [self.discover(str(path)) for path in candidates]
        ids = [item.skill_id for item in skills]
        if len(ids) != len(set(ids)):
            raise ValueError("Skill 组中存在重复的 skill_id")
        return skills

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

    def invoke_skill(
        self, skill: ExternalSkillDefinition, request_payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Prefer a declared quotation command; otherwise use prompt/HTTP execution."""
        selected = {
            SkillStep(item) for item in request_payload.get("selected_steps", [])
        }
        runner = ExternalSkillCommandRunner()
        capability = runner.find_command(
            skill, SkillTaskType.QUOTATION, selected_steps=selected
        )
        if capability is None:
            return self.invoke(skill.endpoint, request_payload)
        result = runner.run(skill, capability, request_payload)
        if not result.success:
            raise RuntimeError(result.message)
        if result.output is None:
            raise ValueError("报价 Skill 命令未生成 output_json")
        return result.output

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

    @staticmethod
    def _read_agent_manifest(folder: Path) -> dict[str, Any]:
        if not folder.is_dir():
            raise ValueError(f"智能体文件夹不存在或无法访问：{folder}")
        manifest = folder / "agent.json"
        if not manifest.is_file():
            raise ValueError("智能体文件夹缺少 agent.json")
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"无法读取智能体文件夹清单：{exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("agent.json 必须是 JSON 对象")
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
        declared_id = str(manifest.get("skill_id") or "")
        declared_version = str(manifest.get("skill_version") or "")
        returned_id = str(result.get("skill_id") or "")
        if returned_id != declared_id:
            warnings = list(result.get("warnings_zh") or [])
            warnings.append(
                f"文件夹 Skill 返回的 skill_id“{returned_id or '空'}”与清单不一致，"
                f"已按 skill.json 规范为“{declared_id}”。"
            )
            result["warnings_zh"] = warnings
            result["skill_id"] = declared_id
        if not result.get("skill_version"):
            result["skill_version"] = declared_version
        return result

    @staticmethod
    def _read_folder_instructions(
        folder: Path,
        manifest: dict[str, Any],
        *,
        default_file: str = "SKILL.md",
    ) -> str:
        root = folder.resolve()
        requested = [str(manifest.get("instruction_file") or default_file)]
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
