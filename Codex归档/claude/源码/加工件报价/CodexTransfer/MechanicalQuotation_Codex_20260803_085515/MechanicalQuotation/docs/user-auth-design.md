# 機構2D自動報價系統 — 用戶認證設計

日期：2026-08-01
版本：V1.0

---

## 一、User Model

```python
# domain/user.py

from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    SALES = "sales"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"  # Too many failed attempts

class User(BaseModel):
    user_id: str                    # UUID
    username: str                   # 唯一，3-32 字符
    password_hash: str              # bcrypt hash (含 salt)
    display_name: str               # "張三"
    department: str | None = None   # "工程部" / "業務部"
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE
    email: str | None = None
    phone: str | None = None

    created_time: str               # ISO datetime
    created_by: str | None = None   # 創建者 user_id

    last_login_time: str | None = None
    last_login_ip: str | None = None

    failed_attempts: int = 0
    locked_until: str | None = None

    must_change_password: bool = False  # 首次登入強制改密碼
```

---

## 二、密碼安全

### 2.1 Hash 方案

使用 **bcrypt**（自動含 salt，成本因子=12）：

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password with bcrypt (salt included in output)."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )
```

### 2.2 密碼策略

| 規則 | 值 |
|---|---|
| 最小長度 | 8 字符 |
| 必須包含 | 字母 + 數字 |
| 建議包含 | 特殊字符 |
| 歷史禁止 | 與前 3 次密碼不同 |
| 過期 | 90 天強制更換 |
| 鎖定 | 連續 5 次失敗 → 鎖定 30 分鐘 |

---

## 三、登入流程

```
1. 使用者啟動程序
        │
        ▼
2. 顯示登入窗口
   - 記住上次登入用戶名
        │
        ▼
3. 輸入 username + password
        │
        ▼
4. 檢查 Local Cache 中用戶資料
        │
   ┌────┴────┐
   ▼         ▼
 命中      未命中
   │         │
   │         ▼
   │    從 SMB:/data/users.json 讀取
   │         │
   └────┬────┘
        │
        ▼
5. bcrypt 驗證密碼
        │
   ┌────┴────┐
   ▼         ▼
 成功      失敗
   │         │
   │         ▼
   │    failed_attempts++
   │    記錄 Audit Log
   │    返回錯誤提示
   │         │
   ▼         ▼
6. 加載角色權限  達到5次?
        │         │
   ┌────┴───┐    ▼
   ▼        ▼  帳號鎖定
 正常    首次    │
 登入    登入    ▼
         │   顯示鎖定提示
         ▼
      強制修改密碼
        │
        ▼
7. 更新 last_login_time, failed_attempts=0
        │
        ▼
8. 進入主界面 (根據角色顯示不同功能)
```

---

## 四、登出

```python
def logout(user_id: str, session_id: str):
    """Log out the current user."""
    audit_log(
        user_id=user_id,
        action="logout",
        result="success",
    )
    # Clear session cache
    # Return to login window
```

---

## 五、密碼修改

### 5.1 用戶自行修改

```python
def change_password(
    user_id: str,
    old_password: str,
    new_password: str,
) -> bool:
    """User changes their own password."""
    user = get_user(user_id)
    if not verify_password(old_password, user.password_hash):
        return False
    if not validate_password_policy(new_password, user_id):
        return False
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    user.password_history.append(old_hash)  # 保留最近3個
    save_user(user)
    audit_log(user_id, "change_password", result="success")
    return True
```

### 5.2 管理員重置

```python
def admin_reset_password(
    admin_user_id: str,
    target_user_id: str,
    temp_password: str,
) -> bool:
    """Admin resets another user's password."""
    if not has_permission(admin_user_id, "user.manage"):
        return False
    user = get_user(target_user_id)
    user.password_hash = hash_password(temp_password)
    user.must_change_password = True
    user.failed_attempts = 0
    user.status = UserStatus.ACTIVE
    save_user(user)
    audit_log(admin_user_id, "admin_reset_password",
              object_type="user", object_id=target_user_id,
              result="success")
    return True
```

---

## 六、用戶存儲

### SMB 存儲

```
SMB:/data/users.json
```

格式為加密 JSON 陣列（使用 AES 加密，密鑰由 Admin 設定時輸入）。

### Local Cache

```
C:\ProgramData\MechanicalQuotation\cache\users_cache.json
```

啟動時優先讀取 Cache，後台比對 SMB 上的版本時間戳決定是否刷新。

---

## 七、桌面程序 Session 設計

本系統為桌面應用，不使用純 Web JWT 模式。

### Session 模型

```python
class UserSession(BaseModel):
    """Desktop application session — in-memory only."""

    session_id: str                 # UUID
    user_id: str
    username: str
    display_name: str
    role: UserRole
    permissions: list[str]          # Cached permissions

    # Timing
    created_at: str                 # ISO datetime
    last_activity_at: str           # Updated on each user action
    expires_at: str                 # absolute timeout

    # State
    is_active: bool = True
```

### Session 管理

```python
class SessionManager:
    """Single-user desktop session (one session per application instance)."""

    SESSION_TIMEOUT_MINUTES: int = 480     # 8 hours absolute max
    IDLE_TIMEOUT_MINUTES: int = 30         # Auto-lock after 30 min idle

    def create_session(self, user: User) -> UserSession: ...
    def check_timeout(self) -> bool:
        """Return True if session has expired (absolute or idle)."""
        ...
    def touch(self) -> None:
        """Update last_activity_at (called on each user action)."""
        ...
    def lock(self) -> None:
        """Lock the session (require re-login)."""
        ...
    def unlock(self, password: str) -> bool:
        """Re-authenticate to unlock."""
        ...
    def destroy(self) -> None:
        """Logout — clear session from memory."""
        ...
```

### Session Timeout 行為

```
用戶操作 → touch() 更新 last_activity_at
    │
    ├─ idle > 30min  → lock() → 顯示解鎖畫面 → 輸入密碼解鎖
    │
    └─ total > 8h    → destroy() → 強制回到登入畫面
```

### Password Retry Lock

```python
class LoginGuard:
    MAX_FAILED_ATTEMPTS: int = 5
    LOCK_DURATION_MINUTES: int = 30

    def attempt_login(self, username: str, password: str) -> LoginResult:
        """
        1. Check account status (ACTIVE/DISABLED/LOCKED)
        2. If LOCKED and lock duration passed → auto-unlock
        3. Verify password
        4. On failure: increment failed_attempts
        5. On 5th failure: set status=LOCKED, locked_until = now+30min
        6. Log to Audit Log
        """
        ...

class LoginResult:
    success: bool
    message: str            # "登入成功" / "密碼錯誤 (剩餘3次)" / "帳號已鎖定，請30分鐘後再試"
    session: UserSession | None
    remaining_attempts: int
```

### 存儲位置

- Session 數據：純內存，不寫入磁盤（安全性）
- 程序關閉 = 自動登出
- User 資料：SMB 加密存儲 + Local Cache 備份

---

*本文件為 Phase 4 多人架構的一部分。*
