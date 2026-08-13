# Examples and anti-patterns

## Good: category Skill with a process Agent

```json
{
  "skill_id": "company.machining-time",
  "skill_name_zh": "加工件工时 Skill",
  "skill_version": "2.0.0",
  "protocol_version": "1.0",
  "supported_steps": ["TIME_ESTIMATION"],
  "supported_processes": ["MILL", "GRIND"],
  "supports_full_quotation": false,
  "instruction_file": "SKILL.md",
  "reference_files": ["references/time-rules.md"],
  "step_agent_routes": {"TIME_ESTIMATION": "company.machining-time-agent"},
  "commands": []
}
```

Why good: the Skill owns the capability contract; the Agent owns reasoning; routing scope and fallback are explicit.

## Good: separate workbook modification command

```json
{
  "command_id": "excel.modify",
  "name_zh": "修改报价工作簿",
  "kind": "PYTHON",
  "task_types": ["EXCEL_READ", "EXCEL_WRITE", "EXCEL_MODIFY"],
  "command": ["python", "scripts/workbook_tool.py", "--input-json", "{input_json}", "--output-json", "{output_json}", "--input-excel", "{input_excel}", "--output-excel", "{output_excel}"],
  "supported_steps": [],
  "timeout_seconds": 90,
  "requirements": ["python", "excel-read-write"]
}
```

## Wrong: category-specific classification

Do not configure steps 1 or 2 under a category; the category does not exist until classification completes.

## Wrong: process route for process planning

Do not route `PROCESS_PLANNING` by `GRIND` or `MILL`; those process codes are outputs of planning. Route downstream time/pricing/audit steps instead.

## Wrong: every step becomes an Agent

Feature parsing, arithmetic totals and exact price lookups should normally remain deterministic. Agent count is based on distinct reasoning roles, not the number of pipeline steps.

## Wrong: one monolithic resource

A folder that understands notes, estimates all processes, audits prices, modifies Excel and launches batch jobs combines unrelated permissions and failure boundaries. Share the note/classification Agent, split process reasoning, and isolate file-mutating commands.

## Wrong: copying GitHub content without provenance

Repository popularity is not permission. Verify the exact file license and attribution obligations. When unclear, record only the general architectural observation and implement independently.

## Training set minimum

For each decision rule provide one normal positive, close negative, ambiguous review, and missing-input example, with expected structured output, source evidence and a “must not infer” statement.

Example: material quantity `3.1 kg` is consumed weight for one quoted part, not `3.1 pieces`. Do not compare it with drawing quantity `1 piece` as a contradiction unless the drawing explicitly declares net weight.
