"""ViewModels for the quotation demo UI.

Pure data transformation layer — no tkinter dependency.
Converts domain Quote/QuoteItem objects into UI-friendly display models.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from quotation.domain.quote import PriceSource, Quote, QuoteItem

# ---------------------------------------------------------------------------
# Tax calculator — UI-layer concern, uses Decimal
# ---------------------------------------------------------------------------


@dataclass
class TaxResult:
    """Immutable tax calculation result."""

    subtotal_excluding_tax: Decimal
    tax_rate: Decimal  # e.g. Decimal("0.13")
    tax_amount: Decimal
    total_including_tax: Decimal

    @classmethod
    def calculate(
        cls,
        items: list[QuoteItem],
        tax_rate: Decimal = Decimal("0.13"),
    ) -> TaxResult:
        """Compute tax from known (non-U) items only."""
        subtotal = Decimal("0")
        for item in items:
            if item.source != PriceSource.U:
                subtotal += Decimal(str(item.amount))
        tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_incl = (subtotal * (Decimal("1") + tax_rate)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return cls(
            subtotal_excluding_tax=subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_including_tax=total_incl,
        )


# ---------------------------------------------------------------------------
# Source label mapping
# ---------------------------------------------------------------------------

SOURCE_LABELS: dict[str, str] = {
    "C": "公司核准價格",
    "H": "歷史成交價格",
    "E": "系統估算價格",
    "S": "供應商報價來源",
    "AI": "AI輔助建議，尚未核准",
    "M": "人工確認價格",
    "U": "價格待確認",
}

SOURCE_SHORT: dict[str, str] = {
    "C": "公司核准",
    "H": "歷史成交",
    "E": "系統估算",
    "S": "供應商",
    "AI": "AI建議",
    "M": "人工確認",
    "U": "待確認",
}

STATUS_DISPLAY: dict[str, str] = {
    "COMPLETE": "報價完整",
    "INCOMPLETE": "部分價格待確認",
    "REVIEW_REQUIRED": "需要人工審核",
    "PARSE_FAILED": "圖紙解析失敗",
    "QUOTE_FAILED": "報價計算失敗",
    "UNSUPPORTED": "暫不支持此文件",
    "WAITING": "等待處理",
    "PARSING": "正在解析圖紙",
    "AI_ANALYZING": "AI正在輔助分析",
    "QUOTING": "正在計算報價",
    "DWG_CONVERTING": "正在轉換DWG圖紙",
    "DWG_CONVERSION_FAILED": "DWG轉換失敗",
    "SCANNED": "已掃描",
}

RESOLUTION_DISPLAY: dict[str, str] = {
    "PUBLISHED_COMPANY_PRICEBOOK": "已發布公司價格表",
    "LEGACY_YAML": "舊版報價規則",
    "LEGACY_YAML_DRAFT": "舊版草稿規則，需人工確認",
    "FEATURE_CALIBRATION_MODEL": "圖紙特徵價格校準模型",
}

MATCH_DISPLAY: dict[str, str] = {
    "MATCHED": "圖紙已配對",
    "UNMATCHED": "未找到對應圖紙",
    "DUPLICATE": "發現重複圖紙",
}


# ---------------------------------------------------------------------------
# QuoteItemViewModel — display wrapper for a single line item
# ---------------------------------------------------------------------------


@dataclass
class QuoteItemViewModel:
    """UI-friendly wrapper for QuoteItem."""

    item: QuoteItem
    index: int = 0

    # -- Display helpers --
    @property
    def is_unknown(self) -> bool:
        return self.item.source == PriceSource.U

    @property
    def display_amount(self) -> str:
        """Formatted amount or '—' for unknown items."""
        if self.is_unknown:
            return "—"
        return f"¥{self.item.amount:,.2f}"

    @property
    def display_unit_price(self) -> str:
        """Formatted unit price or '—' for unknown items."""
        if self.is_unknown:
            return "—"
        return f"¥{self.item.unit_price:,.2f}"

    @property
    def display_ai_estimate(self) -> str:
        """Reference-only AI estimate, never part of the official total."""
        if self.item.ai_estimated_amount is None:
            return "—"
        return f"¥{self.item.ai_estimated_amount:,.2f}（参考）"

    @property
    def source_label(self) -> str:
        return SOURCE_LABELS.get(self.item.source.value, self.item.source.value)

    @property
    def source_short(self) -> str:
        return SOURCE_SHORT.get(self.item.source.value, self.item.source.value)

    @property
    def status_label(self) -> str:
        return "待确认" if self.is_unknown else "已确认"

    @property
    def confidence_label(self) -> str:
        mapping = {"high": "高", "medium": "中", "low": "低", "uncertain": "未确定"}
        return mapping.get(self.item.confidence.value, self.item.confidence.value)

    @property
    def row_tags(self) -> list[str]:
        return ["unknown"] if self.is_unknown else []

    # -- Trace fields (for Resolver Trace panel) --
    @property
    def trace_fields(self) -> list[tuple[str, str]]:
        """Key-value pairs of all trace fields (non-None)."""
        fields: list[tuple[str, str]] = []
        mapping = [
            ("價格來源", self.item.quote_price_source),
            ("解析來源", self.item.resolution_source),
            ("價格版本ID", self.item.price_version_id),
            ("公司價格ID", self.item.company_price_id),
            ("原始供應商價格ID", self.item.origin_price_record_id),
            ("原始供應商ID", self.item.origin_supplier_id),
            ("原始價格來源", self.item.origin_price_source),
            ("計價基礎", self.item.price_basis),
            ("生效日期", self.item.effective_from),
        ]
        for label, value in mapping:
            if value is not None:
                fields.append((label, str(value)))
        if self.is_unknown:
            fields.insert(0, ("定价状态", "未找到可用价格"))
            fields.insert(1, ("未定价原因", self.item.note or "缺少定价所需信息"))
            fields.insert(
                2, ("建议处理", "请人工确认材料牌号、尺寸或工艺，也可启用智能辅助重新分析")
            )
        if self.item.ai_estimated_amount is not None:
            fields.append(
                ("智能辅助参考总额", f"¥{self.item.ai_estimated_amount:,.2f}（不计入正式总价）")
            )
            fields.append(
                (
                    "智能辅助参考单价",
                    f"¥{self.item.ai_estimated_unit_price or 0:,.2f}/"
                    f"{self.item.ai_estimated_unit or '项'}",
                )
            )
            fields.append(("智能辅助估价依据", self.item.ai_estimate_reason or "仅供人工参考"))
            fields.append(
                ("智能辅助估价可信度", f"{(self.item.ai_estimate_confidence or 0) * 100:.0f}%")
            )
        if self.item.fallback_warning:
            fields.append(("⚠ 回退警告", "是"))
            if self.item.fallback_reason:
                fields.append(("回退原因", self.item.fallback_reason))
            if self.item.fallback_approval_status:
                fields.append(("回退審批狀態", self.item.fallback_approval_status))
        return fields


# ---------------------------------------------------------------------------
# QuoteViewModel — display wrapper for the full Quote
# ---------------------------------------------------------------------------


@dataclass
class QuoteViewModel:
    """UI-friendly wrapper for Quote with tax and display helpers."""

    quote: Quote
    tax: TaxResult | None = None

    # -- Basic info --
    @property
    def basic_info(self) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        mapping = [
            ("圖號", self.quote.part_number),
            ("料號", self.quote.part_number),
            ("材料", self.quote.material),
            ("規則版本", self.quote.rule_version),
            ("價格版本", self.quote.price_version),
        ]
        for label, value in mapping:
            rows.append((label, value or "—"))
        return rows

    # -- Feature summary --
    @property
    def feature_summary_fields(self) -> list[tuple[str, str]]:
        """Override these from the pipeline result dict, not from Quote."""
        return []  # Populated externally by demo_app from pipeline result

    # -- Item VMs --
    @property
    def items_vm(self) -> list[QuoteItemViewModel]:
        return [
            QuoteItemViewModel(item=item, index=i + 1) for i, item in enumerate(self.quote.items)
        ]

    # -- Status --
    @property
    def status_text(self) -> str:
        if self.quote.quotation_status == "COMPLETE":
            return "報價完整"
        return f"報價未完整（{self.quote.unknown_count} 項待確認）"

    @property
    def status_color(self) -> str:
        if self.quote.quotation_status == "COMPLETE":
            return "green"
        if self.quote.unknown_count > 0 and self.quote.total > 0:
            return "orange"
        return "red"

    # -- Summary --
    @property
    def known_items(self) -> list[QuoteItem]:
        return [i for i in self.quote.items if i.source != PriceSource.U]

    @property
    def unknown_items(self) -> list[QuoteItem]:
        return [i for i in self.quote.items if i.source == PriceSource.U]

    @property
    def known_total(self) -> float:
        return sum(i.amount for i in self.known_items)

    # -- Tax display --
    @property
    def display_subtotal_excl(self) -> str:
        if self.tax is None:
            return f"¥{self.known_total:,.2f}"
        return f"¥{float(self.tax.subtotal_excluding_tax):,.2f}"

    @property
    def display_tax_rate(self) -> str:
        if self.tax is None:
            return "13%"
        return f"{float(self.tax.tax_rate) * 100:.0f}%"

    @property
    def display_tax_amount(self) -> str:
        if self.tax is None:
            return "¥0.00"
        return f"¥{float(self.tax.tax_amount):,.2f}"

    @property
    def display_total_incl(self) -> str:
        if self.tax is None:
            return f"¥{self.known_total * 1.13:,.2f}"
        return f"¥{float(self.tax.total_including_tax):,.2f}"
