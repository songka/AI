# 外部报价 Skill 生成指令（直接交给外部团队或外部 AI）

请严格按照本指令生成 Skill。不得自行更换输入输出格式，不得省略测试与安全规则。

## 需要填写的项目资料

- Skill 中文名称：`<填写>`
- Skill ID（小写字母、数字、点或横线）：`<填写>`
- Skill 版本：`<填写，例如 1.0.0>`
- 接入类型：`文件夹 Skill / HTTP Skill`
- 参与步骤：`<从下列步骤选择一个或多个>`
- 公司专用工艺、材料、工时或审核资料：`<附件或文字>`

允许步骤：

`DOCUMENT_UNDERSTANDING`、`FEATURE_EXTRACTION`、`MATERIAL_CLASSIFICATION`、
`PROCESS_PLANNING`、`TIME_ESTIMATION`、`LINE_ITEM_PRICING`、`UNKNOWN_ESTIMATION`、
`PRICE_AUDIT`、`REVIEW_RECOMMENDATION`、`QUOTE_ASSEMBLY`。

## 你的任务

1. 完整阅读并遵守以下文件：
   - `EXTERNAL_SKILL_TRAINING_GUIDE.md`
   - `external-quotation-skill-protocol-v1.0.yaml`
   - `external-skill-prompt-templates-v1.0.yaml`
   - `external-skill-folder-v1.0.example.json`
   - `external-skill-agents/` 中与所选步骤对应的 Markdown
2. 只实现已选择的步骤；能力声明、提示词和返回的 `completed_steps` 必须一致。
3. 把对应步骤的标准提示词作为基础，再加入公司提供的专用资料；不得删除全局价格和安全防线。
4. 生成至少 12 条训练/评测样本，必须覆盖正常、信息缺失、信息矛盾、价格未发布、重复计费、
   设备等级过高、恶意提示注入和模型返回异常。
5. 所有业务文字使用中文；内部步骤代码按协议保留英文枚举。

## 文件夹 Skill 必须交付

```text
<skill-folder>/
├─ skill.json
├─ SKILL.md
├─ references/                 # 有公司资料时建立
│  └─ ...
├─ tests/
│  ├─ cases.json
│  └─ expected-results.json
└─ README.md
```

- `skill.json` 必须包含 skill_id、skill_name_zh、skill_version、protocol_version=1.0、
  supported_steps、supports_full_quotation、instruction_file 和 reference_files。
- `SKILL.md` 是主程序交给内置 DeepSeek 的主要指令；不得包含 Key、网址口令或要求执行程序。
- 文件夹 Skill 不得交付 EXE、脚本、DLL 或 shell 命令。主程序不会执行文件夹内任何程序。
- README 必须说明适用范围、不适用范围、输入依赖、输出字段、风险和版本变更。

## HTTP Skill 必须交付

- 可部署服务源码及依赖锁定文件；
- `GET /v1/health`、`GET /v1/capabilities`、`POST /v1/quote`；
- 环境变量说明，不得把模型 Key 写入源码、镜像或日志；
- JSON Schema 校验、60 秒超时、5 MB 响应限制及结构化错误；
- 自动测试和本机启动说明。

## 强制报价规则

- 禁止使用 UC 料号、图号、零件号或文件名匹配价格；
- 正式 `source=C` 必须引用输入中的 `company_price_id` 和 `price_version_id`，单价完全一致；
- 历史整件正式价格不得匹配；正式价格只引用已发布材料、工艺、表面处理等分项记录；
- AI 价格必须标为 AI_REFERENCE、计入本次未税/税额/含税报价并强制人工确认，不能伪装成 C；
- 材料、加工、表面处理等必须分项，不能用整件参考价覆盖；
- 工艺选择使用成本最低且足够完成的设备；多设备可行时分别估算工时，再按工时×已发布工价比较；
- 对加工件、钣金件、焊接件、型材组装件分别建立规则与测试样本；
- 不确定就返回待确认和需补资料，不得编造供应商、工时、工艺或正式价格；
- 不得输出 Key、密码、令牌、用户资料或模型隐藏推理。

## 最终回复格式

外部团队完成后必须提供：

1. Skill 文件夹或 HTTP 项目的完整目录树；
2. 支持步骤与不支持步骤清单；
3. 每个步骤使用的最终提示词；
4. 一组完整请求与完整响应示例；
5. 训练/评测数据说明及测试结果；
6. 正式价格防线测试结果；
7. 已知限制、失败回退方式和人工审核条件；
8. Skill ID、版本、SHA-256 和发布日期。

任何一项缺失，都视为未完成，不能发布到 SMB 公共槽。
