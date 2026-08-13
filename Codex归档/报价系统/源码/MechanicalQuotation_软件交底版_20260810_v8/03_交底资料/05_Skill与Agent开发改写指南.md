# Skill 与 Agent 开发改写指南

## 工具定位

`external-quotation-skill-refactor` 用于把别人编写的 Skill/Agent 改成符合本软件协议的资源，也可根据需求新建、拆分或合并。工具先只读盘点，再让用户选择方式；默认生成到新目录，不覆盖原件。

## 可选方式

1. 改写现有 Skill：保留可验证能力，修正协议、ID、输出、路由和回退。
2. 新建 Skill：从业务规则、样例、脚本、Excel 或接口生成。
3. 拆分 Skill：按不同步骤、工艺、权限、副作用或发布周期拆分。
4. 合并 Skill：仅合并契约、责任和治理真正一致的资源。
5. 改写/新建/拆分/合并 Agent。
6. 生成 Skill+Agent 组合并建立绑定。

## 格式区别

- 软件 Skill：`skill.json` + `SKILL.md`，可含 `references/`、`scripts/`、`assets/` 和命令声明。
- 软件 Agent：`agent.json` + `AGENT.md`，可含 `references/`；负责需要判断的角色。
- Skill 内 `agents/openai.yaml`：只是 Codex 界面显示信息，不是本软件可载入的报价 Agent。

Python、EXE、CLI、BAT/CMD/PS1 和 Excel 文件仅放入目录不代表允许执行，必须在 `skill.json.commands` 声明任务类型、参数数组、运行要求和超时。Excel 读取、写入、修改、导出分别声明；修改默认另存新文件。缺运行环境时程序应提示用户并回退内置功能。

## 必须报告满足哪些项目

工具输出必须逐项给出 `已满足`、`部分满足`、`未满足` 或 `待确认`：格式、ID/版本、11 步映射、类别、具体工艺、输入、输出、证据、Agent 角色、Skill-Agent 绑定、运行环境、命令、超时、失败回退、正常/错误/歧义/缺失输入样例、授权来源、载入发布方式。

详细向导、正确示例和错误示范位于 `04_Skill与Agent工具/external-quotation-skill-refactor/references`。
