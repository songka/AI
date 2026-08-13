# 外部报价 Skill 训练与对接规范

版本：1.0（2026-08-06）

## 1. 交付目标

外部团队应训练或编写一个符合“外接报价 Skill 协议 1.0”的机械加工报价 Agent。Skill 可以：

1. 作为 HTTP/HTTPS 服务，由主程序调用 `/v1/capabilities` 与 `/v1/quote`；
2. 作为本地或 SMB 文件夹中的提示词 Skill，由主程序读取 `SKILL.md` 和参考文档，再调用主程序
   已配置的 DeepSeek；文件夹 Skill 不包含、不启动任何 EXE、脚本或 shell 命令。

机器可读接口以 `external-quotation-skill-protocol-v1.0.yaml` 为唯一标准；本文件用于训练、提示词
设计、联调与验收。

## 2. 不可违反的报价边界

- 禁止使用 UC 料号、图号、零件号或文件名匹配价格；这些字段只能追踪，不能决定金额。
- 正式公司价格 `source=C` 必须引用请求价格表中的 `company_price_id` 和 `price_version_id`，
  返回单价必须与该记录完全一致。
- 历史整件正式价格不得匹配；公司核准价格只从已发布材料、工艺、表面处理等分项记录解析。
- AI 推测金额必须使用 `source=AI`、`price_status=AI_REFERENCE`，设置
  `requires_review=true`、`included_in_quotation=true`。它计入本次报价小计、税额和含税总价，
  但不能伪装为公司核准价格。
- 材料、加工、表面处理、外购、装配和其他费用必须分项展示；不得用一个“整件模型价”覆盖分项。
- 所有业务文字、证据、错误与建议使用中文；信息不足时明确返回待确认，不得编造供应商或来源。
- Skill 只能执行 `selected_steps`；失败时返回协议错误，主系统负责回退内置流程。
- 不得读取、输出或保存 DeepSeek Key、登录密码、用户库口令、访问令牌或模型隐藏推理。

## 3. 运行时 Agent 与标准提示词

标准提示词的机器可复制版本位于 `external-skill-prompt-templates-v1.0.yaml`。外部团队应根据声明的
`supported_steps` 使用相应提示词，不应把没有声明的步骤混入结果。
`external-skill-agents/` 下另有 10 份逐步骤 Markdown 对接说明；开发某一步时必须同时阅读对应文件。

| 步骤代码 | Agent | 训练重点 | 禁止行为 |
|---|---|---|---|
| `DOCUMENT_UNDERSTANDING` | 图纸与备注理解 | 材料、规格、公差、热处理、表面处理、特殊要求 | 不计价、不猜测缺失要求 |
| `FEATURE_EXTRACTION` | 特征提取与零件分类 | 加工/钣金/焊接/型材组装分类，以及孔、螺纹、槽、折弯、焊缝、装配、尺寸 | 不按文件名补特征或类别 |
| `MATERIAL_CLASSIFICATION` | 材料判断 | 标准牌号、形态、厚度、毛坯 | 不按料号推断材料 |
| `PROCESS_PLANNING` | 工艺路线 | 可制造候选、工序顺序、候选工时×工价 | 不默认全部使用 CNC |
| `TIME_ESTIMATION` | 工时估算 | 准备、装夹、加工、检验工时及依据 | 不编造小时费率 |
| `LINE_ITEM_PRICING` | 分项计价 | 引用正式价格、计算数量与金额 | 不伪造 company_price_id |
| `UNKNOWN_ESTIMATION` | 待确认估价 | U 项估价、计入报价、假设、可信度 | 不伪装成公司核准价 |
| `PRICE_AUDIT` | 价格审核 | 漏项、重复、设备过度、单价引用、异常值 | 不直接篡改正式价格 |
| `REVIEW_RECOMMENDATION` | 人工审核建议 | 风险排序、阻断项、需补资料 | 不代替人工批准 |
| `QUOTE_ASSEMBLY` | 报价汇总 | 正式/参考金额分离、税额、来源追踪 | 不用整件价覆盖细项 |

