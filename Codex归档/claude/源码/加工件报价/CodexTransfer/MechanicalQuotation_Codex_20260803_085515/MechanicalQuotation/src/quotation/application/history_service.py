"""Quotation History — SQLite persistence for quote records.

Database location: runtime/data/quotation_history.db (relative to project root)
"""

from __future__ import annotations

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
            conn.commit()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_quote(self, result: Any) -> None:
        """Save a QuoteJobResult to history."""
        from quotation.application.quotation_service import QuoteJobResult
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO quotes
                (quote_id, job_id, drawing_number, file_name, file_path,
                 quotation_status, status_display, cost_completion, unknown_count,
                 subtotal_excl_tax, tax_rate, tax_amount, total_incl_tax,
                 rule_version, price_version, ai_used, excel_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.job_id,
                result.job_id,
                result.drawing_number,
                result.bundle.geometry_source.file_name if result.bundle.geometry_source else "",
                str(result.bundle.geometry_source.full_path) if result.bundle.geometry_source else "",
                result.status,
                _status_display(result.status),
                result.cost_completion,
                result.unknown_item_count,
                float(result.subtotal_excluding_tax),
                0.17,
                float(result.tax.tax_amount) if result.tax else 0,
                float(result.total_including_tax),
                result.quote.rule_version if result.quote else "",
                result.quote.price_version if result.quote else "",
                1 if result.ai_used else 0,
                "",
                now, now,
            ))

            # Save items
            if result.quote:
                for item in result.quote.items:
                    conn.execute("""
                        INSERT INTO quote_items
                        (quote_id, line_id, category, name, source, source_display,
                         quantity, unit, unit_price, amount, confidence, status,
                         resolution_source, resolution_display)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
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
                    ))
            conn.commit()

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
        self, review_id: str, quote_id: str,
        field_name: str, old_value: str, new_value: str,
        reason: str = "", operator: str = "本機使用者",
        ai_suggestion: str = "", ai_accepted: bool = False,
    ) -> None:
        """Save a manual review record."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                INSERT INTO reviews
                (review_id, quote_id, field_name, old_value, new_value,
                 reason, operator, ai_suggestion, ai_accepted, recalculated, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, quote_id, field_name, old_value, new_value,
                reason, operator, ai_suggestion, 1 if ai_accepted else 0, 0, now,
            ))
            conn.commit()


# ---------------------------------------------------------------------------
# Display name helpers
# ---------------------------------------------------------------------------

def _source_display(code: str) -> str:
    mapping = {
        "C": "公司核准價格", "H": "歷史成交價格", "E": "系統估算價格",
        "S": "供應商報價來源", "M": "人工確認價格",
        "AI": "AI輔助建議，尚未核准", "U": "價格待確認",
    }
    return mapping.get(code, code)


def _status_display(code: str) -> str:
    mapping = {
        "COMPLETE": "報價完整", "INCOMPLETE": "部分價格待確認",
        "REVIEW_REQUIRED": "需要人工審核", "PARSE_FAILED": "圖紙解析失敗",
        "QUOTE_FAILED": "報價計算失敗", "UNSUPPORTED": "暫不支持此文件",
        "WAITING": "等待處理", "PARSING": "正在解析圖紙",
        "AI_ANALYZING": "AI正在輔助分析", "QUOTING": "正在計算報價",
    }
    return mapping.get(code, code)


def _resolution_display(code: str) -> str:
    mapping = {
        "PUBLISHED_COMPANY_PRICEBOOK": "已發布公司價格表",
        "LEGACY_YAML": "舊版報價規則",
        "LEGACY_YAML_DRAFT": "舊版草稿規則，需人工確認",
    }
    return mapping.get(code, code)
