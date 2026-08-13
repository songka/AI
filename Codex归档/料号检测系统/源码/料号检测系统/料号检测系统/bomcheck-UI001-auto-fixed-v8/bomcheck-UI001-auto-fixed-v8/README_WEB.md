# BOMCheck Web

基于 FastAPI + Jinja2 的网页版入口，复用原有 `bomcheck_app` 业务逻辑。

## 运行

```bash
pip install -r requirements.txt
uvicorn app_web:app --host 0.0.0.0 --port 8000
```

- 默认读取网络 `config.json`，也可以用环境变量 `BOMCHECK_CONFIG` 指定其他配置文件。
- Web 日志写入 `app_web.log`，包含异常堆栈。
- `/health` 返回 server_time/client_ip/server_ip/port，便于外机探测。
- 访问共享盘路径时不建议使用 `--reload`，直接使用上面的启动命令。

## 查询

- `/query` 无需登录，首次打开只显示查询框，不会加载全库。
- 输入料号、描述或申请人后查询，精确料号会优先走索引。
- 需要浏览全部料号时点击“显示全部”，对应 `/query?show_all=1`。
- 系统料号库和绑定库按文件更新时间与大小缓存，网络文件变化后会自动刷新。

## 数据与账号

- Web 强制使用本地 `./data/accounts.json`，启动时自动创建。
- 即使网络 `config.json` 指向 SMB 账号库，Web 管理也优先写本地账号库。
- 管理页面提供“一键复制 SMB 账号库到本地”，若网络配置可写，会同步切换配置。
- 其他业务库路径仍由网络 `config.json` 控制，保证读取最新公共数据。

## 目录

- 上传文件：`./data/uploads/`，任务完成后删除。
- 处理结果：`./data/results/`，下载后删除，超过 30 分钟自动清理。
- 管理文件：`./data/admin/`。

## 权限

- 匿名可访问：`/`、`/execute`、`/query`、`/jobs/*`、`/parts/*`、`/health`。
- `/admin/*` 需要登录，用户管理和配置仅管理员可用，数据页需要对应权限。

## 管理页整改

- 配置、资料和用户权限保存前会弹出确认。
- 保存成功后页面会显示成功提示。
- 失效料号库会检查空料号和重复料号。
- 绑定料号库会检查条件模式、条件料号和数量。
- 重要物料、屏蔽申请人会检查重复行和异常长行。
