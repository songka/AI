from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
HANDOFF_DIR = ROOT / "handoff" / "chatgpt"
REPORTS_DIR = ROOT / "reports"
STATE_DIR = ROOT / "state"


TARGET_CATEGORY_KEYWORDS = ("機構外購件", "机构外购件", "電控外購件", "电控外购件")


def ensure_dirs() -> None:
    for path in [
        DATA_DIR,
        HANDOFF_DIR / "brand_pending",
        HANDOFF_DIR / "brand_result",
        HANDOFF_DIR / "asset_pending",
        HANDOFF_DIR / "asset_result",
        REPORTS_DIR,
        STATE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        rows = list(reader)
    if not rows:
        return []

    header = normalize_header(rows[0])
    output: list[dict[str, str]] = []
    for raw in rows[1:]:
        if not raw or not any(cell.strip() for cell in raw):
            continue
        padded = raw + [""] * max(0, len(header) - len(raw))
        output.append({header[i]: padded[i].strip() for i in range(len(header))})
    return output


def normalize_header(header: list[str]) -> list[str]:
    fallback = ["part_no", "description", "unit", "requester", "stock"]
    if len(header) >= 5 and ("料" in header[0] or "號" in header[0] or "号" in header[0]):
        return fallback + [f"extra_{idx}" for idx in range(5, len(header))]
    return fallback[: len(header)] + [f"extra_{idx}" for idx in range(len(fallback), len(header))]


def split_description(description: str) -> tuple[list[str], dict[str, str]]:
    parts = [part.strip() for part in re.split(r"[;；]", description or "") if part.strip()]
    kv: dict[str, str] = {}
    for part in parts:
        match = re.match(r"^([^:：]+)[:：](.*)$", part)
        if match:
            kv[match.group(1).strip()] = match.group(2).strip()
    return parts, kv


def infer_model(parts: list[str], kv: dict[str, str]) -> str:
    if kv.get("型號"):
        return kv["型號"]
    if kv.get("型号"):
        return kv["型号"]
    candidates: list[str] = []
    for part in parts[4:] if len(parts) > 4 else parts:
        if re.search(r"[A-Za-z]", part) and re.search(r"\d", part):
            if not re.search(r"輸入|输出|輸出|电压|電壓|功率|點數|点数", part):
                candidates.append(part)
    return candidates[-1] if candidates else ""


def infer_brand(parts: list[str], kv: dict[str, str]) -> tuple[str, str]:
    if kv.get("品牌"):
        return kv["品牌"], "raw_brand_field"
    tail = parts[-1] if parts else ""
    if tail and not re.search(r"[:：]", tail) and not re.search(r"[A-Za-z].*\d|\d.*[A-Za-z]|輸入|輸出|输出|點|点|模塊|模块", tail):
        return tail, "description_tail_brand"
    return "", ""


def normalize_record(row: dict[str, str]) -> dict[str, str]:
    description = row.get("description", "")
    parts, kv = split_description(description)
    brand, brand_source = infer_brand(parts, kv)
    model = infer_model(parts, kv)
    return {
        "part_no": row.get("part_no", ""),
        "description": description,
        "unit": row.get("unit", ""),
        "requester": row.get("requester", ""),
        "stock": row.get("stock", ""),
        "category_1": parts[0] if len(parts) > 0 else "",
        "category_2": parts[1] if len(parts) > 1 else "",
        "category_3": parts[2] if len(parts) > 2 else "",
        "product_type": parts[3] if len(parts) > 3 else "",
        "model": model,
        "brand_raw": brand,
        "brand_source": brand_source,
        "supplier": "",
    }


def is_target(record: dict[str, str]) -> bool:
    text = record.get("description", "")
    return any(keyword in text for keyword in TARGET_CATEGORY_KEYWORDS)


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_state(name: str) -> dict:
    path = STATE_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(name: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / name).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
