# 外接报价 Skill 接入说明

> V2 新增“报价步骤 → 零件类别 → 具体工艺”三层路由、独立外挂 Agent、Skill-Agent 绑定和内容查看。
> 新开发请先读 `V2_THREE_LAYER_ROUTING_AND_MIGRATION.md`，并使用
> `external-skill-folder-v2.0.example.json` / `external-agent-folder-v2.0.example.json`。
> 路由配置版本为 2.0；外接调用协议暂时保持 1.0，以兼容现有 Skill。

![外接 Skill 与内置 DeepSeek AI 十步报价流程](images/current-quotation-flow-with-skill-ai-v3.png)

## 外部开发步骤

1. 选择接入方式：优先使用文件夹 Skill；只有需要自建服务、模型或数据库时才使用 HTTP Skill。
2. 选择整套报价或一个/多个分布式步骤。整套模式必须支持全部 11 步；分布式 Skill 只声明实际支持步骤。
3. 阅读本文件、`external-quotation-skill-protocol-v1.0.yaml`、`EXTERNAL_SKILL_TRAINING_GUIDE.md`，以及
   `external-skill-agents/` 中所选步骤的独立说明。
4. 复制 `external-skill-folder-v1.0.example.json` 建立 `skill.json`，再按标准提示词编写 `SKILL.md`。
5. 用正常、信息缺失、备注冲突、无正式价格、重复计费、设备过度和提示注入案例测试。
6. 在管理员“外接 Skill 设置”先用本地测试目录检测；测试设置必须关闭 SMB 同步。通过协议与价格
   防线验收后，才允许管理员发布到 SMB 公共槽。

## 文件夹 Skill 的运行必需文件

```text
<skill-folder>/
├─ skill.json                  # 必需：身份、版本、协议、支持步骤和文档清单
├─ SKILL.md                    # 必需：交给程序内置 DeepSeek 的主要提示词
└─ references/                # 可选：公司工艺、材料、工时、审核规则
   ├─ 公司工艺规则.md
   └─ 审核注意事项.yaml
```

文件夹 Skill 不得包含 DeepSeek Key 或其他密钥。除 UTF-8 指令与参考文档外，也可包含 Python、EXE、CLI、
批处理脚本和 Excel 资产；但执行能力必须在 `skill.json.commands` 逐项声明。未声明的程序文件不会被执行。

## 外部团队完整验收交付物

除上述运行文件外，开发团队还应交付：`tests/cases.json`、`tests/expected-results.json`、版本与适用
范围说明、支持/不支持步骤清单、完整请求/响应样例、最终提示词、训练/评测数据说明、测试结果、
失败回退与人工审核条件，以及发布版本、日期和 SHA-256。HTTP Skill 还必须提供服务源码、依赖锁定、
启动说明和 `/v1/health`、`/v1/capabilities`、`/v1/quote` 三个接口。

接口正文以 `external-quotation-skill-protocol-v1.0.yaml` 为准。系统支持两种来源：

- HTTP/HTTPS 服务：实现 `GET /v1/capabilities` 与 `POST /v1/quote`。
- 本地或 SMB 公共槽文件夹：提示词步骤由内置 DeepSeek 执行；已声明的 `commands` 可执行文件夹内 Python、EXE、CLI、
  `.bat/.cmd/.ps1` 以及 Excel 读/写/修改/导出任务。程序先检查运行环境，使用参数数组、限时和文件夹边界执行；失败时显示原因并回退。

文件夹清单可复制 `external-skill-folder-v1.0.example.json` 并改名为 `skill.json`。
`instruction_file` 默认是 `SKILL.md`；`reference_files` 可列出同一文件夹内的 Markdown、TXT、JSON
或 YAML。所有文件必须为 UTF-8、不得跳出 Skill 文件夹，指令与参考资料合计上限 128 KB。
程序把这些 Skill 文档作为受控系统指令，再把用户选择的图纸文字、内置解析特征、AI 判断、既有
报价分项和正式价格表作为用户资料交给内置 DeepSeek，要求返回协议 1.0 JSON。

管理员在“外接Skill设置”中可输入 HTTP 地址，或选择本地/SMB 文件夹，再分别点击“检测 Skill”或
“检测外挂智能体”。双击列表资源可查看能力和内容；HTTP 资源只公开能力清单，文件夹资源可查看声明的
SKILL.md/AGENT.md 与 references，内置 Agent 可查看公开执行契约。
整套报价模式只能选择一个声明支持整套报价的 Skill；分布式模式按箭头顺序执行，每一步可选内置
系统或一个支持该步骤的 Skill，也可在不同步骤使用多个 Skill。第 1 步“图纸与备注理解”和第 2 步“零件类别分类”
固定使用全局路由；管理员选择“加工件、钣金件、焊接件、型材组装件”时，只能继承或覆盖第 3～11 步；
配置统一发布到 SMB。

