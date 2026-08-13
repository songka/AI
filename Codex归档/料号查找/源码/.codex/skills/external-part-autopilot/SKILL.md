---
name: external-part-autopilot
description: End-to-end external purchased-part asset pipeline for system material TSV files. Use when Codex or a workspace agent should continuously index source TSV data, identify brands with web evidence, find official product images, import results, download assets, and update assets.json with minimal manual copying. Also use when the first step must ask for an original assets.json and decide whether to update or skip existing assets.
---

# External Part Autopilot

## Overview

Run the purchased-part brand and image pipeline as one continuous workflow. Prefer deterministic local scripts for indexing, validation, importing, and asset manifest updates; use web research only for brand evidence and official image discovery.

This skill extends `external-part-pipeline-manager`: use that skill's local file layout and script names, but remove unnecessary human handoffs when the same agent can do the next action.

## Startup Contract

At the beginning of a new job, ask the user for the original `assets.json`.

- If the user says there is no original `assets.json`, create a new one.
- If the user provides an original `assets.json`, ask one follow-up question: update existing entries or skip existing entries.
- Record the chosen mode as `asset_mode=new`, `asset_mode=update_existing`, or `asset_mode=skip_existing`.
- Do not proceed to image downloading or final `assets.json` updates until this decision is known.

If the request only covers indexing or brand handoff generation, the assets decision can be deferred until before image/asset stages.

## Continuity Rule

Do not create artificial waits between actions that the current agent can perform directly. Continue automatically through local stages after each validation passes:

1. Index TSV.
2. Export brand batch.
3. Research/import brand results.
4. Export asset batch.
5. Research/import asset results.
6. Download images.
7. Update `assets.json`.

Stop only when:

- required user input is missing, such as the initial `assets.json` mode;
- validation fails and the current agent cannot repair the data without inventing evidence;
- a network or filesystem approval is required;
- the user explicitly asks to pause.

## Validation Gates

Be strict. Never import or advance to the next stage when validation fails.

- Brand result CSV must exactly use:
  `part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note`
- Brand `confidence` must be `confirmed`, `suspected`, or `unknown`.
- `evidence_url` must be a public `http://` or `https://` URL.
- `confirmed` requires real supporting evidence, not a local source file.
- Asset result CSV must exactly use:
  `part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note`
- Do not treat Taobao/Tmall as the only source for `product_url_confidence=confirmed`.

When validation fails, create the smallest repair batch possible instead of rerunning the whole batch.

## Assets Policy

When updating `assets.json`, preserve existing metadata unless `asset_mode=update_existing`.

- `new`: create `assets.json` from imported image manifest and downloaded files.
- `update_existing`: merge new assets into the original manifest and replace stale entries for matching `part_no` when new evidence is better.
- `skip_existing`: leave existing `part_no` entries untouched and only add missing parts.

Store downloaded images under `assets/{part_no}/`. Preserve source URL, official URL, angle, image confidence, and brand evidence linkage wherever available.

## Reference

Read `references/agent-operating-contract.md` before configuring a workspace agent or running the full end-to-end workflow.
