from __future__ import annotations

import re
import sys
from pathlib import Path


ALLOWED_KEYS = {"name", "description"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(content: str) -> dict[str, str]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md 缺少有效的 YAML frontmatter")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"无法解析 frontmatter 行: {line}")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key in values:
            raise ValueError(f"frontmatter 字段重复: {key}")
        values[key] = value
    return values


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["SKILL.md 不存在"]
    try:
        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]

    unexpected = sorted(set(frontmatter) - ALLOWED_KEYS)
    if unexpected:
        errors.append(f"frontmatter 含不允许字段: {', '.join(unexpected)}")
    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()
    if not name:
        errors.append("缺少 name")
    elif len(name) > 64 or not NAME_PATTERN.fullmatch(name):
        errors.append("name 必须是不超过 64 字符的 lowercase-hyphen-case")
    elif skill_dir.name != name:
        errors.append(f"目录名 {skill_dir.name!r} 与 name {name!r} 不一致")
    if not description:
        errors.append("缺少 description")
    elif len(description) > 1024:
        errors.append("description 超过 1024 字符")
    elif "<" in description or ">" in description:
        errors.append("description 不得包含尖括号")

    for relative in (
        "agents/openai.yaml",
        "references/safety-policy.md",
        "references/rule-schema.md",
        "references/commands.md",
        "scripts/smoke-test.py",
    ):
        if not (skill_dir / relative).is_file():
            errors.append(f"缺少必需文件: {relative}")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate-skill.py <skill-directory>")
        return 2
    errors = validate(Path(sys.argv[1]).resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: project Skill structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

