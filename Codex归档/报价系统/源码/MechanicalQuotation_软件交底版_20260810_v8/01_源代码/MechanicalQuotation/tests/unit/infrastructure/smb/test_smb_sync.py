from __future__ import annotations

import json
from pathlib import Path

import pytest

from quotation.application.cache_sync_service import CacheSyncService, SyncStatus
from quotation.infrastructure.smb.client import SmbStorageClient, cached_public_path


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_public_slot_initialization_creates_expected_layout(tmp_path):
    root = tmp_path / "公共槽"
    client = SmbStorageClient(root)

    result = client.initialize_layout()

    assert result["available"] is True
    assert (root / "data").is_dir()
    assert (root / "rules" / "published").is_dir()
    assert (root / "prices" / "published").is_dir()
    assert (root / "change-requests").is_dir()
    assert (root / "audit").is_dir()
    manifest = json.loads((root / "system-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1


def test_client_rejects_paths_outside_public_slot(tmp_path):
    client = SmbStorageClient(tmp_path / "公共槽")

    with pytest.raises(ValueError, match="公共槽"):
        client.resolve("../secret.txt")
    with pytest.raises(ValueError, match="公共槽"):
        client.resolve(str(tmp_path / "absolute.txt"))


def test_sync_copies_only_changed_published_files_and_records_manifest(tmp_path):
    root = tmp_path / "公共槽"
    cache = tmp_path / "cache"
    client = SmbStorageClient(root)
    client.initialize_layout()
    _write(root / "rules" / "published" / "quotation-rules.yaml", "version: 1\n")
    _write(root / "prices" / "published" / "current-version-pointer.json", '{"v": 1}')
    service = CacheSyncService(client, cache)

    first = service.sync()
    second = service.sync()
    _write(root / "prices" / "published" / "current-version-pointer.json", '{"v": 2}')
    third = service.sync()

    assert first.status == SyncStatus.ONLINE
    assert first.changed_files == 2
    assert second.changed_files == 0
    assert third.changed_files == 1
    assert (cache / "rules" / "published" / "quotation-rules.yaml").is_file()
    assert json.loads(
        (cache / "prices" / "published" / "current-version-pointer.json").read_text(
            encoding="utf-8"
        )
    ) == {"v": 2}
    manifest = json.loads((cache / "cache-manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_root"] == str(root)
    assert len(manifest["files"]) == 2


def test_offline_sync_preserves_existing_cache(tmp_path):
    root = tmp_path / "公共槽"
    cache = tmp_path / "cache"
    client = SmbStorageClient(root)
    client.initialize_layout()
    _write(root / "rules" / "published" / "quotation-rules.yaml", "version: 1\n")
    service = CacheSyncService(client, cache)
    assert service.sync().status == SyncStatus.ONLINE
    root.rename(tmp_path / "公共槽-离线")

    result = service.sync()

    assert result.status == SyncStatus.OFFLINE_CACHE
    assert result.using_cache is True
    assert (cache / "rules" / "published" / "quotation-rules.yaml").is_file()


def test_health_distinguishes_online_and_offline_roots(tmp_path):
    missing = SmbStorageClient(tmp_path / "missing")
    online_root = tmp_path / "online"
    online_root.mkdir()
    online = SmbStorageClient(online_root)

    assert missing.health()["available"] is False
    assert online.health()["available"] is True


def test_cached_public_path_prefers_synced_file_and_honors_disabled_setting(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    fallback = tmp_path / "data" / "current-version-pointer.json"
    cached = tmp_path / "cache" / "prices" / "published" / fallback.name
    _write(fallback, '{"source": "local"}')
    _write(cached, '{"source": "smb-cache"}')
    settings = tmp_path / "config" / "user_settings.json"
    _write(
        settings,
        json.dumps(
            {
                "smb_cache_dir": str(tmp_path / "cache"),
                "smb_sync_enabled": True,
            }
        ),
    )

    assert cached_public_path("prices/published/current-version-pointer.json", fallback) == cached
    settings.write_text(
        json.dumps({"smb_cache_dir": str(tmp_path / "cache"), "smb_sync_enabled": False}),
        encoding="utf-8",
    )
    assert cached_public_path("prices/published/current-version-pointer.json", fallback) == fallback


def test_bootstrap_places_approved_project_data_without_overwriting(tmp_path):
    project = tmp_path / "project"
    root = tmp_path / "公共槽"
    _write(
        project / "data" / "current-version-pointer.json",
        json.dumps(
            {
                "current_version": "PRICE-V1",
                "snapshot_path": "pricebook.json",
            }
        ),
    )
    _write(project / "data" / "pricebook.json", '{"status": "PUBLISHED"}')
    _write(project / "data" / "feature-price-calibration-gcs-v1.0.json", '{"v": 1}')
    _write(project / "rules" / "quotation-rules.yaml", "version: 1\n")
    _write(
        project
        / "rules"
        / "imports"
        / "r01-v1.0"
        / "pricing-rules-excel-r01-v1.0.json",
        '{"records": []}',
    )
    client = SmbStorageClient(root)

    first = client.bootstrap_published_data(project)
    second = client.bootstrap_published_data(project)

    assert first["price_version"] == "PRICE-V1"
    assert len(first["copied"]) == 6
    assert len(second["skipped_existing"]) == 6
    assert (root / "prices" / "published" / "pricebook.json").is_file()
