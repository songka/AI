from __future__ import annotations

import sys
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MODULES = ROOT / "deploy" / "auto-sign"
sys.path.insert(0, str(MODULES))


def main() -> int:
    for path in MODULES.glob("*.py"):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    from intent_router import is_meta_question, is_preview_request, is_query_request, is_rule_request
    assert is_preview_request("模拟自动签核")
    assert is_meta_question("模拟自动签核为什么执行了？")
    assert not is_query_request("添加多条签核规则")
    assert is_rule_request("添加多条签核规则")

    from notification_policy import notification_decision
    assert notification_decision({}, {}, {}, default_notify=False)[0] is False
    assert notification_decision({}, {}, {}, manual_override=True)[0] is True

    from stats_store import query_actions, record_action
    memory_db = "file:qh_skill_smoke?mode=memory&cache=shared"
    # 保持一个连接存活，让多个存储函数共享同一个内存数据库；不在仓库留下测试文件。
    keeper = sqlite3.connect(memory_db, uri=True)
    try:
        db_path = memory_db
        record_action(db_path, "ou_a", "A", {"no": "1"}, "approve", "manual")
        record_action(db_path, "ou_b", "B", {"no": "2"}, "reject", "auto")
        assert len(query_actions(db_path, "ou_a")) == 1
        assert query_actions(db_path, "ou_a")[0]["application_no"] == "1"
    finally:
        keeper.close()

    print("PASS: Feishu signing safety smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
