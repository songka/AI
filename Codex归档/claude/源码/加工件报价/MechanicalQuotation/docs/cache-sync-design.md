# 機構2D自動報價系統 — Cache 同步設計

日期：2026-08-01
版本：V1.0

---

## 一、Cache 策略

| 資源 | 策略 | 說明 |
|---|---|---|
| 用戶資料 | 啟動時載入 + 定時刷新 | 變更頻率極低 |
| 規則文件 (published) | 版本號比對 | 只在新版本發布時更新 |
| 價格文件 (published) | 版本號比對 | 只在新版本發布時更新 |
| 歷史報價索引 | 增量同步 | 新報價追加到本地索引 |
| 審計日誌 | 不緩存 | 直接寫 SMB |

---

## 二、Cache Manifest

```json
{
  "cache_version": 5,
  "last_sync": "2026-08-01T10:30:00",
  "items": {
    "users": {
      "source_hash": "a1b2c3d4",
      "cached_at": "2026-08-01T10:30:00"
    },
    "rules": {
      "source_version": "RULES-2025-06-15-v2",
      "cached_at": "2026-08-01T10:30:00"
    },
    "prices": {
      "material_version": "MAT-2025-01-01-v1",
      "process_version": "PROC-2025-01-01-v1",
      "surface_version": "SURF-2025-01-01-v1",
      "cached_at": "2026-08-01T10:30:00"
    },
    "history_index": {
      "last_quote_id": "Q-2026-0801-00150",
      "cached_at": "2026-08-01T10:30:00"
    }
  }
}
```

---

## 三、同步流程

### 啟動時

```python
class CacheSyncService:
    """Manages local cache synchronization with SMB."""

    def startup_sync(self) -> SyncStatus:
        """
        1. 檢查 SMB 是否可訪問
        2. 比對本地 Cache Manifest 與 SMB 上的版本號
        3. 只下載變更的文件
        4. 更新 Cache Manifest
        5. 返回 SyncStatus
        """
        if not self._smb_accessible():
            return SyncStatus.OFFLINE_CACHE

        try:
            self._sync_users()
            self._sync_rules()
            self._sync_prices()
            self._sync_history_index()
            self._update_manifest()
            return SyncStatus.ONLINE
        except Exception as e:
            logger.error("Cache sync failed: %s", e)
            return SyncStatus.SYNC_ERROR
```

### 後台定時同步

```python
    def background_sync(self, interval_seconds: int = 60):
        """Run in a background thread, periodically check for updates."""
        while self._running:
            time.sleep(interval_seconds)
            try:
                self._check_for_updates()
            except Exception:
                logger.warning("Background sync failed, will retry")
```

---

## 四、更新通知

當 Admin 發布新版本後，更新 SMB 上的 `version.txt` 文件。Client 後台同步檢測到版本變更：

```python
def _check_for_updates(self):
    """Check SMB for version changes."""
    remote_version = self._read_smb_file("rules/published/version.txt")
    local_version = self._manifest["items"]["rules"]["source_version"]
    if remote_version != local_version:
        logger.info("New rules version detected: %s", remote_version)
        self._sync_rules()
        self._notify_user("規則已更新，已同步最新版本")
```

---

## 五、離線模式

```python
class OfflineMode:
    """Behavior when SMB is unavailable."""

    # 可用功能
    ALLOWED_ACTIONS = [
        "quotation.create",     # 使用 Cache 中的規則
        "quotation.view",       # 查看本地歷史
        "rule.view",            # 查看 Cache 中的規則
    ]

    # 不可用功能
    BLOCKED_ACTIONS = [
        "rule.modify",          # 無法提交變更
        "rule.approve",         # 無法審核
        "user.manage",          # 無法管理用戶
    ]
```

---

*本文件為 Phase 4 多人架構的一部分。*
