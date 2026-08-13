---
name: external-part-official-image-finder
description: Official product page and image URL research for industrial automation and mechanical purchased parts after brand identification. Use only after brand confidence is confirmed or high-quality suspected, to find official URLs, PDFs, and multi-angle image evidence for asset collection.
---

# External Part Official Image Finder

Use this skill when the user provides `asset_pending_*.csv` or asks for official product pages and image URLs after brand identification.

Do not use this skill for raw brand identification. Brand identification must happen first with `external-part-brand-id`.

## Input

Expect rows with fields like:

part_no, name_or_type, original_model, normalized_model, brand, confidence, evidence_url, evidence_type, model_issue, note

Only process rows where:

- `confidence=confirmed`
- or `confidence=suspected` with high evidence quality and low brand conflict

Skip or mark as unknown when:

- `confidence=unknown`
- suspected record has strong multi-brand conflict
- model is too incomplete to identify product page or image

## Required Output

Output CSV only, with exactly this header and order:

part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note

If the input is named `asset_pending_0001.csv`, the output must be named or recommended as `asset_result_0001.csv`.

## Research Priority

Search sources in this order:

1. Brand official product page
2. Brand official product catalog
3. Brand official PDF
4. Authorized distributor page
5. Reliable industrial platform
6. General search result

Prefer official sources. Do not treat search result snippets as product confirmation.

## Product URL Confidence

Use only:

- `confirmed`
- `suspected`
- `unknown`

`confirmed` requires a page or PDF that directly supports the brand plus model or model series.

`suspected` means the page likely corresponds to the part but has incomplete model or parameter evidence.

`unknown` means no reliable page could be matched.

## Image Requirements

Look for multiple angles when available:

- `front`
- `side`
- `back`
- `label`
- `connector`
- `catalog`
- `unknown`

Use one output row per image URL. If one part has three image URLs, output three rows with the same `part_no`.

Image source must be one of:

- `official`
- `catalog`
- `authorized_distributor`
- `industrial_platform`
- `search_result`

Image confidence must be one of:

- `confirmed`
- `suspected`
- `unknown`

## Matching Rules

Confirm image relevance using visible and contextual evidence:

- brand mark
- exact model or model series
- official page context
- product type
- terminal/interface layout
- nameplate or label
- shape and dimensions
- voltage, power, IO count, or other key parameters

Do not confirm an image only because it looks similar.

## URL Rules

- `official_url` should point to the strongest product evidence, preferably official product page or official PDF.
- `image_url` must be a direct image URL when possible.
- If only a catalog PDF image exists, use the PDF URL and set `angle=catalog`, `image_source=catalog`.
- Do not invent URLs.
- Do not leave all URL fields empty unless the row is truly unknown.

## Do Not

- Do not perform broad brand identification here.
- Do not output `brand_result_*.csv`.
- Do not download images.
- Do not generate assets.json.
- Do not output Markdown tables.
- Do not omit required columns.
