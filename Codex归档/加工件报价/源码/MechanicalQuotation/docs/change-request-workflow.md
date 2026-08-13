# 機構2D自動報價系統 — 變更請求審批流程設計

日期：2026-08-01
版本：V1.0

---

## 一、環境限制

| 限制 | 影響 |
|---|---|
| 無公網 IP | 飛書無法回調到內網 |
| 無外部 Web 服務 | 無 REST API 供飛書調用 |
| 僅內網 Windows + SMB | 所有互動在軟件內完成 |

**飛書角色：僅單向通知，不作為簽核入口。**

---

## 二、完整審批流程

```
工程師登入報價軟件
        │
        ▼
提交修改申請
  - 選擇要修改的項目（材料價格/加工價格/規則)
  - 填寫: 舊值 → 新值 → 原因
        │
        ▼
SMB 保存 Change Request
  路徑: SMB:/change-requests/CR-XXX.json
  狀態: PENDING
        │
        ▼
飛書 Webhook 通知管理員
  「📝 新的修改申請: A6061 材料價格 38→45」
        │
        ▼
管理員收到飛書通知
        │
        ▼
管理員登入報價軟件
        │
        ▼
打開「審批中心」
  - 查看 PENDING 的 Change Request 列表
  - 查看修改詳情（新舊值對比、原因）
        │
   ┌────┴────┐
   ▼         ▼
 批准       拒絕
   │         │
   │         ▼
   │    填寫拒絕原因
   │    CR 狀態: REJECTED
   │    Audit Log 記錄
   │         │
   │         ▼
   │    飛書通知提交者
   │    「❌ 你的申請已被拒絕: A6061 材料價格」
   │
   ▼
CR 狀態: APPROVED
生成新價格版本
  - 更新價格文件到 SMB:/prices/published/
  - 歸檔舊版本到 archive/
  - 更新 version.txt
        │
        ▼
Audit Log 記錄
  - action: change_request_approved
  - old_value / new_value
        │
        ▼
飛書通知提交者 + 相關人員
  「✅ A6061 材料價格已更新: 38→45 元/kg」
        │
        ▼
所有 Client 後台同步檢測到 version.txt 變更
  → 更新 Local Cache
```

---

## 三、Change Request 模型

```python
# domain/change_request.py

class ChangeRequestStatus(str, Enum):
    PENDING = "PENDING"          # 等待審批
    APPROVED = "APPROVED"        # 已批准
    REJECTED = "REJECTED"        # 已拒絕
    CANCELLED = "CANCELLED"      # 提交者取消

class ChangeType(str, Enum):
    MATERIAL_PRICE = "material_price"
    PROCESS_PRICE = "process_price"
    SURFACE_PRICE = "surface_price"
    LABOR_RATE = "labor_rate"
    TIME_RULE = "time_rule"

class ChangeRequest(BaseModel):
    """A request to modify any pricing or rule item."""

    cr_id: str = Field(..., description="CR-YYYYMMDD-NNN")
    change_type: ChangeType

    # What is being changed
    target_id: str                    # "MAT_A6061" / "PROC_CNC" / "SURF_ANODIZE"
    target_name: str                  # "A6061-T6 材料價格"
    field_path: str                   # "unit_price"
    old_value: str                    # "38.00"
    new_value: str                    # "45.00"
    reason: str                       # 修改原因

    # Who
    submitted_by: str                 # user_id
    submitted_by_name: str            # "張三"
    submitted_at: str                 # ISO datetime

    # Review
    status: ChangeRequestStatus = ChangeRequestStatus.PENDING
    reviewed_by: str | None = None
    reviewed_by_name: str | None = None
    reviewed_at: str | None = None
    review_comment: str | None = None  # 審批意見（拒絕時必填）

    # Result
    new_version_id: str | None = None  # 發布後的版本 ID
    published_at: str | None = None
```

---

## 四、審批中心（軟件內功能）

### 4.1 CLI 命令

