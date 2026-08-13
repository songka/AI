"""Convert native SOLIDWORKS parts/drawings to DXF through licensed SOLIDWORKS COM."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from quotation.infrastructure.dwg.converter import (
    ConversionStatus,
    DwgConversionResult,
    DEFAULT_CACHE_DIR,
)


class SolidWorksConversionService:
    """Headless SOLIDWORKS SaveAs adapter; source files remain read-only."""

    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR / "solidworks") -> None:
        self._cache_dir = Path(cache_dir)
        self._script = Path(__file__).with_name("convert_to_dxf.ps1")

    @staticmethod
    def is_available() -> bool:
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"SldWorks.Application\CLSID"):
                return True
        except (OSError, ImportError):
            return False

    def health(self) -> dict[str, object]:
        available = self.is_available()
        return {
            "configured": available,
            "available": available,
            "adapter": "SOLIDWORKS COM",
            "message": "SOLIDWORKS 自动化接口可用" if available else "未安装 SOLIDWORKS 或 COM 接口未注册",
        }

    def cleanup_converted_file(self, result: DwgConversionResult) -> bool:
        """Delete a generated DXF while protecting the original SOLIDWORKS file."""
        if not result.converted_file:
            return False
        converted = Path(result.converted_file)
        resolved = converted.resolve()
        if (
            resolved == Path(result.source_file).resolve()
            or resolved.suffix.casefold() != ".dxf"
            or not resolved.is_relative_to(self._cache_dir.resolve())
        ):
            raise ValueError("拒绝删除不属于受控转换目录的文件")
        existed = resolved.is_file()
        resolved.unlink(missing_ok=True)
        return existed

    def convert(self, source_path: str | Path) -> DwgConversionResult:
        source = Path(source_path)
        base = DwgConversionResult(
            source_file=str(source), status=ConversionStatus.FAILED,
            adapter="SOLIDWORKS COM", configuration_source="windows_com",
        )
        if source.suffix.lower() not in {".slddrw", ".sldprt"}:
            base.error = f"不支持的 SOLIDWORKS 文件类型：{source.suffix}"
            return base
        if not source.is_file():
            base.error = "找不到 SOLIDWORKS 来源文件"
            return base
        if not self.is_available():
            base.status = ConversionStatus.NOT_CONFIGURED
            base.error = "本机未安装或未注册 SOLIDWORKS；原生 SLD 文件必须通过合法 SOLIDWORKS 自动化接口转换"
            return base
        digest = hashlib.sha256(source.read_bytes() + b"solidworks-dxf-v1").hexdigest()
        target = self._cache_dir / f"{digest}.dxf"
        if target.is_file() and target.stat().st_size > 0:
            base.status = ConversionStatus.SUCCESS
            base.converted_file = str(target)
            base.cache_hit = True
            return base
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        pending = self._cache_dir / f".{digest}.dxf"
        try:
            completed = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(self._script), "-SourcePath", str(source.resolve()),
                    "-OutputPath", str(pending.resolve()),
                ],
                capture_output=True, text=True, timeout=120, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode != 0 or not pending.is_file() or pending.stat().st_size == 0:
                base.error = (completed.stderr or completed.stdout or "SOLIDWORKS 转换失败").strip()[:500]
                return base
            pending.replace(target)
            base.status = ConversionStatus.SUCCESS
            base.converted_file = str(target)
            return base
        except (OSError, subprocess.TimeoutExpired) as exc:
            base.error = f"SOLIDWORKS 转换失败：{exc}"
            return base
        finally:
            pending.unlink(missing_ok=True)
