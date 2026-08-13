# BOMCheck Web

基于 FastAPI + Jinja2 的网页版入口，复用原有 `bomcheck_app` 业务逻辑。

## 运行

```bash
pip install -r requirements.txt
uvicorn app_web:app --host 0.0.0.0 --port 8000
```

- Web 日志写入 `app_web.log`，包含异常堆栈。
- `/health` 返回 server_time/client_ip/server_ip/port，便于外机探测。
- 访问共享盘路径时不建议使用 `--reload`，直接使用上面的 `uvicorn app_web:app --host 0.0.0.0 --port 8000` 启动。

## 数据与账号

- Web 强制使用本地 `./data/accounts.json`，启动时自动创建（默认 admin/admin）。
- 即使 `config.json` 指向 SMB 账号库，页面会显示警告，并提供“一键复制 SMB 账号库到本地并切换”。
- 其他业务库路径由 `config.json` 控制，管理页面可编辑。

## 目录

- 上传文件：`./data/uploads/`，任务完成后删除。
- 处理结果：`./data/results/`，下载后删除，超过 30 分钟自动清理。
- 管理文件：`./data/admin/`。

## 权限

- 匿名可访问：`/`、`/execute`、`/query`、`/jobs/*`、`/parts/*`、`/health`。
- `/admin/*` 需登录，用户管理/配置仅管理员可用，数据页需对应权限。