```bash
# 提交修改申請（工程師）
quotation change-request submit \
    --type material_price \
    --target MAT_A6061 \
    --old 38.00 \
    --new 45.00 \
    --reason "供應商調價，2025年6月起生效"

# 查看待審批列表（管理員）
quotation change-request list --status PENDING

# 審批（管理員）
quotation change-request approve CR-20260801-001
quotation change-request reject CR-20260801-001 --comment "需提供供應商報價證明"

# 查看我的申請（工程師）
quotation change-request my
```

### 4.2 GUI 審批中心（Phase 8）

```
┌─────────────────────────────────────────┐
│  審批中心                          [X]  │
├─────────────────────────────────────────┤
│  待審批 (3)  │  已處理 (15)             │
├─────────────────────────────────────────┤
│  ☐ CR-001  A6061 材料價格  38→45       │
│    提交: 張三  2026-08-01 10:30         │
│    原因: 供應商調價                      │
│    [批准] [拒絕]                         │
│                                         │
│  ☐ CR-002  CNC 加工費率  80→90         │
│    提交: 李四  2026-08-01 11:00         │
│    原因: 設備折舊更新                    │
│    [批准] [拒絕]                         │
└─────────────────────────────────────────┘
```

---

## 五、SMB 存儲

```
SMB:/change-requests/
├── CR-20260801-001.json     ← PENDING
├── CR-20260801-002.json     ← APPROVED
├── CR-20260715-001.json     ← REJECTED
└── CR-20260715-002.json     ← APPROVED (archived)
```

### CR 文件格式

```json
{
  "cr_id": "CR-20260801-001",
  "change_type": "material_price",
  "target_id": "MAT_A6061",
  "target_name": "A6061-T6 材料價格",
  "field_path": "unit_price",
  "old_value": "38.00",
  "new_value": "45.00",
  "reason": "供應商調價，2025年6月起生效",
  "submitted_by": "user-zhangsan",
  "submitted_by_name": "張三",
  "submitted_at": "2026-08-01T10:30:00",
  "status": "PENDING",
  "reviewed_by": null,
  "reviewed_by_name": null,
  "reviewed_at": null,
  "review_comment": null,
  "new_version_id": null,
  "published_at": null
}
```

---

## 六、飛書通知（僅通知）

### 觸發事件與通知對象

| 事件 | 通知對象 | 優先級 |
|---|---|---|
| 修改申請提交 | Admin 角色所有人 | 高 |
| 申請批准 | 提交者 | 中 |
| 申請拒絕 | 提交者 | 中 |
| 規則/價格發布 | Admin + Engineer + Sales | 中 |
| 系統異常 | Admin | 高 |

### 通知卡片（純資訊，無交互按鈕）

```json
{
  "header": {
    "title": {"content": "📝 新的修改申請", "tag": "plain_text"},
    "template": "blue"
  },
  "elements": [
    {
      "tag": "div",
      "fields": [
        {"is_short": true, "text": {"tag": "lark_md", "content": "**申請人**\n張三"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**修改項**\nA6061 材料價格"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**舊值**\n38.00 元/kg"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**新值**\n45.00 元/kg"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**原因**\n供應商調價"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**時間**\n2026-08-01 10:30"}}
      ]
    },
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "⚠️ 請登入報價軟件 → 審批中心 進行審批"}}
  ]
}
```

### 審批結果通知

```json
{
  "header": {
    "title": {"content": "✅ 修改申請已批准", "tag": "plain_text"},
    "template": "green"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "**A6061 材料價格**: 38.00 → 45.00 元/kg\n**審批人**: 王五\n**時間**: 2026-08-01 11:00\n**新版本**: MAT-2026-08-01-v1"}}
  ]
}
```

---

## 七、管理員儀表板（首頁待辦）

管理員登入後，軟件首頁顯示待辦摘要：

### CLI

```bash
$ quotation dashboard

═══════════════════════════════════════
  機構2D自動報價系統 — 管理員儀表板
═══════════════════════════════════════

  待審批:
    🔴 3 個價格修改申請
    🟡 2 個規則更新申請
    🔵 1 個用戶申請

  最近活動:
    2026-08-01 10:30  張三 提交 A6061 材料價格修改
    2026-08-01 09:00  李四 完成報價 UC1000005854
    2026-07-31 16:00  王五 發布規則 v2.1

  系統狀態:
    SMB:     🟢 已連接 (\\\\10.97.0.210\\...)
    Cache:   🟢 已同步 (2026-08-01 10:30)
    審計日誌: 🟢 正常

═══════════════════════════════════════
  輸入命令: [1]審批中心 [2]報價 [3]規則管理 [4]用戶管理
```

