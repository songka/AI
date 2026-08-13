# 报价 Skill / Agent 三层路由 V2

## 版本边界

- 路由配置：`schema_version = 2.0`。
- 外接调用协议：当前仍为 `protocol_version = 1.0`，以兼容原有 HTTP 和文件夹 Skill。
- V1 配置仍可读取；保存后升级为 V2。此版本只修改源码和文档，不执行打包。

## Skill、Agent 与内部规则的职责

| 对象 | 职责 | 是否独立路由 | 内容是否可查看 |
|---|---|---:|---:|
| Skill | 定义某项报价能力、输入输出、业务规则、可执行命令与回退 | 是 | 文件夹 Skill 可查看完整指令和 references；HTTP 只能查看公开清单 |
| Agent | 承担需要推理的角色，可被 Skill 指定，也可直接作为步骤执行资源 | 是 | 内置 Agent 查看公开执行契约；文件夹 Agent 查看 AGENT.md/references；HTTP 只能看公开清单 |
| 内部规则 | 特征、材料、计价、汇总、合理性约束和故障回退 | 由“内置系统（自动）”选择 | 调试页查看该次实际输入输出 |

一个 Skill 可以在 `step_agent_routes` 中为不同步骤指定不同 Agent。Agent 不能自行接管未声明的步骤，Skill 也不能通过 Agent 越过自身的 `supported_steps`。

## 三层路由

```text
第 1 层：报价步骤
  1 图纸理解 → 2 零件分类 → 3..11 后续步骤
                      ↓
第 2 层：零件类别
  加工件 / 钣金件 / 焊接件 / 型材组装件
                      ↓
第 3 层：具体工艺
  CNC、车、铣、磨、钳工、放电、快丝、慢丝、激光、折弯、焊接、表面处理
```

约束：

1. 第 1、2 步发生在可靠分类之前，只允许全局路由。
2. 第 3～11 步可以按零件类别覆盖全局路由。
3. 只有第6步 `TIME_ESTIMATION`、第7步 `LINE_ITEM_PRICING`、第10步 `PRICE_AUDIT`、第11步 `REVIEW_RECOMMENDATION` 进一步按具体工艺路由。
4. `PROCESS_PLANNING` 负责产出工艺代码，因此不能先按尚未产生的工艺代码路由。
5. “全局默认”页面可以直接设置各工艺的公共路由；具体类别可以只覆盖某个工艺/步骤。没有具体工艺配置时继承类别或全局路由，最终回退内置系统。
6. 同一零件同时包含铣、磨、钳工等工艺时，路由器分别调用对应的多个 Skill/Agent；不同工艺结果保留各自的 `selected_processes` 和调试轨迹，再按步骤合并。

## 现有 Skill 处理建议

现有 `part.cost.estimator 3.0.0` 同时覆盖备注、工艺、计价、审核等多个失败边界，V2 不直接删除，按兼容资源保留，但不建议继续扩大。迁移时按证据选择：

| 现有能力 | V2 处理 | 原因 |
|---|---|---|
| 图纸备注理解 | 共用全局 Agent / Skill | 与零件类别无关，避免重复消耗 token |
| 零件类别分类 | 独立全局 Agent / Skill | 是后续类别路由的前置条件 |
| 特征与材料规则 | 优先共用内部规则 | 确定性高、成本低、容易审计 |
| 工艺规划 | 按零件类别拆分 Skill，可共用规划 Agent | 类别差异大，但输出协议一致 |
| 工时与分项计价 | 按具体工艺拆分或覆盖 | 车、铣、磨、焊等工时模型不同 |
| 价格审核 | 共用审核 Skill，必要时按工艺覆盖 | 通用金额/单位检查可共享，专业工艺异常可专审 |
| Excel 读写修改/导出 | 独立命令型 Skill | 有文件副作用、运行环境和失败边界不同 |

## GitHub 参考与版权边界

本设计只借鉴公开架构思想，没有复制第三方业务提示词、示例代码或报价规则：

| 来源 | 许可证状态 | 仅借鉴的思想 |
|---|---|---|
| [OpenAI skills](https://github.com/openai/skills) / [plugins](https://github.com/openai/plugins) | `skills` 仓库说明每个 Skill 许可证需在其目录单独确认 | `SKILL.md` 作为简短入口，脚本、参考资料和资产按需加载；不复制任何单个 Skill 内容 |
| [Microsoft AutoGen](https://github.com/microsoft/autogen) | 文档 CC BY 4.0、代码 MIT；仓库已进入维护模式 | Agent 职责分层、扩展与运行时分离；未引入依赖或代码 |
| [LangGraph Supervisor](https://github.com/langchain-ai/langgraph-supervisor-py) | [MIT](https://github.com/langchain-ai/langgraph-supervisor-py/blob/main/LICENSE) | 中央路由器协调专业 Agent、保留交接信息和可控上下文；未复制实现 |

引入任何 GitHub 文件前必须记录：仓库、具体路径、版本/提交、许可证、作者署名要求、修改说明和用途。许可证不明确或与本项目专有发布冲突时，只允许重新独立实现通用思想，不复制表达或代码。

## 管理员操作

1. 在“外接报价 Skill 设置”检测 Skill 或外挂智能体。
2. 双击资源查看能力和内容。
3. 选择全局或零件类别，再选择步骤执行 Skill 和 Agent。上栏只选 Skill/内置系统，下栏只选 Agent。
4. 在全局默认或具体类别中选择具体工艺，配置第6、7、10、11步并点击“应用具体工艺路由”。
5. 保存后，文件夹 Skill 发布到公共槽 `external-skills`，文件夹 Agent 发布到 `external-agents`；客户端同步后使用同一版本。

资源目录使用四个切换页分别展示“内置 Skill、外接 Skill、内置智能体、外接智能体”。双击文件夹资源可查看能力、指令正文和完整文件结构；Python、EXE、CLI、批处理、Excel 等非文本文件只显示相对路径、类型和大小，是否执行仍严格以 `skill.json.commands` 为准。

## 可直接载入的示例组

- `samples/external-skills-v2`：按 11 个报价步骤拆分的 Skill，每个步骤一个目录。
- `samples/external-process-skills-v2`：按 12 种具体工艺拆分的 Skill；每个工艺声明支持第 6、7、10、11 步。

在管理员页面点击“载入一组 Skill”，选择上述任一总目录，程序会检测其一级子目录中的所有 `skill.json`，一次登记整组。载入后仍需在步骤、类别或具体工艺路由中选择，并保存发布；示例规则只作为结构和协议起点，正式使用前应替换为公司核准的工时、计价和审核规则。

公共槽只保存只读版本资产。每台电脑的报价任务、缓存、日志、会话和临时文件继续使用各自本地用户目录，避免多人相互覆盖。
