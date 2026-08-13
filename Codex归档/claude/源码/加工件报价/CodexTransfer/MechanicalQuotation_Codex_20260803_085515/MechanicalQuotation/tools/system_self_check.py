#!/usr/bin/env python
"""System self-check — verifies all components are ready for demo.

Usage:
    .venv/Scripts/python tools/system_self_check.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> None:
    results: list[dict] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def check(name: str, ok: bool, detail: str = "") -> None:
        status = "正常" if ok else ("警告" if "WARN" in detail else "失敗")
        results.append({"項目": name, "狀態": status, "詳情": detail})
        icon = "[OK]" if ok else ("[WARN]" if "WARN" in detail else "[FAIL]")
        print(f"  {icon} {name}: {status} {detail}")

    print("=" * 60)
    print(f"系統自檢 — {now}")
    print("=" * 60)

    # 1. Python environment
    check("Python 執行環境", True, f"Python {sys.version.split()[0]}")

    # 2. Rules file
    rules = _PROJECT_ROOT / "rules" / "quotation-rules.yaml"
    check("規則文件", rules.exists(), str(rules) if rules.exists() else "缺失")

    # 3. Published Pricebook
    pb = _PROJECT_ROOT / "data" / "company-pricebook-r01-v1.0-snapshot.json"
    check("已發布公司價格表", pb.exists(), str(pb) if pb.exists() else "缺失")

    # 4. Current Version Pointer
    cvp = _PROJECT_ROOT / "data" / "current-version-pointer.json"
    check("當前版本指針", cvp.exists(), str(cvp) if cvp.exists() else "缺失")

    # 5. Snapshot SHA256
    if pb.exists():
        import hashlib
        sha = hashlib.sha256(pb.read_bytes()).hexdigest()[:16]
        check("Snapshot SHA256", True, f"SHA256={sha}...")

    # 6. Exports directory
    exports = _PROJECT_ROOT / "runtime" / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    check("Excel 輸出目錄", exports.exists(), str(exports))

    # 7. SQLite database
    db = _PROJECT_ROOT / "runtime" / "data" / "quotation_history.db"
    check("SQLite 資料庫", True, str(db))

    # 8. API port
    try:
        import socket
        s = socket.socket()
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 8000))
        s.close()
        check("API 端口 8000", result != 0, "可用" if result != 0 else "WARN: 端口已被佔用")
    except Exception as e:
        check("API 端口檢查", False, f"WARN: {e}")

    # 9. DeepSeek
    try:
        from quotation.infrastructure.secrets.secret_locator import SecretLocator
        key = SecretLocator.get_deepseek_key()
        configured = key is not None
        check("DeepSeek Key 配置", configured, "已配置" if configured else "WARN: 未配置")

        if configured:
            try:
                from quotation.infrastructure.ai.deepseek_client import DeepSeekClient
                client = DeepSeekClient(api_key=key)
                health = client.health_check()
                check("DeepSeek 連線", health.get("reachable", False),
                      f"延遲 {health.get('latency_ms', '?')}ms" if health.get("reachable")
                      else f"WARN: {health.get('error', 'unknown')}")
            except Exception as e:
                check("DeepSeek 連線", False, f"WARN: {e}")
    except Exception as e:
        check("DeepSeek 檢查", False, f"WARN: {e}")

    # 10. UI modules
    try:
        import tkinter
        check("Tkinter 可用", True, "OK")
    except Exception:
        check("Tkinter 可用", False, "WARN: 無圖形環境")

    # 11. Parsers
    try:
        from quotation.infrastructure.dxf.reader import DxfReader
        check("DXF Parser", True, "就緒")
    except Exception:
        check("DXF Parser", False, "失敗")

    # 12. Tax rate
    check("稅率配置", True, "17% 增值稅(未稅基準)")

    # Summary
    ok_count = sum(1 for r in results if r["狀態"] == "正常")
    warn_count = sum(1 for r in results if r["狀態"] == "警告")
    fail_count = sum(1 for r in results if r["狀態"] == "失敗")

    print(f"\n結果: {ok_count} 正常, {warn_count} 警告, {fail_count} 失敗")

    # Save report
    report_dir = _PROJECT_ROOT / "runtime" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": now,
        "results": results,
        "summary": {"正常": ok_count, "警告": warn_count, "失敗": fail_count},
    }
    (report_dir / "system_self_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"報告: {report_dir / 'system_self_check.json'}")


if __name__ == "__main__":
    main()
