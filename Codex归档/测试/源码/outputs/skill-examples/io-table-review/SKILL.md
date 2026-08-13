---
name: io-table-review
description: Use when checking automation IO tables, point lists, PLC tag exports, electrical design drafts, or station signal lists for non-standard automation projects. Review naming consistency, duplicated addresses, signal type mismatches, missing safety/interlock/alarm points, and incomplete station ownership. Use the bundled script for CSV checks when an IO table file is available. Do not use for final electrical sign-off without engineer review.
---

# IO Table Review

Use this skill to review IO table quality before electrical design review or PLC software handoff.

## Workflow

1. If the user provides a CSV IO table, run `scripts/check_io_table.py` first and use its findings as deterministic evidence.
2. Read `references/io-rules.md` for naming, signal, and risk checks.
3. Inspect the table by station, device, signal type, address, tag name, and description.
4. Group findings into duplicates, missing fields, naming issues, signal mismatches, safety/interlock gaps, and questions for the designer.
5. Output a review table with: issue, evidence, impact, priority, suggested owner, and recommended action.
6. End with a readiness status: `ready for review`, `review with corrections`, or `not ready`.

## CSV Expectations

Prefer CSV columns named `station`, `device`, `signal_type`, `address`, `tag`, and `description`. If names differ, infer the closest fields and state the mapping used.

## Safety Boundary

Do not approve safety circuits, emergency stop design, or final PLC logic. Surface issues for a qualified electrical engineer to confirm.