管理员可开启“调试模式”。完成报价后，“查看 Skill 调试”会按 11 步显示实际输入 JSON、实际输出
JSON、执行者、耗时、失败回退和自动验收结果。默认关闭；测试时必须使用 `sync_enabled=False`，只写
本机测试缓存。调试内容不包含 DeepSeek Key、认证头或密码。

分布式 Skill 按依赖分为五个阶段执行，而不是把同一个 Skill 跨阶段的步骤一次混在一起：

1. 图纸与备注理解、零件类别分类；
2. 特征提取、材料判断；
3. 工艺路线、工时估算；
4. 分项计价、待确认项估价、报价汇总；
5. 价格审核、人工审核建议。

每一阶段完成后，系统把精简结果写入下一阶段的 `built_in_context.prior_skill_results`。因此工艺 Skill
能读取分类与特征结果，计价 Skill 能读取工艺与工时，审核 Skill 能读取报价明细。第 1、2 步的全局
Skill 结果也会跨过类别路由继续传递；最多保留最近 12 项，避免上下文无限增长。整套报价 Skill 仍只
调用一次，不拆成多个阶段。

请求中的 `built_in_context` 还会包含内置特征、已有费用行、警告及 AI 审核结果。Skill 可据此继续
审核或生成建议。外接结果仍受正式价格
防线约束：公司正式价必须引用已发布材料、工艺或表面处理记录的 `company_price_id` 且单价一致，
不匹配历史整件正式价格；AI 估价会计入本次报价，但必须醒目标识“AI估算、待人工确认”，不能伪装
成公司核准价。

## 批量性能与缓存

- 批量规则报价默认 4 路并行；启用 AI 时默认 2 路并行，避免短时间压垮 AI 服务。最多 8 路，可用
  环境变量 `MECHANICAL_QUOTATION_BATCH_WORKERS` 调整。
- 批次中只要包含 SLDDRW 或 SLDPRT，整批自动改为单路，因为 SolidWorks COM 不适合并发打开文件。
- AI 缓存只复用“同一 AI 客户端、完全相同输入、低温度且已返回有效 JSON”的成功响应。缓存仅在
  当前程序内存中，最多 256 项；不使用模糊匹配，也不把图纸响应写到共享磁盘，避免旧价格、不同
  用户或相似图纸被误复用。无效、超时和高随机性响应不缓存。
- 非计价阶段不发送正式价格表的全部 `records`，仅发送版本和校验摘要；此时
  `records_omitted_for_non_pricing_step=true`。这样可明显减少分类、理解和特征步骤的输入 token。
- 批量结果的 AI 明细中会显示缓存命中数与未命中数，便于判断实际节省量。

`external-skill-prompt-templates-v1.0.yaml` 给出了 10 个步骤 Agent 的标准提示词。外部 HTTP Skill
可直接采用相同提示词；文件夹 Skill 可把需要的步骤提示词复制到 `SKILL.md`，再补充公司的工艺、
材料、工时或审核规则。

每个步骤都有独立对接文件，外部开发者只需读取共通协议及所选步骤文件：

| 步骤 | 独立对接说明 |
|---|---|
| 图纸与备注理解 | `external-skill-agents/01_DOCUMENT_UNDERSTANDING.md` |
| 特征提取 | `external-skill-agents/02_FEATURE_EXTRACTION.md` |
| 材料判断 | `external-skill-agents/03_MATERIAL_CLASSIFICATION.md` |
| 工艺路线 | `external-skill-agents/04_PROCESS_PLANNING.md` |
| 工时估算 | `external-skill-agents/05_TIME_ESTIMATION.md` |
| 分项计价 | `external-skill-agents/06_LINE_ITEM_PRICING.md` |
| 待确认项参考估价 | `external-skill-agents/07_UNKNOWN_ESTIMATION.md` |
| 价格审核 | `external-skill-agents/08_PRICE_AUDIT.md` |
| 人工审核建议 | `external-skill-agents/09_REVIEW_RECOMMENDATION.md` |
| 报价汇总 | `external-skill-agents/10_QUOTE_ASSEMBLY.md` |

外部团队应先使用 `EXTERNAL_SKILL_GENERATION_PROMPT.md` 生成交付物，再按
`EXTERNAL_SKILL_TRAINING_GUIDE.md` 建立训练/评测样本和执行验收。

生产设置保存到 SMB 公共槽 `data/external-skill-routing.json`，并同步本地缓存。测试应构造
`sync_enabled=False` 的设置服务，只写测试缓存，禁止写真实 SMB。
