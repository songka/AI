import io
import json

from quotation.application.external_skill_settings import (
    AgentSourceType,
    ProcessCode,
    SkillCommandKind,
    SkillSourceType,
    SkillStep,
    SkillTaskType,
)
from quotation.infrastructure.external_skill.client import ExternalSkillClient


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def test_discover_reads_protocol_capabilities_without_real_network():
    payload = {
        "skill_id": "complete.quote",
        "skill_name_zh": "整套报价 Skill",
        "skill_version": "2.0.0",
        "protocol_version": "1.0",
        "supported_steps": [step.value for step in SkillStep],
        "supports_full_quotation": True,
    }

    def opener(request, timeout):
        assert request.full_url == "http://127.0.0.1:8765/v1/capabilities"
        assert timeout == 3
        return _Response(json.dumps(payload).encode())

    skill = ExternalSkillClient(timeout_seconds=3, opener=opener).discover(
        "http://127.0.0.1:8765/"
    )

    assert skill.skill_id == "complete.quote"
    assert skill.supports_full_quotation is True
    assert SkillStep.QUOTE_ASSEMBLY in skill.supported_steps


def test_discover_reads_local_or_smb_folder_manifest(tmp_path):
    folder = tmp_path / "shared-skill"
    folder.mkdir()
    (folder / "skill.json").write_text(
        json.dumps(
            {
                "skill_id": "folder.quote",
                "skill_name_zh": "公共槽报价 Skill",
                "skill_version": "1.2.0",
                "protocol_version": "1.0",
                "supported_steps": ["PROCESS_PLANNING", "PRICE_AUDIT"],
                "supports_full_quotation": False,
                "instruction_file": "SKILL.md",
                "reference_files": ["规则.md"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (folder / "SKILL.md").write_text("按最低成本规划工艺。", encoding="utf-8")
    (folder / "规则.md").write_text("普通孔优先铣床。", encoding="utf-8")

    skill = ExternalSkillClient().discover(str(folder))

    assert skill.source_type == SkillSourceType.FOLDER
    assert skill.endpoint == str(folder)
    assert skill.supported_steps == [SkillStep.PROCESS_PLANNING, SkillStep.PRICE_AUDIT]


def test_discover_group_loads_direct_child_skills(tmp_path):
    root = tmp_path / "skill-set"
    for suffix, step in (("one", "FEATURE_EXTRACTION"), ("two", "MATERIAL_CLASSIFICATION")):
        folder = root / suffix
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("# test", encoding="utf-8")
        (folder / "skill.json").write_text(
            json.dumps({
                "skill_id": f"sample.{suffix}",
                "skill_name_zh": f"示例{suffix}",
                "skill_version": "1.0.0",
                "protocol_version": "1.0",
                "supported_steps": [step],
                "supports_full_quotation": False,
                "instruction_file": "SKILL.md",
            }),
            encoding="utf-8",
        )

    skills = ExternalSkillClient().discover_group(root)

    assert [skill.skill_id for skill in skills] == ["sample.one", "sample.two"]


def test_list_folder_files_includes_non_markdown_assets(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "SKILL.md").write_text("# test", encoding="utf-8")
    (tmp_path / "scripts" / "quote.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / "assets" / "rates.xlsx").write_bytes(b"xlsx-placeholder")

    rows = ExternalSkillClient.list_folder_files(tmp_path)

    paths = {row["path"]: row for row in rows}
    assert paths["scripts/quote.py"]["type"] == "Python"
    assert paths["assets/rates.xlsx"]["type"] == "Excel 工作簿"


def test_discover_reads_python_cli_batch_and_excel_command_capabilities(tmp_path):
    folder = tmp_path / "command-skill"
    folder.mkdir()
    manifest = {
        "skill_id": "command.skill",
        "skill_name_zh": "命令 Skill",
        "skill_version": "1.0.0",
        "protocol_version": "1.0",
        "supported_steps": ["PRICE_AUDIT"],
        "supports_full_quotation": False,
        "instruction_file": "SKILL.md",
        "reference_files": [],
        "commands": [
            {
                "command_id": "excel.modify",
                "name_zh": "修改 Excel",
                "kind": "PYTHON",
                "task_types": ["EXCEL_READ", "EXCEL_WRITE", "EXCEL_MODIFY", "EXCEL_EXPORT"],
                "command": ["python", "scripts/excel.py", "{input_json}", "{output_excel}"],
                "supported_steps": [],
                "timeout_seconds": 45,
                "requirements": ["python", "excel-read-write"],
            },
            {
                "command_id": "batch.run",
                "name_zh": "批处理",
                "kind": "BATCH",
                "task_types": ["BATCH_TASK"],
                "command": ["scripts/run.ps1", "{input_json}", "{output_json}"],
                "supported_steps": [],
                "timeout_seconds": 120,
                "requirements": [],
            },
        ],
    }
    (folder / "skill.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    (folder / "SKILL.md").write_text("命令能力说明", encoding="utf-8")

    skill = ExternalSkillClient().discover(str(folder))

    assert skill.supports_excel_export is True
    assert skill.command_capabilities[0].kind == SkillCommandKind.PYTHON
    assert SkillTaskType.EXCEL_MODIFY in skill.command_capabilities[0].task_types
    assert skill.command_capabilities[1].kind == SkillCommandKind.BATCH


def test_folder_skill_combines_documents_and_calls_program_deepseek(tmp_path):
    folder = tmp_path / "prompt-skill"
    folder.mkdir()
    (folder / "skill.json").write_text(
        json.dumps(
            {
                "skill_id": "folder.prompt",
                "skill_name_zh": "提示词 Skill",
                "skill_version": "1.0.0",
                "protocol_version": "1.0",
                "supported_steps": ["PROCESS_PLANNING"],
                "supports_full_quotation": False,
                "instruction_file": "SKILL.md",
                "reference_files": ["工艺规则.md"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (folder / "SKILL.md").write_text("你是工艺 Agent。", encoding="utf-8")
    (folder / "工艺规则.md").write_text("普通铣床优先。", encoding="utf-8")

    class FakeDeepSeek:
        is_configured = True

        def __init__(self):
            self.call = None

        def invoke_quotation_skill(self, instructions, payload):
            self.call = (instructions, payload)
            return {"request_id": payload["request_id"]}

    ai = FakeDeepSeek()
    payload = {"request_id": "REQ-001", "drawing_package": {"extracted_texts": ["S50C"]}}
    result = ExternalSkillClient(ai_client=ai).invoke(str(folder), payload)

    assert result["request_id"] == "REQ-001"
    assert "你是工艺 Agent" in ai.call[0]
    assert "普通铣床优先" in ai.call[0]
    assert ai.call[1]["drawing_package"]["extracted_texts"] == ["S50C"]


def test_v2_discovers_folder_agent_and_exposes_its_content(tmp_path):
    folder = tmp_path / "grind-agent"
    folder.mkdir()
    (folder / "agent.json").write_text(
        json.dumps(
            {
                "agent_id": "agent.grind",
                "agent_name_zh": "磨床工时智能体",
                "agent_version": "2.0.0",
                "protocol_version": "1.0",
                "supported_steps": ["TIME_ESTIMATION"],
                "supported_processes": ["GRIND"],
                "description_zh": "估算磨削工时",
                "instruction_file": "AGENT.md",
                "reference_files": ["references/rules.md"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (folder / "AGENT.md").write_text("按磨削余量估算单件工时。", encoding="utf-8")
    (folder / "references").mkdir()
    (folder / "references" / "rules.md").write_text(
        "证据不足时转人工审核。", encoding="utf-8"
    )

    client = ExternalSkillClient()
    agent = client.discover_agent(str(folder))
    content = client.read_agent_content(agent)

    assert agent.source_type == AgentSourceType.FOLDER
    assert agent.supported_processes == [ProcessCode.GRIND]
    assert "按磨削余量" in content
    assert "证据不足" in content
