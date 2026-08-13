---
name: external-part-brand-id
description: Brand identification for industrial automation and mechanical purchased parts from uploaded CSV, Excel, or BOM batches. Use for brand recognition, model normalization, typo-tolerant model matching, and confirmed/suspected/unknown classification before any official page or image search.
---

# External Part Brand ID

Use this skill when the user provides `brand_pending_*.csv` or asks to identify brands for purchased parts.

## Input

Expect CSV / Excel rows with some of these fields:

part_no, description, unit, requester, stock, category_1, category_2, category_3, product_type, model, brand_raw, supplier, confidence_expected

## Required Output

Output CSV only, with exactly this header and order:

part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

If the input is named `brand_pending_0001.csv`, the output must be named or recommended as `brand_result_0001.csv`.
If the input is named `brand_pending_uc3_sample_20.csv`, the output must be named or recommended as `brand_result_uc3_sample_20.csv`.

## Workflow

1. Parse each row.
2. Extract product type from `product_type` or from `description`.
3. Extract `original_model` from `model`; if empty, infer from `description`.
4. Generate a conservative `normalized_model`.
5. Identify brand from `brand_raw`, explicit `品牌:` fields, description tail brand, supplier clues, official pages, or credible external sources.
6. Assign `confidence`.
7. Emit one output row per input row.

## Model Tolerance

Model numbers may be wrong or incomplete. Consider:

- `0` vs `O`
- `1` vs `I` vs `l`
- missing or misplaced `-`, `/`, spaces, and underscores
- missing prefixes or suffixes
- mixed voltage, power, point count, and model text
- casing differences

Do not confirm a brand only because one similar model exists. Cross-check product type, voltage, power, IO count, size, interface, and series context.

## Confidence Rules

Use only:

- `confirmed`
- `suspected`
- `unknown`

`confirmed`:
- Calibration mode: the original row has an explicit brand field or clear description tail brand.
- Formal research mode: official product page, official catalog, official PDF, or strong evidence directly matches brand and model.

`suspected`:
- Evidence points toward one brand, but direct official proof is incomplete.
- A model variant matches, but some uncertainty remains.

`unknown`:
- No reliable evidence.
- Multiple brands conflict.
- Model is too incomplete or generic.
- Key parameters do not match.

## Calibration Mode

If the user says sample, calibration, field check, or "先确认字段和分类规则":

- Do not need to perform full web research.
- If brand comes from explicit original data, set `confidence=confirmed`.
- Use `evidence_url=source:fnd_gfm.tsv` unless the user names another source file.
- Use `evidence_type=raw_brand_field` for explicit brand fields.
- Use `evidence_type=description_tail_brand` for brands found at the end of description.
- Use `model_issue=none` unless a specific issue is visible.

## Evidence Type

Use one of:

- `raw_brand_field`
- `description_tail_brand`
- `official_product_page`
- `official_pdf`
- `authorized_distributor`
- `industrial_platform`
- `search_result`
- `no_evidence`

## Model Issue

Use one of:

- `none`
- `possible_0_O`
- `possible_1_I_l`
- `missing_dash`
- `missing_suffix`
- `missing_prefix`
- `partial_model`
- `mixed_spec`
- `conflicting_variants`

## Do Not

- Do not output Markdown tables.
- Do not omit required columns.
- Do not use old column `model` instead of `original_model` and `normalized_model`.
- Do not leave `evidence_url` empty.
- Do not search images in this skill.
- Do not produce `asset_result_*.csv`.
