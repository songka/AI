"""Reusable Tkinter widgets for the quotation demo UI."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable

from quotation.ui.viewmodels import QuoteViewModel

# ---------------------------------------------------------------------------
# Styling constants
# ---------------------------------------------------------------------------

NAV_BG = "#2c3e50"
NAV_FG = "#ecf0f1"
NAV_ACTIVE_BG = "#3498db"
NAV_BUTTON_BG = "#34495e"
CONTENT_BG = "#f5f6fa"
CARD_BG = "#ffffff"
STATUS_GREEN = "#27ae60"
STATUS_ORANGE = "#e67e22"
STATUS_RED = "#e74c3c"
HEADER_BG = "#1a5276"
HEADER_FG = "#ffffff"
WARNING_BG = "#fff3cd"
FONT_FAMILY = ("Microsoft YaHei UI", "Segoe UI", "TkDefaultFont")


def _font(size: int = 10, bold: bool = False) -> tuple:
    return (FONT_FAMILY[0], size, "bold" if bold else "normal")


# ---------------------------------------------------------------------------
# NavPanel — left sidebar
# ---------------------------------------------------------------------------

class NavPanel(tk.Frame):
    """Left navigation sidebar with dark background."""

    NAV_ITEMS = [
        ("新建報價", "\U0001f4c4"),
        ("批量報價", "\U0001f4e6"),
        ("報價記錄", "\U0001f4da"),
        ("價格管理", "\U0001f4c8"),
        ("供應商管理", "\U0001f3ed"),
        ("系統設定", "⚙️"),
    ]

    def __init__(
        self,
        parent: tk.Widget,
        on_nav_change: Callable[[str], None],
        **kw: Any,
    ):
        super().__init__(parent, bg=NAV_BG, width=200, **kw)
        self._on_nav_change = on_nav_change
        self._active_button: tk.Button | None = None
        self._build()

    def _build(self) -> None:
        self.pack_propagate(False)
        # Logo area
        logo_frame = tk.Frame(self, bg=NAV_BG, height=80)
        logo_frame.pack(fill=tk.X, pady=(20, 10))
        logo_frame.pack_propagate(False)
        tk.Label(
            logo_frame, text="Mechanical Quotation", bg=NAV_BG, fg=NAV_FG,
            font=_font(11, bold=True),
        ).pack(pady=(15, 0))
        tk.Label(
            logo_frame, text="機械加工件智能報價系統", bg=NAV_BG, fg="#95a5a6",
            font=_font(8),
        ).pack()

        # Separator
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=10)

        # Nav buttons
        for name, icon in self.NAV_ITEMS:
            btn = tk.Button(
                self,
                text=f"  {icon}  {name}",
                bg=NAV_BUTTON_BG,
                fg=NAV_FG,
                font=_font(10),
                bd=0,
                padx=15,
                pady=10,
                anchor=tk.W,
                cursor="hand2",
                activebackground=NAV_ACTIVE_BG,
                activeforeground="#ffffff",
                relief=tk.FLAT,
                command=lambda n=name: self._select(n),
            )
            btn.pack(fill=tk.X, padx=10, pady=2)
            if name == "新建報價":
                self._active_button = btn
                btn.configure(bg=NAV_ACTIVE_BG, fg="#ffffff")

        # Version at bottom
        tk.Label(
            self, text="v1.0-demo", bg=NAV_BG, fg="#7f8c8d",
            font=_font(8),
        ).pack(side=tk.BOTTOM, pady=15)

    def _select(self, name: str) -> None:
        """Highlight the active nav item and notify parent."""
        for child in self.winfo_children():
            if isinstance(child, tk.Button):
                if child.cget("text").strip().endswith(name if name else ""):
                    # Find the button with matching name
                    pass
        # Reset all buttons
        for child in self.winfo_children():
            if isinstance(child, tk.Button):
                child.configure(bg=NAV_BUTTON_BG, fg=NAV_FG)
        # Highlight active
        for child in self.winfo_children():
            if isinstance(child, tk.Button):
                label = child.cget("text") or ""
                if name in label:
                    child.configure(bg=NAV_ACTIVE_BG, fg="#ffffff")
                    self._active_button = child
                    break
        self._on_nav_change(name)


# ---------------------------------------------------------------------------
# PlaceholderPage — for non-functional nav items
# ---------------------------------------------------------------------------

class PlaceholderPage(tk.Frame):
    """Simple placeholder page with centered text."""

    def __init__(self, parent: tk.Widget, title: str, **kw: Any):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        inner = tk.Frame(self, bg=CARD_BG, bd=1, relief=tk.SOLID)
        inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=400, height=200)
        tk.Label(
            inner, text="\U0001f6a7", font=_font(36), bg=CARD_BG,
        ).pack(pady=(30, 10))
        tk.Label(
            inner, text=title, font=_font(14, bold=True), bg=CARD_BG,
            fg="#2c3e50",
        ).pack()
        tk.Label(
            inner, text="功能開發中", font=_font(10), bg=CARD_BG, fg="#95a5a6",
        ).pack(pady=(5, 20))


# ---------------------------------------------------------------------------
# NewQuotePage — the main functional page
# ---------------------------------------------------------------------------

class NewQuotePage(tk.Frame):
    """The "新建報價" page with toolbar, cards, table, and summary."""

    def __init__(
        self,
        parent: tk.Widget,
        on_load_j003: Callable[[], None],
        on_load_w001: Callable[[], None],
        on_export: Callable[[], None],
        **kw: Any,
    ):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._on_load_j003 = on_load_j003
        self._on_load_w001 = on_load_w001
        self._on_export = on_export
        self._show_tax = tk.BooleanVar(value=True)
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # -- Scrollable container --
        self._canvas = tk.Canvas(self, bg=CONTENT_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)

        self._scroll_frame = tk.Frame(self._canvas, bg=CONTENT_BG)
        self._scroll_frame.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all"))
        )
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor=tk.NW
        )

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Bind mousewheel
        self._canvas.bind("<Enter>", lambda e: self._canvas.bind_all(
            "<MouseWheel>", lambda ev: self._canvas.yview_scroll(
                int(-1 * (ev.delta / 120)), "units")))
        self._canvas.bind("<Leave>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

        # -- Header --
        header = tk.Frame(self._scroll_frame, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="  新建報價", font=_font(14, bold=True),
            bg=HEADER_BG, fg=HEADER_FG,
        ).pack(side=tk.LEFT, pady=10)

        # -- Toolbar --
        self._toolbar = tk.Frame(self._scroll_frame, bg=CARD_BG, bd=1, relief=tk.SOLID)
        self._toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        buttons = [
            ("\U0001f4c2  選擇圖紙", lambda: messagebox.showinfo("提示", "功能開發中")),
            ("\U0001f4e5  載入J003範例", self._on_load_j003),
            ("\U0001f4e5  載入W001範例", self._on_load_w001),
            ("\U0001f50d  開始解析", lambda: messagebox.showinfo("提示", "請先載入圖紙")),
            ("\U0001f504  重新計算", lambda: messagebox.showinfo("提示", "請先載入圖紙")),
            ("\U0001f4ca  匯出Excel", self._on_export),
        ]
        for text, cmd in buttons:
            btn = tk.Button(
                self._toolbar, text=text, font=_font(9),
                bg="#ecf0f1", fg="#2c3e50", bd=1, padx=10, pady=5,
                cursor="hand2", relief=tk.FLAT,
                activebackground=NAV_ACTIVE_BG, activeforeground="#ffffff",
                command=cmd,
            )
            btn.pack(side=tk.LEFT, padx=5, pady=8)

        # -- Cards container --
        cards_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG)
        cards_frame.pack(fill=tk.X, padx=10, pady=5)

        # Basic Info Card
        self._basic_card_frame = tk.LabelFrame(
            cards_frame, text=" 基本資料 ", font=_font(10, bold=True),
            bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID,
        )
        self._basic_card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Feature Card
        self._feature_card_frame = tk.LabelFrame(
            cards_frame, text=" Feature 摘要 ", font=_font(10, bold=True),
            bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID,
        )
        self._feature_card_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # -- Quote table --
        self._table_frame = tk.LabelFrame(
            self._scroll_frame, text=" 報價明細 ", font=_font(10, bold=True),
            bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID,
        )
        self._table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._build_table()

        # -- Trace panel --
        self._trace_frame = ttk.LabelFrame(
            self._scroll_frame, text=" 價格來源詳情 ",
        )
        self._trace_frame.pack(fill=tk.X, padx=10, pady=5)
        self._trace_text = tk.Text(
            self._trace_frame, height=4, font=_font(9), wrap=tk.WORD,
            bg="#f8f9fa", fg="#2c3e50", bd=0,
        )
        self._trace_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self._trace_text.insert("1.0", "點擊上方報價項目查看價格來源詳情")
        self._trace_text.configure(state=tk.DISABLED)

        # -- Tax toggle --
        tax_toggle_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG)
        tax_toggle_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Checkbutton(
            tax_toggle_frame, text="顯示含稅價", variable=self._show_tax,
            command=self._on_tax_toggle,
        ).pack(side=tk.RIGHT)

        # -- Summary cards --
        self._summary_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG)
        self._summary_frame.pack(fill=tk.X, padx=10, pady=5)

        self._summary_cards: dict[str, dict[str, Any]] = {}
        card_configs = [
            ("card_excl", "未稅小計", "#3498db"),
            ("card_rate", "稅率", "#2ecc71"),
            ("card_tax", "稅額", "#e67e22"),
            ("card_incl", "含稅總價", "#e74c3c"),
        ]
        for key, title, color in card_configs:
            card = self._make_summary_card(self._summary_frame, title, color)
            card["frame"].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
            self._summary_cards[key] = card

        # -- Status bar --
        self._status_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG, height=40)
        self._status_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        self._status_frame.pack_propagate(False)
        self._status_label = tk.Label(
            self._status_frame, text="就緒", font=_font(10),
            bg=CONTENT_BG, fg="#95a5a6",
        )
        self._status_label.pack(side=tk.LEFT, pady=5)

        self._completion_label = tk.Label(
            self._status_frame, text="", font=_font(9, bold=True),
            bg=CONTENT_BG, fg="#95a5a6",
        )
        self._completion_label.pack(side=tk.RIGHT, pady=5)

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _build_table(self) -> None:
        columns = ("#", "報價項目", "來源", "數量", "單位", "單價", "未稅金額", "Confidence", "狀態")
        self._tree = ttk.Treeview(
            self._table_frame, columns=columns, show="headings",
            height=8, selectmode="browse",
        )
        widths = [40, 200, 80, 60, 50, 80, 100, 80, 70]
        for col, w in zip(columns, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=tk.CENTER if col != "報價項目" else tk.W)

        # Scrollbar
        vsb = ttk.Scrollbar(self._table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Tags
        self._tree.tag_configure("unknown", background=WARNING_BG)
        self._tree.tag_configure("even", background="#f8f9fa")

        # Bind selection
        self._tree.bind("<<TreeviewSelect>>", self._on_item_select)

    # ------------------------------------------------------------------
    # Summary cards
    # ------------------------------------------------------------------

    def _make_summary_card(
        self, parent: tk.Frame, title: str, accent: str,
    ) -> dict[str, Any]:
        frame = tk.Frame(parent, bg=CARD_BG, bd=1, relief=tk.SOLID)
        tk.Label(
            frame, text=title, font=_font(8), bg=CARD_BG, fg="#7f8c8d",
        ).pack(pady=(10, 2))
        value_label = tk.Label(
            frame, text="—", font=_font(14, bold=True), bg=CARD_BG, fg=accent,
        )
        value_label.pack(pady=(0, 10))
        return {"frame": frame, "value": value_label, "accent": accent}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_basic_info(self, fields: list[tuple[str, str]]) -> None:
        """Replace basic info card content."""
        for w in self._basic_card_frame.winfo_children():
            w.destroy()
        for i, (label, value) in enumerate(fields):
            row, col = divmod(i, 2)
            tk.Label(
                self._basic_card_frame, text=f"{label}：", font=_font(9, bold=True),
                bg=CARD_BG, fg="#7f8c8d",
            ).grid(row=row, column=col * 2, sticky=tk.W, padx=(10, 2), pady=3)
            tk.Label(
                self._basic_card_frame, text=value, font=_font(9),
                bg=CARD_BG, fg="#2c3e50",
            ).grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=(2, 20), pady=3)

    def update_feature_summary(self, fields: list[tuple[str, str]]) -> None:
        """Replace feature summary card content."""
        for w in self._feature_card_frame.winfo_children():
            w.destroy()
        for i, (label, value) in enumerate(fields):
            row, col = divmod(i, 2)
            tk.Label(
                self._feature_card_frame, text=f"{label}：", font=_font(9, bold=True),
                bg=CARD_BG, fg="#7f8c8d",
            ).grid(row=row, column=col * 2, sticky=tk.W, padx=(10, 2), pady=3)
            tk.Label(
                self._feature_card_frame, text=value, font=_font(9),
                bg=CARD_BG, fg="#2c3e50",
            ).grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=(2, 20), pady=3)

    def update_table(self, vm: QuoteViewModel) -> None:
        """Populate the quote table from a QuoteViewModel."""
        self._tree.delete(*self._tree.get_children())
        self._current_vm = vm
        for item_vm in vm.items_vm:
            tags = item_vm.row_tags
            if item_vm.index % 2 == 0:
                tags = list(tags) + ["even"]
            self._tree.insert(
                "", tk.END,
                values=(
                    item_vm.index,
                    item_vm.item.name,
                    item_vm.source_short,
                    item_vm.item.quantity if not item_vm.is_unknown else "—",
                    item_vm.item.unit if not item_vm.is_unknown else "—",
                    item_vm.display_unit_price,
                    item_vm.display_amount,
                    item_vm.confidence_label,
                    item_vm.status_label,
                ),
                tags=tags,
            )

    def update_trace(self, item_vm: QuoteItemViewModel | None) -> None:
        """Update the trace panel with selected item's trace fields."""
        self._trace_text.configure(state=tk.NORMAL)
        self._trace_text.delete("1.0", tk.END)
        if item_vm is None:
            self._trace_text.insert("1.0", "點擊上方報價項目查看價格來源詳情")
        else:
            fields = item_vm.trace_fields
            if not fields:
                self._trace_text.insert("1.0", f"{item_vm.item.name}\n無價格來源追蹤資訊")
            else:
                lines = [f"▸ {item_vm.item.name}"]
                for label, value in fields:
                    lines.append(f"  {label}: {value}")
                self._trace_text.insert("1.0", "\n".join(lines))
        self._trace_text.configure(state=tk.DISABLED)

    def update_summary(self, vm: QuoteViewModel) -> None:
        """Update the four summary cards."""
        self._current_vm = vm
        self._summary_cards["card_excl"]["value"].configure(
            text=vm.display_subtotal_excl
        )
        self._summary_cards["card_rate"]["value"].configure(
            text=vm.display_tax_rate
        )
        self._summary_cards["card_tax"]["value"].configure(
            text=vm.display_tax_amount
        )
        self._summary_cards["card_incl"]["value"].configure(
            text=vm.display_total_incl
        )

    def update_status(
        self, status_text: str, status_color: str, completion: float,
    ) -> None:
        """Update the status bar."""
        color_map = {
            "green": STATUS_GREEN,
            "orange": STATUS_ORANGE,
            "red": STATUS_RED,
        }
        color = color_map.get(status_color, "#95a5a6")
        self._status_label.configure(text=f"  {status_text}", fg=color)
        self._completion_label.configure(
            text=f"報價完整度：{completion:.1f}%  ", fg=color,
        )

    def clear(self) -> None:
        """Reset all display areas."""
        self._tree.delete(*self._tree.get_children())
        self.update_trace(None)
        self.update_status("就緒", "", 0)
        for card in self._summary_cards.values():
            card["value"].configure(text="—")
        self.update_basic_info([("狀態", "尚未載入圖紙")])
        self.update_feature_summary([("狀態", "尚未載入圖紙")])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_item_select(self, event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        item_id = selection[0]
        values = self._tree.item(item_id, "values")
        if not values:
            return
        index = int(values[0]) - 1
        vm: QuoteViewModel | None = getattr(self, "_current_vm", None)
        if vm and 0 <= index < len(vm.items_vm):
            self.update_trace(vm.items_vm[index])

    def _on_tax_toggle(self) -> None:
        show = self._show_tax.get()
        state = tk.NORMAL if show else tk.DISABLED
        for key in ("card_rate", "card_tax", "card_incl"):
            card = self._summary_cards.get(key)
            if card:
                card["frame"].configure(state=state)
                if not show:
                    card["value"].configure(text="—")
                else:
                    vm: QuoteViewModel | None = getattr(self, "_current_vm", None)
                    if vm:
                        if key == "card_rate":
                            card["value"].configure(text=vm.display_tax_rate)
                        elif key == "card_tax":
                            card["value"].configure(text=vm.display_tax_amount)
                        elif key == "card_incl":
                            card["value"].configure(text=vm.display_total_incl)


# ---------------------------------------------------------------------------
# BatchQuotePage — batch quotation with file scanning
# ---------------------------------------------------------------------------

class BatchQuotePage(tk.Frame):
    """Batch quotation page with file scanning, table, and progress."""

    def __init__(
        self, parent: tk.Widget,
        on_scan_dir: Callable[[str, bool], list[Any]],
        on_scan_files: Callable[[list[str]], list[Any]],
        on_run_batch: Callable[[list[Any], bool], list[Any]],
        on_export_selected: Callable[[list[Any], str], str],
        on_export_all: Callable[[list[Any], str], str],
        on_open_dir: Callable[[str], None],
        **kw: Any,
    ):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._on_scan_dir = on_scan_dir
        self._on_scan_files = on_scan_files
        self._on_run_batch = on_run_batch
        self._on_export_selected = on_export_selected
        self._on_export_all = on_export_all
        self._on_open_dir = on_open_dir
        self._bundles: list[Any] = []
        self._results: list[Any] = []
        self._use_ai = tk.BooleanVar(value=False)
        self._recursive = tk.BooleanVar(value=True)
        self._build()

    def _build(self) -> None:
        # Header
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="  批量報價", font=_font(14, bold=True),
                 bg=HEADER_BG, fg=HEADER_FG).pack(side=tk.LEFT, pady=10)

        # Toolbar
        toolbar = tk.Frame(self, bg=CARD_BG, bd=1, relief=tk.SOLID)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        buttons = [
            ("選擇資料夾", lambda: self._do_scan_dir()),
            ("選擇檔案", lambda: self._do_scan_files()),
            ("開始批量報價", lambda: self._do_run_batch()),
            ("匯出選中", lambda: self._do_export_selected()),
            ("匯出全部", lambda: self._do_export_all()),
            ("開啟輸出目錄", lambda: self._on_open_dir("runtime/exports")),
        ]
        for text, cmd in buttons:
            tk.Button(toolbar, text=text, font=_font(9), bg="#ecf0f1",
                      fg="#2c3e50", bd=1, padx=8, pady=4, cursor="hand2",
                      relief=tk.FLAT, activebackground=NAV_ACTIVE_BG,
                      activeforeground="#ffffff", command=cmd
                      ).pack(side=tk.LEFT, padx=3, pady=6)

        ttk.Checkbutton(toolbar, text="啟用AI輔助", variable=self._use_ai).pack(
            side=tk.RIGHT, padx=10)
        ttk.Checkbutton(toolbar, text="遞迴子目錄", variable=self._recursive).pack(
            side=tk.RIGHT, padx=10)

        # Stats bar
        self._stats_frame = tk.Frame(self, bg=CONTENT_BG)
        self._stats_frame.pack(fill=tk.X, padx=10, pady=5)
        stats = [
            ("掃描檔案", "0"), ("報價任務", "0"), ("報價完整", "0"),
            ("需要確認", "0"), ("失敗", "0"),
        ]
        self._stat_labels: dict[str, tk.Label] = {}
        for i, (label, val) in enumerate(stats):
            f = tk.Frame(self._stats_frame, bg=CARD_BG, bd=1, relief=tk.SOLID)
            f.pack(side=tk.LEFT, padx=3, pady=2)
            tk.Label(f, text=label, font=_font(8), bg=CARD_BG, fg="#7f8c8d").pack(padx=8, pady=(5, 0))
            lbl = tk.Label(f, text=val, font=_font(16, bold=True), bg=CARD_BG, fg=HEADER_BG)
            lbl.pack(padx=8, pady=(0, 5))
            self._stat_labels[label] = lbl

        # Progress bar
        self._progress = ttk.Progressbar(self, mode='determinate', length=400)
        self._progress.pack(fill=tk.X, padx=10, pady=5)

        self._progress_text = tk.Label(
            self, text="就緒", font=_font(9), bg=CONTENT_BG, fg="#7f8c8d")
        self._progress_text.pack(padx=10)

        # Batch table
        table_frame = tk.LabelFrame(self, text=" 報價任務 ", font=_font(10, bold=True),
                                     bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("#", "圖號", "文件名", "配對", "解析狀態", "報價狀態",
                   "完整度", "待確認", "未稅", "稅額", "含稅", "AI", "提示")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        widths = [30, 100, 140, 80, 80, 90, 55, 50, 80, 80, 80, 40, 120]
        for col, w in zip(columns, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=tk.CENTER if col != "文件名" else tk.W)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.tag_configure("unknown", background=WARNING_BG)
        self._tree.tag_configure("fail", background="#f8d7da")
        self._tree.tag_configure("complete", background="#d4edda")

    # --- Public API ---

    def set_bundles(self, bundles: list[Any]) -> None:
        self._bundles = bundles
        self._tree.delete(*self._tree.get_children())
        for i, b in enumerate(bundles):
            geom = b.geometry_source
            matched = ",".join(f.file_name for f in b.files if f != geom) or "-"
            self._tree.insert("", tk.END, values=(
                i + 1, b.drawing_number, geom.file_name if geom else "(無幾何)",
                matched, "已掃描", "等待處理", "-", "-", "-", "-", "-", "-", ""
            ))
        self._update_stats()

    def update_result(self, idx: int, result: Any) -> None:
        from quotation.ui.viewmodels import STATUS_DISPLAY
        children = self._tree.get_children()
        if idx < len(children):
            item = children[idx]
            st = result.status
            status_display = STATUS_DISPLAY.get(st, st)
            tags = []
            if st == "COMPLETE":
                tags = ["complete"]
            elif st in ("INCOMPLETE", "REVIEW_REQUIRED"):
                tags = ["unknown"]
            elif st in ("PARSE_FAILED", "QUOTE_FAILED"):
                tags = ["fail"]

            self._tree.item(item, values=(
                idx + 1, result.drawing_number,
                result.bundle.geometry_source.file_name if result.bundle.geometry_source else "-",
                ",".join(f.file_name for f in result.bundle.files if f != result.bundle.geometry_source) or "-",
                status_display, status_display,
                f"{result.cost_completion:.0f}%", result.unknown_item_count,
                f"{float(result.subtotal_excluding_tax):,.0f}",
                f"{float(result.tax.tax_amount) if result.tax else 0:,.0f}",
                f"{float(result.total_including_tax):,.0f}",
                "Y" if result.ai_used else "-",
                "; ".join(result.warnings[:1]) if result.warnings else "",
            ), tags=tags)
            self._update_stats()

    def set_progress(self, current: int, total: int, text: str = "") -> None:
        self._progress["maximum"] = total
        self._progress["value"] = current
        self._progress_text.configure(text=text or f"{current}/{total}")

    def set_results(self, results: list[Any]) -> None:
        self._results = results

    def _update_stats(self) -> None:
        results = self._results
        total = len(results)
        complete = sum(1 for r in results if r.status == "COMPLETE")
        review = sum(1 for r in results if r.status in ("INCOMPLETE", "REVIEW_REQUIRED"))
        failed = sum(1 for r in results if r.status in ("PARSE_FAILED", "QUOTE_FAILED", "UNSUPPORTED"))
        scanned = len(self._bundles)

        self._stat_labels.get("掃描檔案", tk.Label()).configure(text=str(scanned))
        self._stat_labels.get("報價任務", tk.Label()).configure(text=str(total))
        self._stat_labels.get("報價完整", tk.Label()).configure(text=str(complete))
        self._stat_labels.get("需要確認", tk.Label()).configure(text=str(review))
        self._stat_labels.get("失敗", tk.Label()).configure(text=str(failed))
        self._progress["value"] = total
        self._progress["maximum"] = max(total, 1)

    # --- Actions ---

    def _do_scan_dir(self) -> None:
        from tkinter import filedialog
        d = filedialog.askdirectory(title="選擇包含圖紙的資料夾")
        if d:
            self._progress_text.configure(text=f"掃描中: {d}")
            self.update_idletasks()
            bundles = self._on_scan_dir(d, self._recursive.get())
            self.set_bundles(bundles)
            self._results = []
            self._progress_text.configure(text=f"掃描完成: {len(bundles)} 個任務")

    def _do_scan_files(self) -> None:
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="選擇圖紙檔案",
            filetypes=[("CAD files", "*.dxf *.DXF *.dwg *.DWG *.pdf *.PDF"), ("All", "*.*")]
        )
        if files:
            bundles = self._on_scan_files(list(files))
            self.set_bundles(bundles)
            self._results = []
            self._progress_text.configure(text=f"掃描完成: {len(bundles)} 個任務")

    def _do_run_batch(self) -> None:
        if not self._bundles:
            messagebox.showwarning("提示", "請先掃描檔案")
            return
        self._progress_text.configure(text="批量報價中...")
        self.update_idletasks()

        # Run in background via simple thread
        import threading
        def _run() -> None:
            results = self._on_run_batch(self._bundles, self._use_ai.get())
            self.after(0, lambda: self._on_batch_done(results))
        threading.Thread(target=_run, daemon=True).start()

    def _on_batch_done(self, results: list[Any]) -> None:
        self._results = results
        for i, r in enumerate(results):
            self.update_result(i, r)
        complete = sum(1 for r in results if r.status == "COMPLETE")
        review = sum(1 for r in results if r.status in ("INCOMPLETE", "REVIEW_REQUIRED"))
        failed = sum(1 for r in results if r.status in ("PARSE_FAILED", "QUOTE_FAILED"))
        self._progress_text.configure(
            text=f"完成: {complete} 完整, {review} 待確認, {failed} 失敗")

    def _do_export_selected(self) -> None:
        from tkinter import filedialog
        if not self._results:
            messagebox.showwarning("提示", "無報價結果可匯出")
            return
        p = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if p:
            self._on_export_selected(self._results, p)
            messagebox.showinfo("完成", f"已匯出: {p}")

    def _do_export_all(self) -> None:
        from tkinter import filedialog
        if not self._results:
            messagebox.showwarning("提示", "無報價結果可匯出")
            return
        p = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if p:
            self._on_export_all(self._results, p)
            messagebox.showinfo("完成", f"已匯出: {p}")


