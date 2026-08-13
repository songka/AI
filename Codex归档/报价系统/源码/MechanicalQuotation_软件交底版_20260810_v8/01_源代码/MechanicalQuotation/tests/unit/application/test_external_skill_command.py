from __future__ import annotations

import sys

import pytest
import openpyxl

from quotation.application.external_skill_command import ExternalSkillCommandRunner
from quotation.application.external_skill_settings import (
    SkillCommandCapability,
    SkillCommandKind,
    ExternalSkillDefinition,
    SkillSourceType,
    SkillTaskType,
)


def _capability(kind, command):
    return SkillCommandCapability(
        command_id="test.command",
        name_zh="测试命令",
        kind=kind,
        task_types=[SkillTaskType.EXCEL_MODIFY],
        command=command,
        timeout_seconds=30,
    )


def test_python_command_uses_current_runtime_and_requires_script_inside_skill(tmp_path):
    folder = tmp_path / "skill"
    scripts = folder / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "modify.py"
    script.write_text("print('ok')", encoding="utf-8")
    capability = _capability(
        SkillCommandKind.PYTHON,
        ["python", "scripts/modify.py", "{input_json}", "{output_excel}"],
    )

    command = ExternalSkillCommandRunner.resolve_command(
        folder.resolve(),
        capability,
        input_json=tmp_path / "input.json",
        output_json=tmp_path / "output.json",
        input_excel=tmp_path / "source.xlsx",
        output_excel=tmp_path / "revised.xlsx",
    )

    assert command[0] == sys.executable
    assert command[1] == str(script.resolve())
    assert command[-1].endswith("revised.xlsx")


def test_command_rejects_executable_outside_skill_folder(tmp_path):
    folder = tmp_path / "skill"
    folder.mkdir()
    outside = tmp_path / "outside.exe"
    outside.write_bytes(b"MZ")
    capability = _capability(SkillCommandKind.EXECUTABLE, [str(outside)])

    with pytest.raises(ValueError, match="Skill 文件夹内"):
        ExternalSkillCommandRunner.resolve_command(
            folder.resolve(),
            capability,
            input_json=tmp_path / "input.json",
            output_json=tmp_path / "output.json",
            input_excel=None,
            output_excel=None,
        )


def test_quotation_command_requires_supported_steps():
    with pytest.raises(ValueError, match="supported_steps"):
        SkillCommandCapability(
            command_id="quote.command",
            name_zh="报价命令",
            kind=SkillCommandKind.CLI,
            task_types=[SkillTaskType.QUOTATION],
            command=["bin/quote.exe"],
        )


def test_python_excel_command_executes_and_returns_json(tmp_path):
    folder = tmp_path / "excel-skill"
    scripts = folder / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "workbook_tool.py"
    script.write_text(
        """import argparse, json
from openpyxl import Workbook
p=argparse.ArgumentParser()
p.add_argument('--input-json'); p.add_argument('--output-json'); p.add_argument('--output-excel')
a=p.parse_args()
payload=json.load(open(a.input_json, encoding='utf-8'))
wb=Workbook(); wb.active['A1']=payload['title']; wb.save(a.output_excel)
json.dump({'written': True}, open(a.output_json, 'w', encoding='utf-8'))
""",
        encoding="utf-8",
    )
    capability = SkillCommandCapability(
        command_id="excel.write",
        name_zh="生成 Excel",
        kind=SkillCommandKind.PYTHON,
        task_types=[SkillTaskType.EXCEL_WRITE],
        command=[
            "python", "scripts/workbook_tool.py",
            "--input-json", "{input_json}",
            "--output-json", "{output_json}",
            "--output-excel", "{output_excel}",
        ],
        requirements=["python", "excel-read-write"],
    )
    skill = ExternalSkillDefinition(
        skill_id="excel.write.skill",
        name_zh="Excel 写入 Skill",
        endpoint=str(folder),
        source_type=SkillSourceType.FOLDER,
        skill_version="1.0.0",
        supported_steps=[],
        command_capabilities=[capability],
    )
    output = tmp_path / "result.xlsx"

    result = ExternalSkillCommandRunner().run(
        skill, capability, {"title": "报价结果"}, output_excel=output
    )

    assert result.success is True
    assert result.output == {"written": True}
    workbook = openpyxl.load_workbook(output, read_only=True)
    assert workbook.active["A1"].value == "报价结果"


def test_missing_runtime_is_reported_without_execution(tmp_path, monkeypatch):
    folder = tmp_path / "missing-runtime"
    folder.mkdir()
    capability = SkillCommandCapability(
        command_id="custom.cli",
        name_zh="外部 CLI",
        kind=SkillCommandKind.CLI,
        task_types=[SkillTaskType.BATCH_TASK],
        command=["bin/tool.exe"],
        requirements=["definitely-missing-cli-2026"],
    )
    skill = ExternalSkillDefinition(
        skill_id="missing.runtime",
        name_zh="缺少环境",
        endpoint=str(folder),
        source_type=SkillSourceType.FOLDER,
        skill_version="1.0.0",
        supported_steps=[],
        command_capabilities=[capability],
    )

    result = ExternalSkillCommandRunner().run(skill, capability, {})

    assert result.success is False
    assert "definitely-missing-cli-2026" in result.message
