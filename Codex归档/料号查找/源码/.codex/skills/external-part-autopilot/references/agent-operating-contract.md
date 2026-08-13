# Agent Operating Contract

## Mission

Own the external purchased-part asset workflow from raw system material TSV to a validated `assets.json`. Reduce human copying by doing all steps the current agent can safely do itself.

## Required First Interaction

Ask:

```text
请提供原始 assets.json。如果没有，请回复“没有”。
如果有原始 assets.json，我会继续问你是“更新已有”还是“跳过已有”。
```

If the user provides a file, ask:

```text
检测到你提供了原始 assets.json。请确认本次策略：更新已有条目，还是跳过已有条目只补新增料号？
```

Normalize the decision:

- no original file: `asset_mode=new`
- update existing: `asset_mode=update_existing`
- skip existing: `asset_mode=skip_existing`

## Continuous Execution Rules

Perform local deterministic work without asking for confirmation between stages. Examples:

- After indexing succeeds, export the next needed batch.
- After a valid brand result is available, import it and export the corresponding asset batch.
- After a valid asset result is available, import it and proceed to download images if network/file permissions allow it.
- After images download and validate, update `assets.json` according to `asset_mode`.

Ask the user only for missing decisions, unavailable files, external approvals, or irreparable validation failures.

## Evidence Rules

Never invent evidence URLs.

For brand results:

- `confirmed`: requires a real `http/https` evidence URL supporting brand and model/series.
- `suspected`: may use weaker evidence, but `evidence_url` still must be a real `http/https` URL.
- `unknown`: use only when no useful brand can be determined; still include a source URL explaining the uncertainty when possible.

For image results:

- Prefer official product pages and official static image URLs.
- Distributor or industrial marketplace URLs may be used as secondary evidence if official pages are unavailable.
- Taobao/Tmall may be noted only as manual supplemental reference, not as the sole confirmation source.

## Repair Strategy

If a result file mostly passes validation, create a repair batch containing only failed `part_no` rows.

Name repair files predictably:

- Brand pending: `brand_pending_{batch_id}_fixN.csv`
- Brand result: `brand_result_{batch_id}_fixN.csv`
- Asset pending: `asset_pending_{batch_id}_fixN.csv`
- Asset result: `asset_result_{batch_id}_fixN.csv`

Import merged results only after all required rows pass validation.

## Completion Report

Every run should finish with:

- current stage;
- files created or updated;
- validation status;
- exact next action, including whether it is for Codex, ChatGPT Web, or human input.
