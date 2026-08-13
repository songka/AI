"""Quotation History — SQLite persistence for quote records.

Database location: runtime/data/quotation_history.db (relative to project root)
"""

from __future__ import annotations

import getpass
import socket
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def runtime_pc_identity() -> dict[str, str]:
    """Return best-effort Windows/PC audit identity without blocking quotation."""

    try:
        pc_username = getpass.getuser().strip() or "无法获取"
    except Exception:
        pc_username = "无法获取"
    try:
        pc_name = socket.gethostname().strip() or "无法获取"
    except Exception:
        pc_name = "无法获取"
    pc_ip = "无法获取"
    try:
        addresses = socket.gethostbyname_ex(pc_name)[2]
        usable = [value for value in addresses if value and not value.startswith("127.")]
        if usable:
            pc_ip = usable[0]
    except Exception:
        pass
    return {"pc_username": pc_username, "pc_name": pc_name, "pc_ip": pc_ip}


def _db_path() -> Path:
    """Find the database path relative to project root."""
    current = Path.cwd()
    for _ in range(5):
        if (current / "pyproject.toml").exists():
            break
        if current.parent == current:
            break
        current = current.parent
    db_dir = current / "runtime" / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "quotation_history.db"


class QuotationHistory:
    """SQLite-backed quotation history store."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path else _db_path()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_id TEXT UNIQUE NOT NULL,
                    job_id TEXT,
                    drawing_number TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    quotation_status TEXT,
                    status_display TEXT,
                    cost_completion REAL,
                    unknown_count INTEGER,
                    subtotal_excl_tax REAL,
                    tax_rate REAL,
                    tax_amount REAL,
                    total_incl_tax REAL,
                    rule_version TEXT,
                    price_version TEXT,
                    ai_used INTEGER DEFAULT 0,
                    excel_path TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quote_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_id TEXT NOT NULL,
                    line_id TEXT,
                    category TEXT,
                    name TEXT,
                    source TEXT,
                    source_display TEXT,
                    quantity REAL,
                    unit TEXT,
                    unit_price REAL,
                    amount REAL,
                    confidence TEXT,
                    status TEXT,
                    resolution_source TEXT,
                    resolution_display TEXT,
                    ai_estimated_unit_price REAL,
                    ai_estimated_amount REAL,
                    ai_estimated_unit TEXT,
                    ai_estimate_reason TEXT,
                    ai_estimate_confidence REAL,
                    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id TEXT UNIQUE NOT NULL,
                    quote_id TEXT NOT NULL,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    operator TEXT DEFAULT '本機使用者',
                    ai_suggestion TEXT,
                    ai_accepted INTEGER DEFAULT 0,
                    recalculated INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quote_overrides (
                    quote_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (quote_id, field_name),
                    FOREIGN KEY (quote_id) REFERENCES quotes(quote_id)
                )
            """)
            self._ensure_column(conn, "quotes", "quote_version", "INTEGER DEFAULT 1")
            self._ensure_column(conn, "quotes", "quoted_by", "TEXT")
            self._ensure_column(conn, "quotes", "pc_username", "TEXT")
            self._ensure_column(conn, "quotes", "pc_name", "TEXT")
            self._ensure_column(conn, "quotes", "pc_ip", "TEXT")
            self._ensure_column(conn, "reviews", "line_id", "TEXT")
            self._ensure_column(conn, "reviews", "quote_version_before", "INTEGER")
            self._ensure_column(conn, "reviews", "quote_version_after", "INTEGER")
            self._ensure_column(conn, "quote_items", "ai_estimated_unit_price", "REAL")
            self._ensure_column(conn, "quote_items", "ai_estimated_amount", "REAL")
            self._ensure_column(conn, "quote_items", "ai_estimated_unit", "TEXT")
            self._ensure_column(conn, "quote_items", "ai_estimate_reason", "TEXT")
            self._ensure_column(conn, "quote_items", "ai_estimate_confidence", "REAL")
            conn.commit()

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_quote(
        self,
        result: Any,
        *,
        quoted_by: str | None = None,
        pc_identity: dict[str, str] | None = None,
    ) -> None:
        """Save a QuoteJobResult to history."""
        now = datetime.now(timezone.utc).isoformat()
        identity = pc_identity or runtime_pc_identity()
        quote_operator = quoted_by or getattr(result.quote, "quoted_by", None) or "免登录用户"

        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quotes
                (quote_id, job_id, drawing_number, file_name, file_path,
                 quotation_status, status_display, cost_completion, unknown_count,
                 subtotal_excl_tax, tax_rate, tax_amount, total_incl_tax,
                 rule_version, price_version, ai_used, excel_path, created_at, updated_at,
                 quoted_by, pc_username, pc_name, pc_ip)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.job_id,
                    result.job_id,
                    result.drawing_number,
                    result.bundle.geometry_source.file_name
                    if result.bundle.geometry_source
                    else "",
                    str(result.bundle.geometry_source.full_path)
                    if result.bundle.geometry_source
                    else "",
                    result.status,
                    _status_display(result.status),
                    result.cost_completion,
                    result.unknown_item_count,
                    float(result.subtotal_excluding_tax),
                    float(getattr(result.tax, "tax_rate", 0.13)) if result.tax else 0.13,
                    float(result.tax.tax_amount) if result.tax else 0,
                    float(result.total_including_tax),
                    result.quote.rule_version if result.quote else "",
                    result.quote.price_version if result.quote else "",
                    1 if result.ai_used else 0,
                    "",
                    now,
                    now,
                    quote_operator,
                    identity.get("pc_username", "无法获取"),
                    identity.get("pc_name", "无法获取"),
                    identity.get("pc_ip", "无法获取"),
                ),
            )

            # Save items
            conn.execute("DELETE FROM quote_items WHERE quote_id = ?", (result.job_id,))
            if result.quote:
                for item in result.quote.items:
                    conn.execute(
                        """
                        INSERT INTO quote_items
                        (quote_id, line_id, category, name, source, source_display,
                         quantity, unit, unit_price, amount, confidence, status,
                         resolution_source, resolution_display, ai_estimated_unit_price,
                         ai_estimated_amount, ai_estimated_unit, ai_estimate_reason,
                         ai_estimate_confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            result.job_id,
                            item.line_id,
                            item.category,
                            item.name,
                            item.source.value,
                            _source_display(item.source.value),
                            item.quantity,
                            item.unit,
                            item.unit_price,
                            item.amount,
                            item.confidence.value,
                            "待確認" if item.source.value == "U" else "已確認",
                            item.resolution_source or "",
                            _resolution_display(item.resolution_source or ""),
                            item.ai_estimated_unit_price,
                            item.ai_estimated_amount,
                            item.ai_estimated_unit,
                            item.ai_estimate_reason,
                            item.ai_estimate_confidence,
                        ),
                    )
            conn.commit()

    def delete_quote(self, quote_id: str) -> bool:
        """Delete one quotation and all of its local detail/audit rows."""

        with sqlite3.connect(str(self._db_path)) as conn:
            exists = conn.execute(
                "SELECT 1 FROM quotes WHERE quote_id = ?", (quote_id,)
            ).fetchone()
            if exists is None:
                return False
            conn.execute("DELETE FROM reviews WHERE quote_id = ?", (quote_id,))
            conn.execute("DELETE FROM quote_overrides WHERE quote_id = ?", (quote_id,))
            conn.execute("DELETE FROM quote_items WHERE quote_id = ?", (quote_id,))
            conn.execute("DELETE FROM quotes WHERE quote_id = ?", (quote_id,))
            conn.commit()
        return True

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def search(
        self,
        drawing_number: str | None = None,
        file_name: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search quote history."""
        sql = "SELECT * FROM quotes WHERE 1=1"
        params: list[Any] = []
        if drawing_number:
            sql += " AND drawing_number LIKE ?"
            params.append(f"%{drawing_number}%")
        if file_name:
            sql += " AND file_name LIKE ?"
            params.append(f"%{file_name}%")
        if status:
            sql += " AND quotation_status = ?"
            params.append(status)
        if date_from:
            sql += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND created_at <= ?"
            params.append(date_to)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def get_quote(self, quote_id: str) -> dict[str, Any] | None:
        """Return one quote summary."""
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM quotes WHERE quote_id = ?", (quote_id,)).fetchone()
            return dict(row) if row else None

    def get_detail(self, quote_id: str) -> dict[str, Any] | None:
        """Return quote, items, field overrides, and the immutable review audit trail."""
        quote = self.get_quote(quote_id)
        if quote is None:
            return None
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            overrides = conn.execute(
                "SELECT field_name, value, updated_at FROM quote_overrides WHERE quote_id = ?",
                (quote_id,),
            ).fetchall()
        return {
            "quote": quote,
            "items": self.get_items(quote_id),
            "overrides": {row["field_name"]: dict(row) for row in overrides},
            "reviews": self.get_reviews(quote_id),
        }

    def review_queue(self, limit: int = 100) -> list[dict[str, Any]]:
        """List quotes that still need human review."""
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM quotes
                WHERE quotation_status IN ('INCOMPLETE', 'REVIEW_REQUIRED')
                ORDER BY updated_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_items(self, quote_id: str) -> list[dict[str, Any]]:
        """Get line items for a quote."""
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_reviews(self, quote_id: str) -> list[dict[str, Any]]:
        """Get review records for a quote."""
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM reviews WHERE quote_id = ? ORDER BY created_at DESC", (quote_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_review(
        self,
        review_id: str,
        quote_id: str,
        field_name: str,
        old_value: str,
        new_value: str,
        reason: str = "",
        operator: str = "本機使用者",
        ai_suggestion: str = "",
        ai_accepted: bool = False,
    ) -> None:
        """Save a manual review record."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                INSERT INTO reviews
                (review_id, quote_id, field_name, old_value, new_value,
                 reason, operator, ai_suggestion, ai_accepted, recalculated, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    review_id,
                    quote_id,
                    field_name,
                    old_value,
                    new_value,
                    reason,
                    operator,
                    ai_suggestion,
                    1 if ai_accepted else 0,
                    0,
                    now,
                ),
            )
            conn.commit()

    def apply_manual_review(
        self,
        quote_id: str,
        *,
        field_name: str,
        new_value: str,
        reason: str,
        operator: str,
        line_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply one quote-scoped manual correction and record a versioned audit entry."""

        allowed = {
            "material",
            "thickness",
            "dimensions",
            "surface_treatment",
            "process",
            "manual_price",
        }
        if field_name not in allowed:
            raise ValueError(f"Unsupported review field: {field_name}")
        if not reason.strip() or not operator.strip():
            raise ValueError("Review reason and operator are required")
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            quote = conn.execute("SELECT * FROM quotes WHERE quote_id = ?", (quote_id,)).fetchone()
            if quote is None:
                raise KeyError(quote_id)
            version_before = int(quote["quote_version"] or 1)
            old_value = ""

            if field_name == "manual_price":
                if not line_id:
                    raise ValueError("line_id is required for manual_price")
                item = conn.execute(
                    "SELECT * FROM quote_items WHERE quote_id = ? AND line_id = ?",
                    (quote_id, line_id),
                ).fetchone()
                if item is None:
                    raise ValueError(f"Quote item not found: {line_id}")
                price = float(new_value)
                if price < 0:
                    raise ValueError("Manual price cannot be negative")
                old_value = str(item["unit_price"])
                amount = round(float(item["quantity"] or 0) * price, 2)
                conn.execute(
                    """
                    UPDATE quote_items
                    SET unit_price = ?, amount = ?, source = 'M',
                        source_display = ?, confidence = 'medium', status = ?,
                        resolution_source = 'MANUAL_QUOTE_OVERRIDE',
                        resolution_display = ?
                    WHERE quote_id = ? AND line_id = ?
                    """,
                    (
                        price,
                        amount,
                        "人工確認價格",
                        "已確認",
                        "僅限當前報價的人工確認價格",
                        quote_id,
                        line_id,
                    ),
                )
            else:
                previous = conn.execute(
                    "SELECT value FROM quote_overrides WHERE quote_id = ? AND field_name = ?",
                    (quote_id, field_name),
                ).fetchone()
                old_value = previous["value"] if previous else ""
                conn.execute(
                    """
                    INSERT INTO quote_overrides (quote_id, field_name, value, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(quote_id, field_name)
                    DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                    """,
                    (quote_id, field_name, new_value, now),
                )

            version_after = version_before + 1
            self._recalculate_quote(conn, quote_id, version_after, now)
            conn.execute(
                """
                INSERT INTO reviews
                (review_id, quote_id, field_name, old_value, new_value, reason,
                 operator, ai_suggestion, ai_accepted, recalculated, created_at,
                 line_id, quote_version_before, quote_version_after)
                VALUES (?, ?, ?, ?, ?, ?, ?, '', 0, 1, ?, ?, ?, ?)
                """,
                (
                    f"REV-{uuid.uuid4().hex[:12]}",
                    quote_id,
                    field_name,
                    old_value,
                    new_value,
                    reason,
                    operator,
                    now,
                    line_id,
                    version_before,
                    version_after,
                ),
            )
            conn.commit()

        detail = self.get_detail(quote_id)
        assert detail is not None
        return detail

    @staticmethod
    def _recalculate_quote(
        conn: sqlite3.Connection, quote_id: str, quote_version: int, now: str
    ) -> None:
        items = conn.execute(
            "SELECT source, amount FROM quote_items WHERE quote_id = ?", (quote_id,)
        ).fetchall()
        unknown_count = sum(row["source"] == "U" for row in items)
        subtotal = round(sum(float(row["amount"] or 0) for row in items if row["source"] != "U"), 2)
        tax_row = conn.execute(
            "SELECT tax_rate FROM quotes WHERE quote_id = ?", (quote_id,)
        ).fetchone()
        tax_rate = float(tax_row["tax_rate"] or 0.13) if tax_row else 0.13
        tax_amount = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax_amount, 2)
        completion = round((len(items) - unknown_count) / len(items) * 100, 1) if items else 0.0
        status = "COMPLETE" if items and unknown_count == 0 else "INCOMPLETE"
        conn.execute(
            """
            UPDATE quotes SET quotation_status = ?, status_display = ?, cost_completion = ?,
                unknown_count = ?, subtotal_excl_tax = ?, tax_amount = ?, total_incl_tax = ?,
                quote_version = ?, updated_at = ? WHERE quote_id = ?
            """,
            (
                status,
                _status_display(status),
                completion,
                unknown_count,
                subtotal,
                tax_amount,
                total,
                quote_version,
                now,
                quote_id,
            ),
        )


