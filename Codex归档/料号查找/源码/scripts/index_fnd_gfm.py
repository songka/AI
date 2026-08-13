from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_common import (
    DATA_DIR,
    REPORTS_DIR,
    ROOT,
    ensure_dirs,
    is_target,
    normalize_record,
    read_tsv,
    write_csv,
    write_jsonl,
)


TARGET_FIELDS = [
    "part_no",
    "description",
    "unit",
    "requester",
    "stock",
    "category_1",
    "category_2",
    "category_3",
    "product_type",
    "model",
    "brand_raw",
    "brand_source",
    "supplier",
]


def resolve_source(source_arg: str, parser: argparse.ArgumentParser) -> Path:
    source = Path(source_arg)
    if not source.is_absolute():
        source = ROOT / source
    source = source.resolve()

    if not source.exists():
        parser.error(f"source TSV not found: {source}")
    if not source.is_file():
        parser.error(f"source path is not a file: {source}")
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description="Index external purchased-part records from a source TSV.")
    parser.add_argument(
        "--source",
        default="fnd_gfm.tsv",
        help="Source TSV file path, relative to the workspace or absolute.",
    )
    args = parser.parse_args()

    ensure_dirs()
    source = resolve_source(args.source, parser)
    raw_rows = read_tsv(source)
    indexed = [normalize_record(row) for row in raw_rows]
    targets = [row for row in indexed if is_target(row)]

    write_jsonl(DATA_DIR / "indexed_parts.jsonl", indexed)
    write_jsonl(DATA_DIR / "target_parts.jsonl", targets)
    write_csv(DATA_DIR / "target_parts.tsv", targets, TARGET_FIELDS)

    category_counts: dict[str, int] = {}
    for row in targets:
        key = row.get("category_2", "") or "(blank)"
        category_counts[key] = category_counts.get(key, 0) + 1

    lines = [
        "# TSV 索引报告",
        "",
        f"- 源文件: {source}",
        f"- 原始记录数: {len(raw_rows)}",
        f"- 索引记录数: {len(indexed)}",
        f"- 目标外购件记录数: {len(targets)}",
        "",
        "## 目标分类统计",
        "",
    ]
    for key, count in sorted(category_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            "- data/indexed_parts.jsonl",
            "- data/target_parts.jsonl",
            "- data/target_parts.tsv",
        ]
    )
    (REPORTS_DIR / "index_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"source={source}")
    print(f"indexed={len(indexed)} targets={len(targets)}")


if __name__ == "__main__":
    main()
