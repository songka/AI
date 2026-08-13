---
name: external-part-pipeline-manager
description: Manage the local Codex side of the external purchased-part research pipeline for fnd_gfm/system material TSV files. Use when working on this project to index TSV data, export ChatGPT Web handoff CSV batches, import brand and asset result CSVs, validate outputs, update assets manifests, and always report the current stage plus the exact next step.
---

# External Part Pipeline Manager

Use this skill for the `料号查找` workflow whenever the user asks to continue, test, run, resume, import, export, check, or plan the external purchased-part pipeline.

The workflow has two agents:

- Codex desktop: local files, deterministic scripts, indexing, CSV handoff, result import, validation, image download, `assets.json`.
- ChatGPT Web agent: web research through `external-part-brand-id` and `external-part-official-image-finder`.

Do not use Codex quota for broad web research unless the user explicitly asks. Prefer producing clean handoff files for ChatGPT Web.

## Mandatory Response Pattern

Every time this skill is used, finish with a short "下一步" block containing:

- `执行人`: Codex / ChatGPT Web / 人工
- `输入`: exact file path or file name
- `动作`: one sentence
- `输出`: expected file path or file name

If work was performed, also state:

- what changed
- which files were created or updated
- whether validation passed

## Workspace Layout

Important paths:

- Source TSV: `fnd_gfm.tsv` or a newer system material TSV supplied by the user.
- Local scripts: `scripts/`
- Indexed data: `data/`
- ChatGPT handoff: `handoff/chatgpt/`
- State: `state/`
- Reports: `reports/`
- Images: `assets/{part_no}/`
- Asset index: `assets.json`

## Pipeline Stages

### Stage 0: Source TSV

If the user provides a newer TSV:

1. Copy or ingest it into the workspace only if accessible.
2. Preserve the old file unless the user explicitly says to replace it.
3. Prefer naming the active source clearly, for example `system_material_20260701.tsv`.
4. Run the index step against the active source. If scripts only support `fnd_gfm.tsv`, update scripts to accept `--source` before continuing.

### Stage 1: Index TSV

Command:

```powershell
python scripts\index_fnd_gfm.py
```

Outputs:

- `data/indexed_parts.jsonl`
- `data/target_parts.jsonl`
- `data/target_parts.tsv`
- `reports/index_report.md`

Check record count, target count, category coverage, and encoding in files rather than PowerShell display.

### Stage 2: Export Brand Batch

Command example:

```powershell
python scripts\export_brand_batch.py --prefix UC3 --limit 50 --batch-id uc3_0001
```

Output:

- `handoff/chatgpt/brand_pending/brand_pending_uc3_0001.csv`

Give this to ChatGPT Web with `external-part-brand-id`.

Expected Web output:

- `handoff/chatgpt/brand_result/brand_result_uc3_0001.csv`

Required brand result fields:

```text
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note
```

### Stage 3: Import Brand Result

Command:

```powershell
python scripts\import_brand_result.py handoff\chatgpt\brand_result\brand_result_uc3_0001.csv
```

Outputs:

- `data/brand_candidates.jsonl`
- `reports/brand_import_brand_result_uc3_0001.md`

If validation fails, do not export asset batch. Report the exact field, enum, or evidence issue and ask the user to rerun the Web agent with stricter instructions.

### Stage 4: Export Asset Batch

Command:

```powershell
python scripts\export_asset_batch.py --limit 20 --batch-id uc3_0001
```

Output:

- `handoff/chatgpt/asset_pending/asset_pending_uc3_0001.csv`

Give this to ChatGPT Web with `external-part-official-image-finder`.

Expected Web output:

- `handoff/chatgpt/asset_result/asset_result_uc3_0001.csv`

Required asset result fields:

```text
part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note
```

### Stage 5: Import Asset Result

Command:

```powershell
python scripts\import_asset_result.py handoff\chatgpt\asset_result\asset_result_uc3_0001.csv
```

Outputs:

- `data/image_manifest.jsonl`
- `reports/asset_import_asset_result_uc3_0001.md`

Check direct image URL count, rows per part number, multi-angle coverage, and no Taobao/Tmall as official confirmation.

### Stage 6: Download Images and Update Assets

Only after asset result validation is acceptable:

- download direct image URLs
- store images under `assets/{part_no}/`
- update `assets.json`
- preserve source URL, angle, image confidence, and official URL

If direct image URLs are sparse, ask Web agent for better image links before downloading.

## ChatGPT Web Rules

Brand identification must use `external-part-brand-id`.

Official image lookup must use `external-part-official-image-finder`.

Do not mix stages:

- `brand_pending_*.csv` -> `brand_result_*.csv`
- `asset_pending_*.csv` -> `asset_result_*.csv`

Taobao/Tmall policy:

- Do not use for scheduled automatic scraping.
- Use only as manual supplemental image reference.
- Never use as the only source for `product_url_confidence=confirmed`.

## Status Detection

When asked "下一步", "继续", "跑流程", or similar:

1. List newest files under `handoff/chatgpt/brand_pending`, `brand_result`, `asset_pending`, `asset_result`.
2. Check `data/brand_candidates.jsonl` and `data/image_manifest.jsonl`.
3. Check `state/*.json`.
4. Infer the current stage:
   - no indexed data -> Stage 1
   - brand pending exists but no matching result -> wait for ChatGPT Web
   - brand result exists but not imported -> Stage 3
   - brand candidates exist but no asset pending -> Stage 4
   - asset pending exists but no matching result -> wait for ChatGPT Web
   - asset result exists but not imported -> Stage 5
   - image manifest exists -> Stage 6
5. Report the next action with exact command or handoff instruction.

## Handoff Prompts

For exact ChatGPT Web prompt templates, read `references/web-agent-handoff.md` when preparing a handoff file.

## Validation Bias

Be strict about:

- exact CSV headers
- required evidence URL
- valid enum values
- file naming
- line counts matching batch names
- image URLs being downloadable when expected

Do not silently fix Web output unless creating a clearly named calibrated copy for testing.

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Not every skill requires all three types of resources.**
