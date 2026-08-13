from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "manage-gomoku"


def json_block(path: Path, label: str) -> object:
    text = path.read_text(encoding="utf-8")
    pattern = rf"<!-- CONTRACT:{re.escape(label)} -->\s*```json\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise AssertionError(f"{path} lacks CONTRACT:{label} JSON block")
    return json.loads(match.group(1))


def python_version() -> str:
    tree = ast.parse((PROJECT_ROOT / "src" / "gomoku" / "__init__.py").read_text("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError("__version__ not found")


def test_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def main() -> int:
    contract = json.loads((PROJECT_ROOT / "project-contract.json").read_text("utf-8"))
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text("utf-8"))
    skill_text = (SKILL_ROOT / "SKILL.md").read_text("utf-8")
    skill_version = re.search(r"Project version:\s*`([^`]+)`", skill_text)
    versions = {
        contract["version"],
        pyproject["project"]["version"],
        python_version(),
        skill_version.group(1) if skill_version else None,
    }
    if len(versions) != 1:
        raise AssertionError(f"Version mismatch: {versions}")

    documented_commands = json_block(SKILL_ROOT / "references" / "commands.md", "COMMANDS")
    if documented_commands != contract["commands"]:
        raise AssertionError("commands.md differs from project-contract.json")

    documented_schema = json_block(SKILL_ROOT / "references" / "data-schema.md", "DATA_SCHEMA")
    if documented_schema != contract["data_schema"]:
        raise AssertionError("data-schema.md differs from project-contract.json")

    documented_safety = json_block(SKILL_ROOT / "references" / "safety-policy.md", "SAFETY_RULES")
    if documented_safety != contract["safety_rules"]:
        raise AssertionError("safety-policy.md differs from project-contract.json")

    for rule in contract["safety_rules"]:
        test_path_text, test_name = rule["test"].split("::", 1)
        test_path = PROJECT_ROOT / test_path_text
        if not test_path.is_file() or test_name not in test_names(test_path):
            raise AssertionError(f"{rule['id']} lacks test {rule['test']}")

    missing = [
        relative
        for relative in contract["required_skill_files"]
        if not (SKILL_ROOT / relative).is_file()
    ]
    if missing:
        raise AssertionError(f"Required Skill files missing: {missing}")
    print("CONTRACT PASS: versions, commands, schema, safety tests, and Skill files")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"CONTRACT FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)

