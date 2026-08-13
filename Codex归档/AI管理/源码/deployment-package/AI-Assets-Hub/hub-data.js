window.AI_ASSETS_HUB_DATA = {
  "registryVersion": 1,
  "generation": 1,
  "issuedAt": "2026-07-25T00:00:00Z",
  "exportedAt": "2026-07-27T01:50:03.470282+00:00",
  "counts": {
    "packages": 3,
    "releases": 10,
    "dependencies": 1
  },
  "submissionStatuses": {},
  "packages": [
    {
      "id": "cli/codex",
      "owner": "AI Platform Team",
      "releases": [
        {
          "version": "1.4.0",
          "channel": "preview",
          "releaseNotes": "Codex CLI 1.4.0 预览版本，用于试点验证。",
          "dependencies": []
        },
        {
          "version": "1.3.0",
          "channel": "stable",
          "releaseNotes": "团队批准使用的 Codex CLI 1.3.0 稳定版本。",
          "dependencies": []
        }
      ]
    },
    {
      "id": "skill/ai-assets-manager",
      "owner": "AI Platform Team",
      "releases": [
        {
          "version": "1.0.6",
          "channel": "stable",
          "releaseNotes": "修复非域电脑登录 SMB 成功后 Get-SmbConnection 仍不显示身份的问题：保留原检查，并使用 Windows WNetGetUser 从实际 UNC 会话读取账号作为可信后备；Hub 使用 Skill 内置客户端，避免 SMB 旧客户端抵消修复；无法确认身份时仍拒绝特权操作。",
          "dependencies": []
        },
        {
          "version": "1.0.5",
          "channel": "stable",
          "releaseNotes": "修复交互式 net use 的密码提示和成功文字混入 PowerShell 函数返回值，导致真实退出码 0 被误判为失败的问题。",
          "dependencies": []
        },
        {
          "version": "1.0.4",
          "channel": "stable",
          "releaseNotes": "修复清理 SMB 冲突连接时，候选共享不存在所产生的 net.exe 提示被 PowerShell 误判为致命错误的问题；现在检查退出码并继续处理同服务器其他连接。",
          "dependencies": []
        },
        {
          "version": "1.0.3",
          "channel": "stable",
          "releaseNotes": "处理 Windows 1219 多账户 SMB 连接冲突：仅在用户本地确认后，断开指向 10.97.0.210 的旧连接并重新登录，不影响其他文件服务器。",
          "dependencies": []
        },
        {
          "version": "1.0.2",
          "channel": "stable",
          "releaseNotes": "修复特权命令无法确认 SMB 身份的问题：hub.ps1 在当前命令进程中检查 Get-SmbConnection，缺少身份时先执行本地安全登录，确认实际账户后再继续。",
          "dependencies": []
        },
        {
          "version": "1.0.1",
          "channel": "stable",
          "releaseNotes": "修复非域电脑在独立窗口登录后仍被重复要求登录的问题：使用 Windows 用户会话级非持久 SMB 连接，并把未登录与 Hub 尚未初始化区分为不同状态。",
          "dependencies": []
        },
        {
          "version": "1.0.0",
          "channel": "stable",
          "releaseNotes": "首次发布统一 AI 资产管理 Skill：兼容多款 Code，支持双 SMB、角色控制、三类资产版本与依赖、自动草稿 Git 双备份、中文更新说明、管理 Skill 自更新三代备份与静态 Hub 看板。",
          "dependencies": []
        }
      ]
    },
    {
      "id": "skill/code-review",
      "owner": "Developer Experience Team",
      "releases": [
        {
          "version": "1.1.0",
          "channel": "stable",
          "releaseNotes": "统一代码评审流程，并声明 Codex CLI 版本依赖。",
          "dependencies": [
            {
              "id": "cli/codex",
              "version": ">=1.3.0 <2.0.0",
              "required": true
            }
          ]
        }
      ]
    }
  ]
};