### 3.1 图纸备注输入规则

备注理解 Agent 必须优先读取 `drawing_package.extracted_texts`。每条文字都带
`source_file_id/page/entity_id/confidence`；`built_in_context.note_inputs` 另带
`source_file_name/source_kind`，用于标识原生 DWG/DXF/SolidWorks 图纸文字。

处理优先级：原生图纸明确标注 > 内置摘要或模型推断。
必须保留原文和来源，不得先改写后当成原始证据。OCR 低可信文字不能覆盖原生标注；不同来源冲突时
同时列出冲突内容、来源和可信度，并设置人工审核。标题栏、材料栏、技术要求、局部引线备注要分别
理解；“未注公差”“其余倒角”“去毛刺”等全局备注不得错误绑定到单一特征。

### 3.2 四类零件路由与十步流程

请求中的 `built_in_context.part_category` 为 `MACHINING`、`SHEET_METAL`、`WELDMENT` 或
`FRAME_ASSEMBLY`。每类都经过相同 10 步，但可使用不同 Skill 和规则；训练/评测必须覆盖四类。
外部 Skill 不得自行改写类别来绕过管理员路由。

## 4. 文件夹 Skill 交付结构

```text
company-process-agent/
├─ skill.json
├─ SKILL.md
├─ 公司工艺规则.md          # 可选
└─ 审核注意事项.yaml        # 可选
```

`skill.json` 示例：

```json
{
  "skill_id": "company.process.agent",
  "skill_name_zh": "公司工艺路线 Agent",
  "skill_version": "1.0.0",
  "protocol_version": "1.0",
  "supported_steps": ["PROCESS_PLANNING", "TIME_ESTIMATION"],
  "supports_full_quotation": false,
  "instruction_file": "SKILL.md",
  "reference_files": ["公司工艺规则.md", "审核注意事项.yaml"]
}
```

文件要求：UTF-8；只允许 `.md/.txt/.json/.yaml/.yml`；指令与参考文档合计不超过 128 KB；相对路径
不得包含 `..` 或跳出 Skill 文件夹。主程序把 Skill 文档作为受控系统指令，把用户图纸资料作为
DeepSeek 用户输入。

## 5. 可直接复制的 SKILL.md 骨架

```markdown
# 公司工艺路线报价 Skill

## 角色
你是公司机械加工工艺路线 Agent，只执行请求 selected_steps 中本 Skill 声明支持的步骤。

## 任务
读取 drawing_package.extracted_texts、built_in_context.manufacturing_features、
built_in_context.existing_quote_items 和 published_pricebook。
选择成本最低且足以完成的设备与工序。普通平面、直边、槽和常规孔优先普通铣床；只有复杂曲面、
多轴、高重复定位精度或图纸明确要求时使用 CNC。同一去除加工不得同时使用铣床与 CNC 重复计费。
多种设备可行时分别估算准备、装夹、加工和检验工时，使用输入的已发布小时工价计算总成本后选择。

## 输出
严格返回外接报价 Skill 协议 1.0 JSON。completed_steps 只能包含获授权步骤。
PROCESS_PLANNING 的 step_results 必须含 process_route、equipment_choices、
rejected_expensive_options、evidence、confidence。
TIME_ESTIMATION 必须含 time_items、assumptions、calculation_evidence、review_required、confidence。

## 价格边界
禁止按 UC/图号/文件名查价。正式 C 价必须引用请求中的 company_price_id 且单价一致。
AI 推测价必须标为 AI_REFERENCE、计入本次报价并进入人工审核，不得伪装成公司核准价。
信息不足时返回待确认，不得编造。
```

## 6. HTTP Skill 能力接口

`GET /v1/capabilities` 应返回：

```json
{
  "skill_id": "company.process.agent",
  "skill_name_zh": "公司工艺路线 Agent",
  "skill_version": "1.0.0",
  "protocol_version": "1.0",
  "supported_steps": ["PROCESS_PLANNING", "TIME_ESTIMATION"],
  "supports_full_quotation": false
}
```