### GUI 儀表板 (Phase 8)

```
┌──────────────────────────────────────────────────┐
│  機構2D自動報價系統 — 歡迎, 王五 (管理員)         │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─ 待辦事項 ─────────────────────────────┐     │
│  │                                         │     │
│  │  🔴 價格修改    3 筆待審批   [查看]     │     │
│  │  🟡 規則更新    2 筆待審批   [查看]     │     │
│  │  🔵 用戶申請    1 筆待審批   [查看]     │     │
│  │                                         │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ┌─ 最近活動 ─────────────────────────────┐     │
│  │  10:30  張三 提交 A6061 材料價格修改     │     │
│  │  09:00  李四 完成報價 #Q2026-0801-015   │     │
│  │  昨日   系統規則 v2.1 發布               │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ┌─ 快速入口 ─────────────────────────────┐     │
│  │  [審批中心]  [新建報價]  [規則管理]      │     │
│  │  [用戶管理]  [審計日誌]  [系統設置]      │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  系統狀態: 🟢 SMB 已連接  |  🟢 Cache 已同步     │
└──────────────────────────────────────────────────┘
```

### 不同角色的首頁

| 角色 | 首頁顯示 |
|---|---|
| **Admin** | 待審批數量 + 最近活動 + 快速入口（審批中心/用戶管理/審計日誌） |
| **Engineer** | 我的申請狀態 + 最近報價 + 快速入口（新建報價/提交修改） |
| **Sales** | 最近報價 + 快速入口（新建報價/查看報價）**不顯示成本** |
| **Viewer** | 已發布報價列表（唯讀） |

---

## 八、管理員待辦中心狀態分類

### 審批中心分頁

```
┌──────────────────────────────────────────────┐
│  審批中心                                     │
├──────────────────────────────────────────────┤
│  [待審核 3]  [已批准 15]  [已拒絕 2]          │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─ 待審核 ──────────────────────────────┐   │
│  │  🔴 CR-001  A6061 材料價格 38→45       │   │
│  │     提交: 張三  2026-08-01 10:30       │   │
│  │     原因: 供應商調價                    │   │
│  │     [批准]  [拒絕]                      │   │
│  │                                        │   │
│  │  🟡 CR-002  CNC 加工費率 80→90         │   │
│  │     提交: 李四  2026-08-01 11:00       │   │
│  │     [批准]  [拒絕]                      │   │
│  └────────────────────────────────────────┘   │
│                                              │
│  ┌─ 已批准 (最近5筆) ────────────────────┐   │
│  │  ✅ CR-000  SUS304 材料價格           │   │
│  │     審批人: 王五  2026-07-31           │   │
│  └────────────────────────────────────────┘   │
│                                              │
│  ┌─ 已拒絕 (最近5筆) ────────────────────┐   │
│  │  ❌ CR-099  CNC 加工費率               │   │
│  │     審批人: 王五  原因: 需提供證明      │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### API 查詢

```python
class ApprovalCenter:
    def get_pending(self) -> list[ChangeRequest]: ...
    def get_approved(self, limit: int = 20) -> list[ChangeRequest]: ...
    def get_rejected(self, limit: int = 20) -> list[ChangeRequest]: ...
    def get_summary(self) -> dict:
        return {
            "pending": 3,
            "approved_today": 1,
            "rejected_today": 0,
        }
```

---

## 九、並發審批鎖

### 問題

多管理員同時打開審批中心，可能同時批准同一 CR。

### 解決：樂觀鎖 + SMB 文件鎖

```python
class ApprovalLock(BaseModel):
    """Prevents concurrent approval of the same Change Request."""

    cr_id: str = Field(..., description="Target CR ID")
    locked_by: str = Field(..., description="user_id who holds the lock")
    locked_by_name: str = Field(..., description="Display name")
    lock_time: str = Field(..., description="ISO datetime")
    lock_expires: str = Field(..., description="ISO datetime (lock_time + 5 min)")
