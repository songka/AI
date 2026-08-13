# AI Coding Session Manager 任务交接书

文档版本：V1.0  
交接日期：2026-08-13  
项目目录：`D:\codex\AI 编程助手会话迁移与归档工具`  
目标仓库：`https://github.com/songka/AI/tree/main/AI-Coding-Session-Manager`

## 1. 交接结论

项目已形成可运行的 Windows WPF 桌面程序，具备 Codex、Claude Code、OpenCode 和 Claude Desktop 数据导入/浏览基础能力，并包含统一会话格式、隐私导出、会话归档、项目备份恢复、安全扫描及迁移上下文导出。

当前本地最新版已经完成 OpenCode 当前版 SQLite 数据库的严格只读支持，并针对 Claude Desktop 无稳定本地会话接口的情况增加了明确提示。全量测试 71 个全部通过，最新版 EXE 已完成启动与响应性冒烟验证。

项目尚未完成最终 GitHub 发布：远端目前仅有占位 README；本地克隆中存在完整项目提交 `9a102a7`，但因 GitHub 443 网络超时未推送。该提交还早于本轮 OpenCode SQLite 与 UI 提示修复，因此接手后必须先同步本地最新源码到上传克隆，再重新提交和推送。

## 2. 当前交付物

| 交付物 | 位置 | 状态 |
|---|---|---|
| 最新源码 | 项目根目录下 `src/`、`tests/`、`docs/` | 可编译、已测试 |
| 解决方案 | `AICodingSessionManager.sln` | 13 个源码项目、6 个测试项目 |
| 最新自包含 EXE | `publish-desktop-detection-fixed/AICodingSessionManager.exe` | 已冒烟验证 |
| EXE SHA-256 | `9514D873E35882FF18EE92E43090764F6418C4BF03FDEC7660DB19F51CD9F426` | 已校验 |
| 脱敏开发对话 | `conversation-archive/` | Markdown 与 ZIP，排除内部推理和工具输出 |
| GitHub 上传克隆 | `.github-upload/` | `main` 比远端领先 1 个提交 |
| 待推送完整项目提交 | `9a102a7 Add complete AI Coding Session Manager project` | 尚未推送，且不含本轮最新修复 |

## 3. 已完成功能

### 3.1 桌面界面

- WPF 三栏界面：Agent 导航、会话列表、会话预览。
- 会话搜索、项目过滤、日期过滤、刷新、虚拟化列表和取消加载。
- 正文、reasoning、工具调用、工具结果、命令和补丁等内容预览。
- FILLER 压缩显示及原始内容展开。
- 原始数据查看、诊断窗口和状态提示。

### 3.2 Agent 数据支持

- Codex：只读扫描 `%USERPROFILE%\.codex\sessions` JSONL。
- Claude Code：只读扫描 `%USERPROFILE%\.claude\projects` JSONL，容忍损坏记录并保留异常原文。
- OpenCode：优先使用官方 CLI `session list/export`；兼容旧版 JSON storage；最新版已增加 `opencode.db` 的 SQLite 严格只读 fallback，并由 SQLite 引擎一致读取 WAL。
- Claude Desktop：支持显式导入官方数据导出的 ZIP 或 `conversations.json`；不读取登录令牌、Cookies 或不完整 Electron 缓存。

### 3.3 导出、归档与迁移

- USF 1.0 统一会话模型和 JSON Schema。
- JSON、Markdown、单文件离线 HTML 及批量 HTML 索引。
- `.ai-session` 会话归档与 SHA-256 校验。
- 程序自有归档库的安全导入、查看和副本删除。
- 目标 Agent 兼容性报告和 Context Resume 导出。
- `.ai-project` 项目备份、校验、Dry Run、冲突防护、回滚快照和安全恢复。

### 3.4 隐私与安全

- 导出默认启用隐私模式。
- 常见 API Key、Bearer、GitHub Token、私钥、Windows 用户名等脱敏。
- ZIP 路径穿越、重复条目、大小和篡改防护。
- HTML 对不可信内容进行编码，并包含 XSS 回归测试。
- 不修改任何 Codex、Claude Code、OpenCode 或 Claude Desktop 原始会话数据。

## 4. 最新桌面版探测调查

### 4.1 OpenCode Desktop

已确认本机安装 OpenCode Desktop 1.18.18：