# ---------------------------------------------------------------------------
# Display name helpers
# ---------------------------------------------------------------------------


def _source_display(code: str) -> str:
    mapping = {
        "C": "公司核准價格",
        "H": "歷史成交價格",
        "E": "系統估算價格",
        "S": "供應商報價來源",
        "M": "人工確認價格",
        "AI": "AI輔助建議，尚未核准",
        "U": "價格待確認",
    }
    return mapping.get(code, code)


def _status_display(code: str) -> str:
    mapping = {
        "COMPLETE": "報價完整",
        "INCOMPLETE": "部分價格待確認",
        "REVIEW_REQUIRED": "需要人工審核",
        "PARSE_FAILED": "圖紙解析失敗",
        "QUOTE_FAILED": "報價計算失敗",
        "UNSUPPORTED": "暫不支持此文件",
        "DWG_CONVERTING": "正在轉換DWG圖紙",
        "DWG_CONVERSION_FAILED": "DWG轉換失敗",
        "WAITING": "等待處理",
        "PARSING": "正在解析圖紙",
        "AI_ANALYZING": "AI正在輔助分析",
        "QUOTING": "正在計算報價",
    }
    return mapping.get(code, code)


def _resolution_display(code: str) -> str:
    mapping = {
        "PUBLISHED_COMPANY_PRICEBOOK": "已發布公司價格表",
        "LEGACY_YAML": "舊版報價規則",
        "LEGACY_YAML_DRAFT": "舊版草稿規則，需人工確認",
    }
    return mapping.get(code, code)
