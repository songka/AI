# 飞书自动签核项目维护规则

本项目的业务代码位于 `deploy/auto-sign/`，项目专用 Skill 位于
`.agents/skills/manage-feishu-signing/`。诊断、修改、测试、打包或部署本项目时，
必须使用该 Skill，并将签核、拒签视为高风险动作。

## 修改前

1. 阅读 `.agents/skills/manage-feishu-signing/SKILL.md`。
2. 修改消息路由、AI、确认、签核或拒签前，阅读
   `references/safety-policy.md`。
3. 修改规则、用户组、内容组或群通知前，阅读
   `references/rule-schema.md`。
4. 修改 CLI、飞书指令、菜单或卡片入口前，阅读
   `references/commands.md`。
5. 保留 `users/`、运行配置、登录凭证和统计数据；不得把它们写入测试、日志或发布包。

## 代码与 Skill 同步矩阵

| 修改范围 | 必须同步检查 |
|---|---|
| `intent_router.py`、AI 路由、确认和动作执行 | `references/safety-policy.md` 与安全回归测试 |
| `rules.py`、`group_store.py`、`notification_policy.py` | `references/rule-schema.md` 与规则回归测试 |
| `qh.py`、`cli.py`、`cli_feishu.py`、飞书菜单和用户指令 | `references/commands.md` 与命令回归测试 |
| 模块职责、统计、OAuth、部署或发布方式 | `SKILL.md`、部署文档与合同测试 |
| 用户可见行为或已报告 Bug | `deploy/auto-sign/tests/test_regressions.py` |
| Skill 结构、触发范围或默认提示 | `SKILL.md`、`agents/openai.yaml` 与 Skill 校验 |

不要求为了形式修改无关 Skill 文件；必须明确判断“已同步”或“无需同步及原因”。

## 完成条件

1. 为行为变化增加或更新回归测试。
2. 运行 `scripts/validate-project.ps1`。
3. 验证失败时不得声称完成、不得打包、不得部署。
4. 只能通过 `build-release.ps1` 生成发布包；该脚本必须先运行统一验证。
5. 默认发布包仅包含运行所需内容；只有明确使用 `-IncludeSkill` 时才将 `.agents/` 放入包内。

## 安全底线

- AI 不得根据自然语言判断直接执行签核、拒签、全签或全拒。
- 模拟、测试、预览和试跑只能进入只读流程。
- 全签、全拒及与匹配规则相反的人工动作必须确认。
- 只有平台重新查询验证成功的动作才能统计或发送成功通知。
- OAuth 统计必须由服务端按当前飞书 `open_id` 隔离。

