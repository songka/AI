# OpenCode 本地会话格式研究

研究基于 2026-08-13 只读克隆的 OpenCode 官方仓库 `anomalyco/opencode`。本机没有 OpenCode 用户数据，因此测试全部使用合成、脱敏 fixture。

## 官方当前格式

官方源码确认当前主存储为 SQLite：

- 数据库路径由 `packages/core/src/database/database.ts` 决定；稳定渠道默认是 `Global.Path.data/opencode.db`。
- `session`、`message`、`part` 表定义在 `packages/core/src/session/sql.ts`。
- message 和 part 的 provider-specific 内容保存在 `data` JSON 列。
- OpenCode 启动时会应用数据库 migration，并使用 WAL。

应用不直接打开或复制活动 SQLite 数据库。优先调用 OpenCode 自己的只读接口：

```text
opencode session list --format json
opencode export <sessionID>
```

官方 CLI 负责数据库位置、渠道和 migration 差异，应用只解析 export 的 `{ info, messages: [{ info, parts }] }` JSON。命令不通过 shell 拼接，session ID 作为独立参数传递；输出有大小上限，缓存只写入程序自有目录。

## 官方旧版 JSON storage

官方 `packages/opencode/src/storage/storage.ts` 仍记录了旧格式和迁移逻辑：

```text
storage/session/<projectID>/<sessionID>.json
storage/message/<sessionID>/<messageID>.json
storage/part/<messageID>/<partID>.json
```

适配器会只读组合这三层 JSON，并支持 text、reasoning、tool call/result、patch、file、subtask 及 metadata。未知 part 原样进入 USF 的 `unsupported_records`，不会猜测或丢弃。

## 安全边界

- 不直接写入或迁移 `opencode.db`。
- 不执行原生会话导入。
- `.ai-session` 中保存完整 OpenCode export JSON（未脱敏）；普通 JSON/Markdown/HTML 导出可启用隐私模式。
- 未知 schema 或 CLI 失败会明确报告；若发现官方旧 JSON storage，则只读回退。

官方源码参考：

- <https://github.com/anomalyco/opencode/blob/dev/packages/core/src/database/database.ts>
- <https://github.com/anomalyco/opencode/blob/dev/packages/core/src/session/sql.ts>
- <https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/cli/cmd/export.ts>
- <https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/storage/storage.ts>
