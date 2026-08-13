from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pipeline_common import DATA_DIR, REPORTS_DIR, ensure_dirs, read_csv, read_jsonl, write_jsonl


EXPECTED = [
    "part_no",
    "name_or_type",
    "original_model",
    "normalized_model",
    "brand",
    "confidence",
    "evidence_url",
    "evidence_type",
    "model_issue",
    "note",
]
CONFIDENCE_VALUES = {"confirmed", "suspected", "unknown"}
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def summarize_part_numbers(part_numbers: list[str], limit: int = 12) -> str:
    shown = ", ".join(part_numbers[:limit])
    if len(part_numbers) > limit:
        shown += f", ... (+{len(part_numbers) - limit})"
    return shown


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    header = list(rows[0].keys()) if rows else []
    if header != EXPECTED:
        issues.append(f"表头不匹配: {header}")

    bad_conf = [row.get("part_no", "") for row in rows if row.get("confidence") not in CONFIDENCE_VALUES]
    empty_evidence = [row.get("part_no", "") for row in rows if not row.get("evidence_url")]
    non_url_evidence = [
        row.get("part_no", "")
        for row in rows
        if row.get("evidence_url") and not URL_RE.match(row.get("evidence_url", ""))
    ]
    confirmed_without_url = [
        row.get("part_no", "")
        for row in rows
        if row.get("confidence") == "confirmed" and not URL_RE.match(row.get("evidence_url", ""))
    ]

    if bad_conf:
        issues.append(f"confidence 非法: {summarize_part_numbers(bad_conf)}")
    if empty_evidence:
        issues.append(f"evidence_url 为空: {summarize_part_numbers(empty_evidence)}")
    if non_url_evidence:
        issues.append(f"evidence_url 不是 http/https URL: {summarize_part_numbers(non_url_evidence)}")
    if confirmed_without_url:
        issues.append(f"confirmed 缺少真实证据 URL: {summarize_part_numbers(confirmed_without_url)}")
    return issues


def write_report(path: Path, row_count: int, merged_count: int, issues: list[str], imported: bool) -> Path:
    report = [
        "# 品牌结果导入报告",
        "",
        f"- 输入文件: {path}",
        f"- 输入记录数: {row_count}",
        f"- 累计品牌候选数: {merged_count}",
        f"- 导入状态: {'已导入' if imported else '未导入'}",
        f"- 校验结果: {'通过' if not issues else '存在问题'}",
        "",
    ]
    if issues:
        report.append("## 问题")
        report.extend(f"- {issue}" for issue in issues)
        report.append("")
    report_path = REPORTS_DIR / f"brand_import_{path.stem}.md"
    report_path.write_text("\n".join(report), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()

    ensure_dirs()
    path = Path(args.csv_path)
    rows = read_csv(path)
    issues = validate_rows(rows)
    existing = {row["part_no"]: row for row in read_jsonl(DATA_DIR / "brand_candidates.jsonl") if row.get("part_no")}

    if issues:
        report_path = write_report(path, len(rows), len(existing), issues, imported=False)
        print(f"imported=0 total={len(existing)} issues={len(issues)} report={report_path}")
        sys.exit(1)

    for row in rows:
        existing[row["part_no"]] = row
    merged = [existing[key] for key in sorted(existing)]
    write_jsonl(DATA_DIR / "brand_candidates.jsonl", merged)

    report_path = write_report(path, len(rows), len(merged), issues, imported=True)
    print(f"imported={len(rows)} total={len(merged)} issues=0 report={report_path}")


if __name__ == "__main__":
    main()
