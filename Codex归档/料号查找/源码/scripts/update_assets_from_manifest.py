from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pipeline_common import DATA_DIR, REPORTS_DIR, ROOT, ensure_dirs, read_jsonl


URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def local_images(part_no: str) -> list[str]:
    folder = ROOT / "assets" / part_no
    if not folder.exists():
        return []
    return [str(path.relative_to(ROOT / "assets")) for path in sorted(folder.iterdir()) if path.is_file()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["new", "update_existing", "skip_existing"], required=True)
    parser.add_argument("--assets-json", default=str(ROOT / "assets.json"))
    parser.add_argument("--manifest", default=str(DATA_DIR / "image_manifest.jsonl"))
    args = parser.parse_args()

    ensure_dirs()
    assets_path = Path(args.assets_json)
    if args.mode == "new" or not assets_path.exists():
        assets: dict[str, dict] = {}
    else:
        assets = json.loads(assets_path.read_text(encoding="utf-8"))

    rows = read_jsonl(Path(args.manifest))
    changed_parts: list[str] = []
    skipped_existing = 0

    for row in rows:
        part_no = row.get("part_no", "").strip()
        if not part_no:
            continue
        if args.mode == "skip_existing" and part_no in assets:
            skipped_existing += 1
            continue

        entry = assets.get(part_no, {"part_no": part_no})
        entry.setdefault("part_no", part_no)
        entry.setdefault("images", [])
        entry.setdefault("model_file", None)
        entry.setdefault("local_paths", [])
        entry.setdefault("remote_links", [])

        images = unique([*entry.get("images", []), *local_images(part_no)])
        remote_links = unique(
            [
                *entry.get("remote_links", []),
                row.get("official_url", "").strip(),
                row.get("image_url", "").strip(),
            ]
        )
        evidence = entry.get("external_part_evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        evidence_item = {
            "brand": row.get("brand", ""),
            "original_model": row.get("original_model", ""),
            "normalized_model": row.get("normalized_model", ""),
            "official_url": row.get("official_url", ""),
            "source_url": row.get("image_url", ""),
            "angle": row.get("angle", ""),
            "image_source": row.get("image_source", ""),
            "image_confidence": row.get("image_confidence", ""),
            "product_url_confidence": row.get("product_url_confidence", ""),
            "note": row.get("note", ""),
        }
        evidence_key = json.dumps(evidence_item, ensure_ascii=False, sort_keys=True)
        existing_keys = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in evidence if isinstance(item, dict)}
        if evidence_key not in existing_keys and (URL_RE.match(evidence_item["official_url"]) or URL_RE.match(evidence_item["source_url"])):
            evidence.append(evidence_item)

        before = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        entry["images"] = images
        entry["remote_links"] = remote_links
        entry["external_part_evidence"] = evidence
        assets[part_no] = entry
        after = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        if before != after:
            changed_parts.append(part_no)

    assets_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = REPORTS_DIR / "assets_update_from_manifest.md"
    report_path.write_text(
        "\n".join(
            [
                "# Assets Update Report",
                "",
                f"- mode: {args.mode}",
                f"- manifest_rows: {len(rows)}",
                f"- changed_parts: {len(set(changed_parts))}",
                f"- skipped_existing: {skipped_existing}",
                "",
                "## Changed Part Numbers",
                *[f"- {part_no}" for part_no in sorted(set(changed_parts))],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"changed={len(set(changed_parts))} skipped={skipped_existing} report={report_path}")


if __name__ == "__main__":
    main()
