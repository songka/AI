# AI Coding Session Manager

Windows 桌面端 AI 编程助手会话浏览、隐私导出、归档和安全项目迁移工具。程序只读访问 Codex、Claude Code 和 OpenCode 原始数据；所有可写操作仅面向程序自有归档库或用户明确选择的普通项目目录。

## 已实现

- WPF 三栏中文 UI，搜索、Agent/项目/日期筛选、惰性预览与虚拟化；
- Codex、Claude Code JSONL 的正文、reasoning、工具、命令、patch/diff 与未知记录保留；
- OpenCode CLI 与 OpenCode Desktop 正式版/Beta/Dev：官方 `session list/export` 只读支持，以及官方旧版 `storage/session|message|part` JSON 回退；
- Claude Desktop：导入官方数据导出 ZIP 或 `conversations.json`，保存在程序自有只读目录后显示完整消息、附件元数据和可识别的工具块；
- FILLER 压缩显示和一键展开未修改的原始正文；
- USF 1.0、JSON、Markdown、可搜索的离线单文件 HTML、批量 HTML 索引；
- 默认开启的隐私模式：隐藏常见 API Key、Authorization、私钥和 Windows 用户名；
- `.ai-session` 原子归档、SHA-256 清单、ZIP 路径/重复项/大小/篡改防护；
- 程序自有离线归档库，可安全导入、查看和仅删除程序副本；
- 目标 Agent 兼容性报告与安全 Context Resume（历史命令、工具调用、patch 标为不可重放）；
- `.ai-project` 项目备份与恢复：默认排除 `.git/node_modules/bin/obj`，先 Dry Run，冲突拒绝写入，带 rollback snapshot；
- 隐私化诊断与日志；
- Windows x64 self-contained 单文件 EXE，目标电脑无需安装 .NET Runtime。

## 重要边界

`.ai-session` 和 `.ai-project` 为完整归档，会保留未脱敏原始内容，UI 会在写出前提示。普通 JSON/Markdown/HTML 与 Context Resume 才应用“隐私模式”。

Codex 与 Claude Code 没有公开、稳定的第三方会话 Writer 合约；因此程序不会伪造或写入它们的私有会话库。OpenCode 虽有官方 import 实现，但跨版本原生恢复仍未在真实安装上完成可回滚验证。当前 Native Resume 明确显示为未验证，安全替代是 Context Resume。

Claude Desktop 的对话与 Claude 账户同步，本地 Electron 缓存不是稳定的官方会话接口。请在 Claude 中申请官方数据导出，然后使用“迁移 → 导入 Claude 桌面版数据导出”。程序不会读取 Claude 登录令牌或直接改动桌面版缓存。

## 构建、测试与发布

```powershell
dotnet restore AICodingSessionManager.sln --configfile NuGet.Config --packages .nuget\packages -p:NuGetAudit=false
dotnet test AICodingSessionManager.sln --no-restore -c Release

dotnet restore .\src\AICodingSessionManager.UI\AICodingSessionManager.UI.csproj -r win-x64 --configfile NuGet.Config --packages .nuget\packages -p:NuGetAudit=false
dotnet publish .\src\AICodingSessionManager.UI\AICodingSessionManager.UI.csproj -c Release -r win-x64 --self-contained true --no-restore -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:DebugType=None -o .\publish-full-safe
```

格式和安全设计见 `docs/`。