# ---------------------------------------------------------------------------
# HistoryPage — quotation history browser
# ---------------------------------------------------------------------------

class HistoryPage(tk.Frame):
    """View and search past quotations."""

    def __init__(self, parent: tk.Widget, **kw: Any):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._build()

    def _build(self) -> None:
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X); header.pack_propagate(False)
        tk.Label(header, text="  報價記錄", font=_font(14, bold=True),
                 bg=HEADER_BG, fg=HEADER_FG).pack(side=tk.LEFT, pady=10)

        # Search bar
        search = tk.Frame(self, bg=CARD_BG, bd=1, relief=tk.SOLID)
        search.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(search, text="圖號/文件名:", bg=CARD_BG, font=_font(9)).pack(side=tk.LEFT, padx=5)
        self._search_var = tk.StringVar()
        tk.Entry(search, textvariable=self._search_var, width=25).pack(side=tk.LEFT, padx=5)
        tk.Button(search, text="搜尋", command=self._do_search, font=_font(9),
                  bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        from quotation.ui.viewmodels import STATUS_DISPLAY
        self._status_var = tk.StringVar(value="全部")
        status_opts = ["全部"] + list(STATUS_DISPLAY.values())
        ttk.Combobox(search, textvariable=self._status_var, values=status_opts,
                     width=14, state="readonly").pack(side=tk.LEFT, padx=5)

        # Table
        tf = tk.LabelFrame(self, text=" 報價記錄 ", font=_font(10, bold=True),
                           bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID)
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cols = ("ID", "圖號", "文件名", "報價狀態", "完整度", "未稅", "含稅", "時間")
        self._tree = ttk.Treeview(tf, columns=cols, show="headings", height=12)
        widths = [30, 100, 140, 100, 60, 90, 90, 140]
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c); self._tree.column(c, width=w, anchor=tk.CENTER if c != "文件名" else tk.W)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self._tree.yview).pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons
        ctrl = tk.Frame(self, bg=CONTENT_BG)
        ctrl.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(ctrl, text="重新整理", command=self._do_search, font=_font(9)).pack(side=tk.LEFT, padx=3)
        tk.Button(ctrl, text="查看明細", command=self._show_detail, font=_font(9)).pack(side=tk.LEFT, padx=3)

        self._do_search()

    def _do_search(self) -> None:
        try:
            from quotation.application.history_service import QuotationHistory
            h = QuotationHistory()
            q = self._search_var.get().strip()
            st = self._status_var.get()
            st_code = None
            if st and st != "全部":
                from quotation.ui.viewmodels import STATUS_DISPLAY
                for k, v in STATUS_DISPLAY.items():
                    if v == st:
                        st_code = k; break
            rows = h.search(drawing_number=q if q else None, file_name=q if q else None,
                          status=st_code)
            self._tree.delete(*self._tree.get_children())
            for i, r in enumerate(rows):
                self._tree.insert("", tk.END, values=(
                    i + 1, r.get("drawing_number", ""), r.get("file_name", ""),
                    r.get("status_display", r.get("quotation_status", "")),
                    f"{r.get('cost_completion', 0):.0f}%",
                    f"{r.get('subtotal_excl_tax', 0):,.0f}",
                    f"{r.get('total_incl_tax', 0):,.0f}",
                    r.get("created_at", "")[:19],
                ))
        except Exception:
            pass

    def _show_detail(self) -> None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("提示", "請先選擇一筆記錄")
            return
        vals = self._tree.item(sel[0], "values")
        dn = vals[1] if len(vals) > 1 else ""
        try:
            from quotation.application.history_service import QuotationHistory
            h = QuotationHistory()
            rows = h.search(drawing_number=dn, limit=1)
            if rows:
                r = rows[0]
                items = h.get_items(r["quote_id"])
                info = f"圖號: {r['drawing_number']}\n文件: {r['file_name']}\n狀態: {r['status_display']}\n"
                info += f"完整度: {r['cost_completion']:.0f}%\n未稅: {r['subtotal_excl_tax']:,.2f}\n含稅: {r['total_incl_tax']:,.2f}\n"
                info += f"\n明細 ({len(items)} 項):\n"
                for it in items:
                    info += f"  {it['name']} | {it['source_display']} | {it['amount']:,.2f}\n"
                messagebox.showinfo("報價明細", info)
        except Exception as e:
            messagebox.showerror("錯誤", str(e))


