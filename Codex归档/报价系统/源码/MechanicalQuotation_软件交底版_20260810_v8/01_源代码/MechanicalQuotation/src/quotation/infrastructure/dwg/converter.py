"""Safe, pluggable DWG-to-DXF conversion.

The quotation system never parses DWG binary data itself.  A configured external
converter produces a DXF in a managed cache; the existing DXF reader then owns all
parsing.  No converter is downloaded or bundled by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "runtime" / "config" / "user_settings.json"
PORTABLE_SETTINGS_PATH = PROJECT_ROOT / "config" / "user_settings.json"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "runtime" / "cache" / "dwg"

_COMMON_ODA_PATHS = (
    Path(r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe"),
    Path(r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe"),
    Path(r"C:\ODA\ODAFileConverter.exe"),
)


class ConversionStatus:
    SUCCESS = "SUCCESS"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"
    EMPTY_DXF = "EMPTY_DXF"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ConverterLocation:
    path: Path | None
    source: str

    @property
    def configured(self) -> bool:
        return self.path is not None


@dataclass(frozen=True)
class ConverterHealth:
    configured: bool
    available: bool
    adapter: str = "ODA File Converter"
    configuration_source: str = "none"
    executable_path: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "available": self.available,
            "adapter": self.adapter,
            "configuration_source": self.configuration_source,
            "executable_path": self.executable_path,
            "message": self.message,
        }


@dataclass
class DwgConversionResult:
    source_file: str
    status: str
    converted_file: str | None = None
    adapter: str = ""
    configuration_source: str = ""
    cache_hit: bool = False
    duration_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == ConversionStatus.SUCCESS and self.converted_file is not None

    def to_trace(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "status": self.status,
            "converted_file": self.converted_file,
            "adapter": self.adapter,
            "configuration_source": self.configuration_source,
            "cache_hit": self.cache_hit,
            "duration_ms": round(self.duration_ms, 1),
            "warnings": list(self.warnings),
            "error": self.error,
            "original_preserved": True,
        }


class DwgConverterLocator:
    """Resolve the converter using the documented priority order."""

    def __init__(
        self,
        settings_path: str | Path | None = None,
        common_paths: tuple[Path, ...] = _COMMON_ODA_PATHS,
        local_appdata: str | Path | None = None,
    ) -> None:
        self._settings_paths = (
            (Path(settings_path),)
            if settings_path is not None
            else (PORTABLE_SETTINGS_PATH, DEFAULT_SETTINGS_PATH)
        )
        self._common_paths = common_paths
        local_value = (
            str(local_appdata)
            if local_appdata is not None
            else os.environ.get("LOCALAPPDATA", "").strip()
        )
        self._local_appdata = Path(local_value) if local_value else None

    def locate(self) -> ConverterLocation:
        env_value = os.environ.get("MECHANICAL_QUOTATION_DWG_CONVERTER", "").strip()
        if env_value:
            return ConverterLocation(Path(env_value.strip('"')), "environment")

        configured = self._read_settings_path()
        if configured:
            return ConverterLocation(configured, "user_settings")

        for candidate in self._common_paths:
            if candidate.is_file():
                return ConverterLocation(candidate, "windows_common_path")

        # The official MSI may be extracted as a per-user administrative image
        # when the operator does not have machine-wide installation rights.
        # Only accept the expected executable below our own LocalAppData folder;
        # do not search arbitrary executables or treat interactive CAD as a
        # headless converter.
        if self._local_appdata is not None:
            install_root = self._local_appdata / "MechanicalQuotation"
            candidates = sorted(
                install_root.glob("ODAFileConverter-*/ODAFileConverter.exe"),
                reverse=True,
            )
            for candidate in candidates:
                if candidate.is_file():
                    return ConverterLocation(candidate, "local_appdata")

        found = shutil.which("ODAFileConverter")
        if found:
            return ConverterLocation(Path(found), "PATH")
        return ConverterLocation(None, "none")

    def _read_settings_path(self) -> Path | None:
        for settings_path in self._settings_paths:
            configured = self._read_one_settings_path(settings_path)
            if configured is not None:
                return configured
        return None

    @staticmethod
    def _read_one_settings_path(settings_path: Path) -> Path | None:
        if not settings_path.is_file():
            return None
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None

        values = (
            data.get("dwg_converter_path"),
            (data.get("dwg_converter") or {}).get("path")
            if isinstance(data.get("dwg_converter"), dict)
            else None,
            (data.get("dwg") or {}).get("converter_path")
            if isinstance(data.get("dwg"), dict)
            else None,
        )
        for value in values:
            if isinstance(value, str) and value.strip():
                path = Path(value.strip()).expanduser()
                if not path.is_absolute():
                    path = (settings_path.parent / path).resolve()
                return path
        return None


class DwgConverterAdapter(ABC):
    """Adapter contract for external DWG converters."""

    @property
    @abstractmethod
    def identity(self) -> str:
        """Stable identity used to isolate cache entries."""

    @abstractmethod
    def health(self) -> ConverterHealth:
        """Return configuration and availability without executing the converter."""

    @abstractmethod
    def convert(
        self,
        source_path: Path,
        output_path: Path,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> DwgConversionResult:
        """Convert one source without modifying it."""


class OdaDwgConverter(DwgConverterAdapter):
    """ODA File Converter adapter.  The ODA binary is supplied by the operator."""

    def __init__(
        self,
        executable_path: str | Path | None = None,
        *,
        configuration_source: str = "explicit",
        timeout_seconds: float = 60.0,
        locator: DwgConverterLocator | None = None,
    ) -> None:
        if executable_path is None:
            located = (locator or DwgConverterLocator()).locate()
            self._path = located.path
            self._source = located.source
        else:
            self._path = Path(executable_path)
            self._source = configuration_source
        self._timeout = timeout_seconds

    @property
    def identity(self) -> str:
        return f"oda:{self._path or 'unconfigured'}"

    def health(self) -> ConverterHealth:
        configured = self._path is not None
        available = bool(self._path and self._path.is_file())
        if not configured:
            message = "未配置DWG轉換器"
        elif not available:
            message = "已配置的DWG轉換器不可用"
        else:
            message = "DWG轉換器可用"
        return ConverterHealth(
            configured=configured,
            available=available,
            configuration_source=self._source,
            executable_path=str(self._path) if self._path else None,
            message=message,
        )

    def convert(
        self,
        source_path: Path,
        output_path: Path,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> DwgConversionResult:
        started = time.monotonic()
        health = self.health()
        base = DwgConversionResult(
            source_file=str(source_path),
            status=ConversionStatus.FAILED,
            adapter=health.adapter,
            configuration_source=health.configuration_source,
        )
        if not health.configured:
            base.status = ConversionStatus.NOT_CONFIGURED
            base.error = "未配置DWG轉換器，請在環境變數或使用者設定中指定"
            return base
        if not health.available:
            base.status = ConversionStatus.UNAVAILABLE
            base.error = "已配置的DWG轉換器不存在或無法執行"
            return base
        if cancellation_check and cancellation_check():
            base.status = ConversionStatus.CANCELLED
            base.error = "DWG轉換已取消"
            return base

        work = output_path.parent / f".work-{uuid.uuid4().hex}"
        input_dir = work / "input"
        output_dir = work / "output"
        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir(parents=True, exist_ok=False)
        staged_source = input_dir / source_path.name
        shutil.copy2(source_path, staged_source)

        command = [
            str(self._path),
            str(input_dir),
            str(output_dir),
            "ACAD2018",
            "DXF",
            "0",
            "1",
            "*.DWG",
        ]
        proc: subprocess.Popen[str] | None = None
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            while proc.poll() is None:
                if cancellation_check and cancellation_check():
                    proc.kill()
                    proc.communicate()
                    base.status = ConversionStatus.CANCELLED
                    base.error = "DWG轉換已取消"
                    return base
                if time.monotonic() - started > self._timeout:
                    proc.kill()
                    proc.communicate()
                    base.status = ConversionStatus.TIMEOUT
                    base.error = f"DWG轉換超時（{self._timeout:g}秒）"
                    return base
                time.sleep(0.05)

            _stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                base.status = ConversionStatus.FAILED
                detail = stderr.strip()[:500]
                base.error = "DWG轉換器執行失敗" + (f"：{detail}" if detail else "")
                return base

            candidates = list(output_dir.rglob(f"{source_path.stem}.dxf"))
            if not candidates:
                candidates = list(output_dir.rglob("*.dxf"))
            if not candidates:
                base.status = ConversionStatus.FAILED
                base.error = "DWG轉換器未產生DXF文件"
                return base
            if candidates[0].stat().st_size == 0:
                base.status = ConversionStatus.EMPTY_DXF
                base.error = "DWG轉換器產生空白DXF文件"
                return base

            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidates[0], output_path)
            base.status = ConversionStatus.SUCCESS
            base.converted_file = str(output_path)
            return base
        except OSError as exc:
            base.status = ConversionStatus.FAILED
            base.error = f"DWG轉換器啟動失敗：{exc}"
            return base
        finally:
            base.duration_ms = (time.monotonic() - started) * 1000
            shutil.rmtree(work, ignore_errors=True)


class DwgConversionService:
    """Cache and validate adapter output before handing it to the DXF parser."""

    def __init__(
        self,
        converter: DwgConverterAdapter | None = None,
        cache_dir: str | Path = DEFAULT_CACHE_DIR,
    ) -> None:
        self._converter = converter or OdaDwgConverter()
        self._cache_dir = Path(cache_dir)

    def health(self) -> dict[str, Any]:
        data = self._converter.health().to_dict()
        data["cache_directory"] = str(self._cache_dir)
        return data

    def cleanup_converted_file(self, result: DwgConversionResult) -> bool:
        """Delete a generated DXF after its caller has finished parsing it."""
        if not result.converted_file:
            return False
        converted = Path(result.converted_file)
        try:
            resolved = converted.resolve()
            cache_root = self._cache_dir.resolve()
            source = Path(result.source_file).resolve()
        except OSError:
            return False
        if (
            resolved == source
            or resolved.suffix.casefold() != ".dxf"
            or not resolved.is_relative_to(cache_root)
        ):
            raise ValueError("拒绝删除不属于受控转换目录的文件")
        existed = resolved.is_file()
        resolved.unlink(missing_ok=True)
        return existed

    def convert(
        self,
        source_path: str | Path,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> DwgConversionResult:
        started = time.monotonic()
        source = Path(source_path)
        health = self._converter.health()

        if not source.is_file():
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.FAILED,
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                error="找不到DWG來源文件",
            )
        if cancellation_check and cancellation_check():
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.CANCELLED,
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                error="DWG轉換已取消",
            )
        if not health.configured:
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.NOT_CONFIGURED,
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                error="未配置DWG轉換器，請設定 MECHANICAL_QUOTATION_DWG_CONVERTER",
            )
        if not health.available:
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.UNAVAILABLE,
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                error="已配置的DWG轉換器不存在或無法執行",
            )

        digest = hashlib.sha256()
        with source.open("rb") as source_stream:
            for chunk in iter(lambda: source_stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(self._converter.identity.encode("utf-8"))
        digest.update(b"dwg-cache-v1")
        cache_key = digest.hexdigest()
        cached = self._cache_dir / f"{cache_key}.dxf"
        if cached.is_file() and cached.stat().st_size > 0:
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.SUCCESS,
                converted_file=str(cached),
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                cache_hit=True,
                duration_ms=(time.monotonic() - started) * 1000,
            )

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        pending = self._cache_dir / f".{cache_key}-{uuid.uuid4().hex}.dxf"
        source_stage = self._cache_dir / f".source-{uuid.uuid4().hex}"
        try:
            source_stage.mkdir(parents=True, exist_ok=False)
            staged_source = source_stage / source.name
            shutil.copy2(source, staged_source)
            result = self._converter.convert(staged_source, pending, cancellation_check)
            result.source_file = str(source)
            if not result.is_success:
                return result
            if not pending.is_file() or pending.stat().st_size == 0:
                return DwgConversionResult(
                    source_file=str(source),
                    status=ConversionStatus.EMPTY_DXF,
                    adapter=health.adapter,
                    configuration_source=health.configuration_source,
                    duration_ms=(time.monotonic() - started) * 1000,
                    error="DWG轉換器產生空白DXF文件",
                )
            pending.replace(cached)
            result.converted_file = str(cached)
            result.duration_ms = (time.monotonic() - started) * 1000
            return result
        except subprocess.TimeoutExpired:
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.TIMEOUT,
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                duration_ms=(time.monotonic() - started) * 1000,
                error="DWG轉換超時",
            )
        except Exception as exc:
            return DwgConversionResult(
                source_file=str(source),
                status=ConversionStatus.FAILED,
                adapter=health.adapter,
                configuration_source=health.configuration_source,
                duration_ms=(time.monotonic() - started) * 1000,
                error=f"DWG轉換失敗：{exc}",
            )
        finally:
            pending.unlink(missing_ok=True)
            shutil.rmtree(source_stage, ignore_errors=True)


class DwgConverter:
    """Backward-compatible facade for the original public converter API.

    New code should inject a :class:`DwgConverterAdapter` into
    :class:`DwgConversionService`.  The facade keeps existing callers working
    while gaining persistent output and structured conversion behavior.
    """

    def __init__(
        self,
        oda_path: str | Path | None = None,
        timeout_seconds: float = 60.0,
        cache_dir: str | Path = DEFAULT_CACHE_DIR,
    ) -> None:
        self._adapter = OdaDwgConverter(
            oda_path,
            configuration_source="explicit" if oda_path else "auto",
            timeout_seconds=timeout_seconds,
        )
        self._service = DwgConversionService(self._adapter, cache_dir)

    @property
    def is_available(self) -> bool:
        return self._adapter.health().available

    def health(self) -> ConverterHealth:
        return self._adapter.health()

    def convert(self, dwg_path: str | Path):
        from quotation.domain.import_result import ImportResult

        converted = self._service.convert(dwg_path)
        result = ImportResult(
            source_file=str(dwg_path),
            source_format="DWG",
            import_status="success" if converted.is_success else "failed",
            converted_file=converted.converted_file,
            warnings=converted.warnings,
            conversion_duration_ms=converted.duration_ms,
            import_duration_ms=converted.duration_ms,
        )
        if converted.error:
            result.errors.append(converted.error)
        return result