`POST /v1/quote` 接收完整 `QuotationSkillRequest`，响应必须为 `QuotationSkillResponse`。HTTP Skill
自行调用模型；文件夹 Skill 则由主程序调用 DeepSeek。两者的业务输入输出完全相同。

## 7. 训练输入样本格式

每条监督训练或评测样本建议包含：

```json
{
  "input": {
    "selected_steps": ["PROCESS_PLANNING"],
    "drawing_texts": ["材料：S50C", "4-M8", "表面镀铬"],
    "manufacturing_features": {"holes": 4, "threads": 4, "bounding_box": "120x80x15"},
    "existing_quote_items": [],
    "published_pricebook": {"price_version_id": "示例版本", "records": []}
  },
  "expected": {
    "completed_steps": ["PROCESS_PLANNING"],
    "step_results": {
      "PROCESS_PLANNING": {
        "process_route": ["下料", "普通铣床", "钻孔", "攻牙", "检验"],
        "equipment_choices": [{"equipment": "铣床", "reason": "常规平面、孔和螺纹可完成"}],
        "rejected_expensive_options": [{"equipment": "CNC", "reason": "无复杂曲面或多轴证据"}],
        "evidence": ["4-M8", "120x80x15"],
        "confidence": 0.85
      }
    }
  }
}
```

训练集必须同时包含：正常件、缺失材料、矛盾备注、普通铣床足够、必须 CNC、车削件、钣金件、
焊接件、正式价格命中、无正式价格、重复费用、过期价格和恶意提示注入样本。

## 8. 响应最小结构

```json
{
  "request_id": "必须与请求一致",
  "protocol_version": "1.0",
  "skill_id": "必须与能力声明一致",
  "completed_steps": ["PROCESS_PLANNING"],
  "step_results": {"PROCESS_PLANNING": {}},
  "quotation": null,
  "review": {
    "requires_human_review": true,
    "risk_level": "MEDIUM",
    "issues_zh": [],
    "required_actions_zh": []
  },
  "execution_trace": {
    "started_at": "2026-08-06T00:00:00Z",
    "completed_at": "2026-08-06T00:00:01Z",
    "duration_ms": 1000,
    "input_sha256": "64位十六进制SHA256",
    "pricebook_sha256": "请求中的正式价格表哈希",
    "used_steps": ["PROCESS_PLANNING"],
    "model_or_engine_versions": {"model": "实际模型名称"}
  }
}
```

## 9. 外部团队验收清单

- 能力接口、Skill ID、协议版本和支持步骤一致；
- 未选步骤不会出现在 `completed_steps`；
- 相同请求 ID 原样返回；
- 所有正式 C 价都能在输入价格表找到，单价完全一致；
- U 不进入合计；AI_REFERENCE 计入本次报价并醒目标识待人工确认；
- 普通铣床足够时不会无依据选择 CNC；
- 多个设备可行时按各自工时×已发布工价选择最低成本可制造路线；
- 加工件、钣金件、焊接件、型材组装件样本均符合各自规则；
- 调试模式能看到十步实际输入、输出和自动验收，且不泄露 Key；
- 缺少信息时返回待确认和明确问题，不编造；
- 所有展示文字为中文，内部代码只出现在协议字段；
- 失败返回结构化错误，主程序能安全回退；
- 不记录用户图纸正文、Key、令牌或隐藏推理；
- 在 60 秒内返回，响应不超过 5 MB；
- 通过主系统提供的协议、价格防线和回归测试后才允许发布到 SMB 公共槽。

## 10. 对接文件

- `external-quotation-skill-protocol-v1.0.yaml`：机器可读输入输出协议；
- `external-skill-prompt-templates-v1.0.yaml`：10 个 Agent 标准提示词；
- `external-skill-folder-v1.0.example.json`：文件夹 Skill 清单范例；
- `EXTERNAL_SKILL_INTEGRATION.md`：管理员安装和路由说明。
- `external-skill-agents/*.md`：每个步骤独立的输入、提示词、输出与验收说明。
