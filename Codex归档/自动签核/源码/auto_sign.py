"""自动签核入口包装 — 实际逻辑在 .claude/auto-sign/auto_sign.py"""

from __future__ import annotations

import sys
from pathlib import Path

_skill_dir = Path(__file__).resolve().parent / ".claude" / "auto-sign"
if str(_skill_dir) not in sys.path:
    sys.path.insert(0, str(_skill_dir))

from auto_sign import build_arg_parser, run

if __name__ == "__main__":
    try:
        raise SystemExit(run(build_arg_parser().parse_args()))
    except Exception as exc:
        import sys as _sys
        print(f"自动签核任务执行失败: {exc}", file=_sys.stderr)
        raise SystemExit(1)
