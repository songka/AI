"""File Scanner — external drawing file discovery and matching.

Scans directories for supported CAD files, normalizes drawing numbers,
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

SUPPORTED_EXTENSIONS = {'.dxf', '.dwg', '.slddrw', '.sldprt'}
GEOMETRY_EXTENSIONS = {'.dxf', '.dwg', '.slddrw', '.sldprt'}
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
    preferred_input_path: Path | None = None

    @property
    def geometry_source(self) -> DrawingFile | None:
        """Return the explicitly selected geometry, otherwise use format priority."""
        if self.preferred_input_path is not None:
            preferred = self.preferred_input_path.resolve()
            for drawing_file in self.files:
                if drawing_file.full_path == preferred:
                    return drawing_file if drawing_file.is_geometry else None
            return None

        for extension in ('.dwg', '.dxf', '.slddrw', '.sldprt'):
            candidates = [f for f in self.files if f.extension == extension]
            if candidates:
                return candidates[0]
        return None

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
            preferred_input_path=df.full_path,
        )

    def scan_selected_files(self, file_paths: list[Path]) -> list[JobBundle]:
        """Group explicitly selected files without allowing unselected sidecars to win.

        A sole selected geometry is always preferred.  When the user explicitly
        selects multiple geometry files with the same drawing number, the bundle's
        normal DWG/DXF/SolidWorks format priority applies among those selections.
        """
        groups: dict[str, list[DrawingFile]] = {}
        for file_path in file_paths:
            drawing_file = DrawingFile.from_path(file_path)
            if drawing_file is not None:
                groups.setdefault(drawing_file.drawing_number, []).append(drawing_file)

        bundles: list[JobBundle] = []
        for drawing_number, files in groups.items():
            geometry_files = [drawing_file for drawing_file in files if drawing_file.is_geometry]
            preferred = geometry_files[0].full_path if len(geometry_files) == 1 else None
            bundles.append(JobBundle(
                drawing_number=drawing_number,
                files=files,
                match_status=(
                    MatchStatus.MATCHED if len(files) > 1 else MatchStatus.UNMATCHED
                ),
                preferred_input_path=preferred,
            ))
        return bundles

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