- 程序：`%LOCALAPPDATA%\Programs\@opencode-aidesktop\OpenCode.exe`
- 主数据目录：`%USERPROFILE%\.local\share\opencode`
- 数据库：`opencode.db`、`opencode.db-wal`、`opencode.db-shm`
- 当前 Schema 包含 `session`、`message`、`part` 等表。

原适配器漏检原因是只扫描旧版 JSON/JSONL，在找不到独立 CLI 时没有读取 SQLite。现已增加 `Microsoft.Data.Sqlite` 严格只读模式，检查必要表后读取会话，并将 `message.data`、`part.data` 组合为官方 export 结构。

但是本机实测数据库的 `session/message/part` 均为 0 行，`drafts.sqlite` 也为 0 行。截图中的“PPT下载询问”“报告编写”等标题没有出现在本机文件中，可能来自远程状态、其他工作区或尚未落盘的数据。因此修复后若仍显示 0，属于当前本机数据事实，不再是适配器漏扫 SQLite。

### 4.2 Claude Desktop

本机没有发现标准 Claude Desktop 安装、Electron profile、AppX 包或程序自有导入目录。截图客户端底部显示 `Gateway` 和 `deepseek-v4-flash`，不符合标准 Anthropic Claude Desktop 的本地数据形态，可能属于网关/定制客户端或另一台环境。

Claude 会话通常保存在账号云端；Electron 的 Local Storage、IndexedDB、Cookies、Network 和 Cache 不构成稳定、完整且安全的会话接口。当前生产级方案仍是用户在对应环境申请官方数据导出，然后使用“迁移 → 导入 Claude 桌面版数据导出”。UI 已增加明确说明，不再仅显示含糊的 0。

## 5. 架构与关键文件

| 模块 | 职责 | 关键路径 |
|---|---|---|
| Domain | USF 模型、JSONL、安全枚举 | `src/AICodingSessionManager.Domain/` |
| Adapters | 四类 Agent 只读适配 | `src/AICodingSessionManager.Adapters.*/` |
| UI | WPF 界面与流程编排 | `src/AICodingSessionManager.UI/` |
| Export | JSON/Markdown/HTML | `src/AICodingSessionManager.Export/` |
| Backup | `.ai-session` 归档 | `src/AICodingSessionManager.Backup/` |
| Library | 程序自有归档库 | `src/AICodingSessionManager.Library/` |
| Migration | 兼容性与 Context Resume | `src/AICodingSessionManager.Migration/` |
| ProjectArchive | `.ai-project` 备份恢复 | `src/AICodingSessionManager.ProjectArchive/` |
| Security | 隐私脱敏和密钥扫描 | `src/AICodingSessionManager.Security/` |
| Tests | 解析、导出、归档、安全和恢复测试 | `tests/` |

本轮重点修改：

- `src/AICodingSessionManager.Adapters.OpenCode/OpenCodeAdapter.cs`
- `src/AICodingSessionManager.Adapters.OpenCode/AICodingSessionManager.Adapters.OpenCode.csproj`
- `src/AICodingSessionManager.UI/MainViewModel.cs`
- `src/AICodingSessionManager.UI/MainWindow.xaml`
- `tests/AICodingSessionManager.ParserTests/ParserTests.cs`

## 6. 构建、测试与发布

环境要求：Windows x64、.NET 8 SDK；`dotnet.exe` 当前位于 `C:\Program Files\dotnet\dotnet.exe`。

```powershell
Set-Location 'D:\codex\AI 编程助手会话迁移与归档工具'

dotnet restore AICodingSessionManager.sln `
  --configfile NuGet.Config `
  --packages .nuget\packages `
  -p:NuGetAudit=false

dotnet test AICodingSessionManager.sln --no-restore -c Release

dotnet restore .\src\AICodingSessionManager.UI\AICodingSessionManager.UI.csproj `
  -r win-x64 --configfile NuGet.Config --packages .nuget\packages `
  -p:NuGetAudit=false

dotnet publish .\src\AICodingSessionManager.UI\AICodingSessionManager.UI.csproj `
  -c Release -r win-x64 --self-contained true --no-restore `
  -p:PublishSingleFile=true `
  -p:IncludeNativeLibrariesForSelfExtract=true `
  -p:DebugType=None `
  -o .\publish-desktop-detection-fixed
```

最近验证结果：

- 全量测试：71 个通过，0 失败，0 跳过。
- 最新 EXE：164,116,862 字节。
- 冒烟验证：进程保持运行、`Responding=True`、主窗口标题正确。

