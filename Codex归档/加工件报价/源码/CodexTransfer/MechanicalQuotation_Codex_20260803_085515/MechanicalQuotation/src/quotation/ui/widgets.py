"""Reusable Tkinter widgets for the quotation demo UI."""

from __future__ import annotations

import tkinter as tk
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