# ---------------------------------------------------------------------------
# PriceManagementPage — read-only price browser
# ---------------------------------------------------------------------------

class PriceManagementPage(tk.Frame):
    """Read-only view of the published company pricebook."""

    def __init__(self, parent: tk.Widget, **kw: Any):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._build()

    def _build(self) -> None:
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X); header.pack_propagate(False)
        tk.Label(header, text="  價格管理（唯讀）", font=_font(14, bold=True),
                 bg=HEADER_BG, fg=HEADER_FG).pack(side=tk.LEFT, pady=10)

        # Info bar
        info = tk.Frame(self, bg="#d4edda", bd=1, relief=tk.SOLID)
        info.pack(fill=tk.X, padx=10, pady=(10, 5))
        self._info_label = tk.Label(info, text="載入中...", font=_font(9),
                                     bg="#d4edda", fg="#155724")
        self._info_label.pack(padx=10, pady=5)

        # Notebook for material/process/surface
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._mat_tree = self._make_tree_tab(nb, "材料價格")
        self._proc_tree = self._make_tree_tab(nb, "加工價格")
        self._surf_tree = self._make_tree_tab(nb, "表面處理價格")

        self._load_data()

    def _make_tree_tab(self, nb, title: str) -> ttk.Treeview:
        f = tk.Frame(nb, bg=CARD_BG)
        nb.add(f, text=title)
        cols = ("名稱", "單價", "單位", "來源", "公司價格ID")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=10)
        widths = [160, 100, 80, 120, 180]
        for c, w in zip(cols, widths):
            tree.heading(c, text=c); tree.column(c, width=w, anchor=tk.CENTER if c != "名稱" else tk.W)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def _load_data(self) -> None:
        try:
            import json
            from pathlib import Path
            pb = Path("data/company-pricebook-r01-v1.0-snapshot.json")
            if not pb.exists():
                self._info_label.configure(text="未找到已發布公司價格表")
                return
            data = json.loads(pb.read_text(encoding="utf-8"))
            meta = data.get("metadata", {})
            self._info_label.configure(
                text=f"價格版本: {meta.get('version_id', '?')} | "
                     f"狀態: 已發布 | 生效日期: {meta.get('effective_date', '?')} | "
                     f"材料: {len(data.get('materials', []))} 項 | "
                     f"加工: {len(data.get('processes', []))} 項 | "
                     f"表面: {len(data.get('surfaces', []))} 項")

            for item in data.get("materials", []):
                src = "供應商價格記錄" if item.get("origin_type") == "SUPPLIER_PRICE_RECORD" else "公司核准"
                self._mat_tree.insert("", tk.END, values=(
                    item.get("name", ""), item.get("unit_price", ""),
                    item.get("unit", ""), src, item.get("company_price_id", "")))

            for item in data.get("processes", []):
                self._proc_tree.insert("", tk.END, values=(
                    item.get("name", ""), item.get("unit_price", ""),
                    item.get("unit", ""), "公司核准", item.get("company_price_id", "")))

            for item in data.get("surfaces", []):
                self._surf_tree.insert("", tk.END, values=(
                    item.get("name", ""), item.get("unit_price", ""),
                    item.get("unit", ""), "公司核准", item.get("company_price_id", "")))
        except Exception as e:
            self._info_label.configure(text=f"載入失敗: {e}")


