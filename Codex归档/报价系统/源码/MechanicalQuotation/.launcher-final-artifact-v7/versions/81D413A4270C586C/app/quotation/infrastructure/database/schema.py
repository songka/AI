"""SQLite schema for quotation history database."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- Historical parts table
CREATE TABLE IF NOT EXISTS historical_parts (
    id TEXT PRIMARY KEY,
    part_no TEXT NOT NULL,
    part_code TEXT,
    part_name TEXT,

    material TEXT,
    material_raw TEXT,

    overall_length REAL DEFAULT 0,
    overall_width REAL DEFAULT 0,
    overall_height REAL DEFAULT 0,
    dimensions_raw TEXT,

    weight_kg REAL,
    volume_mm3 REAL,

    hole_count INTEGER DEFAULT 0,
    thread_specs TEXT,          -- JSON array
    contour_type TEXT,

    surface_treatment TEXT,
    surface_raw TEXT,

    process_hint TEXT,
    tolerance_grade TEXT,

    historical_price REAL DEFAULT 0,
    price_source TEXT DEFAULT 'BOM',
    price_date TEXT,

    source_bom TEXT,
    source_bom_row INTEGER DEFAULT 0,
    source_dwg TEXT,
    source_pdf TEXT,

    project_name TEXT,

    created_at TEXT,
    updated_at TEXT
);

-- Index for similarity search
CREATE INDEX IF NOT EXISTS idx_hist_material
    ON historical_parts(material);
CREATE INDEX IF NOT EXISTS idx_hist_surface
    ON historical_parts(surface_treatment);
CREATE INDEX IF NOT EXISTS idx_hist_contour
    ON historical_parts(contour_type);
CREATE INDEX IF NOT EXISTS idx_hist_part_no
    ON historical_parts(part_no);
CREATE INDEX IF NOT EXISTS idx_hist_project
    ON historical_parts(project_name);
"""

# Column name → SQL type mapping for parameter binding
COLUMNS = [
    "id", "part_no", "part_code", "part_name",
    "material", "material_raw",
    "overall_length", "overall_width", "overall_height", "dimensions_raw",
    "weight_kg", "volume_mm3",
    "hole_count", "thread_specs", "contour_type",
    "surface_treatment", "surface_raw",
    "process_hint", "tolerance_grade",
    "historical_price", "price_source", "price_date",
    "source_bom", "source_bom_row", "source_dwg", "source_pdf",
    "project_name",
    "created_at", "updated_at",
]

INSERT_SQL = f"""
    INSERT OR REPLACE INTO historical_parts (
        {', '.join(COLUMNS)}
    ) VALUES (
        {', '.join('?' * len(COLUMNS))}
    )
"""
