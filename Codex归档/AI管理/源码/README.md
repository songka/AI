# AI Assets Hub

本项目统一管理团队共用的 **Skill、CLI、Agent**。用户把
`skills/ai-assets-manager` 整个文件夹复制到所用 Code/Agent 的 skills 目录即可；
同一份 Skill 兼容 Codex、Claude Code、Gemini CLI 和 Cursor。

## 固定仓库

- 公共槽：`\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets`
- 备份/权威槽：`\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup`

公共槽用于查询、安装、候选提交和每个用户的草稿 Git 备份；备份槽保存第二份
草稿 Git 历史、已审核发布物和恢复快照。正式发布按“备份槽 → 公共槽”单向同步。

## 核心行为

- 登录前只提示如何在独立 Windows 窗口登录 SMB，不显示其他操作。
- 账号未写域时自动补成 `GETACAD\账号`；临时账号也只在独立窗口输入。
- SMB 密码不进入 AI 对话、命令参数、环境变量或磁盘文件。
- 每次初始化、状态检查、改版或打包，自动把未发布内容提交到两处 SMB 的用户专属
  Git 草稿库；不需要用户提出，也不检查 Hub 角色。
- 正式版本支持 SemVer、多版本并存、依赖自动解析、SHA-256 校验和本地激活。
- 管理 Skill 自身也登记为 `skill/ai-assets-manager`，可从 Hub 更新；更新前备份用户
  当前副本，最多保留三代，并支持回滚。
- 角色包括管理员、审核者、发布者、使用者；管理员负责账户角色分配。

## 文档

- [完整部署与使用说明](docs/deployment-and-usage.md)
- [使用者操作说明书](docs/user-manual.md)
- [管理员操作说明书](docs/administrator-manual.md)
- [流程图谱](docs/process-map.md)
- [多 Code 兼容与便携 Skill](docs/portable-skill.md)
- [双 SMB 架构](docs/dual-smb-architecture.md)
- [权限不可改时的防篡改边界](docs/untrusted-smb-security.md)
- [登录与临时账户](docs/smb-login.md)
- [凭据安全](docs/credential-security.md)
- [角色与发布治理](docs/governance.md)
- [账户角色配置](docs/account-role-setup.md)
- [SMB 初始目录](docs/smb-initial-layout.md)
- [SMB 部署步骤](docs/smb-deployment.md)

本地测试：

```powershell
python -m unittest discover -s tests -v
python .\tools\asset_hub.py validate
```
