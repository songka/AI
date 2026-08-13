# 多 Code 兼容与便携 Skill

## 安装方式

复制整个 `ai-assets-manager` 文件夹，不要只复制 `SKILL.md`。

| 客户端 | 用户级目录 | 项目级目录 |
|---|---|---|
| Codex | `%USERPROFILE%\.codex\skills\ai-assets-manager` | 客户端配置的项目 Skill 目录 |
| Claude Code | `%USERPROFILE%\.claude\skills\ai-assets-manager` | `.claude\skills\ai-assets-manager` |
| Gemini CLI | `%USERPROFILE%\.gemini\skills\ai-assets-manager` 或 `%USERPROFILE%\.agents\skills\ai-assets-manager` | `.gemini\skills\...` 或 `.agents\skills\...` |
| Cursor | `%USERPROFILE%\.cursor\skills\ai-assets-manager` | `.cursor\skills\...` 或 `.agents\skills\...` |

各客户端只负责发现 `SKILL.md`；所有判断和写操作都调用同一份
`scripts/ai_assets_skill.py`，因此角色、登录、安全和版本行为一致。

用户创建或修改 Skill、CLI、Agent 时，智能体运行 `status`。脚本在 SMB 已登录时
自动建立 Git 草稿提交并推送公共槽和备份槽。用户不需要说“备份”，也没有单独的
Hub 备份权限。若 SMB 未登录，脚本只返回独立登录窗口的启动方式并停止。

## 管理 Skill 自更新

1. `self-check` 比较本地版本与 Hub 稳定版。
2. 用户明确同意后才执行 `self-update`。
3. 下载后核对 Hub 中的 SHA-256，并验证 `SKILL.md` 和控制脚本。
4. 当前用户副本改名为时间戳备份，新版原子切换到原目录。
5. 只保留最近三代 `.ai-assets-manager.backup.*`。
6. 用户关闭并重新打开当前 Code/Agent 会话。
7. 异常时执行 `self-rollback`，再重启会话。

Git 开发源目录不允许自更新，避免覆盖开发者尚未提交的修改。
