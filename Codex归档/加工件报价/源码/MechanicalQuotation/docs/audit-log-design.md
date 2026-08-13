# 機構2D自動報價系統 — 審計日誌設計

日期：2026-08-01
版本：V1.0

---

## 一、AuditLog Model

```python
# domain/audit.py

class AuditLog(BaseModel):
    """Immutable record of a system operation."""

    log_id: str = Field(..., description="Unique log ID (UUID)")
    timestamp: str = Field(..., description="ISO datetime with timezone")

    # -- Actor --
    user_id: str = Field(..., description="Who performed the action")
    username: str = Field(..., description="Username at time of action")
    client_host: str = Field(default="", description="Client machine hostname or IP")

    # -- Action --
    action: str = Field(..., description="Action type (see action catalog)")
    category: str = Field(..., description="auth | quotation | rule | price | user | system")

    # -- Target --
    object_type: str | None = Field(default=None, description="Type of object acted upon")
    object_id: str | None = Field(default=None, description="ID of object acted upon")

    # -- Changes --
    old_value: str | None = Field(default=None, description="Value before change (truncated)")
    new_value: str | None = Field(default=None, description="Value after change (truncated)")
    change_summary: str | None = Field(default=None, description="Human-readable summary")

    # -- Result --
    result: str = Field(..., description="success | failure | denied")
    error_message: str | None = Field(default=None)
```

---

## 二、記錄的操作類型

| category | action | 說明 |
|---|---|---|
| auth | login | 使用者登入 |
| auth | login_failed | 登入失敗 |
| auth | logout | 使用者登出 |
| auth | change_password | 修改密碼 |
| auth | admin_reset_password | 管理員重置密碼 |
| auth | account_locked | 帳號鎖定 |
| auth | account_unlocked | 帳號解鎖 |
| user | user_created | 建立用戶 |
| user | user_updated | 修改用戶 |
| user | user_disabled | 停用用戶 |
| user | role_changed | 角色變更 |
| quotation | quote_created | 新建報價 |
| quotation | quote_snapshot | 報價快照 |
| quotation | quote_exported | 匯出報價 |
| quotation | quote_deleted | 刪除報價 |
| rule | rule_viewed | 查看規則 |
| rule | change_request_submitted | 提交變更請求 |
| rule | change_request_approved | 審核通過 |
| rule | change_request_rejected | 審核退回 |
| rule | rule_published | 規則發布 |
| price | price_modified | 價格修改 |
| price | price_published | 價格發布 |
| price | version_rolled_back | 版本回滾 |
| system | config_changed | 系統配置變更 |
| system | cache_synced | Cache 同步 |
| system | error | 系統錯誤 |

---

## 三、存儲方案

### SMB 存儲

```
SMB:/audit/audit-log.db    ← SQLite, append-only (中央記錄)
```

### 雙層寫入設計

多人環境中，不能只保存 Local SQLite。設計為：

```
Client 操作
    │
    ├──→ 1. 立即寫入 Local Audit Cache (SQLite)
    │       路徑: C:\ProgramData\MechanicalQuotation\cache\audit_cache.db
    │
    └──→ 2. 非同步寫入 SMB 中央 Audit Log
            SMB:/audit/audit-log.db
            │
            ├── 成功 → 標記 Cache 記錄為 synced
            └── 失敗 → Cache 保留，後台重試
```

### 寫入策略

```python
class AuditLogger:
    """Dual-write: local cache (fast) + SMB sync (centralized)."""

    def __init__(self, local_db_path: str, smb_db_path: str): ...

    def log(self, entry: AuditLog) -> None:
        # 1. Always write to local cache first (fast, reliable)
        self._write_local(entry)

        # 2. Try SMB (may fail if offline)
        try:
            self._write_smb(entry)
            self._mark_synced(entry.log_id)
        except IOError:
            entry.sync_status = "pending"

    def sync_pending(self) -> int:
        """Retry syncing pending entries to SMB. Returns count synced."""
        ...
```

### 同步狀態

| 狀態 | 說明 |
|---|---|
| `synced` | 已成功寫入 SMB |
| `pending` | 本地已保存，等待同步到 SMB |
| `failed` | 同步失敗超過重試次數 |

---

## 四、安全性

| 規則 | 說明 |
|---|---|
| **不可修改** | Audit Log 寫入後不可被任何用戶修改或刪除 |
| **不可刪除** | 無 delete 接口 |
| **權限保護** | 查看 Audit Log 需 `system.audit_log` 權限（僅 Admin）|
| **不可偽造** | log_id 包含 hash chain，確保連續性 |
| **保留期** | 預設保留 2 年，超過可歸檔但不可刪除 |

---

*本文件為 Phase 4 多人架構的一部分。*
