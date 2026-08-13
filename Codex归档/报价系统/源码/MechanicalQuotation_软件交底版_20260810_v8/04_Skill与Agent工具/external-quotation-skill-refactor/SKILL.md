---
name: external-quotation-skill-refactor
description: Guided analysis, repair, standardization, migration, splitting, merging, creation, and training of MechanicalQuotation V2 Skills and Agents. Use when Codex receives a requirement, Skill/Agent folder, prompts, Python, EXE, CLI or batch tools, Excel workbooks, APIs, business rules, or GitHub references and must guide a non-technical user toward an evidence-backed design, map step/category/process routes, create import-ready skill.json or agent.json resources, bind Agents, check runtime and licensing, and validate examples, failures, and fallbacks.
---

# MechanicalQuotation Skill / Agent 引导式设计工具

引导用户把现有材料或业务需求变成可载入、可解释、可回退的 Skill/Agent。不要要求用户先理解协议、路由或 Agent 术语。

## 启动向导

先用简短中文说明能完成以下工作：

1. 检查现有 Skill/Agent 能做什么、哪里不规范。
2. 修复或迁移现有资源，同时尽量保持兼容。
3. 从业务规则、案例、脚本、Excel 或接口创建新 Skill/Agent。
4. 判断应做成一个 Skill、多个步骤 Skill、多个工艺 Skill，还是共用 Agent。
5. 新建或改写 Agent，并建立明确的 Skill-Agent 绑定。
6. 生成可载入文件、正反例、环境检查和回退方案。

然后按 `references/guided-wizard.md` 运行向导。每轮只询问一个关键选择；提供推荐项和影响。用户已经明确选择时直接采用，不重复询问。

## 引导原则

- 先说业务结果，再解释 Skill、Agent、内部规则和三层路由。
- 先检查用户给出的文件和证据，再推荐方案；不要让用户填写能够自动发现的信息。
- 每个选择都给出推荐理由，并允许“采用推荐方案”。
- 分析模式不得修改输入资源。写入模式在生成前展示目标目录和拟生成资源清单。
- 若用户只给需求，先形成训练样例草案；若用户给现有目录，先形成能力与问题清单。
- 未给足信息时仍完成安全部分，并把缺失项列为待确认，不臆造公司规则或正式价格。

## 核心工作流

1. 记录向导选择：目标、输入来源、写入许可、路由粒度、运行方式和交付形式。
2. 盘点指令、示例、references、Python、EXE、CLI、批处理、API、Excel、依赖、权限、副作用、所有者、版本和回退。
3. 将每项能力标记为 `SUPPORTED`、`PARTIAL`、`UNSUPPORTED` 或 `UNKNOWN`，附文件/章节证据。
4. 判断能力归属：确定性内部规则、Skill、Agent 或命令。精确解析、查价、算术和格式校验优先规则；不确定语义和专业判断才使用 Agent。
5. 选择 `KEEP`、`SHARE`、`STANDARDIZE`、`SPLIT`、`MERGE`、`DEPRECATE` 或 `REPLACE`。读取 `references/work-modes.md`。
6. 映射步骤、零件类别和具体工艺三层路由。读取 `references/v2-routing-and-agents.md` 与 `references/step-catalog.md`。
7. 用户选择 Agent 或现有材料包含 Agent 时，读取 `references/agent-authoring.md`；选择改写、新建、拆分、合并或 Skill+Agent 组合，并验证角色边界。
8. 对 Python、EXE、CLI、批处理或 Excel 读取 `references/runtime-and-manifest.md`，声明精确命令、环境检查、超时和可见回退。
9. 涉及 GitHub 或第三方材料时，写入前读取 `references/licensing-and-provenance.md`。
10. 将入口说明保持简洁；把详细规则、案例和反例放在 references，把工作簿和模板放在 assets，把确定性重复操作放在 scripts。
11. 验证 manifest、ID、步骤/类别/工艺兼容性、输出协议、错误输出、缺失运行时、超时、ID 不一致和内置回退。
12. 交付前读取 `references/examples-and-anti-patterns.md`，至少验证正常、相近反例、歧义复核和缺失输入四类样例。

“训练新 Skill”表示把业务证据、规则、正常样例、错误示范、边界样例和验收测试编码成可复现资源。除非存在真实训练管线，不得暗示进行了模型微调。

## 阶段性确认

在以下节点给出一张简短“向导结果卡”并请求确认；用户已授权自动采用推荐方案时可连续执行：

- 方案确认：一个 Skill、按步骤拆分、按类别拆分、按工艺拆分或混合方案。
- 执行确认：只分析、生成到新目录、原地兼容改写。
- 发布确认：只生成本地资源，或交由主程序载入并发布公共槽。

不要在同一轮同时询问目录、步骤、工艺、Agent、运行时和发布方式。

## 必须交付

- 用户选择及采用的推荐方案。
- 能力矩阵和证据。
- 保留/共用/标准化/拆分/合并/弃用决策。
- 三层路由与 Skill-Agent 绑定。
- 可载入目录树、manifest 和简洁指令。
- Python/EXE/CLI/批处理/Excel 环境报告。
- 正常、错误、歧义和失败回退样例。
- 迁移、兼容和发布说明。
- 面向非技术用户的“能做什么、不能做什么、如何载入、如何选择路由”。
- “需求满足度”清单：每项标记 `已满足`、`部分满足`、`未满足` 或 `待确认`，给出证据文件、限制和下一步；不得只写笼统的“支持”。

## 禁止事项

- 不从文件名或宣传文字推断能力。
- 不让步骤 1、2 依赖尚未产生的零件类别，也不让工艺规划依赖尚未产生的具体工艺。
- 不把每个步骤都变成 Agent；Skill 是能力契约，Agent 是推理执行者。
- 分析阶段不执行用户附带程序；测试只运行 manifest 明确声明、位于资源目录内且受超时约束的命令。
- 不覆盖公司核准价格、原始证据或内置回退。
- 不复制许可证不兼容或来源不清的第三方提示词、代码、数据、图标和模板。
