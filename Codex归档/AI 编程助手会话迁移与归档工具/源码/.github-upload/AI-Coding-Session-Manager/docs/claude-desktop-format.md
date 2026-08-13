# Claude Desktop 对话导入

Claude Desktop 对话主要与 Claude 账户同步。Electron 的 LevelDB、Cache 和 Local Storage 属于实现缓存，可能包含登录状态，既不完整也不是官方稳定的对话导出合约。因此应用不会扫描这些文件或读取令牌。

支持的可靠路径是 Claude 官方数据导出中的 `conversations.json`：

1. 在 Claude 账户设置中请求数据导出；
2. 下载导出的 ZIP；
3. 在本程序选择“迁移 → 导入 Claude 桌面版数据导出”；
4. 程序验证 ZIP 中唯一的 `conversations.json`，把每个会话原子写入 `%LOCALAPPDATA%\AICodingSessionManager\imports\claude-desktop`；
5. 左侧“Claude 桌面版”来源显示程序自有只读副本。

解析器支持 `human/user`、`assistant`、`system`，纯 `text`，以及数组内容中的 text、thinking、tool_use、tool_result。未知字段保留为 metadata，未知内容块进入 `unsupported_records`。附件仅保存导出中提供的元数据；程序不会自动上传或执行任何内容。

安全限制：ZIP/JSON 大小上限、唯一 `conversations.json`、JSON 深度限制、会话结构验证、临时文件加原子替换。不会写入 Claude Desktop 数据目录。
