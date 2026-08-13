from __future__ import annotations

import json

import pytest

from quotation.application.settings_service import UserSettingsService


def test_settings_round_trip_contains_no_secret(tmp_path):
    converter = tmp_path / "ODAFileConverter.exe"
    converter.write_bytes(b"converter")
    settings = tmp_path / "user_settings.json"
    service = UserSettingsService(settings)

    saved = service.save(
        dwg_converter_path=str(converter),
        api_host="127.0.0.1",
        api_port=8000,
        smb_root=str(tmp_path / "公共槽"),
        smb_cache_dir=str(tmp_path / "cache"),
        smb_sync_enabled=True,
        database_address=str(tmp_path / "database"),
    )

    assert saved == settings
    assert service.load()["dwg_converter_path"] == str(converter)
    assert service.load()["smb_root"] == str(tmp_path / "公共槽")
    assert service.load()["smb_sync_enabled"] is True
    assert service.load()["database_address"] == str(tmp_path / "database")
    payload = json.loads(settings.read_text(encoding="utf-8"))
    assert not any("key" in key.casefold() or "secret" in key.casefold() for key in payload)


def test_settings_rejects_non_oda_executable_and_public_bind(tmp_path):
    executable = tmp_path / "ZWCAD.EXE"
    executable.write_bytes(b"cad")
    service = UserSettingsService(tmp_path / "user_settings.json")

    with pytest.raises(ValueError, match="ODAFileConverter"):
        service.save(dwg_converter_path=str(executable), api_host="127.0.0.1", api_port=8000)
    with pytest.raises(ValueError, match="本机数据安全"):
        service.save(dwg_converter_path="", api_host="0.0.0.0", api_port=8000)


def test_settings_defaults_are_local_only(tmp_path):
    loaded = UserSettingsService(tmp_path / "missing.json").load()

    assert loaded == {
        "dwg_converter_path": "",
        "api_host": "127.0.0.1",
        "api_port": 8000,
        "smb_root": (
            r"\\10.97.0.210\lfaf_Engineer\Mechanical\3-標準文檔"
            r"\10-自動報價系統\data"
        ),
        "smb_cache_dir": "runtime/cache/smb",
        "smb_sync_enabled": True,
        "smb_sync_interval_seconds": 60,
        "auth_enabled": False,
        "database_address": "runtime/data/quotation_history.db",
    }


def test_database_address_accepts_local_file_and_shared_or_directory_form(tmp_path):
    service = UserSettingsService(tmp_path / "user_settings.json")

    service.save(
        dwg_converter_path="",
        api_host="127.0.0.1",
        api_port=8000,
        database_address=str(tmp_path / "quotes.db"),
    )
    assert service.load()["database_address"].endswith("quotes.db")
