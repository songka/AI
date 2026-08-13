# Runtime, command, and workbook contract

The V2 routing schema is `2.0`; the current external transport protocol remains `1.0` for backward compatibility. A Skill may additionally declare `supported_processes` and `step_agent_routes`. An external Agent uses a separate `agent.json` and must not declare workbook commands; keep side-effecting commands in a Skill.

## Supported folder contents

A published folder Skill may contain UTF-8 instructions and references, Python `.py`, Windows `.exe`, CLI programs, `.bat`/`.cmd`/`.ps1` batch scripts, and Excel `.xlsx`/`.xlsm` assets. Declare executable behavior in `skill.json.commands`; merely placing a file in the folder does not authorize execution.

## Command schema

```json
{
  "commands": [
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
  ]
}
```

Kinds: `PYTHON`, `EXECUTABLE`, `CLI`, `BATCH`.

Task types: `QUOTATION`, `BATCH_TASK`, `EXCEL_READ`, `EXCEL_WRITE`, `EXCEL_MODIFY`, `EXCEL_EXPORT`. A `QUOTATION` command must also declare the exact `supported_steps`.

Exact placeholders: `{input_json}`, `{output_json}`, `{input_excel}`, `{output_excel}`, `{skill_dir}`. Each placeholder must be a separate command-array item. Do not embed placeholders in shell strings.

## Runtime behavior

- Python: program checks for its Python runtime and runs the `.py` inside the Skill folder with the active interpreter.
- EXE/CLI: executable must be inside the published Skill folder. Run without shell interpolation.
- Batch: `.bat`, `.cmd`, and `.ps1` must be inside the folder and run non-interactively through the matching Windows host.
- Requirements: missing `python`, `python-package:<import-name>`, named CLI host, or `excel-read-write` produces a visible warning and fallback. Declare every non-standard Python import, for example `python-package:pandas`.
- Every command has a timeout and must return a nonzero exit code on failure.
- Before execution resolve every path under the published Skill folder, reject traversal/symlinks, and never use a shell string assembled from user input.
- Quotation commands write protocol JSON to `{output_json}`. Excel commands must produce the declared output workbook and may also write a JSON summary.

## Excel read/write/modify

Use task-specific commands rather than one ambiguous “Excel support” flag:

- `EXCEL_READ`: inspect workbook sheets/cells and return structured JSON; input workbook is required.
- `EXCEL_WRITE`: create a new workbook from structured input; output workbook is required.
- `EXCEL_MODIFY`: read an existing workbook and write a separate modified workbook. Do not overwrite the source unless the user explicitly authorizes it.
- `EXCEL_EXPORT`: create the final quotation workbook. Failure visibly falls back to the built-in exporter.

CLI usage:

```powershell
quotation skill-command <skill-folder> --task EXCEL_READ --input-excel source.xlsx --output-json summary.json
quotation skill-command <skill-folder> --task EXCEL_MODIFY --input-excel source.xlsx --output-excel revised.xlsx --payload-json changes.json
quotation skill-command <skill-folder> --task BATCH_TASK --payload-json jobs.json --output-json result.json
```

## Compatibility checklist

Report `available`, `missing`, or `not required` for Python, every named executable/host, PowerShell/cmd for batch files, Excel read/write library, input asset accessibility, and output-directory write access. A missing optional command does not disable prompt-only quotation behavior.
