# 报价 Agent 新建与改写

## 目录

1. 选择操作
2. Agent 必需格式
3. 角色边界与 Skill 绑定
4. 拆分与合并
5. 验收清单
6. 正确与错误示范

## 1. 选择操作

根据用户选择执行一种模式：

- `REFACTOR_AGENT`：保留原角色与可验证行为，修正 ID、格式、步骤、工艺、证据和输出约束。
- `CREATE_AGENT`：从需求、规则、案例与反例创建新 Agent。
- `SPLIT_AGENT`：当角色、步骤、工艺知识、权限或验收标准明显不同时拆分。
- `MERGE_AGENT`：仅当角色、输入输出、工艺范围、所有者和发布周期一致时合并。
- `SKILL_AGENT_BUNDLE`：同时生成能力契约 Skill 和负责不确定判断的 Agent，并在 `step_agent_routes` 中绑定。

默认生成到新目录，不覆盖原件。改写时记录旧 ID、兼容策略和路由迁移方法。

## 2. Agent 必需格式

报价流程的文件夹 Agent 必须包含：

```text
agent-folder/
├── agent.json
├── AGENT.md
└── references/       # 只有确有需要时建立
```

`agent.json` 至少声明：

```json
{
  "agent_id": "company.milling-time-agent",
  "agent_name_zh": "铣削工时智能体",
  "agent_version": "1.0.0",
  "protocol_version": "1.0",
  "description_zh": "根据铣削证据估算单件工时并列出假设",
  "supported_steps": ["TIME_ESTIMATION"],
  "supported_processes": ["MILL"],
  "instruction_file": "AGENT.md",
  "reference_files": ["references/time-rules.md"]
}
```

`AGENT.md` 使用明确命令式说明：角色目标、允许输入、必须输出、证据优先级、单位规则、不得推断事项、置信度、何时转人工、失败输出。不要放 Key、价格表或机器路径。

## 3. 角色边界与 Skill 绑定

Agent 只负责需要判断的工作。精确解析、公司价格查表、税额合计、文件写入和格式验证保留为规则或 Skill 命令。Skill 通过以下字段绑定：

```json
"step_agent_routes": {"TIME_ESTIMATION": "company.milling-time-agent"}
```

步骤必须同时被 Skill 与 Agent 支持。第 1、2 步只走全局路由；第 6、7、10、11 步可按具体工艺路由。多工艺零件允许同一步调用多个工艺 Agent，输出必须保留工艺代码再合并。

注意：Skill 目录内的 `agents/openai.yaml` 只是 Codex 的显示信息，不是本软件报价流程的外接 Agent，不能载入 Agent 页。

## 4. 拆分与合并

出现任一情况时优先拆分：不同工艺知识、输出结构、权限、副作用、负责人、失败回退或版本周期。只有提示文字相似不是合并依据。

合并前逐项证明角色、步骤、工艺、输入、输出、证据、置信度、人工复核标准和发布治理一致。保留旧 ID 的迁移表；先迁移路由再弃用旧 Agent。

## 5. 验收清单

逐项输出状态与证据：

| 项目 | 验收要求 |
|---|---|
| 格式 | `agent.json`、`AGENT.md`、引用文件均存在且 UTF-8 可读 |
| 身份 | 文件夹、清单、运行输出的 ID 和版本一致 |
| 路由 | 步骤与工艺合法，不依赖尚未产生的类别/工艺 |
| 输入 | 字段、单位、来源证据和前序步骤清楚 |
| 输出 | JSON 字段、置信度、风险和人工复核条件清楚 |
| 边界 | 列出不得推断、不得改价、不得覆盖证据事项 |
| 失败 | 超时、无效 JSON、ID 不一致时可见告警并回退内置规则 |
| 样例 | 正常、相近反例、歧义、缺失输入各至少一个 |
| 绑定 | Skill ID、Agent ID、步骤和工艺相互兼容 |

## 6. 正确与错误示范

正确：铣削与磨削共享相同输入结构，但工时依据和误差阈值不同，因此使用两个工艺 Agent，由一个加工工时 Skill 分工艺绑定。

错误：创建一个“万能报价 Agent”同时理解备注、查正式价格、改 Excel、审核并发布。它混合了不同权限、证据和失败边界，应拆成 Skill、确定性命令与少量专业 Agent。

错误：只有 `agents/openai.yaml` 就声称已生成外接 Agent。该文件只用于 Skill 界面展示，外接 Agent 仍缺 `agent.json` 和 `AGENT.md`。
