from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_common import DATA_DIR, REPORTS_DIR, ensure_dirs, read_csv, read_jsonl, write_jsonl


EXPECTED = [
    "part_no",
    "brand",
    "original_model",
    "normalized_model",
    "official_url",
    "product_url_confidence",
    "image_url",
    "angle",
    "image_source",
    "image_confidence",
    "note",
]
ANGLES = {"front", "side", "back", "label", "connector", "catalog", "unknown"}
SOURCES = {
    "official",
    "catalog",
    "authorized_distributor",
    "industrial_platform",
    "international_distributor",
    "taobao_manual",
    "tmall_manual",
    "search_result",
}
CONF = {"confirmed", "suspected", "unknown"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()

    ensure_dirs()
    path = Path(args.csv_path)
    rows = read_csv(path)
    header = list(rows[0].keys()) if rows else []
    issues: list[str] = []
    if header != EXPECTED:
        issues.append(f"表头不匹配：{header}")

    for row in rows:
        part = row.get("part_no", "")
        if row.get("angle") not in ANGLES:
            issues.append(f"{part} angle 非法：{row.get('angle')}")
        if row.get("image_source") not in SOURCES:
            issues.append(f"{part} image_source 非法：{row.get('image_source')}")
        if row.get("image_confidence") not in CONF:
            issues.append(f"{part} image_confidence 非法：{row.get('image_confidence')}")
        if row.get("product_url_confidence") not in CONF:
            issues.append(f"{part} product_url_confidence 非法：{row.get('product_url_confidence')}")
        if not row.get("official_url"):
            issues.append(f"{part} official_url 为空")

    merged: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in read_jsonl(DATA_DIR / "image_manifest.jsonl"):
        key = (
            row.get("part_no", ""),
            row.get("official_url", ""),
            row.get("image_url", ""),
            row.get("angle", ""),
        )
        merged[key] = row
    for row in rows:
        key = (
            row.get("part_no", ""),
            row.get("official_url", ""),
            row.get("image_url", ""),
            row.get("angle", ""),
        )
        merged[key] = row
    write_jsonl(DATA_DIR / "image_manifest.jsonl", [merged[key] for key in sorted(merged)])

    by_part: dict[str, int] = {}
    direct_images = 0
    for row in rows:
        by_part[row.get("part_no", "")] = by_part.get(row.get("part_no", ""), 0) + 1
        if row.get("image_url", "").lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            direct_images += 1

    report = [
        "# 官网图片结果导入报告",
        "",
        f"- 输入文件：{path}",
        f"- 导入行数：{len(rows)}",
        f"- 覆盖料号数：{len(by_part)}",
        f"- 直接图片链接数：{direct_images}",
        f"- 校验结果：{'通过' if not issues else '存在问题'}",
        "",
        "## 每料号图片行数",
        "",
    ]
    report.extend(f"- {part}: {count}" for part, count in sorted(by_part.items()))
    if issues:
        report.extend(["", "## 问题", ""])
        report.extend(f"- {issue}" for issue in issues)
    (REPORTS_DIR / f"asset_import_{path.stem}.md").write_text("\n".join(report), encoding="utf-8")
    print(f"imported={len(rows)} parts={len(by_part)} direct_images={direct_images} issues={len(issues)}")


if __name__ == "__main__":
    main()
