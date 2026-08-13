"""SQLite repository for HistoricalFeature records."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from quotation.domain.historical import HistoricalFeature
from quotation.infrastructure.database.schema import INSERT_SQL, SCHEMA_SQL

logger = logging.getLogger("quotation.infrastructure.database.repository")


class HistoryRepository:
    """CRUD for historical part records in SQLite."""

    def __init__(self, db_path: str | Path):
        self._db_path = str(db_path)
        self._ensure_schema()

    # -- Internal helpers --

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            conn.commit()
            return rows
        finally:
            conn.close()

    def _execute_insert(self, sql: str, params: tuple) -> None:
        conn = self._connect()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _execute_script(self, sql: str) -> None:
        conn = self._connect()
        try:
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()

    def _execute_batch(self, sql: str, param_list: list[tuple]) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            for params in param_list:
                conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    # -- Schema --

    def _ensure_schema(self) -> None:
        self._execute_script(SCHEMA_SQL)

    # -- Insert --

    def insert(self, record: HistoricalFeature) -> str:
        self._execute_insert(INSERT_SQL, self._to_row(record))
        logger.debug("Inserted historical part: %s", record.part_no)
        return record.id

    def insert_batch(self, records: list[HistoricalFeature]) -> int:
        rows = [self._to_row(r) for r in records]
        self._execute_batch(INSERT_SQL, rows)
        logger.info("Inserted %d historical parts", len(records))
        return len(records)

    # -- Query --

    def get_by_part_no(self, part_no: str) -> HistoricalFeature | None:
        rows = self._execute(
            "SELECT * FROM historical_parts WHERE part_no = ?", (part_no,)
        )
        return self._from_row(rows[0]) if rows else None

    def get_all(self, limit: int = 100, offset: int = 0) -> list[HistoricalFeature]:
        rows = self._execute(
            "SELECT * FROM historical_parts ORDER BY part_no LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [self._from_row(r) for r in rows]

    def get_by_material(self, material: str) -> list[HistoricalFeature]:
        rows = self._execute(
            "SELECT * FROM historical_parts WHERE material = ?", (material,)
        )
        return [self._from_row(r) for r in rows]

    def get_by_project(self, project_name: str) -> list[HistoricalFeature]:
        rows = self._execute(
            "SELECT * FROM historical_parts WHERE project_name = ?",
            (project_name,),
        )
        return [self._from_row(r) for r in rows]

    # -- Count --

    def count(self) -> int:
        rows = self._execute("SELECT COUNT(*) FROM historical_parts")
        return rows[0][0] if rows else 0

    def count_by_material(self) -> dict[str, int]:
        rows = self._execute(
            "SELECT material, COUNT(*) FROM historical_parts "
            "WHERE material IS NOT NULL GROUP BY material"
        )
        return {r[0]: r[1] for r in rows}

    # -- Serialization --

    @staticmethod
    def _to_row(record: HistoricalFeature) -> tuple:
        return (
            record.id, record.part_no, record.part_code, record.part_name,
            record.material, record.material_raw,
            record.overall_length, record.overall_width, record.overall_height,
            record.dimensions_raw,
            record.weight_kg, record.volume_mm3,
            record.hole_count,
            json.dumps(record.thread_specs, ensure_ascii=False),
            record.contour_type,
            record.surface_treatment, record.surface_raw,
            record.process_hint, record.tolerance_grade,
            record.historical_price, record.price_source, record.price_date,
            record.source_bom, record.source_bom_row, record.source_dwg, record.source_pdf,
            record.project_name,
            record.created_at, record.updated_at,
        )

    @staticmethod
    def _from_row(row: tuple) -> HistoricalFeature:
        try:
            thread_specs = json.loads(row[13]) if row[13] else []
        except (json.JSONDecodeError, TypeError, IndexError):
            thread_specs = []

        def _f(val, idx, default=None):
            try:
                return val[idx]
            except IndexError:
                return default

        return HistoricalFeature(
            id=row[0], part_no=row[1],
            part_code=_f(row, 2), part_name=_f(row, 3),
            material=_f(row, 4), material_raw=_f(row, 5),
            overall_length=float(_f(row, 6) or 0),
            overall_width=float(_f(row, 7) or 0),
            overall_height=float(_f(row, 8) or 0),
            dimensions_raw=_f(row, 9),
            weight_kg=float(v) if (v := _f(row, 10)) is not None else None,
            volume_mm3=float(v) if (v := _f(row, 11)) is not None else None,
            hole_count=int(_f(row, 12) or 0),
            thread_specs=thread_specs,
            contour_type=_f(row, 14),
            surface_treatment=_f(row, 15), surface_raw=_f(row, 16),
            process_hint=_f(row, 17), tolerance_grade=_f(row, 18),
            historical_price=float(_f(row, 19) or 0),
            price_source=_f(row, 20) or "BOM",
            price_date=_f(row, 21),
            source_bom=_f(row, 22),
            source_bom_row=int(_f(row, 23) or 0),
            source_dwg=_f(row, 24), source_pdf=_f(row, 25),
            project_name=_f(row, 26),
            created_at=_f(row, 27), updated_at=_f(row, 28),
        )