## 7. GitHub 发布状态

目标公开仓库为 `songka/AI`，独立目录为 `AI-Coding-Session-Manager/`。

远端当前只有早期占位 README。`.github-upload` 克隆的本地 `main` 比 `origin/main` 领先一个提交：

```text
9a102a7 Add complete AI Coding Session Manager project
```

连续推送失败原因是命令行访问 `github.com:443` 超时。Edge 已登录 GitHub，但浏览器扩展未开启“允许访问文件 URL”，导致网页文件选择器拒绝自动上传。

接手后的正确发布顺序：

1. 将项目根目录的最新源码重新同步到 `.github-upload/AI-Coding-Session-Manager/`，排除 `bin/obj/.nuget/.research/publish-*` 等目录。
2. 重新运行全量敏感信息扫描和 `dotnet test`。
3. 在 `.github-upload` 创建包含本轮 SQLite/UI 修复的新提交。
4. 优先重试 Git 推送；若仍超时，在 Edge 扩展中开启“允许访问文件 URL”后使用网页上传源码 ZIP。
5. 约 164 MB 原始 EXE 不得直接提交；压缩后作为 GitHub Release 附件发布，并附 SHA-256。
6. 发布后验证仓库目录、源码包、对话归档和 Release 下载链接。

## 8. 已知限制与风险

- OpenCode 桌面首页显示的远程/最近状态不一定已写入本地 SQLite；程序只能归档可验证的本地数据或官方 export。
- OpenCode SQLite Schema 可能继续变化；当前实现会检查关键表，但需要持续补充列级 Schema gate。
- Claude Desktop 没有公开稳定的本地第三方会话 Writer/Reader 合约；官方数据导出仍是唯一生产级入口。
- 不应从 Cookies、Network Cache、Local Storage 或日志中提取认证信息来访问 Claude/OpenCode 服务。
- Codex 与 Claude Code 没有稳定公开的原生会话写回合约；当前只提供安全归档和 Context Resume，不声称原生恢复。
- 当前源文件曾在部分 PowerShell 输出中出现终端编码乱码，但文件本身是 UTF-8；继续编辑时必须保持 UTF-8。
- 工作区不是 Git 仓库；版本控制操作均发生在 `.github-upload` 克隆中，容易出现“本地源码已更新但上传克隆未同步”的版本漂移。

## 9. 接手后优先级

### P0：发布闭环

- 同步最新源码到上传克隆。
- 完成敏感扫描、测试、新提交和 GitHub 推送。
- 发布最新版 EXE Release，并验证下载与 SHA-256。

### P1：桌面数据可观测性

- 在诊断窗口显示 OpenCode 数据库路径、Schema 状态、表行数、CLI/SQLite 数据源选择和扫描错误。
- 在 Agent 导航状态中区分“未安装”“已安装但本地无会话”“需要官方导入”“扫描失败”。
- 为 OpenCode SQLite 增加真实版本 Schema 快照测试，覆盖 WAL、归档会话和 Schema 漂移。

### P2：产品完善

- 为官方 Claude 导出增加导入向导与状态记录。
- 增加应用版本号、About 页面、Release Notes 和自动升级策略。
- 补充许可证、隐私说明和用户操作手册。

## 10. 验收清单

- [ ] `dotnet test AICodingSessionManager.sln --no-restore -c Release` 全部通过。
- [ ] 新版 EXE 可启动、可刷新、界面响应正常。
- [ ] Codex 和 Claude Code 真实会话数量正常。
- [ ] OpenCode 有本地 SQLite 会话时能显示并读取正文；数据库为空时提示准确。
- [ ] Claude Desktop 无导入数据时提示使用官方导出，不读取登录缓存。
- [ ] GitHub 目录包含最新源码、测试、文档和脱敏对话归档。
- [ ] GitHub Release 包含 Windows x64 自包含 ZIP 和 SHA-256。
- [ ] 仓库中不存在真实 Token、私钥、用户级配置、原始会话 JSONL、NuGet 缓存或第三方研究仓库。

## 11. 安全底线

继续遵循：Read First. Backup Before Write. Never Destroy Unknown Data.

任何未来写入 Agent 原生数据的功能，必须同时具备 Schema/版本预检、Dry Run、写前备份、原子事务或临时文件、写后校验和可验证回滚；未完成这些门槛前，不得启用原生写回。
