# 機構2D自動報價系統 — SMB 部署設計

日期：2026-08-01
版本：V1.0

---

## 一、SMB 資料夾結構

```
SMB: \\10.97.0.210\lfaf_Engineer\Mechanical\3-標準文檔\10-自動報價系統\data\
│
├── data\                          ← 系統資料
│   ├── users.json                 ← 用戶資料（AES 加密）
│   ├── permissions.yaml           ← 權限定義
│   └── roles.yaml                 ← 角色定義
│
├── rules\                         ← 報價規則
│   ├── draft\                     ← 審核中的規則
│   │   ├── material-prices.xlsx
│   │   └── ...
│   ├── published\                 ← 已發布規則（Client 讀取來源）
│   │   ├── quotation-rules.yaml   ← 當前生效的規則
│   │   ├── material-prices.xlsx
│   │   ├── process-prices.xlsx
│   │   ├── surface-prices.xlsx
│   │   ├── labor-rates.xlsx
│   │   ├── process-times.xlsx
│   │   └── material-density.yaml
│   └── archive\                   ← 歷史版本
│       ├── v2025-01-01\
│       ├── v2025-06-15\
│       └── ...
│
├── prices\                        ← 價格數據（結構同 rules/）
│   ├── draft\
│   ├── published\
│   └── archive\
│
├── history\                       ← 歷史報價
│   └── quotation_history.db       ← SQLite (單寫多讀)
│
├── audit\                         ← 審計日誌
│   └── audit-log.db               ← SQLite (append-only)
│
├── change-requests\               ← 變更請求隊列
│   ├── CR-001.json
│   ├── CR-002.json
│   └── ...
│
├── logs\                          ← 系統日誌
│   ├── client-A\
│   ├── client-B\
│   └── ...
│
└── templates\                     ← 模板
    └── quotation-template.xlsx
```

---

## 二、Client 端目錄

```
C:\ProgramData\MechanicalQuotation\
│
├── cache\                         ← 本地 Cache
│   ├── users_cache.json
│   ├── rules_cache\               ← 規則本地副本
│   │   └── quotation-rules.yaml
│   ├── prices_cache\              ← 價格本地副本
│   ├── history_index.json         ← 歷史報價索引
│   └── cache_manifest.json        ← Cache 版本資訊
│
├── logs\                          ← 本地日誌
│   └── client.log
│
├── config\                        ← 本地配置
│   ├── smb-config.yaml            ← SMB 連線設定
│   └── user-preferences.yaml      ← 用戶偏好
│
└── temp\                          ← 臨時文件
```

---

## 三、SMB 連線配置

```yaml
# smb-config.yaml
smb:
  server: "\\\\10.97.0.210\\lfaf_Engineer\\Mechanical\\3-標準文檔\\10-自動報價系統\\data"

  # 連線方式
  auth_type: "current_user"     # current_user | specific_credentials

  # 若使用 specific_credentials:
  # username: "svc_quotation"
  # password: "***"  # 加密存儲

  # Cache
  cache:
    enabled: true
    local_dir: "C:\\ProgramData\\MechanicalQuotation\\cache"
    sync_interval_seconds: 60    # 後台同步間隔

  # 重試
  retry:
    max_attempts: 3
    backoff_seconds: 5

  # 超時
  timeout_seconds: 30
```

---

## 四、同步狀態

```python
class SyncStatus(str, Enum):
    ONLINE = "online"              # SMB 可訪問，Cache 已同步
    ONLINE_SYNCING = "syncing"     # 正在同步中
    OFFLINE_CACHE = "offline_cache" # SMB 不可訪問，使用 Cache
    SYNC_ERROR = "sync_error"      # 同步失敗，使用舊 Cache
```

### 狀態轉換

```
ONLINE ──→ SMB斷線 ──→ OFFLINE_CACHE
  │                       │
  │                    SMB恢復
  │                       │
  └────── ONLINE ←────────┘
```

---

## 五、SMB 訪問模式

| 文件 | 讀取方 | 寫入方 | 並發控制 |
|---|---|---|---|
| users.json | 所有 Client | Admin | Admin 寫入時短暫鎖定 |
| rules/published/* | 所有 Client | Admin（發布時） | 版本號樂觀鎖 |
| rules/draft/* | Admin + Engineer | Engineer（提交） | Change Request 機制 |
| quotation_history.db | 所有 Client | Admin（導入） | SQLite WAL 模式 |
| audit-log.db | Admin（查看） | 所有 Client（追加） | SQLite WAL + append-only |
| change-requests/*.json | 所有 Client | Engineer（提交） | 文件鎖 |

---

*本文件為 Phase 4 多人架構的一部分。*
