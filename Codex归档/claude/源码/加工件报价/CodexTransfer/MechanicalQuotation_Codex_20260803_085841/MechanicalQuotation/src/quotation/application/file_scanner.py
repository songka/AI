"""File Scanner — external drawing file discovery and matching.

Scans directories for DWG/DXF/PDF files, normalizes drawing numbers,
and creates JobBundles for matched file groups.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Supported extensions
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {'.dxf', '.dwg', '.pdf'}
GEOMETRY_EXTENSIONS = {'.dxf', '.dwg'}
PDF_EXTENSIONS = {'.pdf'}
TEMP_PATTERNS = ('~$', '.tmp', '.bak', 'Thumbs.db', '.DS_Store')


# ---------------------------------------------------------------------------
# DrawingFile
# ---------------------------------------------------------------------------

@dataclass
class DrawingFile:
    """A single drawing file discovered by the scanner."""

    file_name: str
    full_path: Path
    extension: str
    drawing_number: str  # normalized
    is_geometry: bool
    is_pdf: bool

    @classmethod
    def from_path(cls, path: Path) -> DrawingFile | None:
        """Create from file path, returning None for unsupported/temp files."""
        fname = path.name
        for pattern in TEMP_PATTERNS:
            if pattern in fname:
                return None
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return None
        dn = normalize_drawing_number(path.stem)
        return cls(
            file_name=fname,
            full_path=path.resolve(),
            extension=ext,
            drawing_number=dn,
            is_geometry=ext in GEOMETRY_EXTENSIONS,
            is_pdf=ext in PDF_EXTENSIONS,
        )


# ---------------------------------------------------------------------------
# Match status
# ---------------------------------------------------------------------------

class MatchStatus:
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"
    DUPLICATE = "DUPLICATE"


# ---------------------------------------------------------------------------
# JobBundle
# ---------------------------------------------------------------------------

@dataclass
class JobBundle:
    """A group of files sharing the same normalized drawing number."""

    drawing_number: str
    files: list[DrawingFile] = field(default_factory=list)
    match_status: str = MatchStatus.UNMATCHED

    @property
    def geometry_source(self) -> DrawingFile | None:
        """Primary geometry source (DWG preferred over DXF)."""
        dwg = [f for f in self.files if f.extension == '.dwg']
        if dwg:
            return dwg[0]
        dxf = [f for f in self.files if f.extension == '.dxf']
        return dxf[0] if dxf else None

    @property
    def pdf_sources(self) -> list[DrawingFile]:
        return [f for f in self.files if f.extension == '.pdf']

    @property
    def supplementary_sources(self) -> list[DrawingFile]:
        """All non-geometry sources (PDFs)."""
        return [f for f in self.files if not f.is_geometry]

    @property
    def has_geometry(self) -> bool:
        return self.geometry_source is not None

    @property
    def file_count(self) -> int:
        return len(self.files)


# ---------------------------------------------------------------------------
# Drawing number normalization
# ---------------------------------------------------------------------------

def normalize_drawing_number(raw: str) -> str:
    """Normalize a drawing number for consistent matching.

    Handles:
    - Case insensitivity
    - Fullwidth/halfwidth characters
    - Whitespace trimming
    - Hyphen/underscore/space equivalence
    - Common revision suffixes (REV-A, REV01, R01, V1, VERSION)
    """
    s = raw.strip()
    # Fullwidth to halfwidth
    s = unicodedata.normalize('NFKC', s)
    # Lowercase
    s = s.lower()
    # Remove revision suffixes
    s = re.sub(r'[-_\s]*rev[-_\s]*[a-z0-9]+$', '', s)
    s = re.sub(r'[-_\s]*r\d+$', '', s)
    s = re.sub(r'[-_\s]*v\d+$', '', s)
    s = re.sub(r'[-_\s]*version[-_\s]*\d+$', '', s)
    # Normalize separators to hyphens
    s = re.sub(r'[\s_]+', '-', s)
    # Collapse multiple hyphens
    s = re.sub(r'-+', '-', s)
    # Trim trailing hyphens
    s = s.strip('-')
    return s


# ---------------------------------------------------------------------------
# FileScanner
# ---------------------------------------------------------------------------

class FileScanner:
    """Scan directories for drawing files and create matched job bundles."""

    def scan_single_file(self, file_path: Path) -> JobBundle:
        """Scan a single file and auto-match related files in its directory."""
        df = DrawingFile.from_path(file_path)
        if df is None:
            ext = file_path.suffix.lower()
            return JobBundle(
                drawing_number=file_path.stem,
                match_status=MatchStatus.UNMATCHED,
            )

        # Search for related files in the same directory
        parent = file_path.parent
        related = self._find_related(parent, df.drawing_number, exclude=file_path)

        files = [df] + related
        status = MatchStatus.MATCHED if len(related) > 0 else MatchStatus.UNMATCHED
        return JobBundle(
            drawing_number=df.drawing_number,
            files=files,
            match_status=status,
        )

    def scan_directory(self, directory: Path, recursive: bool = True) -> list[JobBundle]:
        """Scan a directory and group files by normalized drawing number."""
        all_files: list[DrawingFile] = []
        pattern = "**/*" if recursive else "*"
        for path in directory.glob(pattern):
            if path.is_file():
                df = DrawingFile.from_path(path)
                if df is not None:
                    all_files.append(df)

        # Group by drawing number
        groups: dict[str, list[DrawingFile]] = {}
        for df in all_files:
            groups.setdefault(df.drawing_number, []).append(df)

        # Create bundles
        bundles: list[JobBundle] = []
        seen_full_paths: set[str] = set()

        for dn, files in groups.items():
            # Check for duplicates (same extension, same drawing number)
            deduped: list[DrawingFile] = []
            ext_seen: set[str] = set()
            for f in files:
                key = f"{f.extension}:{f.file_name.lower()}"
                if key in ext_seen:
                    # Mark as duplicate but still include paths for reporting
                    continue
                ext_seen.add(key)
                deduped.append(f)
                seen_full_paths.add(str(f.full_path))

            status = MatchStatus.MATCHED if len(deduped) > 1 else MatchStatus.UNMATCHED
            bundles.append(JobBundle(
                drawing_number=dn,
                files=deduped,
                match_status=status,
            ))

        return bundles

    def _find_related(
        self, directory: Path, drawing_number: str, exclude: Path,
    ) -> list[DrawingFile]:
        """Find files with the same normalized drawing number in a directory."""
        related: list[DrawingFile] = []
        for path in directory.iterdir():
            if path.is_file() and path != exclude:
                df = DrawingFile.from_path(path)
                if df is not None and df.drawing_number == drawing_number:
                    related.append(df)
        return related
