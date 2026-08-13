from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT.parent / ".agents" / "skills" / "manage-gomoku"


def main() -> int:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    required_triggers = ("modify", "diagnose", "test", "release", "Gomoku")
    missing = [trigger for trigger in required_triggers if trigger.lower() not in skill.lower()]
    if missing:
        raise AssertionError(f"SKILL.md trigger coverage missing: {missing}")
    for reference in (
        "safety-policy.md",
        "architecture.md",
        "data-schema.md",
        "commands.md",
    ):
        if f"references/{reference}" not in skill:
            raise AssertionError(f"SKILL.md does not link references/{reference}")
    print("SKILL SMOKE PASS: trigger coverage and direct reference links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