```

### 鎖定流程

```python
def acquire_approval_lock(cr_id: str, user: User) -> ApprovalLock | None:
    """
    1. 檢查 SMB:/change-requests/{cr_id}.lock 是否存在
    2. 如果存在且未過期 → 返回 None (已被他人鎖定)
    3. 如果存在但已過期 → 覆蓋鎖定
    4. 如果不存在 → 建立新鎖文件
    5. 返回 ApprovalLock
    """

def release_approval_lock(cr_id: str, user_id: str) -> bool:
    """釋放鎖定。僅鎖定者本人可釋放（或 Admin 強制釋放）。"""

def check_approval_lock(cr_id: str) -> ApprovalLock | None:
    """查詢當前鎖定狀態。"""
```

### 鎖定檔案

```
SMB:/change-requests/CR-20260801-001.lock
{
  "cr_id": "CR-20260801-001",
  "locked_by": "user-wangwu",
  "locked_by_name": "王五",
  "lock_time": "2026-08-01T11:00:00",
  "lock_expires": "2026-08-01T11:05:00"
}
```

### UI 提示

```
其他管理員打開同一 CR 時：

  ⚠️ 此申請正在被「王五」審批中（鎖定至 11:05）
  [查看詳情（唯讀）]  [返回列表]
```

---

## 十、飛書通知消息隊列

### 問題

Webhook 可能失敗（網路抖動、飛書限流），不能讓核心審批流程因通知失敗而中斷。

### 解決：本地隊列 + 非同步發送 + 重試

```python
class NotifyStatus(str, Enum):
    PENDING = "PENDING"    # 等待發送
    SENT = "SENT"          # 已成功發送
    FAILED = "FAILED"      # 發送失敗（超過重試次數）

class NotificationMessage(BaseModel):
    """A notification message in the local queue."""

    msg_id: str = Field(..., description="UUID")
    event_type: str                   # "cr_submitted" | "cr_approved" | ...
    target_users: list[str]           # user_ids to notify
    card_payload: dict                # Feishu card JSON
    status: NotifyStatus = NotifyStatus.PENDING
    created_at: str
    sent_at: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    last_error: str | None = None
```

### 隊列流程

```python
class NotificationQueue:
    """Local queue → async send → SMB persistent log."""

    QUEUE_DIR = "C:\\ProgramData\\MechanicalQuotation\\notification_queue\\"

    def enqueue(self, msg: NotificationMessage) -> str:
        """1. 保存到本地隊列目錄 (JSON 文件)
           2. 返回 msg_id
           3. 核心流程繼續（不等待發送結果）"""
        ...

    def process_queue(self):
        """後台線程: 逐條發送 PENDING 消息
           - 成功 → status=SENT, 刪除本地文件
           - 失敗 → retry_count++, 指數退避重試
           - 超過 max_retries → status=FAILED, 記錄錯誤"""
        ...

    def get_failed(self) -> list[NotificationMessage]:
        """查詢發送失敗的消息（供管理員檢查）"""
        ...
```

### 發送策略

| 重試次數 | 退避時間 |
|---|---|
| 1st | 10s |
| 2nd | 30s |
| 3rd | 60s |
| 超過 | → FAILED，記錄到日誌 |

### 核心流程不阻塞

```python
# 審批通過後:
def approve_change_request(cr_id: str, reviewer: User) -> ChangeRequest:
    cr = load_cr(cr_id)
    cr.status = APPROVED
    cr.reviewed_by = reviewer.user_id
    save_cr(cr)                      # ← 核心: 保存 CR
    publish_new_version(cr)          # ← 核心: 發布新版本
    write_audit_log(cr)              # ← 核心: 審計日誌

    # 非核心: 通知（不阻塞返回）
    notification_queue.enqueue(
        NotificationMessage(
            event_type="cr_approved",
            target_users=[cr.submitted_by],
            card_payload=build_approval_card(cr),
        )
    )
    # ← 立即返回，通知在後台發送
    return cr
```

---

*本文件定義完整的內網審批流程。審批中心、並發鎖、通知隊列實作在 Phase 4-5。*
