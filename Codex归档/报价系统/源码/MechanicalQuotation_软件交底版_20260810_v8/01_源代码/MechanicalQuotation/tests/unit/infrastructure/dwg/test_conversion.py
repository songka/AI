from __future__ import annotations

import subprocess
from pathlib import Path

import ezdxf
import pytest

from quotation.infrastructure.dwg.converter import (
    ConversionStatus,
    ConverterHealth,
    DwgConversionResult,
    DwgConversionService,
    DwgConverterAdapter,
    DwgConverterLocator,
    OdaDwgConverter,
)


def _write_valid_dxf(path: Path) -> None:
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0))
    msp.add_line((100, 0), (100, 50))
    msp.add_line((100, 50), (0, 50))
    msp.add_line((0, 50), (0, 0))
    msp.add_text("S50C", height=5).set_placement((5, 55))
    doc.saveas(path)


class FakeConverter(DwgConverterAdapter):
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode
        self.calls = 0

    @property
    def identity(self) -> str:
        return f"fake:{self.mode}"

    def health(self) -> ConverterHealth:
        if self.mode == "not_configured":
            return ConverterHealth(False, False, adapter="Fake", configuration_source="none")
        if self.mode == "unavailable":
            return ConverterHealth(True, False, adapter="Fake", configuration_source="test")
        return ConverterHealth(True, True, adapter="Fake", configuration_source="test")

    def convert(self, source_path, output_path, cancellation_check=None):
        self.calls += 1
        if self.mode == "mutate_source":
            source_path.write_bytes(b"adapter-mutated-staging-copy")
        if self.mode == "timeout":
            raise subprocess.TimeoutExpired("fake", 1)
        if self.mode == "failed":
            return DwgConversionResult(
                str(source_path), ConversionStatus.FAILED, adapter="Fake", error="模擬失敗"
            )
        if self.mode == "empty":
            output_path.write_bytes(b"")
        else:
            _write_valid_dxf(output_path)
        return DwgConversionResult(
            str(source_path),
            ConversionStatus.SUCCESS,
            converted_file=str(output_path),
            adapter="Fake",
            configuration_source="test",
        )


def _dwg(path: Path) -> Path:
    path.write_bytes(b"AC1027\x00fake-dwg-content")
    return path


def test_success_preserves_original_and_supports_chinese_space_path(tmp_path):
    source = _dwg(tmp_path / "中文 圖紙.dwg")
    before = source.read_bytes()
    service = DwgConversionService(FakeConverter(), tmp_path / "cache with space")
    result = service.convert(source)
    assert result.is_success
    assert Path(result.converted_file).is_file()
    assert source.read_bytes() == before
    assert result.cache_hit is False


def test_adapter_cannot_modify_original_dwg(tmp_path):
    source = _dwg(tmp_path / "protected.dwg")
    before = source.read_bytes()
    result = DwgConversionService(FakeConverter("mutate_source"), tmp_path / "cache").convert(
        source
    )
    assert result.is_success
    assert source.read_bytes() == before


def test_cache_avoids_second_conversion(tmp_path):
    source = _dwg(tmp_path / "cache.dwg")
    converter = FakeConverter()
    service = DwgConversionService(converter, tmp_path / "cache")
    first = service.convert(source)
    second = service.convert(source)
    assert first.is_success and second.is_success
    assert converter.calls == 1
    assert second.cache_hit is True
    assert first.converted_file == second.converted_file


def test_cleanup_deletes_only_generated_dxf_and_preserves_source(tmp_path):
    source = _dwg(tmp_path / "cleanup.dwg")
    service = DwgConversionService(FakeConverter(), tmp_path / "cache")
    result = service.convert(source)

    assert service.cleanup_converted_file(result) is True
    assert source.is_file()
    assert not Path(result.converted_file).exists()


