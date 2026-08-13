# SMB 公共资料槽运行说明

版本：1.0（2026-08-04）

## 1. 正式路径

```text
\\10.97.0.210\lfaf_Engineer\Mechanical\3-標準文檔\10-自動報價系統\data
```

系统使用当前 Windows 登录身份访问 SMB，不保存共享盘用户名或密码。

## 2. 当前公共资料

- `rules/published/quotation-rules.yaml`：已发布报价规则。
- `prices/published/current-version-pointer.json`：当前正式价格版本指针。
- `prices/published/company-pricebook-r01-v1.1-snapshot.json`：正式公司价格快照。
- `prices/published/feature-price-calibration-gcs-v1.0.json`：图纸特征价格模型。
- `prices/published/pricing-source-records-r01-v1.0.json`：供应商及价格来源资料。
- `prices/published/version.txt`：供客户端检测价格版本变化。

`draft`、`archive`、`change-requests`、`audit`、`history`、`templates` 和 `logs` 目录已经建立，
将在后续账号权限、价格维护、审批发布和中央审计里程碑启用。

## 3. 客户端同步规则

1. UI 或 FastAPI 启动时先同步一次公共资料。
2. 运行期间默认每 60 秒在后台检查一次。
3. 只复制内容哈希发生变化的文件，写入时先生成临时文件再原子替换。
4. 本地缓存位于 `runtime/cache/smb`，清单为 `cache-manifest.json`。
5. SMB 离线时不删除旧缓存；报价继续使用最近一次成功同步的已发布资料。
6. 正式价格加载器、特征模型和管理查询优先读取缓存；没有缓存时才回退到包内已发布资料。
7. 客户端同步只读取 `published`，不会读取 `draft` 作为正式价格，也不会写入已发布目录。

## 4. 设置与接口

系统设置页面提供：

- SMB 公共槽路径；
- 本地缓存路径；
- 公共槽及缓存状态；
- “立即同步公共资料”按钮。

FastAPI：

- `GET /api/v1/smb/health`：查看公共槽和缓存状态。
- `POST /api/v1/smb/sync`：立即执行增量同步。

非敏感配置位于 `config/user_settings.json` 或 `runtime/config/user_settings.json`：

```json
{
  "smb_root": "\\\\10.97.0.210\\lfaf_Engineer\\Mechanical\\3-標準文檔\\10-自動報價系統\\data",
  "smb_auth_type": "current_user",
  "smb_cache_dir": "runtime/cache/smb",
  "smb_sync_enabled": true,
  "smb_sync_interval_seconds": 60
}
```

## 5. 初始化与保护

首次初始化命令：

```powershell
.\.venv\Scripts\python.exe tools\bootstrap_smb_public_slot.py
```

默认不覆盖公共槽已有同名文件。只有管理员确认需要重新部署当前版本时，才可显式使用
`--overwrite`。该工具不会复制 DeepSeek Key、运行日志、报价历史或第三方转换器。

当前阶段公共槽中的已发布资料仍应视为只读。用户价格维护必须通过后续 Change Request、
管理员审批和新版本发布流程，不能直接编辑 `prices/published`。
