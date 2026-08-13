# 外接报价 Skill 接入说明

![外接 Skill 与内置 DeepSeek AI 报价流程](images/current-quotation-flow-with-skill-ai-v2.png)

## 外部开发步骤

1. 选择接入方式：优先使用文件夹 Skill；只有需要自建服务、模型或数据库时才使用 HTTP Skill。
2. 选择整套报价或一个/多个分布式步骤。整套模式必须支持全部 10 步；分布式 Skill 只声明实际支持步骤。
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

文件夹 Skill 不需要也不允许提供 EXE、DLL、脚本或 DeepSeek Key。程序只读取 UTF-8 文档，并由
程序内置 DeepSeek 执行。

## 外部团队完整验收交付物

除上述运行文件外，开发团队还应交付：`tests/cases.json`、`tests/expected-results.json`、版本与适用
范围说明、支持/不支持步骤清单、完整请求/响应样例、最终提示词、训练/评测数据说明、测试结果、
失败回退与人工审核条件，以及发布版本、日期和 SHA-256。HTTP Skill 还必须提供服务源码、依赖锁定、
启动说明和 `/v1/health`、`/v1/capabilities`、`/v1/quote` 三个接口。

接口正文以 `external-quotation-skill-protocol-v1.0.yaml` 为准。系统支持两种来源：

- HTTP/HTTPS 服务：实现 `GET /v1/capabilities` 与 `POST /v1/quote`。
- 本地或 SMB 公共槽文件夹：文件夹内放置 UTF-8 `skill.json`、`SKILL.md` 和可选参考文档；
  程序读取这些文件后调用交付包内置 DeepSeek，不执行文件夹内的程序。

文件夹清单可复制 `external-skill-folder-v1.0.example.json` 并改名为 `skill.json`。
`instruction_file` 默认是 `SKILL.md`；`reference_files` 可列出同一文件夹内的 Markdown、TXT、JSON
或 YAML。所有文件必须为 UTF-8、不得跳出 Skill 文件夹，指令与参考资料合计上限 128 KB。
程序把这些 Skill 文档作为受控系统指令，再把用户选择的图纸文字、内置解析特征、AI 判断、既有
报价分项和正式价格表作为用户资料交给内置 DeepSeek，要求返回协议 1.0 JSON。

管理员在“外接Skill设置”中可输入 HTTP 地址，或选择本地/SMB 文件夹，再点击“检测并添加/更新”。
整套报价模式只能选择一个声明支持整套报价的 Skill；分布式模式按箭头顺序执行，每一步可选内置
系统或一个支持该步骤的 Skill，也可在不同步骤使用多个 Skill。

分布式调用发生在内置图纸解析、AI 工艺判断和分项报价之后，因此请求中的 `built_in_context` 会包含
内置特征、已有费用行、警告及 AI 审核结果。Skill 可据此继续审核或生成建议。外接结果仍受正式价格
防线约束：公司正式价必须引用已发布 `company_price_id` 且单价一致；AI 估价只能作为待确认参考，
不能直接进入正式总价。

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
