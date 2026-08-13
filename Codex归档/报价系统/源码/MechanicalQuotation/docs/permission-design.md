# 機構2D自動報價系統 — 角色權限設計

日期：2026-08-01
版本：V1.0

---

## 一、設計原則

1. **權限不硬編碼** — 權限定義在 YAML 配置文件中
2. **RBAC（角色基礎存取控制）** — 權限分配給角色，角色分配給用戶
3. **默認拒絕** — 未明確授權的操作一律拒絕
4. **Admin 不可刪除** — 至少保留一個 Admin 帳號

---

## 二、Permission Model

```python
# domain/permission.py

class Permission(BaseModel):
    """A single permission that can be granted to a role."""
    permission_id: str           # "quotation.create"
    name: str                    # "建立報價"
    description: str             # "允許建立新的報價單"
    category: str                # "quotation" | "rule" | "user" | "system"

class Role(BaseModel):
    """A role is a named collection of permissions."""
    role_id: str                 # "engineer"
    name: str                    # "工程師"
    permissions: list[str]       # ["quotation.create", "quotation.view_cost", ...]
    is_system: bool = False      # True = 不可修改/刪除的內建角色
```

---

## 三、權限清單

```yaml
# config/permissions.yaml

permissions:
  # === 報價相關 ===
  quotation.create:
    name: "建立報價"
    category: quotation
    description: "允許建立新的報價單"

  quotation.view:
    name: "查看報價"
    category: quotation
    description: "允許查看已建立的報價"

  quotation.view_cost:
    name: "查看成本明細"
    category: quotation
    description: "允許查看材料費/加工費等成本細節"

  quotation.export:
    name: "匯出報價"
    category: quotation
    description: "允許匯出 Excel 報價單"

  quotation.delete:
    name: "刪除報價"
    category: quotation
    description: "允許刪除報價單"

  # === 規則相關 ===
  rule.view:
    name: "查看規則"
    category: rule
    description: "允許查看報價規則"

  rule.modify:
    name: "修改規則"
    category: rule
    description: "允許提交規則/價格修改請求"

  rule.approve:
    name: "審核規則"
    category: rule
    description: "允許審核並發布規則變更"

  price.view_cost:
    name: "查看成本價格"
    category: rule
    description: "允許查看材料/加工/表面處理的成本價格"

  price.modify:
    name: "修改價格"
    category: rule
    description: "允許提交價格修改請求"

  # === 用戶管理 ===
  user.manage:
    name: "管理用戶"
    category: user
    description: "允許建立/修改/停用用戶"

  user.view:
    name: "查看用戶"
    category: user
    description: "允許查看用戶列表"

  # === 系統管理 ===
  system.audit_log:
    name: "查看審計日誌"
    category: system
    description: "允許查看操作審計日誌"

  system.config:
    name: "系統配置"
    category: system
    description: "允許修改系統配置"
```

---

## 四、角色定義

```yaml
# config/roles.yaml

roles:
  admin:
    name: "管理員"
    is_system: true
    permissions:
      - quotation.create
      - quotation.view
      - quotation.view_cost
      - quotation.export
      - quotation.delete
      - rule.view
      - rule.modify
      - rule.approve
      - price.view_cost
      - price.modify
      - user.manage
      - user.view
      - system.audit_log
      - system.config

  engineer:
    name: "工程師"
    is_system: true
    permissions:
      - quotation.create
      - quotation.view
      - quotation.view_cost       # 工程師可看成本
      - quotation.export
      - rule.view
      - rule.modify               # 可提交修改，需審核
      - price.view_cost
      - price.modify              # 可提交修改，需審核

  sales:
    name: "業務"
    is_system: true
    permissions:
      - quotation.create
      - quotation.view
      # 不可查看成本明細
      - quotation.export
      - rule.view

  viewer:
    name: "查看者"
    is_system: true
    permissions:
      - quotation.view
```

---

## 五、權限檢查

```python
# application/auth_service.py

class AuthService:
    """Centralized permission checking."""

    def __init__(self, roles_config: dict, permissions_config: dict): ...

    def has_permission(self, user: User, permission: str) -> bool:
        """Check if a user has a specific permission."""
        if user.status != UserStatus.ACTIVE:
            return False
        role = self.get_role(user.role)
        return permission in role.permissions

    def require_permission(self, user: User, permission: str) -> None:
        """Raise PermissionError if user lacks permission."""
        if not self.has_permission(user, permission):
            raise PermissionError(
                f"User '{user.username}' lacks permission '{permission}'"
            )

    def get_user_permissions(self, user: User) -> list[str]:
        """List all permissions granted to a user."""
        ...

# Usage:
auth.require_permission(current_user, "price.modify")
# If the user lacks the permission → PermissionError raised
```

---

## 六、UI 權限控制

根據角色顯示/隱藏功能：

```python
# CLI 或 GUI 層
if auth.has_permission(current_user, "quotation.view_cost"):
    show_cost_details()
else:
    show_selling_price_only()  # Sales 只看售價
```

| 功能 | Admin | Engineer | Sales | Viewer |
|---|---|---|---|---|
| 建立報價 | ✅ | ✅ | ✅ | ❌ |
| 查看成本明細 | ✅ | ✅ | ❌ | ❌ |
| 查看售價 | ✅ | ✅ | ✅ | ✅ |
| 修改價格(提交) | ✅ | ✅ | ❌ | ❌ |
| 審核發布 | ✅ | ❌ | ❌ | ❌ |
| 管理用戶 | ✅ | ❌ | ❌ | ❌ |
| 查看審計日誌 | ✅ | ❌ | ❌ | ❌ |

---

## 七、安全管理

- 權限配置文件 (roles.yaml, permissions.yaml) 存放在 SMB:/data/，由程序載入
- 修改權限配置需 system.config 權限（僅 Admin）
- 權限變更記錄到 Audit Log
- 內建角色 (is_system=true) 不可刪除

---

*本文件為 Phase 4 多人架構的一部分。*