# ---------------------------------------------------------------------------
# SupplierManagementPage — read-only supplier list
# ---------------------------------------------------------------------------

class SupplierManagementPage(tk.Frame):
    """Read-only supplier information display."""

    def __init__(self, parent: tk.Widget, **kw: Any):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._build()

    def _build(self) -> None:
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X); header.pack_propagate(False)
        tk.Label(header, text="  供應商管理（唯讀）", font=_font(14, bold=True),
                 bg=HEADER_BG, fg=HEADER_FG).pack(side=tk.LEFT, pady=10)

        cols = ("供應商名稱", "材料/加工項目", "原始報價", "單位", "報價日期", "審核狀態")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        widths = [160, 160, 120, 80, 120, 150]
        for c, w in zip(cols, widths):
            tree.heading(c, text=c); tree.column(c, width=w, anchor=tk.CENTER if c != "供應商名稱" else tk.W)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree.tag_configure("pending", background=WARNING_BG)

        try:
            import json
            pb = Path("data/company-pricebook-r01-v1.0-snapshot.json")
            if pb.exists():
                data = json.loads(pb.read_text(encoding="utf-8"))
                seen: set[str] = set()
                for item in data.get("materials", []):
                    sid = item.get("origin_supplier_id") or "未記錄"
                    if item.get("origin_type") == "SUPPLIER_PRICE_RECORD":
                        status = "已採用（公司核准價格）"
                        key = f"{sid}:{item.get('name','')}"
                        if key not in seen:
                            seen.add(key)
                            tree.insert("", tk.END, values=(
                                f"供應商-{sid[:8]}", item.get("name", ""),
                                item.get("unit_price", ""), item.get("unit", ""),
                                item.get("effective_from", ""), status))
        except Exception:
            pass

        tk.Label(self, text="供應商原始報價記錄來自已發布公司價格表的 origin_supplier_id 追溯",
                 font=_font(8), bg=CONTENT_BG, fg="#95a5a6").pack(pady=10)


