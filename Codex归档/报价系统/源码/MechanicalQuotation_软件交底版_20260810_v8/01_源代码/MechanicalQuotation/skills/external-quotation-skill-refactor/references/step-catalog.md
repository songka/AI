# MechanicalQuotation step catalog

| # | Step | 当前内置执行方式 | Minimum evidence/output | Usual owner |
|---:|---|---|---|---|
| 1 | `DOCUMENT_UNDERSTANDING` | AI 主处理，失败回退规则 | summary, requirements, ambiguities, source evidence, confidence | shared global Agent/Skill |
| 2 | `PART_CLASSIFICATION` | AI 主处理，失败回退规则 | one category, alternatives, evidence, confidence | shared global Agent/Skill |
| 3 | `FEATURE_EXTRACTION` | 非 AI 确定性规则 | features, conflicts, missing evidence | internal rule or category Skill |
| 4 | `MATERIAL_CLASSIFICATION` | 非 AI 确定性规则 | material/specification, assumptions, evidence | internal rule or category Skill |
| 5 | `PROCESS_PLANNING` | AI 主处理，失败回退规则 | ordered processes, alternatives rejected, evidence | category Skill/Agent |
| 6 | `TIME_ESTIMATION` | 混合；规则基线，满足条件时采用 AI 工时 | single-part setup/process/inspection time and assumptions | process-specific Skill/Agent |
| 7 | `LINE_ITEM_PRICING` | 非 AI 价格表与计算规则 | source IDs, quantity, unit, price and amount | internal rule or process Skill |
| 8 | `UNKNOWN_ESTIMATION` | 条件式 AI；仅在存在缺价待确认项时执行 | AI references, assumptions, confidence, review flag | shared Agent/Skill |
| 9 | `QUOTE_ASSEMBLY` | 非 AI 算术与汇总规则 | subtotal, tax, total and arithmetic validation | deterministic internal rule |
| 10 | `PRICE_AUDIT` | AI 主审核，失败回退规则审核 | verdict, issues, executable actions, confidence | shared audit plus process override |
| 11 | `REVIEW_RECOMMENDATION` | 非 AI 风险聚合规则 | prioritized risks, blockers, required evidence | deterministic aggregator or audit Agent |

Steps 1–2 are global because no validated category exists. Category routing starts at step 3. Concrete-process routing is allowed for `TIME_ESTIMATION`, `LINE_ITEM_PRICING`, `PRICE_AUDIT`, and `REVIEW_RECOMMENDATION`. `PROCESS_PLANNING` produces the process codes and therefore cannot depend on them beforehand.

Set `supports_full_quotation` only when a Skill covers the complete chain and returns a valid quotation. Classification, audit, process planning, Excel or partial pricing alone never qualifies.

“内置执行方式”描述当前默认实现，不是不可改变的硬限制。管理员配置外接 Skill/Agent 后，实际执行者可能不同；以报价详情中的执行类型、Skill、Agent 和回退状态为准。