def test_cleanup_rejects_file_outside_managed_conversion_directory(tmp_path):
    source = _dwg(tmp_path / "protected.dwg")
    unrelated = tmp_path / "unrelated.dxf"
    _write_valid_dxf(unrelated)
    service = DwgConversionService(FakeConverter(), tmp_path / "cache")
    forged = DwgConversionResult(
        source_file=str(source),
        status=ConversionStatus.SUCCESS,
        converted_file=str(unrelated),
    )

    with pytest.raises(ValueError, match="受控转换目录"):
        service.cleanup_converted_file(forged)
    assert unrelated.is_file()


def test_not_configured(tmp_path):
    result = DwgConversionService(FakeConverter("not_configured"), tmp_path / "cache").convert(
        _dwg(tmp_path / "a.dwg")
    )
    assert result.status == ConversionStatus.NOT_CONFIGURED
    assert "未配置" in result.error


def test_configured_but_unavailable(tmp_path):
    result = DwgConversionService(FakeConverter("unavailable"), tmp_path / "cache").convert(
        _dwg(tmp_path / "a.dwg")
    )
    assert result.status == ConversionStatus.UNAVAILABLE


def test_timeout_is_structured(tmp_path):
    result = DwgConversionService(FakeConverter("timeout"), tmp_path / "cache").convert(
        _dwg(tmp_path / "a.dwg")
    )
    assert result.status == ConversionStatus.TIMEOUT
    assert "超時" in result.error


def test_failure_is_structured(tmp_path):
    result = DwgConversionService(FakeConverter("failed"), tmp_path / "cache").convert(
        _dwg(tmp_path / "a.dwg")
    )
    assert result.status == ConversionStatus.FAILED
    assert result.error == "模擬失敗"


def test_empty_dxf_is_rejected(tmp_path):
    result = DwgConversionService(FakeConverter("empty"), tmp_path / "cache").convert(
        _dwg(tmp_path / "a.dwg")
    )
    assert result.status == ConversionStatus.EMPTY_DXF


def test_cancelled_before_adapter_runs(tmp_path):
    converter = FakeConverter()
    result = DwgConversionService(converter, tmp_path / "cache").convert(
        _dwg(tmp_path / "a.dwg"), cancellation_check=lambda: True
    )
    assert result.status == ConversionStatus.CANCELLED
    assert converter.calls == 0


def test_locator_priority_environment_then_user_settings(tmp_path, monkeypatch):
    settings = tmp_path / "user_settings.json"
    settings.write_text('{"dwg_converter_path": "settings.exe"}', encoding="utf-8")
    locator = DwgConverterLocator(settings, common_paths=())
    monkeypatch.setenv("MECHANICAL_QUOTATION_DWG_CONVERTER", str(tmp_path / "env.exe"))
    assert locator.locate().source == "environment"
    assert locator.locate().path == tmp_path / "env.exe"
    monkeypatch.delenv("MECHANICAL_QUOTATION_DWG_CONVERTER")
    assert locator.locate().source == "user_settings"
    assert locator.locate().path == (tmp_path / "settings.exe").resolve()


def test_locator_finds_per_user_oda_administrative_image(tmp_path, monkeypatch):
    monkeypatch.delenv("MECHANICAL_QUOTATION_DWG_CONVERTER", raising=False)
    executable = (
        tmp_path
        / "MechanicalQuotation"
        / "ODAFileConverter-27.1"
        / "ODAFileConverter.exe"
    )
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"signed-oda-placeholder")

    located = DwgConverterLocator(
        settings_path=tmp_path / "missing-settings.json",
        common_paths=(),
        local_appdata=tmp_path,
    ).locate()

    assert located.source == "local_appdata"
    assert located.path == executable


def test_oda_health_does_not_execute_converter(tmp_path):
    configured = OdaDwgConverter(tmp_path / "missing.exe", configuration_source="test")
    health = configured.health()
    assert health.configured is True
    assert health.available is False
    assert health.configuration_source == "test"
