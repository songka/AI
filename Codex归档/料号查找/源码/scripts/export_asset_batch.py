from __future__ import annotations

import argparse

from pipeline_common import HANDOFF_DIR, ensure_dirs, load_state, read_jsonl, save_state, write_csv, DATA_DIR


FIELDS = [
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    candidates = read_jsonl(DATA_DIR / "brand_candidates.jsonl")
    eligible = [row for row in candidates if row.get("confidence") in {"confirmed", "suspected"} and row.get("brand")]

    state = {} if args.reset else load_state("asset_state.json")
    cursor = int(state.get("cursor", 0))
    batch = eligible[cursor : cursor + args.limit]
    batch_id = args.batch_id or f"{(cursor // args.limit) + 1:04d}"
    out = HANDOFF_DIR / "asset_pending" / f"asset_pending_{batch_id}.csv"
    write_csv(out, batch, FIELDS)
    state.update(
        {
            "cursor": cursor + len(batch),
            "last_batch_id": batch_id,
            "last_output": str(out),
            "last_count": len(batch),
            "total_available": len(eligible),
        }
    )
    save_state("asset_state.json", state)
    print(f"output={out} rows={len(batch)} cursor={state['cursor']}/{len(eligible)}")


if __name__ == "__main__":
    main()
