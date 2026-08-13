"""DWG to DXF Converter — wraps ODA File Converter."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from quotation.domain.import_result import ImportResult

logger = logging.getLogger("quotation.infrastructure.dxf.converter")

# Default ODA install paths to try
_ODA_SEARCH_PATHS = [
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\ODA\ODAFileConverter.exe",
]

# DWG magic bytes: "AC" + version digits
_DWG_MAGIC = b"AC"


class DwgConverter:
    """Convert DWG files to DXF using ODA File Converter."""

    def __init__(self, oda_path: str | None = None, timeout_seconds: int = 60):
        self._oda_path = oda_path or self._find_oda()
        self._timeout = timeout_seconds

    @property
    def is_available(self) -> bool:
        return self._oda_path is not None and Path(self._oda_path).exists()

    def convert(self, dwg_path: str | Path) -> ImportResult:
        """Convert a single DWG file to DXF.

        Returns ImportResult with converted_file pointing to the generated DXF.
        """
        import time

        dwg = Path(dwg_path)
        started = time.monotonic()

        result = ImportResult(
            source_file=str(dwg),
            source_format="DWG",
        )

        # 1) File existence check
        if not dwg.exists():
            result.import_status = "failed"
            result.errors.append(f"File not found: {dwg}")
            return result

        # 2) Format check
        dwg_check = self._check_dwg_format(dwg)
        if dwg_check:
            result.warnings.append(dwg_check)

        # 3) ODA availability
        if not self.is_available:
            result.import_status = "failed"
            result.errors.append(
                "ODA File Converter not found. "
                "Please install from https://www.opendesign.com/guestfiles/oda_file_converter"
            )
            return result

        # 4) Convert
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            conv_started = time.monotonic()

            try:
                success, stderr = self._run_oda(dwg, tmp_dir)
                result.conversion_duration_ms = (time.monotonic() - conv_started) * 1000

                if not success:
                    result.import_status = "failed"
                    result.errors.append(f"ODA conversion failed: {stderr}")
                    return result

                # Find the generated DXF
                dxf_files = list(tmp_dir.glob("*.dxf"))
                if not dxf_files:
                    result.import_status = "failed"
                    result.errors.append("ODA ran but no DXF file was generated")
                    return result

                result.converted_file = str(dxf_files[0])
                result.import_status = "success"

            except subprocess.TimeoutExpired:
                result.import_status = "failed"
                result.errors.append(f"ODA conversion timed out after {self._timeout}s")
            except FileNotFoundError:
                result.import_status = "failed"
                result.errors.append(f"ODA executable not found: {self._oda_path}")
            except Exception as e:
                result.import_status = "failed"
                result.errors.append(f"ODA conversion error: {e}")

        result.import_duration_ms = (time.monotonic() - started) * 1000
        return result

    # -- Internal --

    def _find_oda(self) -> str | None:
        """Search common install paths for ODAFileConverter.exe."""
        for path in _ODA_SEARCH_PATHS:
            if Path(path).exists():
                logger.info("Found ODA: %s", path)
                return path
        # Check PATH
        import shutil
        found = shutil.which("ODAFileConverter")
        if found:
            return found
        return None

    def _check_dwg_format(self, path: Path) -> str | None:
        """Check DWG file magic bytes. Returns warning string or None."""
        try:
            with open(path, "rb") as f:
                header = f.read(10)
            if not header.startswith(_DWG_MAGIC):
                return f"File does not appear to be a valid DWG (magic: {header[:6].hex()})"
            # Extract version
            version_str = header[2:6].decode("ascii", errors="replace").strip()
            if version_str < "1021":  # R2007 = AC1021
                return f"DWG version AC{version_str} is older than R2007 — may have issues"
        except Exception:
            return "Could not read DWG header"
        return None

    def _run_oda(self, dwg: Path, output_dir: Path) -> tuple[bool, str]:
        """Run ODA File Converter. Returns (success, stderr)."""
        cmd = [
            self._oda_path,
            str(dwg),
            str(output_dir),
            "ACAD2018", "DXF",   # out_version, out_format
            "0",                   # audit (0=no)
            "1",                   # recurse (1=no)
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self._timeout,
        )
        return proc.returncode == 0, proc.stderr.strip()
