# SMB 部署步骤

1. 将 `deployment-package/AI-Assets` 内容复制到公共槽。
2. 将 `deployment-package/AI-Assets-Backup` 内容复制到备份槽。
3. 将 `hub-web` 复制为 `...\014-AI\AI-Assets-Hub`。
4. 在每台电脑把 `skills/ai-assets-manager` 整个目录复制到所用 Code 的 skills
   目录并重启客户端。
5. 运行 `gate`；未登录时按独立窗口提示登录。
6. 运行 `validate`、`releases` 和一次带依赖安装。
7. 创建测试资产并运行 `status`，确认公共槽和备份槽的草稿 Git commit 相同。
8. 运行 `web-export`，用 Chrome 打开 `AI-Assets-Hub\index.html`。

```powershell
python "<公共槽>\client\asset_hub.py" validate
python "<公共槽>\client\asset_hub.py" web-export
```

`publish` 后应执行 `mirror`；CLI 的 `mirror` 成功后会自动刷新网页数据。若当前
SMB 未登录，先登录，不要在 AI 对话中提供凭据。

首次部署可双击或运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-secure-launch.ps1
```

它在独立窗口获取凭据，先确认三处目标均为空，再执行复制；不会把密码传给 AI，也
不会覆盖已有非空目录。
