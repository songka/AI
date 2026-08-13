from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: quick_validate.py <skill-directory>")
        return 2
    root = Path(sys.argv[1]).resolve()
    skill_file = root / "SKILL.md"
    if not skill_file.is_file():
        raise AssertionError("SKILL.md is missing")
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise AssertionError("SKILL.md must begin with YAML frontmatter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise AssertionError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    if set(fields) != {"name", "description"}:
        raise AssertionError("Frontmatter must contain only name and description")
    if not NAME_PATTERN.fullmatch(fields["name"]):
        raise AssertionError("Skill name must use lowercase hyphen-case")
    if root.name != fields["name"]:
        raise AssertionError("Skill folder and frontmatter name differ")
    if len(fields["description"]) < 80:
        raise AssertionError("Skill description is too short to cover real triggers")
    if not (root / "agents" / "openai.yaml").is_file():
        raise AssertionError("agents/openai.yaml is missing")
    print("QUICK VALIDATE PASS: skill structure and frontmatter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

