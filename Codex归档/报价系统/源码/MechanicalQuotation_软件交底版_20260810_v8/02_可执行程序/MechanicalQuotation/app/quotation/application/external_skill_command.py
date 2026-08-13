"""Safe, manifest-declared command execution for published folder Skills."""

from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quotation.application.external_skill_settings import (
    ExternalSkillDefinition,
    SkillCommandCapability,
    SkillCommandKind,
    SkillTaskType,
)


@dataclass(frozen=True)
class SkillCommandResult:
    success: bool
    message: str
    output: dict[str, Any] | None = None


class ExternalSkillCommandRunner:
    """Run only commands declared by an administrator-published folder Skill."""

    def find_command(
        self,
        skill: ExternalSkillDefinition,
        task_type: SkillTaskType,
        *,
        selected_steps: set | None = None,
    ) -> SkillCommandCapability | None:
        for capability in skill.command_capabilities:
            if task_type not in capability.task_types:
                continue
            if selected_steps and not selected_steps.issubset(set(capability.supported_steps)):
                continue
            return capability
        return None

    def run(
        self,
        skill: ExternalSkillDefinition,
        capability: SkillCommandCapability,
        payload: dict[str, Any],
        *,
        input_excel: str | Path | None = None,
        output_excel: str | Path | None = None,
    ) -> SkillCommandResult:
        folder = Path(skill.endpoint).resolve()
        if not folder.is_dir():
            return SkillCommandResult(False, f"Skill 文件夹不可访问：{folder}")
        missing = [item for item in capability.requirements if not self.requirement_ok(item)]
        if missing:
            return SkillCommandResult(
                False,
                "本机缺少 Skill 运行环境：" + "、".join(missing),
            )
        input_name = output_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".json", delete=False
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                input_name = handle.name
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
                output_name = handle.name
            Path(output_name).unlink(missing_ok=True)
            command = self.resolve_command(
                folder,
                capability,
                input_json=Path(input_name),
                output_json=Path(output_name),
                input_excel=Path(input_excel).resolve() if input_excel else None,
                output_excel=Path(output_excel).resolve() if output_excel else None,
            )
            completed = subprocess.run(
                command,
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=capability.timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "未知错误").strip()[:500]
                return SkillCommandResult(
                    False, f"命令执行失败（代码 {completed.returncode}）：{detail}"
                )
            output: dict[str, Any] | None = None
            output_path = Path(output_name)
            if output_path.is_file() and output_path.stat().st_size:
                value = json.loads(output_path.read_text(encoding="utf-8"))
                if not isinstance(value, dict):
                    return SkillCommandResult(False, "Skill 输出 JSON 必须是对象")
                output = value
            if output_excel is not None:
                excel_path = Path(output_excel)
                if not excel_path.is_file() or excel_path.stat().st_size == 0:
                    return SkillCommandResult(False, "Skill 未生成有效 Excel 文件")
            return SkillCommandResult(True, f"已执行：{capability.name_zh}", output)
        except subprocess.TimeoutExpired:
            return SkillCommandResult(False, f"Skill 命令超时（{capability.timeout_seconds} 秒）")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return SkillCommandResult(False, f"Skill 命令无法运行：{exc}")
        finally:
            if input_name:
                Path(input_name).unlink(missing_ok=True)
            if output_name:
                Path(output_name).unlink(missing_ok=True)

    @staticmethod
    def requirement_ok(requirement: str) -> bool:
        value = requirement.strip()
        if not value:
            return True
        if value.casefold() in {"python", "python3"}:
            return bool(sys.executable)
        if value.casefold() == "excel-read-write":
            try:
                import openpyxl  # noqa: F401
                return True
            except ImportError:
                return False
        if value.casefold().startswith("python-package:"):
            package = value.split(":", 1)[1].strip()
            return bool(package and importlib.util.find_spec(package) is not None)
        return shutil.which(value) is not None

    @classmethod
    def resolve_command(
        cls,
        folder: Path,
        capability: SkillCommandCapability,
        *,
        input_json: Path,
        output_json: Path,
        input_excel: Path | None,
        output_excel: Path | None,
    ) -> list[str]:
        values = {
            "{input_json}": str(input_json),
            "{output_json}": str(output_json),
            "{input_excel}": str(input_excel) if input_excel else "",
            "{output_excel}": str(output_excel) if output_excel else "",
            "{skill_dir}": str(folder),
        }
        raw = [values.get(item, item) for item in capability.command]
        if not raw or not raw[0]:
            raise ValueError("commands.command 不能为空")
        target = Path(raw[0])
        if capability.kind == SkillCommandKind.PYTHON and raw[0].casefold() in {
            "python", "python3"
        }:
            if len(raw) < 2:
                raise ValueError("Python 命令缺少脚本")
            script = cls._inside(folder, Path(raw[1]), {".py"})
            return [sys.executable, str(script), *raw[2:]]
        suffixes = {
            SkillCommandKind.EXECUTABLE: {".exe"},
            SkillCommandKind.CLI: {".exe"},
            SkillCommandKind.BATCH: {".bat", ".cmd", ".ps1"},
            SkillCommandKind.PYTHON: {".py"},
        }[capability.kind]
        target = cls._inside(folder, target, suffixes)
        if capability.kind == SkillCommandKind.PYTHON:
            return [sys.executable, str(target), *raw[1:]]
        if target.suffix.casefold() == ".ps1":
            host = shutil.which("powershell") or shutil.which("pwsh")
            if not host:
                raise ValueError("本机缺少 PowerShell")
            return [host, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(target), *raw[1:]]
        if target.suffix.casefold() in {".bat", ".cmd"}:
            host = shutil.which("cmd")
            if not host:
                raise ValueError("本机缺少 cmd.exe")
            return [host, "/d", "/c", str(target), *raw[1:]]
        return [str(target), *raw[1:]]

    @staticmethod
    def _inside(folder: Path, path: Path, suffixes: set[str]) -> Path:
        resolved = path.resolve() if path.is_absolute() else (folder / path).resolve()
        if not resolved.is_relative_to(folder) or not resolved.is_file():
            raise ValueError("执行文件必须存在于 Skill 文件夹内")
        if resolved.suffix.casefold() not in suffixes:
            raise ValueError("执行文件类型与 commands.kind 不一致")
        return resolved
