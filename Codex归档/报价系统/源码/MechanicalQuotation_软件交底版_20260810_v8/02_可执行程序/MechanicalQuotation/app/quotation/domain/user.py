"""User, role and in-memory desktop session models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class UserRole(str, Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    SALES = "sales"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"


@dataclass
class User:
    user_id: str
    username: str
    password_hash: str
    display_name: str
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    created_time: str = ""
    created_by: str | None = None
    last_login_time: str | None = None
    failed_attempts: int = 0
    locked_until: str | None = None
    must_change_password: bool = False
    password_history: list[str] = field(default_factory=list)
    password_changed_time: str | None = None
    assigned_permissions: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["role"] = self.role.value
        payload["status"] = self.status.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "User":
        values = dict(payload)
        values["role"] = UserRole(values.get("role", UserRole.VIEWER.value))
        values["status"] = UserStatus(values.get("status", UserStatus.ACTIVE.value))
        return cls(**values)


@dataclass(frozen=True)
class UserSession:
    session_id: str
    user_id: str
    username: str
    display_name: str
    role: UserRole
    permissions: tuple[str, ...]
    created_at: str
    last_activity_at: str
    expires_at: str
    is_active: bool = True
