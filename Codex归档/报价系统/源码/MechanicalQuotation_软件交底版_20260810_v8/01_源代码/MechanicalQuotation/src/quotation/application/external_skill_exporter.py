"""Optional folder-Skill Excel export with safe fallback-friendly execution."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quotation.application.external_skill_settings import ExternalSkillRoutingConfig
from quotation.application.external_skill_settings import SkillTaskType
from quotation.application.external_skill_command import ExternalSkillCommandRunner


@dataclass(frozen=True)
class SkillExportResult:
    used_skill: bool
    success: bool
    message: str


class ExternalSkillExcelExporter:
    """Execute only an administrator-selected, manifest-declared export command."""

    def __init__(self, config: ExternalSkillRoutingConfig) -> None:
        self.config = config

    def export(self, results: list[Any], output_path: str | Path) -> SkillExportResult:
        skill_id = self.config.excel_export_skill_id
        if not skill_id:
            return SkillExportResult(False, False, "未选择外接 Excel 导出 Skill")
        skill = next(
            (
                item for item in self.config.skills
                if item.enabled and item.skill_id == skill_id and item.supports_excel_export
            ),
            None,
        )
        if skill is None:
            return SkillExportResult(True, False, "配置的 Excel 导出 Skill 不存在或已停用")
        folder = Path(skill.endpoint)
        if not folder.is_dir():
            return SkillExportResult(True, False, f"Excel 导出 Skill 文件夹不可访问：{folder}")
        missing = [item for item in skill.execution_requirements if not self._requirement_ok(item)]
        if missing:
            return SkillExportResult(
                True,
                False,
                "本机缺少导出 Skill 所需环境：" + "、".join(missing),
            )
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "skill_id": skill.skill_id,
            "output_path": str(output.resolve()),
            "results": [
                result.to_dict() if hasattr(result, "to_dict") else result
                for result in results
            ],
        }
        runner = ExternalSkillCommandRunner()
        capability = runner.find_command(skill, SkillTaskType.EXCEL_EXPORT)
        if capability is not None:
            command_result = runner.run(
                skill,
                capability,
                payload,
                output_excel=output,
            )
            return SkillExportResult(
                True,
                command_result.success,
                command_result.message,
            )
        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".json", delete=False
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                temporary_name = handle.name
            command = self._resolve_command(
                folder,
                skill.excel_export_command,
                Path(temporary_name),
                output,
            )
            completed = subprocess.run(
                command,
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=skill.excel_export_timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "未知错误").strip()[:500]
                return SkillExportResult(
                    True, False, f"导出 Skill 执行失败（代码 {completed.returncode}）：{detail}"
                )
            if not output.is_file() or output.stat().st_size == 0:
                return SkillExportResult(True, False, "导出 Skill 未生成有效 Excel 文件")
            return SkillExportResult(True, True, f"已使用 {skill.name_zh} 导出")
        except subprocess.TimeoutExpired:
            return SkillExportResult(True, False, "导出 Skill 执行超时")
        except (OSError, ValueError) as exc:
            return SkillExportResult(True, False, f"导出 Skill 无法运行：{exc}")
        finally:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _requirement_ok(requirement: str) -> bool:
        value = requirement.strip()
        if not value:
            return True
        if value.casefold() in {"python", "python3"}:
            return bool(sys.executable)
        return shutil.which(value) is not None

    @staticmethod
    def _resolve_command(
        folder: Path,
        template: list[str],
        input_json: Path,
        output_xlsx: Path,
    ) -> list[str]:
        if not template:
            raise ValueError("excel_export.command 为空")
        values = {
            "{input_json}": str(input_json),
            "{output_xlsx}": str(output_xlsx.resolve()),
            "{skill_dir}": str(folder.resolve()),
        }
        command = [values.get(item, item) for item in template]
        executable = command[0]
        if executable.casefold() in {"python", "python3"}:
            command[0] = sys.executable
        else:
            executable_path = Path(executable)
            if not executable_path.is_absolute():
                executable_path = (folder / executable_path).resolve()
            root = folder.resolve()
            if not executable_path.is_relative_to(root):
                raise ValueError("导出执行文件必须位于 Skill 文件夹内")
            if executable_path.suffix.casefold() != ".exe" or not executable_path.is_file():
                raise ValueError("导出执行文件必须是 Skill 文件夹内存在的 .exe")
            command[0] = str(executable_path)
        for index, item in enumerate(command[1:], 1):
            candidate = Path(item)
            if candidate.suffix.casefold() == ".py":
                resolved = (
                    candidate.resolve()
                    if candidate.is_absolute()
                    else (folder / candidate).resolve()
                )
                if not resolved.is_relative_to(folder.resolve()) or not resolved.is_file():
                    raise ValueError(
                        f"Python 导出脚本必须位于 Skill 文件夹内且存在：{item}"
                    )
                command[index] = str(resolved)
        return command
