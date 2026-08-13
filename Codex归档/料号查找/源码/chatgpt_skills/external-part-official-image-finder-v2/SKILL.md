---
name: external-part-official-image-finder-v2
description: Chinese-first official product page and multi-angle image URL research for industrial automation and mechanical purchased parts after brand identification. Use after brand confidence is confirmed or high-quality suspected, prioritizing Chinese official sites, Chinese PDFs, Chinese industrial platforms, and Taobao/Tmall only as supplemental image evidence.
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

Use one output row per image URL. If one part has 4 image URLs, output 4 rows with the same `part_no`.

## Chinese-First Research Priority

Search sources in this order:

1. Brand Chinese official site, China official site, Taiwan official site, Hong Kong official site, or Chinese product page.
2. Brand Chinese official catalog, Chinese manual, Chinese datasheet, or official PDF.
3. Chinese authorized distributor, Chinese official shop, or brand-recognized reseller.
4. Chinese industrial platforms such as MISUMI China, Yiheda, ZKH, Gongpinhui, 1688, JD Industrial, or similar.
5. International industrial platforms such as DigiKey, Mouser, RS, Automation24, Radwell, EU Automation, PLC-City, or similar.
6. Public image search results that lead to accessible product pages.
7. Taobao / Tmall only for manual supplemental image reference. Do not rely on Taobao/Tmall for scheduled automated image collection because pages often require login, use dynamic rendering, and are unstable for direct image extraction.
8. English, Japanese, or other language official product pages/PDFs if Chinese evidence is insufficient.

Prefer Chinese official sources when available. Do not treat Taobao/Tmall as official confirmation. For brands that state they do not sell through online marketplaces, Taobao/Tmall can only be a visual reference and must not affect official confidence.

## Product URL Confidence

Use only:

- `confirmed`
- `suspected`
- `unknown`

`confirmed` requires a page or PDF that directly supports the brand plus model or model series.

`suspected` means the page likely corresponds to the part but has incomplete model or parameter evidence.

`unknown` means no reliable page could be matched.

## Multi-Angle Image Requirements

Find multiple images per part whenever possible:

- Target 3-6 images per `part_no`.
- Prefer at least front, side, back, label/nameplate, connector/terminal, and catalog drawing.
- If only one image is available, output it and state missing angles in `note`.
- If catalog/PDF images are the only reliable visual source, output the PDF URL with `angle=catalog` and `image_source=catalog`.
- Avoid duplicate images from the same page unless they show different angles or details.

Allowed `angle` values:

- `front`
- `side`
- `back`
- `label`
- `connector`
- `catalog`
- `unknown`

Allowed `image_source` values:

- `official`
- `catalog`
- `authorized_distributor`
- `industrial_platform`
- `international_distributor`
- `taobao`
- `tmall`
- `taobao_manual`
- `tmall_manual`
- `search_result`

Allowed `image_confidence` values:

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

- `official_url` should point to the strongest product evidence, preferably Chinese official product page, Chinese official PDF, or official product series page.
- `image_url` should be a direct image URL when possible.
- If 1688 images are used, keep `product_url_confidence=suspected` unless official evidence separately confirms the product.
- If Taobao/Tmall images are used manually, set `image_source=taobao_manual` or `image_source=tmall_manual`; keep `image_confidence=suspected`; do not set `product_url_confidence=confirmed` based on Taobao/Tmall.
- Do not invent URLs.
- Do not leave all URL fields empty unless the row is truly unknown.

## Do Not

- Do not perform broad brand identification here.
- Do not output `brand_result_*.csv`.
- Do not download images.
- Do not generate assets.json.
- Do not output Markdown tables.
- Do not omit required columns.
