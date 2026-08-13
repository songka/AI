# 兼容性矩阵

| 能力 | OpenCode / Desktop | Codex | Claude Code | Claude Desktop | 程序归档库 |
|---|---:|---:|---:|---:|---:|
| 检测与列出会话 | 是 | 是 | 是 | 官方导入后 | 是 |
| 读取真实消息正文 | 官方 CLI export / 旧 JSON storage | JSONL | JSONL（容错） | 官方 `conversations.json` | USF 1.0 |
| reasoning / tool / patch | 是 | 是 | 是 | 是 |
| JSON / Markdown / 离线 HTML | 是 | 是 | 是 | 是 |
| `.ai-session` 完整归档 | 是 | 是 | 是 | 是 | 已是归档 |
| Context Resume | 是 | 是 | 是 | 是 |
| 原生导入 / Native Resume | 未验证、禁用 | 无公开 Writer 合约 | 无公开 Writer 合约 | 无本地 Writer 合约 | 不适用 |
| 修改 Agent 原始数据 | 否 | 否 | 否 | 否 | 否 |

Archive、Context Resume、Native Resume 是三个独立指标。`Archive Supported` 只说明可以无损保留和离线查看，不能推导出目标 Agent 可原生继续会话。

## 当前策略

- Codex：官方公开 `codex resume` 仅恢复 Codex 自己保存的会话，没有第三方 JSONL Writer 合约。
- Claude Code：没有经版本验证的第三方本地会话写入合约。
- OpenCode：读取使用官方 CLI export，旧版本回退到官方 JSON storage；数据库写入与 native import 在真实版本、备份、验证、回滚全部完成前保持禁用。
- 跨 Agent 延续使用脱敏 Context Resume；历史命令、工具调用和 patch 明确标为 inert，不自动执行。
