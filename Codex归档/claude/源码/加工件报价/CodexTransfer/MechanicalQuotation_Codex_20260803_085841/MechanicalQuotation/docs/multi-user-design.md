# 機構2D自動報價系統 — 多人使用架構設計

日期：2026-08-01
版本：V1.0

---

## 一、部署架構

```
                    ┌─────────────────────────┐
                    │     SMB 共享盤 (網路磁碟) │
                    │                          │
                    │  /data/                  │
                    │    users.json            │ ← 用戶資料（加密）|
                    │    permissions.yaml      │ ← 角色權限定義    │
                    │                          │
                    │  /rules/                 │
                    │    published/            │ ← 已發布規則（唯讀）|
                    │    draft/                │ ← 審核中的規則      │
                    │    archive/              │ ← 歷史版本歸檔      │
                    │                          │
                    │  /prices/                │
                    │    published/            │ ← 已發布價格（唯讀）|
                    │    draft/                │ ← 審核中的價格      │
                    │    archive/              │ ← 歷史版本歸檔      │
                    │                          │
                    │  /history/               │
                    │    quotation_history.db  │ ← 歷史報價庫（單寫多讀）|
                    │                          │
                    │  /audit/                 │
                    │    audit-log.db          │ ← 審計日誌（append-only）|
                    │                          │
                    │  /change-requests/       │
                    │    CR-*.json             │ ← 變更請求隊列        │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
         Client A          Client B         Client C
     (Windows 10)      (Windows 11)     (Windows 10)

     登入: 張三         登入: 李四        登入: 王五
     角色: Admin        角色: Engineer    角色: Sales

     Local Cache:       Local Cache:      Local Cache:
     C:\ProgramData\    C:\ProgramData\   C:\ProgramData\
     MechanicalQuotation\  ...
```

---

## 二、核心原則

| 原則 | 說明 |
|---|---|
| **SMB 僅作存儲** | SMB 不執行任何邏輯，只存放文件 |
| **Client 執行邏輯** | 所有解析、計算、驗證在 Client 端完成 |
| **Local Cache 優先** | 啟動時讀 Cache，後台同步 SMB |
| **單一寫入者** | 同一時間只有一人能修改規則/價格（Change Request 機制）|
| **發布即鎖定** | 已發布的規則/價格唯讀，修改需新建版本 |
| **不直接操作 SQLite** | SMB 上的 SQLite 僅由 Admin 端寫入，Client 端讀取 Cache 副本 |

---

## 三、規則/價格發布流程

```
工程師修改規則/價格
        │
        ▼
儲存到 SMB:/rules/draft/ (或 /prices/draft/)
        │
        ▼
建立 Change Request → 通知管理員
        │
        ▼
管理員審核
        │
   ┌────┴────┐
   ▼         ▼
 通過       退回
   │         │
   ▼         ▼
發布到      通知工程師
published/  修改原因
   │
   ▼
更新版本號 + 歸檔舊版到 archive/
   │
   ▼
通知所有 Client: 規則已更新，請同步 Cache
   │
   ▼
發送飛書通知
```

### 規則狀態機

```
Draft ──→ Review ──→ Published ──→ Archived
  ↑                    │
  └── 退回 ───────────┘
```

---

## 四、防止同時修改衝突

### 4.1 Change Request 隊列

```python
class ChangeRequest(BaseModel):
    """A request to modify a pricing rule."""

    cr_id: str
    created_by: str               # user_id
    created_at: str               # ISO datetime

    target_type: str              # "material_price" | "process_price" | "surface_price" | "rule"
    target_id: str                # e.g. "MAT_A6061"

    old_value: str                # "38.00"
    new_value: str                # "45.00"
    reason: str                   # "供應商調價"

    status: str = "PENDING"       # PENDING → APPROVED → PUBLISHED | REJECTED
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_comment: str | None = None
```

### 4.2 樂觀鎖

```python
# 讀取價格時記錄當前 version_id
# 修改提交時檢查 version_id 是否仍然是最新
# 如果已被他人修改 → 拒絕提交，提示刷新

class VersionConflict(Exception):
    """Raised when attempting to modify a rule that has been updated since read."""
    ...
```

---

## 五、報價一致性保證

### 問題

A 正在報價時，B 發布了新價格 → A 的報價結果可能變化。

### 解決：報價鎖定價格版本

```python
class QuoteSession:
    """A quotation session with frozen price versions."""

    session_id: str
    user_id: str
    started_at: str

    # Frozen versions for this session
    locked_material_version: str
    locked_process_version: str
    locked_surface_version: str
    locked_labor_version: str

    # All price lookups use these locked versions,
    # even if new versions are published during the session.
```

當 Quote 產生 Snapshot 時，鎖定的版本號寫入快照。

---

## 六、Windows Mutex 防多開

```python
import ctypes

MUTEX_NAME = "Global\\MechanicalQuotation_SingleInstance"

def check_single_instance() -> bool:
    """Return True if this is the only instance."""
    import ctypes.wintypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        return False
    return True
```

---

## 七、國際化 (i18n)

### 7.1 文件結構

```
locales/
├── zh-CN.json    ← 簡體中文（默認）
├── zh-TW.json    ← 繁體中文
└── en-US.json    ← 英文
```

### 7.2 使用方式

```python
from quotation.utils.i18n import t

# 所有 UI 文字通過 t() 函數獲取
print(t("quotation.total"))        # "總價" / "总价" / "Total"
print(t("error.file_not_found"))   # "找不到文件" / "找不到檔案" / "File not found"
```

---

## 八、Phase 開發順序更新

```
Phase 0-2 ✅  現有（核心報價邏輯）
Phase 3       CAD 解析

Phase 4       [新增] 多人架構基礎
              ├── User Model + 認證
              ├── Permission/RBAC
              ├── SMB 部署適配
              ├── Local Cache + Sync
              ├── Audit Log
              └── Windows Mutex

Phase 5       [新增] 協作流程
              ├── Change Request
              ├── 規則發布流程 (Draft→Review→Published)
              ├── 飛書通知
              └── i18n

Phase 6       報價規則引擎 + 定價管理

Phase 7       AI 輔助

Phase 8       GUI
```

---

*本文件定義多人使用架構的整體設計。各子系統詳見對應設計文檔。*
