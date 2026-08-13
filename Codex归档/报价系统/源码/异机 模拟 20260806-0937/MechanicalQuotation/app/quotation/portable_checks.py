"""Self-check and smoke reports used by the portable Windows package."""

from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _write_report(name: str, title: str, checks: list[dict[str, Any]]) -> Path:
    root = _root()
    report_dir = root / "runtime" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    passed = sum(check["ok"] for check in checks)
    report = {
        "timestamp": datetime.now().isoformat(),
        "root": str(root),
        "summary": {"passed": passed, "failed": len(checks) - passed},
        "checks": checks,
    }
    (report_dir / f"{name}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    rows = "".join(
        "<tr><td>{}</td><td class='{}'>{}</td><td>{}</td></tr>".format(
            html.escape(str(check["name"])),
            "pass" if check["ok"] else "fail",
            "通過" if check["ok"] else "失敗",
            html.escape(str(check.get("detail", ""))),
        )
        for check in checks
    )
    document = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>{html.escape(title)}</title><style>
body{{font-family:'Microsoft YaHei UI',sans-serif;max-width:1000px;margin:24px auto}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px}}
th{{background:#1a5276;color:white}}.pass{{color:#17833b}}.fail{{color:#bd2222}}
</style><h1>{html.escape(title)}</h1><p>通過 {passed}/{len(checks)}</p>
<table><tr><th>检查项目</th><th>状态</th><th>详情</th></tr>{rows}</table></html>"""
    output = report_dir / f"{name}.html"
    output.write_text(document, encoding="utf-8")
    return output


def run_self_check() -> int:
    root = _root()
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    pointer_path = root / "data" / "current-version-pointer.json"
    check("程式根目錄", root.exists(), str(root))
    check("正式價格版本指標", pointer_path.exists(), str(pointer_path))
    if pointer_path.exists():
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        snapshot = root / "data" / pointer["snapshot_path"]
        check("正式价格表", snapshot.exists(), pointer["current_version"])
        if snapshot.exists():
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            canonical = json.dumps(payload["company_prices"], sort_keys=True, ensure_ascii=False)
            actual = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            check("价格表完整性校验", actual == payload.get("snapshot_sha256"), actual)

    secret = root / "runtime" / "secrets" / "deepseek_api_key.txt"
    check("DeepSeek 密钥外置文件路径", secret.exists(), str(secret))
    check(
        "DeepSeek AI 配置",
        secret.is_file() and bool(secret.read_text(encoding="utf-8").strip()),
        "密钥已配置且不会写入软件设置或清单" if secret.is_file() else "密钥文件不存在",
    )
    skill_protocol = root / "docs" / "external-quotation-skill-protocol-v1.0.yaml"
    check(
        "外接 Skill 协议",
        skill_protocol.is_file(),
        "支持 HTTP、本地文件夹和 SMB 公共槽文件夹",
    )
    settings_path = root / "config" / "user_settings.json"
    check("设置目录", settings_path.exists(), "密钥与非敏感设置分离")
    check("输出目录", (root / "exports").is_dir(), str(root / "exports"))
    oda_files = list(root.rglob("ODAFileConverter.exe"))
    if oda_files:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        configured = Path(settings.get("dwg_converter_path", ""))
        resolved = (settings_path.parent / configured).resolve()
        check(
            "DWG 转换器",
            resolved.is_file() and resolved in [item.resolve() for item in oda_files],
            "包内 ODA 已配置（仅限获授权电脑）",
        )
    else:
        check("DWG 转换器", True, "使用电脑需另行合法安装并配置 ODA")

    try:
        from quotation.infrastructure.rules.published_pricebook_loader import PublishedPricebookLoader
        loader = PublishedPricebookLoader(pointer_path)
        check("正式价格加载器", loader.loaded, loader.price_version or loader.load_error or "")
    except Exception as exc:
        check("Pricebook Loader", False, str(exc))

    try:
        import tkinter  # noqa: F401
        check("桌面界面", True, "可载入")
    except Exception as exc:
        check("Tkinter UI", False, str(exc))

    try:
        from quotation.api.main import app
        check("接口服务", bool(app.openapi()["paths"]), "接口文档可生成")
    except Exception as exc:
        check("FastAPI", False, str(exc))

    try:
        import pymupdf  # noqa: F401
        import onnxruntime  # noqa: F401
        from rapidocr import RapidOCR  # noqa: F401
        check("扫描 PDF 本地识别", True, "PyMuPDF、RapidOCR 与 ONNX Runtime 可载入")
    except Exception as exc:
        check("扫描 PDF 本地识别", False, str(exc))

    output = _write_report("portable_self_check", "机械报价系统便携版自检报告", checks)
    print(f"自檢報告：{output}")
    return 0 if all(check["ok"] for check in checks) else 1


def run_smoke() -> int:
    root = _root()
    checks: list[dict[str, Any]] = []
    temp_dxf = root / "runtime" / "tmp" / "portable_smoke.dxf"
    try:
        import ezdxf
        from quotation.application.batch_excel import export_batch_excel
        from quotation.application.quotation_service import QuotationApplicationService

        temp_dxf.parent.mkdir(parents=True, exist_ok=True)
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        for start, end in [((0, 0), (100, 0)), ((100, 0), (100, 50)), ((100, 50), (0, 50)), ((0, 50), (0, 0))]:
            msp.add_line(start, end)
        msp.add_text("S50C", height=5).set_placement((5, 55))
        doc.saveas(temp_dxf)
        result = QuotationApplicationService().quote_single_file(temp_dxf)
        from quotation.ui.localization import display_value
        checks.append({
            "name": "示例报价",
            "ok": result.quote is not None,
            "detail": display_value("status", result.status),
        })
        checks.append({
            "name": "13% 税务",
            "ok": result.tax is not None and result.tax.total_including_tax == result.tax.subtotal_excluding_tax + result.tax.tax_amount,
            "detail": f"未稅={result.subtotal_excluding_tax}, 含稅={result.total_including_tax}",
        })
        excel = root / "exports" / "portable_smoke.xlsx"
        export_batch_excel([result], excel)
        checks.append({"name": "批量 Excel", "ok": excel.exists() and excel.stat().st_size > 0, "detail": str(excel)})
    except Exception as exc:
        checks.append({"name": "Demo smoke", "ok": False, "detail": str(exc)})
    finally:
        temp_dxf.unlink(missing_ok=True)

    output = _write_report("portable_demo_smoke", "机械报价系统便携版功能检查报告", checks)
    print(f"Smoke 報告：{output}")
    return 0 if checks and all(check["ok"] for check in checks) else 1
