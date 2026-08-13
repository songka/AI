"""签核 CLI 入口包装 — 实际逻辑在 .claude/auto-sign/cli.py"""

from __future__ import annotations

import sys
from pathlib import Path

_skill_dir = Path(__file__).resolve().parent / ".claude" / "auto-sign"
if str(_skill_dir) not in sys.path:
    sys.path.insert(0, str(_skill_dir))

from cli import main

if __name__ == "__main__":
    raise SystemExit(main())