# ---------------------------------------------------------------------------
# SettingsPage — system configuration
# ---------------------------------------------------------------------------

class SettingsPage(tk.Frame):
    """System settings display."""

    def __init__(self, parent: tk.Widget, **kw: Any):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._build()

    def _build(self) -> None:
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X); header.pack_propagate(False)
        tk.Label(header, text="  系統設定", font=_font(14, bold=True),
                 bg=HEADER_BG, fg=HEADER_FG).pack(side=tk.LEFT, pady=10)

        # Settings grid
        sf = tk.LabelFrame(self, text=" 報價設定 ", font=_font(10, bold=True),
                           bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID)
        sf.pack(fill=tk.X, padx=10, pady=10)

        settings = [
            ("稅率", "17% (增值稅)"),
            ("價格基準", "未稅價格 (EXCLUDING_TAX)"),
            ("默認 Excel 輸出目錄", "runtime/exports/"),
            ("當前規則版本", self._get_rule_version()),
            ("當前價格版本", self._get_price_version()),
            ("AI 輔助", self._get_ai_status()),
            ("API 地址", "http://127.0.0.1:8000"),
        ]
        for i, (label, value) in enumerate(settings):
            tk.Label(sf, text=f"{label}：", font=_font(9, bold=True),
                     bg=CARD_BG, fg="#7f8c8d").grid(row=i, column=0, sticky=tk.W, padx=(15, 5), pady=6)
            tk.Label(sf, text=value, font=_font(9), bg=CARD_BG, fg="#2c3e50").grid(
                row=i, column=1, sticky=tk.W, padx=(5, 15), pady=6)

        # AI status detail
        ai_frame = tk.LabelFrame(self, text=" DeepSeek AI 狀態 ", font=_font(10, bold=True),
                                  bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID)
        ai_frame.pack(fill=tk.X, padx=10, pady=5)
        self._ai_detail = tk.Label(ai_frame, text="檢查中...", font=_font(9),
                                    bg=CARD_BG, fg="#2c3e50", justify=tk.LEFT)
        self._ai_detail.pack(padx=15, pady=10, anchor=tk.W)
        self._check_ai()

        tk.Label(self, text="API Key 從未顯示 — 安全保管於 runtime/secrets/",
                 font=_font(8), bg=CONTENT_BG, fg="#95a5a6").pack(pady=10)

    def _get_rule_version(self) -> str:
        try:
            import yaml; d = yaml.safe_load(Path("rules/quotation-rules.yaml").read_text(encoding="utf-8"))
            return d.get("version", "?")
        except Exception:
            return "?"

    def _get_price_version(self) -> str:
        try:
            j = json.loads(Path("data/current-version-pointer.json").read_text(encoding="utf-8"))
            return j.get("current_version", "?")
        except Exception:
            return "?"

    def _get_ai_status(self) -> str:
        from quotation.infrastructure.secrets.secret_locator import SecretLocator
        return "已配置" if SecretLocator.is_configured() else "未配置"

    def _check_ai(self) -> None:
        try:
            from quotation.infrastructure.secrets.secret_locator import SecretLocator
            key = SecretLocator.get_deepseek_key()
            if key:
                from quotation.infrastructure.ai.deepseek_client import DeepSeekClient
                c = DeepSeekClient(api_key=key)
                h = c.health_check()
                if h.get("reachable"):
                    self._ai_detail.configure(
                        text=f"狀態: 已連接\n模型: {h.get('model','?')}\n延遲: {h.get('latency_ms','?')}ms")
                else:
                    self._ai_detail.configure(text=f"狀態: 不可用\n原因: {h.get('error','?')}")
            else:
                self._ai_detail.configure(text="狀態: 未配置\n設置方式: 執行 tools/prepare_runtime_secrets.py")
        except Exception as e:
            self._ai_detail.configure(text=f"狀態: 檢查失敗\n{type(e).__name__}")
