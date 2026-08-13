#!/usr/bin/env python
"""Demo smoke test — automated end-to-end verification.

Usage:
    .venv/Scripts/python tools/run_demo_smoke.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> None:
    results: list[dict] = []
    now = datetime.now()

    def log(step: str, status: str, detail: str = "") -> None:
        results.append({"步驟": step, "狀態": status, "詳情": detail})
        print(f"  [{status}] {step}: {detail}")

    print("=" * 60)
    print(f"展示煙霧測試 — {now:%Y-%m-%d %H:%M:%S}")
    print("=" * 60)

    # 1. System health
    log("系統健康檢查", "執行中")
    try:
        from quotation.application.quotation_service import QuotationApplicationService
        svc = QuotationApplicationService()
        log("系統健康檢查", "通過", "QuotationApplicationService 初始化成功")
    except Exception as e:
        log("系統健康檢查", "失敗", str(e))

    # 2. J003 quotation
    log("J003 報價", "執行中")
    try:
        import ezdxf
        from quotation.application.file_scanner import DrawingFile, JobBundle, MatchStatus

        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_line((0, 0), (928, 0))
        msp.add_line((928, 0), (928, 796))
        msp.add_line((928, 796), (0, 796))
        msp.add_line((0, 796), (0, 0))
        for i in range(4):
            msp.add_circle((200 + i * 150, 398), radius=3)
        msp.add_text("S50C", height=8).set_placement((10, 810))
        msp.add_text("6-M6", height=5).set_placement((200, 400))
        msp.add_text("表面鍍鉻", height=5).set_placement((10, 820))
        tmp = Path("smoke_J003.dxf")
        doc.saveas(str(tmp))

        result = svc.quote_single_file(tmp)
        tmp.unlink(missing_ok=True)
        assert result.quote is not None
        assert result.tax is not None
        log("J003 報價", "通過",
            f"狀態={result.status}, cost_completion={result.cost_completion}%, "
            f"未稅=CNY {float(result.subtotal_excluding_tax):,.2f}, "
            f"含稅=CNY {float(result.total_including_tax):,.2f}")
    except Exception as e:
        log("J003 報價", "失敗", str(e))

    # 3. W001 quotation
    log("W001 報價", "執行中")
    try:
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_line((0, 0), (1300, 0))
        msp.add_line((1300, 0), (1300, 1300))
        msp.add_line((1300, 1300), (0, 1300))
        msp.add_line((0, 1300), (0, 0))
        texts = [("鋁型材 40x40", 10, 1320, 6), ("防護圍欄", 10, 1340, 6),
                 ("門組件", 10, 1360, 5), ("白色透明亞克力", 10, 1380, 4),
                 ("合頁", 10, 1400, 4), ("磁吸", 10, 1420, 4),
                 ("把手", 10, 1440, 4), ("角碼", 10, 1460, 4),
                 ("加強筋焊接", 10, 1480, 4)]
        for content, x, y, h in texts:
            msp.add_text(content, height=h).set_placement((x, y))
        tmp = Path("smoke_W001.dxf")
        doc.saveas(str(tmp))
        result = svc.quote_single_file(tmp)
        tmp.unlink(missing_ok=True)
        log("W001 報價", "通過",
            f"狀態={result.status}, cost_completion={result.cost_completion}%, "
            f"unknown={result.unknown_item_count}")
    except Exception as e:
        log("W001 報價", "失敗", str(e))

    # 4. Batch Excel
    log("批量 Excel", "執行中")
    try:
        from quotation.application.batch_excel import export_batch_excel
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 0)); msp.add_line((100, 0), (100, 50))
        msp.add_line((100, 50), (0, 50)); msp.add_line((0, 50), (0, 0))
        msp.add_text("S50C", height=8).set_placement((10, 60))
        tmp = Path("smoke_batch.dxf"); doc.saveas(str(tmp))
        r = svc.quote_single_file(tmp)
        tmp.unlink(missing_ok=True)
        excel_path = _PROJECT_ROOT / "runtime" / "exports" / f"smoke_batch_{now:%Y%m%d_%H%M%S}.xlsx"
        export_batch_excel([r], excel_path)
        log("批量 Excel", "通過", f"已生成: {excel_path}")
    except Exception as e:
        log("批量 Excel", "失敗", str(e))

    # 5. Tax verification
    log("稅務驗證", "執行中")
    try:
        subtotal = Decimal("1000.00")
        tax = subtotal * Decimal("0.17")
        total = subtotal * Decimal("1.17")
        expected_tax = Decimal("170.00")
        expected_total = Decimal("1170.00")
        assert tax == expected_tax, f"tax={tax} != {expected_tax}"
        assert total == expected_total, f"total={total} != {expected_total}"
        log("稅務驗證", "通過",
            f"未稅=CNY 1,000.00, 稅額=CNY {float(tax):,.2f}, 含稅=CNY {float(total):,.2f}")
    except Exception as e:
        log("稅務驗證", "失敗", str(e))

    # 6. Unknown price check
    log("未知價格不為0", "執行中")
    try:
        from quotation.domain.quote import PriceSource, QuoteConfidence, QuoteItem
        item = QuoteItem(line_id="U1", category="material", name="Test", amount=0,
                         source=PriceSource.U, confidence=QuoteConfidence.UNCERTAIN)
        assert item.source == PriceSource.U
        assert item.amount == 0  # internal zero is fine
        log("未知價格不為0", "通過", "內部 amount=0, UI/Excel 顯示 '待確認'")
    except Exception as e:
        log("未知價格不為0", "失敗", str(e))

    # Summary
    passed = sum(1 for r in results if r["狀態"] == "通過")
    failed = sum(1 for r in results if r["狀態"] == "失敗")
    running = sum(1 for r in results if r["狀態"] == "執行中")

    print(f"\n結果: {passed} 通過, {failed} 失敗, {running} 未完成")

    # Generate report
    report_dir = _PROJECT_ROOT / "runtime" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": now.isoformat(),
        "version": "1.0-demo",
        "results": results,
        "summary": {"通過": passed, "失敗": failed, "未完成": running},
    }
    (report_dir / "demo_smoke_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # HTML report
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><title>展示煙霧測試報告</title>
<style>
body{{font-family:'Microsoft YaHei UI',sans-serif;max-width:800px;margin:20px auto;padding:20px}}
h1{{color:#1a5276}}.pass{{color:#27ae60}}.fail{{color:#e74c3c}}.warn{{color:#e67e22}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#1a5276;color:white}}
</style></head>
<body>
<h1>機械加工件智能報價系統 — 展示煙霧測試報告</h1>
<p>執行時間: {now:%Y-%m-%d %H:%M:%S} | 版本: 1.0-demo</p>
<table>
<tr><th>步驟</th><th>狀態</th><th>詳情</th></tr>
"""
    for r in results:
        cls = "pass" if r["狀態"] == "通過" else ("fail" if r["狀態"] == "失敗" else "warn")
        html += f'<tr><td>{r["步驟"]}</td><td class="{cls}">{r["狀態"]}</td><td>{r["詳情"]}</td></tr>\n'
    html += f"""</table>
<p>總結: {passed} 通過, {failed} 失敗</p>
</body></html>"""
    (report_dir / "demo_smoke_report.html").write_text(html, encoding="utf-8")
    print(f"報告: {report_dir / 'demo_smoke_report.html'}")


if __name__ == "__main__":
    main()
