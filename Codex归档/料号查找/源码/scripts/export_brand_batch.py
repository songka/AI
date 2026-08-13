from __future__ import annotations

import argparse

from pipeline_common import DATA_DIR, HANDOFF_DIR, ensure_dirs, load_state, read_jsonl, save_state, write_csv


FIELDS = [
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
    "supplier",
    "confidence_expected",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    rows = read_jsonl(DATA_DIR / "target_parts.jsonl")
    if args.prefix:
        rows = [row for row in rows if row.get("part_no", "").startswith(args.prefix)]

    state_name = f"brand_state_{args.prefix or 'all'}.json"
    state = {} if args.reset else load_state(state_name)
    cursor = int(state.get("cursor", 0))
    batch = rows[cursor : cursor + args.limit]

    for row in batch:
        row["confidence_expected"] = "production"

    if args.batch_id:
        batch_id = args.batch_id
    else:
        batch_id = f"{(cursor // args.limit) + 1:04d}"
        if args.prefix:
            batch_id = f"{args.prefix.lower()}_{batch_id}"

    out = HANDOFF_DIR / "brand_pending" / f"brand_pending_{batch_id}.csv"
    write_csv(out, batch, FIELDS)

    state.update(
        {
            "prefix": args.prefix,
            "cursor": cursor + len(batch),
            "last_batch_id": batch_id,
            "last_output": str(out),
            "last_count": len(batch),
            "total_available": len(rows),
        }
    )
    save_state(state_name, state)
    print(f"output={out} rows={len(batch)} cursor={state['cursor']}/{len(rows)}")


if __name__ == "__main__":
    main()
