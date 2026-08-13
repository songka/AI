# 多 Agent 审核评估流程

本项目使用多个独立 Codex agent 对 WPF 重写进行分轮审核：

- `01-architect.md` — 架构与正确性审核员
- `02-security.md` — 安全审核员
- `03-wpf-ux.md` — WPF 界面与 UX 审核员
- `04-qa.md` — 质量与构建审核员

## 运行一轮审核

```powershell
powershell -ExecutionPolicy Bypass -File review\run-round.ps1 -Round 1
```

每轮输出写入 `review/round-XX/<agent>.md`。主 agent 根据发现的问题修复代码后，
进入下一轮（共 5 轮），最后执行 Release 发布打包。
