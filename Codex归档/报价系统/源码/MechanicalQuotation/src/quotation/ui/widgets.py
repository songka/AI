"""Reusable Tkinter widgets for the quotation demo UI."""

from __future__ import annotations

import calendar
import json
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

from quotation.infrastructure.secrets.secret_locator import SecretLocator
from quotation.ui.localization import display_value, field_label
from quotation.ui.viewmodels import QuoteItemViewModel, QuoteViewModel

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


class DatePickerEntry(ttk.Frame):
    """Dependency-free ISO date entry with a clickable monthly calendar."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        textvariable: tk.StringVar | None = None,
        width: int = 34,
    ) -> None:
        super().__init__(master)
        self.variable = textvariable or tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.variable, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self, text="选择日期", width=8, command=self._open_calendar).pack(
            side=tk.LEFT, padx=(5, 0)
        )

    def get(self) -> str:
        return self.variable.get()

    def _selected_date(self) -> date:
        try:
            return datetime.strptime(self.variable.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            return date.today()

    def _open_calendar(self) -> None:
        selected = self._selected_date()
        popup = tk.Toplevel(self)
        popup.title("选择日期")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        year_month = [selected.year, selected.month]

        header = ttk.Frame(popup, padding=(8, 8, 8, 3))
        header.pack(fill=tk.X)
        title = ttk.Label(header, anchor=tk.CENTER, font=_font(10, True))
        title.pack(side=tk.LEFT, fill=tk.X, expand=True)
        body = ttk.Frame(popup, padding=(8, 3, 8, 8))
        body.pack()

        def choose(day: int) -> None:
            self.variable.set(date(year_month[0], year_month[1], day).isoformat())
            popup.destroy()

        def render() -> None:
            for child in body.winfo_children():
                child.destroy()
            title.configure(text=f"{year_month[0]} 年 {year_month[1]} 月")
            for column, name in enumerate(("一", "二", "三", "四", "五", "六", "日")):
                ttk.Label(body, text=name, anchor=tk.CENTER, width=4).grid(
                    row=0, column=column, padx=1, pady=1
                )
            weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(
                year_month[0], year_month[1]
            )
            for row, week in enumerate(weeks, start=1):
                for column, day_number in enumerate(week):
                    if not day_number:
                        ttk.Label(body, text="", width=4).grid(row=row, column=column)
                        continue
                    ttk.Button(
                        body,
                        text=str(day_number),
                        width=3,
                        command=lambda value=day_number: choose(value),
                    ).grid(row=row, column=column, padx=1, pady=1)

        def change_month(offset: int) -> None:
            value = year_month[1] - 1 + offset
            year_month[0] += value // 12
            year_month[1] = value % 12 + 1
            render()

        ttk.Button(header, text="‹", width=3, command=lambda: change_month(-1)).pack(
            side=tk.LEFT
        )
        ttk.Button(header, text="›", width=3, command=lambda: change_month(1)).pack(
            side=tk.RIGHT
        )
        render()


def _configure_progress_styles(widget: tk.Widget) -> None:
    """Create consistent high-contrast progress styles for quotation pages."""
    style = ttk.Style(widget)
    for name, color in (
        ("Quote", NAV_ACTIVE_BG),
        ("QuoteSuccess", STATUS_GREEN),
        ("QuoteWarning", STATUS_ORANGE),
        ("QuoteError", STATUS_RED),
    ):
        style.configure(
            f"{name}.Horizontal.TProgressbar",
            troughcolor="#e8eef3",
            background=color,
            lightcolor=color,
            darkcolor=color,
            bordercolor="#d5dde5",
            thickness=14,
        )


# ---------------------------------------------------------------------------
# NavPanel — left sidebar
# ---------------------------------------------------------------------------

class NavPanel(tk.Frame):
    """Left navigation sidebar with dark background."""

    NAV_ITEMS = [
        ("新建报价", "\U0001f4c4"),
        ("批量报价", "\U0001f4e6"),
        ("报价记录", "\U0001f4da"),
        ("价格管理", "\U0001f4c8"),
        ("供应商管理", "\U0001f3ed"),
        ("价格审核", "\u2705"),
        ("用户管理", "👥"),
        ("外接Skill设置", "🔌"),
        ("系统设置", "⚙️"),
        ("管理员登录", "🔐"),
        ("退出登录", "↩"),
    ]

    def __init__(
        self,
        parent: tk.Widget,
        on_nav_change: Callable[[str], None],
        allowed_items: set[str] | None = None,
        **kw: Any,
    ):
        super().__init__(parent, bg=NAV_BG, width=200, **kw)
        self._on_nav_change = on_nav_change
        self._allowed_items = allowed_items
        self._active_button: tk.Button | None = None
        self._buttons: dict[str, tk.Button] = {}
        self._build()

    def _build(self) -> None:
        self.pack_propagate(False)
        # Logo area
        logo_frame = tk.Frame(self, bg=NAV_BG, height=80)
        logo_frame.pack(fill=tk.X, pady=(20, 10))
        logo_frame.pack_propagate(False)
        tk.Label(
            logo_frame, text="智能报价系统", bg=NAV_BG, fg=NAV_FG,
            font=_font(11, bold=True),
        ).pack(pady=(15, 0))
        tk.Label(
            logo_frame, text="机械加工件报价与审核", bg=NAV_BG, fg="#95a5a6",
            font=_font(8),
        ).pack()

        # Separator
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=10)

        # Reserve the footer before the expanding navigation viewport.
        tk.Label(
            self, text="版本 2.0", bg=NAV_BG, fg="#7f8c8d",
            font=_font(8),
        ).pack(side=tk.BOTTOM, pady=15)

        # Keep the long navigation reachable at the supported 600px window height.
        nav_host = tk.Frame(self, bg=NAV_BG)
        nav_host.pack(fill=tk.BOTH, expand=True)
        nav_canvas = tk.Canvas(nav_host, bg=NAV_BG, highlightthickness=0, bd=0)
        nav_scrollbar = ttk.Scrollbar(
            nav_host, orient=tk.VERTICAL, command=nav_canvas.yview
        )
        nav_buttons = tk.Frame(nav_canvas, bg=NAV_BG)
        nav_window = nav_canvas.create_window((0, 0), window=nav_buttons, anchor=tk.NW)
        nav_buttons.bind(
            "<Configure>",
            lambda _event: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")),
        )
        nav_canvas.bind(
            "<Configure>",
            lambda event: nav_canvas.itemconfigure(nav_window, width=event.width),
        )
        nav_canvas.configure(yscrollcommand=nav_scrollbar.set)
        nav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        nav_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Nav buttons
        for name, icon in self.NAV_ITEMS:
            if self._allowed_items is not None and name not in self._allowed_items:
                continue
            btn = tk.Button(
                nav_buttons,
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
            self._buttons[name] = btn
            if name == "新建报价":
                self._active_button = btn
                btn.configure(bg=NAV_ACTIVE_BG, fg="#ffffff")

    def _select(self, name: str) -> None:
        """Highlight the active nav item and notify parent."""
        for button in self._buttons.values():
            button.configure(bg=NAV_BUTTON_BG, fg=NAV_FG)
        selected = self._buttons.get(name)
        if selected is not None:
            selected.configure(bg=NAV_ACTIVE_BG, fg="#ffffff")
            selected.focus_set()
            self._active_button = selected
        self._on_nav_change(name)


class SystemSettingsPage(tk.Frame):
    """Editable non-secret settings and runtime health overview."""

    def __init__(
        self,
        parent: tk.Widget,
        settings_service: Any,
        on_auth_required: Callable[[], bool] | None = None,
        **kw: Any,
    ):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._service = settings_service
        self._on_auth_required = on_auth_required
        self._converter_path = tk.StringVar()
        self._api_host = tk.StringVar()
        self._api_port = tk.StringVar()
        self._smb_root = tk.StringVar()
        self._smb_cache_dir = tk.StringVar()
        self._database_address = tk.StringVar()
        self._auth_enabled = tk.BooleanVar(value=False)
        self._status_labels: dict[str, tk.Label] = {}
        self._build()
        self.refresh()

    def _build(self) -> None:
        tk.Label(self, text="系统设置", bg=CONTENT_BG, fg="#2c3e50", font=_font(18, True)).pack(
            anchor=tk.W, padx=24, pady=(20, 10)
        )
        card = tk.LabelFrame(
            self, text=" 外部转换器与本机服务 ", bg=CARD_BG, fg="#2c3e50",
            font=_font(10, True), padx=16, pady=12,
        )
        card.pack(fill=tk.X, padx=24, pady=8)
        card.columnconfigure(1, weight=1)

        rows = [
            ("DWG 转换器", self._converter_path),
            ("接口地址", self._api_host),
            ("接口端口", self._api_port),
            ("SMB 公共槽", self._smb_root),
            ("本地缓存", self._smb_cache_dir),
            ("数据库地址", self._database_address),
        ]
        for index, (label, variable) in enumerate(rows):
            tk.Label(card, text=f"{label}：", bg=CARD_BG, font=_font(9, True)).grid(
                row=index, column=0, sticky=tk.W, padx=4, pady=7
            )
            tk.Entry(card, textvariable=variable).grid(
                row=index, column=1, sticky=tk.EW, padx=4, pady=7
            )
        tk.Button(card, text="选择转换器", command=self._select_converter).grid(
            row=0, column=2, padx=4, pady=7
        )
        tk.Button(card, text="选择数据库", command=self._select_database).grid(
            row=5, column=2, padx=4, pady=7
        )
        key_actions = tk.Frame(card, bg=CARD_BG)
        key_actions.grid(row=6, column=0, columnspan=3, sticky=tk.W, padx=4, pady=7)
        tk.Label(
            key_actions, text="人工智能 Key：", bg=CARD_BG, font=_font(9, True)
        ).pack(side=tk.LEFT)
        tk.Button(key_actions, text="从文件设置/更换", command=self._select_ai_key).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(key_actions, text="删除本机 Key", command=self._remove_ai_key).pack(
            side=tk.LEFT, padx=4
        )
        tk.Label(
            key_actions, text="Key 内容不会显示", bg=CARD_BG, fg="#7f8c8d", font=_font(9)
        ).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(
            card,
            text="启用账号登录与权限控制（保存后立即登录）",
            variable=self._auth_enabled,
            bg=CARD_BG,
            anchor=tk.W,
        ).grid(row=7, column=0, columnspan=3, sticky=tk.W, padx=4, pady=7)

        actions = tk.Frame(card, bg=CARD_BG)
        actions.grid(row=8, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        tk.Button(actions, text="保存设置", command=self._save).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="刷新状态", command=self.refresh).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="立即同步公共资料", command=self._sync_smb).pack(
            side=tk.LEFT, padx=4
        )

        status_card = tk.LabelFrame(
            self, text=" 运行状态 ", bg=CARD_BG, fg="#2c3e50",
            font=_font(10, True), padx=16, pady=12,
        )
        status_card.pack(fill=tk.X, padx=24, pady=8)
        for index, key in enumerate(
            (
                "登录模式", "转换器", "人工智能辅助", "数据库", "SMB 公共槽",
                "本地缓存", "设置文件",
            )
        ):
            tk.Label(status_card, text=f"{key}：", bg=CARD_BG, font=_font(9, True)).grid(
                row=index, column=0, sticky=tk.W, padx=4, pady=6
            )
            value = tk.Label(status_card, text="—", bg=CARD_BG, fg="#2c3e50", font=_font(9))
            value.grid(row=index, column=1, sticky=tk.W, padx=4, pady=6)
            self._status_labels[key] = value

        tk.Label(
            self,
            text=(
                "安全说明：DeepSeek Key 单独保存在 runtime/secrets，本页面不显示内容；"
                "数据库地址切换在重启后生效。"
            ),
            bg=CONTENT_BG, fg="#7f8c8d", font=_font(9),
        ).pack(anchor=tk.W, padx=28, pady=8)

    def _select_converter(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 ODA DWG 转换器",
            filetypes=[("ODA 转换器", "ODAFileConverter.exe"), ("可执行文件", "*.exe")],
        )
        if path:
            self._converter_path.set(path)

    def _select_database(self) -> None:
        path = filedialog.asksaveasfilename(
            title="选择或新建报价数据库",
            defaultextension=".db",
            filetypes=[("SQLite 数据库", "*.db *.sqlite *.sqlite3"), ("所有文件", "*.*")],
        )
        if path:
            self._database_address.set(path)

    def _select_ai_key(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 DeepSeek Key 文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as stream:
                SecretLocator.save_deepseek_key(stream.read())
            self.refresh()
            messagebox.showinfo(
                "Key 已设置", "Key 已单独保存到本机运行目录，配置页面不会显示内容。"
            )
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror("Key 设置失败", str(exc))

    def _remove_ai_key(self) -> None:
        if not messagebox.askyesno("删除本机 Key", "确定删除本程序运行目录中的 Key 吗？"):
            return
        try:
            removed = SecretLocator.remove_deepseek_key()
            self.refresh()
            messagebox.showinfo("处理完成", "本机 Key 已删除。" if removed else "本机未保存 Key。")
        except OSError as exc:
            messagebox.showerror("删除失败", str(exc))

    def _save(self) -> None:
        try:
            was_enabled = bool(self._service.load().get("auth_enabled", False))
            self._service.save(
                dwg_converter_path=self._converter_path.get(),
                api_host=self._api_host.get().strip(),
                api_port=int(self._api_port.get()),
                smb_root=self._smb_root.get().strip(),
                smb_cache_dir=self._smb_cache_dir.get().strip(),
                smb_sync_enabled=True,
                auth_enabled=self._auth_enabled.get(),
                database_address=self._database_address.get().strip(),
            )
            self.refresh()
            if (
                self._auth_enabled.get()
                and not was_enabled
                and self._on_auth_required is not None
            ):
                messagebox.showinfo(
                    "登录模式已启用",
                    "设置已保存，现在请直接建立管理员或登录，无需重启软件。",
                    parent=self,
                )
                if self._on_auth_required():
                    return
                self._auth_enabled.set(False)
                self._service.save(
                    dwg_converter_path=self._converter_path.get(),
                    api_host=self._api_host.get().strip(),
                    api_port=int(self._api_port.get()),
                    smb_root=self._smb_root.get().strip(),
                    smb_cache_dir=self._smb_cache_dir.get().strip(),
                    smb_sync_enabled=True,
                    auth_enabled=False,
                    database_address=self._database_address.get().strip(),
                )
                self.refresh()
                messagebox.showwarning(
                    "未完成登录",
                    "已取消本次登录，系统已恢复为免登录模式。",
                    parent=self,
                )
                return
            messagebox.showinfo(
                "保存成功", "系统设置已保存；若修改了数据库地址，请重启软件后使用新数据库。"
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("保存失败", str(exc))

    def _sync_smb(self) -> None:
        try:
            result = self._service.sync_shared_storage()
            self.refresh()
            if result["status"] == "online":
                messagebox.showinfo(
                    "同步完成",
                    f"公共资料同步完成；更新 {result['changed_files']} 个文件。",
                )
            else:
                messagebox.showwarning(
                    "同步未完成", result.get("error") or "当前使用本地缓存"
                )
        except (ValueError, OSError) as exc:
            messagebox.showerror("同步失败", str(exc))

    def refresh(self) -> None:
        status = self._service.status()
        settings = status["settings"]
        self._converter_path.set(str(settings.get("dwg_converter_path", "")))
        self._api_host.set(str(settings.get("api_host", "127.0.0.1")))
        self._api_port.set(str(settings.get("api_port", 8000)))
        self._smb_root.set(str(settings.get("smb_root", "")))
        self._smb_cache_dir.set(str(settings.get("smb_cache_dir", "runtime/cache/smb")))
        self._database_address.set(
            str(settings.get("database_address", "runtime/data/quotation_history.db"))
        )
        self._auth_enabled.set(bool(settings.get("auth_enabled", False)))
        self._status_labels["登录模式"].configure(
            text="已启用（当前会话要求登录）" if self._auth_enabled.get() else "未启用（默认免登录）"
        )
        converter = status["converter"]
        self._status_labels["转换器"].configure(
            text="可用" if converter.get("available") else "不可用",
            fg=STATUS_GREEN if converter.get("available") else STATUS_RED,
        )
        self._status_labels["人工智能辅助"].configure(
            text="已配置" if status["ai_configured"] else "未配置",
            fg=STATUS_GREEN if status["ai_configured"] else STATUS_ORANGE,
        )
        database = status["database"]
        self._status_labels["数据库"].configure(
            text=("已存在：" if database["exists"] else "首次保存时创建：")
            + database["resolved_path"],
            fg=STATUS_GREEN if database["exists"] else STATUS_ORANGE,
        )
        shared = status["shared_storage"]
        smb_available = shared["smb"]["available"]
        self._status_labels["SMB 公共槽"].configure(
            text="已连接" if smb_available else "离线",
            fg=STATUS_GREEN if smb_available else STATUS_ORANGE,
        )
        self._status_labels["本地缓存"].configure(
            text=(
                f"可用（{shared['cached_files']} 个文件）"
                if shared["cache_available"]
                else "尚未同步"
            ),
            fg=STATUS_GREEN if shared["cache_available"] else STATUS_ORANGE,
        )
        self._status_labels["设置文件"].configure(text=status["settings_path"])


class StructuredDetailWindow(tk.Toplevel):
    """Tabbed, table-based detail window; never exposes raw JSON to users."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        sections: list[tuple[str, list[tuple[str, str, int]], list[dict[str, Any]]]],
    ) -> None:
        super().__init__(parent)
        self.title(title)
        width = min(1280, max(self.winfo_screenwidth() - 100, 900))
        height = min(760, max(self.winfo_screenheight() - 140, 520))
        self.geometry(f"{width}x{height}")
        self.minsize(760, 440)
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for tab_name, columns, rows in sections:
            frame = tk.Frame(notebook, bg=CARD_BG)
            notebook.add(frame, text=tab_name)
            names = [column[0] for column in columns]
            tree = ttk.Treeview(frame, columns=names, show="headings")
            for key, label, width in columns:
                tree.heading(key, text=label)
                tree.column(key, width=width, anchor=tk.W)
            yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            tree.grid(row=0, column=0, sticky=tk.NSEW)
            yscroll.grid(row=0, column=1, sticky=tk.NS)
            xscroll.grid(row=1, column=0, sticky=tk.EW)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            row_by_item: dict[str, dict[str, Any]] = {}
            for row in rows:
                item_id = tree.insert(
                    "", tk.END, values=[row.get(key, "—") for key in names]
                )
                row_by_item[item_id] = row

            def show_complete_row(
                event: tk.Event | None = None,
                *,
                current_tree: ttk.Treeview = tree,
                current_rows: dict[str, dict[str, Any]] = row_by_item,
                current_columns: list[tuple[str, str, int]] = columns,
                current_tab: str = tab_name,
            ) -> None:
                if event is not None:
                    item_id = current_tree.identify_row(event.y)
                    if item_id:
                        current_tree.selection_set(item_id)
                        current_tree.focus(item_id)
                selection = current_tree.selection()
                if not selection:
                    return
                row = current_rows.get(str(selection[0]))
                if row is not None:
                    self._show_complete_row(current_tab, current_columns, row)

            tree.bind("<Double-1>", show_complete_row)
            menu = tk.Menu(tree, tearoff=False)
            menu.add_command(label="查看完整内容", command=show_complete_row)

            def popup_menu(
                event: tk.Event,
                *,
                current_tree: ttk.Treeview = tree,
                current_menu: tk.Menu = menu,
            ) -> None:
                item_id = current_tree.identify_row(event.y)
                if not item_id:
                    return
                current_tree.selection_set(item_id)
                current_tree.focus(item_id)
                try:
                    current_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    current_menu.grab_release()

            tree.bind("<Button-3>", popup_menu)
        tk.Button(self, text="关闭", command=self.destroy).pack(pady=(0, 10))

    def _show_complete_row(
        self,
        tab_name: str,
        columns: list[tuple[str, str, int]],
        row: dict[str, Any],
    ) -> None:
        detail = tk.Toplevel(self)
        detail.title(f"完整内容 — {tab_name}")
        detail.geometry("900x600")
        detail.minsize(620, 400)
        container = tk.Frame(detail, bg=CARD_BG)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text = tk.Text(
            container,
            wrap=tk.WORD,
            font=_font(10),
            padx=10,
            pady=10,
            background="#ffffff",
        )
        scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for key, label, _width in columns:
            value = row.get(key, "—")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2, default=str)
            text.insert(tk.END, f"{label}\n", ("label",))
            text.insert(tk.END, f"{value}\n\n")
        text.tag_configure("label", font=_font(10, True), foreground=HEADER_BG)
        text.configure(state=tk.DISABLED)
        tk.Button(detail, text="关闭", command=detail.destroy).pack(pady=(0, 10))
        detail.transient(self)
        detail.lift()
        detail.focus_force()


def record_detail_sections(row: dict[str, Any]) -> list[tuple[str, list[tuple[str, str, int]], list[dict[str, Any]]]]:
    """Convert an arbitrary management record into a friendly field table."""
    rows = [
        {"field": field_label(key), "value": display_value(key, value)}
        for key, value in row.items()
        if not isinstance(value, (dict, list))
    ]
    return [("基本信息", [("field", "字段", 230), ("value", "内容", 720)], rows)]


def quote_detail_sections(detail: dict[str, Any]) -> list[tuple[str, list[tuple[str, str, int]], list[dict[str, Any]]]]:
    """Build structured tabs for a persisted quote and its audit history."""
    quote_rows = [
        {"field": field_label(key), "value": display_value(key, value)}
        for key, value in detail.get("quote", {}).items()
        if key not in {"status_display"}
    ]
    item_rows = []
    for item in detail.get("items", []):
        item_rows.append({
            "line_id": display_value("line_id", item.get("line_id")),
            "category": display_value("category", item.get("category")),
            "name": display_value("name", item.get("name")),
            "source": item.get("source_display") or display_value("source", item.get("source")),
            "quantity": display_value("quantity", item.get("quantity")),
            "unit": display_value("unit", item.get("unit")),
            "unit_price": display_value("unit_price", item.get("unit_price")),
            "amount": display_value("amount", item.get("amount")),
            "confidence": display_value("confidence", item.get("confidence")),
            "status": display_value("status", item.get("status")),
            "basis": item.get("resolution_display") or "—",
        })
    override_rows = [
        {
            "field_name": display_value("field_name", key),
            "value": display_value("value", row.get("value")),
            "updated_at": display_value("updated_at", row.get("updated_at")),
        }
        for key, row in detail.get("overrides", {}).items()
    ]
    review_rows = [
        {
            key: display_value(key, review.get(key))
            for key in (
                "field_name", "line_id", "old_value", "new_value", "reason", "operator",
                "quote_version_before", "quote_version_after", "created_at",
            )
        }
        for review in detail.get("reviews", [])
    ]
    return [
        ("报价摘要", [("field", "字段", 230), ("value", "内容", 720)], quote_rows),
        ("费用明细", [
            ("line_id", "费用行编号", 110), ("category", "费用类别", 100),
            ("name", "报价项目", 180), ("source", "价格来源", 150),
            ("quantity", "数量", 70), ("unit", "单位", 70),
            ("unit_price", "单价", 90), ("amount", "未税金额", 100),
            ("confidence", "可信度", 70), ("status", "状态", 90),
            ("basis", "定价依据", 220),
        ], item_rows),
        ("人工调整", [
            ("field_name", "调整字段", 180), ("value", "调整值", 420),
            ("updated_at", "更新时间", 220),
        ], override_rows),
        ("审核记录", [
            ("field_name", "调整字段", 120), ("line_id", "费用行编号", 110),
            ("old_value", "调整前", 120), ("new_value", "调整后", 120),
            ("reason", "调整原因", 220), ("operator", "操作人", 100),
            ("quote_version_before", "调整前版本", 100),
            ("quote_version_after", "调整后版本", 100), ("created_at", "时间", 180),
        ], review_rows),
    ]


def batch_ai_detail_sections(result: Any) -> list[tuple[str, list[tuple[str, str, int]], list[dict[str, Any]]]]:
    """Build friendly batch-item tabs for AI and Skill step outputs."""
    suggestions = dict(getattr(result, "ai_suggestions", {}) or {})

    def compact(value: Any, limit: int = 1200) -> str:
        if value in (None, "", [], {}):
            return "—"
        if isinstance(value, list):
            text = "；".join(
                compact(item, limit=300) if isinstance(item, (dict, list)) else str(item)
                for item in value
            )
        elif isinstance(value, dict):
            text = json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", "："),
                default=str,
            )
        else:
            text = str(value)
        return text[:limit]

    retry = suggestions.get("dependency_retry") or {}
    overview_rows = [
        {"field": "图号", "value": getattr(result, "drawing_number", "—")},
        {
            "field": "AI 与 Skill 的区别",
            "value": "11 项是报价流程步骤；4 个 DeepSeek 专职角色执行其中部分步骤，另有 1 个内部风险汇总。",
        },
        {"field": "报价状态", "value": getattr(result, "status", "—")},
        {"field": "是否使用 AI", "value": "是" if getattr(result, "ai_used", False) else "否"},
        {"field": "AI 精确缓存", "value": compact(suggestions.get("batch_ai_cache"))},
        {"field": "依赖重试", "value": compact(retry)},
        {"field": "警告", "value": compact(getattr(result, "warnings", []))},
        {"field": "错误", "value": compact(getattr(result, "errors", []))},
    ]
    agent_rows = []
    for name, payload in (suggestions.get("agents") or {}).items():
        data = payload if isinstance(payload, dict) else {"result": payload}
        conclusion = (
            data.get("summary")
            or data.get("verdict")
            or data.get("part_category")
            or data.get("result")
            or (f"{len(payload)} 项工艺" if isinstance(payload, list) else "已执行")
        )
        evidence = (
            data.get("evidence")
            or data.get("issues")
            or data.get("risks")
            or data.get("actions")
            or payload
        )
        agent_rows.append({
            "agent": name,
            "executor": (
                "内部规则汇总" if name == "风险汇总智能体" else "内置 DeepSeek"
            ),
            "conclusion": compact(conclusion, 100000),
            "confidence": data.get("confidence", "—"),
            "evidence": compact(evidence, 100000),
        })
    process_rows = [
        {
            "name": item.get("process_name") or item.get("code") or "—",
            "hours": item.get("estimated_hours", "—"),
            "confidence": item.get("confidence", "—"),
            "evidence": compact(item.get("evidence"), 100000),
        }
        for item in suggestions.get("processes", [])
        if isinstance(item, dict)
    ]
    skill_traces = [
        trace for trace in suggestions.get("skill_debug_trace", [])
        if isinstance(trace, dict)
    ]
    unknown_trace = next(
        (trace for trace in skill_traces if trace.get("step") == "UNKNOWN_ESTIMATION"),
        {},
    )
    external_runs = [
        run for run in suggestions.get("external_skills", [])
        if isinstance(run, dict)
    ]
    unknown_run = next(
        (
            run for run in external_runs
            if "UNKNOWN_ESTIMATION" in (run.get("selected_steps") or [])
        ),
        {},
    )
    unknown_skill = unknown_run.get("skill") or {}
    unknown_agent = unknown_run.get("agent") or {}
    default_unknown_skill = (
        unknown_trace.get("provider")
        or unknown_skill.get("name_zh")
        or "内置待确认项 AI 估价 Skill"
    )
    default_unknown_agent = (
        unknown_trace.get("agent")
        or unknown_agent.get("name_zh")
        or "内置待确认项价格智能体"
    )
    estimate_rows = [
        {
            "line_id": item.get("line_id", "—"),
            "unit_price": item.get("unit_price", "—"),
            "quantity": item.get("quantity", "—"),
            "amount": item.get("amount", "—"),
            "confidence": item.get("confidence", "—"),
            "skill": item.get("skill_name") or default_unknown_skill,
            "agent": item.get("agent_name") or default_unknown_agent,
            "reason": compact(item.get("reason"), 100000),
        }
        for item in suggestions.get("price_estimates", [])
        if isinstance(item, dict)
    ]
    quote_rows = []
    quote = getattr(result, "quote", None)
    for item in getattr(quote, "items", []) or []:
        source = getattr(item, "source", None)
        confidence = getattr(item, "confidence", None)
        quote_rows.append({
            "name": getattr(item, "name", "—"),
            "category": display_value("category", getattr(item, "category", None)),
            "quantity": getattr(item, "quantity", "—"),
            "unit": display_value("unit", getattr(item, "unit", None)),
            "unit_price": getattr(item, "unit_price", "—"),
            "amount": getattr(item, "amount", "—"),
            "source": display_value("source", getattr(source, "value", source)),
            "confidence": display_value(
                "confidence", getattr(confidence, "value", confidence)
            ),
            "basis": getattr(item, "resolution_source", None) or "—",
            "evidence": compact(getattr(item, "evidence", None), 100000),
            "note": compact(getattr(item, "note", None), 100000),
        })
    trace_rows = [
        {
            "step": trace.get("step_name_zh") or trace.get("step") or "—",
            "provider": trace.get("provider", "—"),
            "provider_type": trace.get("provider_type", "—"),
            "agent": trace.get("agent") or "未单独绑定",
            "processes": "、".join(trace.get("process_codes") or []) or "通用步骤",
            "status": trace.get("status", "—"),
            "duration": trace.get("duration_ms") or "—",
            "output": compact(trace.get("output"), 100000),
        }
        for trace in skill_traces
    ]
    return [
        ("执行概况", [("field", "字段", 180), ("value", "内容", 790)], overview_rows),
        ("正式报价明细", [
            ("name", "报价项目", 170), ("category", "类别", 80),
            ("quantity", "数量/工时", 85), ("unit", "单位", 65),
            ("unit_price", "单价", 80), ("amount", "金额", 85),
            ("source", "价格来源", 120), ("confidence", "可信度", 70),
            ("basis", "定价/执行来源", 190), ("evidence", "计算依据", 300),
            ("note", "审核提示", 250),
        ], quote_rows),
        ("AI 角色（4+1）", [
            ("agent", "角色", 170), ("executor", "真实执行类型", 130),
            ("conclusion", "结论", 260),
            ("confidence", "可信度", 80), ("evidence", "证据、问题或建议", 470),
        ], agent_rows),
        ("工艺路线", [
            ("name", "工艺", 140), ("hours", "估算工时", 90),
            ("confidence", "可信度", 80), ("evidence", "选择依据", 660),
        ], process_rows),
        ("AI 估价", [
            ("line_id", "费用行", 120), ("unit_price", "单价", 90),
            ("quantity", "数量", 70), ("amount", "金额", 90),
            ("confidence", "可信度", 80), ("skill", "使用 Skill", 190),
            ("agent", "执行智能体", 170), ("reason", "估价依据", 420),
        ], estimate_rows),
        ("Skill 调试", [
            ("step", "步骤", 170), ("provider", "执行方", 160),
            ("provider_type", "执行类型", 110), ("agent", "执行智能体", 170),
            ("processes", "具体工艺", 150), ("status", "状态", 130),
            ("duration", "耗时ms", 80), ("output", "输出摘要", 400),
        ], trace_rows),
    ]


class ManagementPage(tk.Frame):
    """Searchable management table used by history, pricebook, and supplier pages."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        title: str,
        columns: list[tuple[str, str, int]],
        loader: Callable[[str, str], list[dict[str, Any]]],
        on_detail: Callable[[dict[str, Any]], None] | None = None,
        on_export: Callable[[dict[str, Any]], None] | None = None,
        on_review: Callable[[dict[str, Any]], None] | None = None,
        actions: list[tuple[str, Callable[[dict[str, Any] | None], None], bool]] | None = None,
        filter_values: list[str] | None = None,
        **kw: Any,
    ):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._columns = columns
        self._loader = loader
        self._on_detail = on_detail
        self._on_export = on_export
        self._on_review = on_review
        self._rows: dict[str, dict[str, Any]] = {}

        tk.Label(self, text=title, bg=CONTENT_BG, fg="#2c3e50", font=_font(18, True)).pack(
            anchor=tk.W, padx=24, pady=(20, 10)
        )
        toolbar = tk.Frame(self, bg=CONTENT_BG)
        toolbar.pack(fill=tk.X, padx=24, pady=(0, 10))
        tk.Label(toolbar, text="关键词：", bg=CONTENT_BG).pack(side=tk.LEFT)
        self._query = tk.Entry(toolbar, width=26)
        self._query.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(toolbar, text="状态/类型：", bg=CONTENT_BG).pack(side=tk.LEFT)
        self._filter = ttk.Combobox(
            toolbar, values=filter_values or [""], state="readonly", width=22
        )
        self._filter.set("")
        self._filter.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(toolbar, text="搜尋/重新整理", command=self.refresh).pack(side=tk.LEFT)
        if on_detail:
            tk.Button(toolbar, text="查看明細", command=self._detail).pack(side=tk.RIGHT, padx=4)
        if on_export:
            tk.Button(toolbar, text="重新匯出", command=self._export).pack(side=tk.RIGHT, padx=4)
        if on_review:
            tk.Button(toolbar, text="人工審核", command=self._review).pack(side=tk.RIGHT, padx=4)
        for label, callback, needs_selection in reversed(actions or []):
            tk.Button(
                toolbar,
                text=label,
                command=lambda cb=callback, needed=needs_selection: self._action(cb, needed),
            ).pack(side=tk.RIGHT, padx=4)

        names = [column[0] for column in columns]
        table_frame = tk.Frame(self, bg=CONTENT_BG)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))
        self._tree = ttk.Treeview(table_frame, columns=names, show="headings")
        for key, label, width in columns:
            self._tree.heading(key, text=label)
            self._tree.column(key, width=width, anchor=tk.W)
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        horizontal = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        horizontal.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(fill=tk.BOTH, expand=True)
        self._tree.bind("<Double-1>", lambda _event: self._detail())
        self.refresh()

    def refresh(self) -> None:
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        self._rows.clear()
        for index, row in enumerate(self._loader(self._query.get().strip(), self._filter.get())):
            iid = str(index)
            self._rows[iid] = row
            self._tree.insert("", tk.END, iid=iid, values=[row.get(c[0], "") for c in self._columns])

    def _selected(self) -> dict[str, Any] | None:
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("提示", "請先選擇一筆資料")
            return None
        return self._rows[selected[0]]

    def _detail(self) -> None:
        row = self._selected()
        if row is not None and self._on_detail:
            self._on_detail(row)

    def _export(self) -> None:
        row = self._selected()
        if row is not None and self._on_export:
            self._on_export(row)

    def _review(self) -> None:
        row = self._selected()
        if row is not None and self._on_review:
            self._on_review(row)
            self.refresh()

    def _action(
        self,
        callback: Callable[[dict[str, Any] | None], None],
        needs_selection: bool,
    ) -> None:
        row = self._selected() if needs_selection else None
        if needs_selection and row is None:
            return
        callback(row)
        self.refresh()


# ---------------------------------------------------------------------------
# NewQuotePage — the main functional page
# ---------------------------------------------------------------------------

class NewQuotePage(tk.Frame):
    """The new-quotation page with toolbar, cards, table, and summary."""

    def __init__(
        self,
        parent: tk.Widget,
        on_load_j003: Callable[[], None],
        on_load_w001: Callable[[], None],
        on_select_file: Callable[[], None],
        on_run_file: Callable[[], None],
        on_recalculate: Callable[[], None],
        on_export: Callable[[], None] | None,
        can_view_skill_debug: bool = False,
        **kw: Any,
    ):
        super().__init__(parent, bg=CONTENT_BG, **kw)
        self._on_load_j003 = on_load_j003
        self._on_load_w001 = on_load_w001
        self._on_select_file = on_select_file
        self._on_run_file = on_run_file
        self._on_recalculate = on_recalculate
        self._on_export = on_export
        self._can_view_skill_debug = can_view_skill_debug
        self._show_tax = tk.BooleanVar(value=True)
        self._use_ai = tk.BooleanVar(value=True)
        self._skill_debug_trace: list[dict[str, Any]] = []
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
            header, text="  新建报价", font=_font(14, bold=True),
            bg=HEADER_BG, fg=HEADER_FG,
        ).pack(side=tk.LEFT, pady=10)

        # -- Toolbar --
        self._toolbar = tk.Frame(self._scroll_frame, bg=CARD_BG, bd=1, relief=tk.SOLID)
        self._toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        buttons: list[tuple[str, Callable[[], None]]] = [
            ("\U0001f4c2  选择图纸", self._on_select_file),
            ("\U0001f4e5  载入J003示例", self._on_load_j003),
            ("\U0001f4e5  载入W001示例", self._on_load_w001),
            ("\U0001f50d  开始解析", self._on_run_file),
            ("\U0001f504  重新计算", self._on_recalculate),
        ]
        if self._on_export is not None:
            buttons.append(("\U0001f4ca  导出Excel", self._on_export))
        for text, cmd in buttons:
            btn = tk.Button(
                self._toolbar, text=text, font=_font(9),
                bg="#ecf0f1", fg="#2c3e50", bd=1, padx=10, pady=5,
                cursor="hand2", relief=tk.FLAT,
                activebackground=NAV_ACTIVE_BG, activeforeground="#ffffff",
                command=cmd,
            )
            btn.pack(side=tk.LEFT, padx=5, pady=8)

        self._skill_debug_button: tk.Button | None = None
        if self._can_view_skill_debug:
            self._skill_debug_button = tk.Button(
                self._toolbar,
                text="查看 Skill 调试",
                font=_font(9),
                bg="#ecf0f1",
                fg="#2c3e50",
                bd=1,
                padx=10,
                pady=5,
                state=tk.NORMAL,
                command=self._show_skill_debug,
            )
            self._skill_debug_button.pack(side=tk.LEFT, padx=5, pady=8)

        ttk.Checkbutton(
            self._toolbar,
            text="启用 AI 工艺判断与 AI 估价（计入报价、需人工确认）",
            variable=self._use_ai,
        ).pack(side=tk.RIGHT, padx=10)

        self._selected_file_label = tk.Label(
            self._toolbar, text="尚未选择图纸", font=_font(9),
            bg=CARD_BG, fg="#7f8c8d", anchor=tk.W,
        )
        self._selected_file_label.pack(fill=tk.X, padx=8, pady=(0, 8))

        # -- Cards container --
        cards_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG)
        cards_frame.pack(fill=tk.X, padx=10, pady=5)

        # Basic Info Card
        self._basic_card_frame = tk.LabelFrame(
            cards_frame, text=" 基本资料 ", font=_font(10, bold=True),
            bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID,
        )
        self._basic_card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Feature Card
        self._feature_card_frame = tk.LabelFrame(
            cards_frame, text=" 特征摘要 ", font=_font(10, bold=True),
            bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID,
        )
        self._feature_card_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # -- Quote table --
        self._table_frame = tk.LabelFrame(
            self._scroll_frame, text=" 报价明细 ", font=_font(10, bold=True),
            bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID,
        )
        self._table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._build_table()

        # -- Trace panel --
        self._trace_frame = ttk.LabelFrame(
            self._scroll_frame, text=" 价格来源详情 ",
        )
        self._trace_frame.pack(fill=tk.X, padx=10, pady=5)
        self._trace_text = tk.Text(
            self._trace_frame, height=4, font=_font(9), wrap=tk.WORD,
            bg="#f8f9fa", fg="#2c3e50", bd=0,
        )
        self._trace_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self._trace_text.insert("1.0", "点击上方报价项目查看价格来源详情")
        self._trace_text.configure(state=tk.DISABLED)

        # -- Tax toggle --
        tax_toggle_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG)
        tax_toggle_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Checkbutton(
            tax_toggle_frame, text="显示含税价", variable=self._show_tax,
            command=self._on_tax_toggle,
        ).pack(side=tk.RIGHT)

        # -- Summary cards --
        self._summary_frame = tk.Frame(self._scroll_frame, bg=CONTENT_BG)
        self._summary_frame.pack(fill=tk.X, padx=10, pady=5)

        self._summary_cards: dict[str, dict[str, Any]] = {}
        card_configs = [
            ("card_excl", "未税小计", "#3498db"),
            ("card_rate", "税率", "#2ecc71"),
            ("card_tax", "税额", "#e67e22"),
            ("card_incl", "含税总价", "#e74c3c"),
        ]
        for key, title, color in card_configs:
            card = self._make_summary_card(self._summary_frame, title, color)
            card["frame"].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
            self._summary_cards[key] = card

        # -- Status bar --
        _configure_progress_styles(self)
        self._status_frame = tk.Frame(self._scroll_frame, bg=CARD_BG, bd=1, relief=tk.SOLID)
        self._status_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        status_row = tk.Frame(self._status_frame, bg=CARD_BG)
        status_row.pack(fill=tk.X, padx=10, pady=(7, 3))
        self._status_label = tk.Label(
            status_row, text="就绪", font=_font(10, True),
            bg=CARD_BG, fg="#95a5a6",
        )
        self._status_label.pack(side=tk.LEFT, pady=5)

        self._completion_label = tk.Label(
            status_row, text="", font=_font(9, bold=True),
            bg=CARD_BG, fg="#95a5a6",
        )
        self._completion_label.pack(side=tk.RIGHT, pady=5)
        self._progress = ttk.Progressbar(
            self._status_frame,
            mode="determinate",
            maximum=100,
            style="Quote.Horizontal.TProgressbar",
        )
        self._progress.pack(fill=tk.X, padx=10, pady=(0, 10))

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _build_table(self) -> None:
        columns = (
            "序号", "报价项目", "来源", "数量", "单位", "单价", "未税金额",
            "智能辅助参考估价", "可信度", "状态",
        )
        self._tree = ttk.Treeview(
            self._table_frame, columns=columns, show="headings",
            height=8, selectmode="browse",
        )
        widths = [40, 190, 80, 60, 50, 80, 100, 145, 70, 70]
        for col, w in zip(columns, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=tk.CENTER if col != "报价项目" else tk.W)

        # Scrollbar
        vsb = ttk.Scrollbar(self._table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        hsb = ttk.Scrollbar(self._table_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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

    def set_selected_file(self, path: str | None) -> None:
        """Show the selected drawing without parsing it immediately."""
        self._selected_file_label.configure(
            text=path or "尚未选择图纸",
            fg="#2c3e50" if path else "#7f8c8d",
        )

    @property
    def use_ai(self) -> bool:
        """Whether single-file analysis should request AI assistance."""
        return self._use_ai.get()

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
                    item_vm.display_ai_estimate,
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
            self._trace_text.insert("1.0", "点击上方报价项目查看价格来源详情")
        else:
            fields = item_vm.trace_fields
            if not fields:
                self._trace_text.insert("1.0", f"{item_vm.item.name}\n没有价格来源追踪信息")
            else:
                lines = [f"▸ {item_vm.item.name}"]
                for label, value in fields:
                    lines.append(f"  {label}: {value}")
                self._trace_text.insert("1.0", "\n".join(lines))
        self._trace_text.configure(state=tk.DISABLED)

    def update_skill_debug(self, trace: list[dict[str, Any]] | None) -> None:
        """Attach the pre-classification plus ten-step Skill trace."""
        self._skill_debug_trace = list(trace or [])
        if self._skill_debug_button is not None:
            self._skill_debug_button.configure(
                state=tk.NORMAL
            )

    def _show_skill_debug(self) -> None:
        if not self._skill_debug_trace:
            messagebox.showinfo(
                "Skill 调试",
                "请先完成一次报价；报价完成后可查看内置及外接 Skill 的实际输入输出。",
                parent=self,
            )
            return
        dialog = tk.Toplevel(self)
        dialog.title("Skill 前置分类与十步流程输入输出调试")
        dialog.geometry("1180x720")
        dialog.transient(self.winfo_toplevel())

        left = ttk.Frame(dialog, padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        tree = ttk.Treeview(
            left,
            columns=("provider", "status", "validation"),
            show="tree headings",
            height=28,
        )
        tree.heading("#0", text="步骤")
        tree.heading("provider", text="执行者")
        tree.heading("status", text="状态")
        tree.heading("validation", text="验收")
        tree.column("#0", width=180)
        tree.column("provider", width=130)
        tree.column("status", width=120)
        tree.column("validation", width=70, anchor=tk.CENTER)
        tree.pack(fill=tk.Y, expand=True)

        notebook = ttk.Notebook(dialog)
        notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        panes: dict[str, tk.Text] = {}
        for key, label in (("input", "实际输入"), ("output", "实际输出"), ("validation", "自动验收")):
            frame = ttk.Frame(notebook)
            text_widget = tk.Text(frame, wrap=tk.NONE, font=("Consolas", 10))
            ybar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
            xbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text_widget.xview)
            text_widget.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
            text_widget.grid(row=0, column=0, sticky="nsew")
            ybar.grid(row=0, column=1, sticky="ns")
            xbar.grid(row=1, column=0, sticky="ew")
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            notebook.add(frame, text=label)
            panes[key] = text_widget

        for index, entry in enumerate(self._skill_debug_trace):
            validation = entry.get("validation") or {}
            ok = validation.get("input_ok") and validation.get("output_ok")
            tree.insert(
                "",
                tk.END,
                iid=str(index),
                text=f"{index + 1}. {entry.get('step_name_zh', entry.get('step'))}",
                values=(entry.get("provider"), entry.get("status"), "通过" if ok else "异常"),
            )

        def show_entry(_event=None) -> None:
            selection = tree.selection()
            if not selection:
                return
            entry = self._skill_debug_trace[int(selection[0])]
            for key, widget in panes.items():
                widget.configure(state=tk.NORMAL)
                widget.delete("1.0", tk.END)
                widget.insert(
                    "1.0",
                    json.dumps(entry.get(key), ensure_ascii=False, indent=2, default=str),
                )
                widget.configure(state=tk.DISABLED)

        tree.bind("<<TreeviewSelect>>", show_entry)
        if self._skill_debug_trace:
            tree.selection_set("0")
            show_entry()

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
        style_map = {
            "green": "QuoteSuccess.Horizontal.TProgressbar",
            "orange": "QuoteWarning.Horizontal.TProgressbar",
            "red": "QuoteError.Horizontal.TProgressbar",
        }
        self._status_label.configure(text=f"  {status_text}", fg=color)
        self._completion_label.configure(
            text=f"报价完整度：{completion:.1f}%  ", fg=color,
        )
        self._progress.configure(
            value=max(0, min(float(completion), 100)),
            style=style_map.get(status_color, "Quote.Horizontal.TProgressbar"),
        )

    def clear(self) -> None:
        """Reset all display areas."""
        self._tree.delete(*self._tree.get_children())
        self.update_trace(None)
        self.update_skill_debug(None)
        self.update_status("就绪", "", 0)
        for card in self._summary_cards.values():
            card["value"].configure(text="—")
        self.update_basic_info([("状态", "尚未载入图纸")])
        self.update_feature_summary([("状态", "尚未载入图纸")])

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
        on_run_batch: Callable[
            [list[Any], bool, Callable[[int, int, Any], None] | None], list[Any]
        ],
        on_export_selected: Callable[[list[Any], str], str] | None,
        on_export_all: Callable[[list[Any], str], str] | None,
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
        self._result_by_item: dict[str, Any] = {}
        self._detail_windows: set[tk.Toplevel] = set()
        self._use_ai = tk.BooleanVar(value=True)
        self._recursive = tk.BooleanVar(value=True)
        self._build()

    def _build(self) -> None:
        # Header
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="  批量报价", font=_font(14, bold=True),
                 bg=HEADER_BG, fg=HEADER_FG).pack(side=tk.LEFT, pady=10)

        # Toolbar
        toolbar = tk.Frame(self, bg=CARD_BG, bd=1, relief=tk.SOLID)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        buttons: list[tuple[str, Callable[[], None]]] = [
            ("选择文件夹", lambda: self._do_scan_dir()),
            ("选择文件", lambda: self._do_scan_files()),
            ("开始批量报价", lambda: self._do_run_batch()),
            ("打开输出目录", lambda: self._on_open_dir("runtime/exports")),
        ]
        if self._on_export_selected is not None:
            buttons.insert(3, ("导出选中", lambda: self._do_export_selected()))
        if self._on_export_all is not None:
            buttons.insert(4, ("导出全部", lambda: self._do_export_all()))
        for text, cmd in buttons:
            tk.Button(toolbar, text=text, font=_font(9), bg="#ecf0f1",
                      fg="#2c3e50", bd=1, padx=8, pady=4, cursor="hand2",
                      relief=tk.FLAT, activebackground=NAV_ACTIVE_BG,
                      activeforeground="#ffffff", command=cmd
                      ).pack(side=tk.LEFT, padx=3, pady=6)

        ttk.Checkbutton(toolbar, text="启用 AI 工艺判断", variable=self._use_ai).pack(
            side=tk.RIGHT, padx=10)
        ttk.Checkbutton(toolbar, text="遍历子目录", variable=self._recursive).pack(
            side=tk.RIGHT, padx=10)

        # Stats bar
        self._stats_frame = tk.Frame(self, bg=CONTENT_BG)
        self._stats_frame.pack(fill=tk.X, padx=10, pady=5)
        stats = [
            ("扫描文件", "0"), ("报价任务", "0"), ("报价完整", "0"),
            ("需要确认", "0"), ("失败", "0"),
        ]
        self._stat_labels: dict[str, tk.Label] = {}
        for i, (label, val) in enumerate(stats):
            f = tk.Frame(self._stats_frame, bg=CARD_BG, bd=1, relief=tk.SOLID)
            f.pack(side=tk.LEFT, padx=3, pady=2)
            tk.Label(f, text=label, font=_font(8), bg=CARD_BG, fg="#7f8c8d").pack(padx=8, pady=(5, 0))
            lbl = tk.Label(f, text=val, font=_font(16, bold=True), bg=CARD_BG, fg=HEADER_BG)
            lbl.pack(padx=8, pady=(0, 5))
            self._stat_labels[label] = lbl

        # Progress card
        _configure_progress_styles(self)
        progress_card = tk.Frame(self, bg=CARD_BG, bd=1, relief=tk.SOLID)
        progress_card.pack(fill=tk.X, padx=10, pady=5)
        progress_row = tk.Frame(progress_card, bg=CARD_BG)
        progress_row.pack(fill=tk.X, padx=10, pady=(7, 3))
        self._progress_text = tk.Label(
            progress_row, text="就绪", font=_font(9, True), bg=CARD_BG, fg="#566573")
        self._progress_text.pack(side=tk.LEFT)
        self._progress_percent = tk.Label(
            progress_row, text="0%", font=_font(10, True), bg=CARD_BG, fg=NAV_ACTIVE_BG
        )
        self._progress_percent.pack(side=tk.RIGHT)
        self._progress = ttk.Progressbar(
            progress_card,
            mode="determinate",
            maximum=100,
            style="Quote.Horizontal.TProgressbar",
        )
        self._progress.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Batch table
        table_frame = tk.LabelFrame(self, text=" 报价任务 ", font=_font(10, bold=True),
                                     bg=CARD_BG, fg="#2c3e50", bd=1, relief=tk.SOLID)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("序号", "图号", "文件名", "配对", "解析状态", "报价状态",
                   "完整度", "待确认", "未税", "税额", "含税", "智能辅助", "提示")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        widths = [30, 100, 140, 80, 80, 90, 55, 50, 80, 80, 80, 40, 120]
        for col, w in zip(columns, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=tk.CENTER if col != "文件名" else tk.W)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.tag_configure("unknown", background=WARNING_BG)
        self._tree.tag_configure("fail", background="#f8d7da")
        self._tree.tag_configure("complete", background="#d4edda")
        self._tree.bind("<Button-3>", self._show_batch_context_menu)
        self._tree.bind("<Double-1>", self._show_selected_ai_detail)
        self._tree.bind("<Return>", self._show_selected_ai_detail)
        self._tree.bind("<space>", self._show_selected_ai_detail)
        self._context_menu = tk.Menu(self, tearoff=False)
        self._context_menu.add_command(
            label="查看详细报价明细与 AI 分步依据",
            command=self._show_selected_ai_detail,
        )

    # --- Public API ---

    def set_bundles(self, bundles: list[Any]) -> None:
        self._bundles = bundles
        self._result_by_item.clear()
        self._tree.delete(*self._tree.get_children())
        for i, b in enumerate(bundles):
            geom = b.geometry_source
            matched = ",".join(f.file_name for f in b.files if f != geom) or "-"
            self._tree.insert("", tk.END, iid=f"batch-{i}", values=(
                i + 1, b.drawing_number, geom.file_name if geom else "(無幾何)",
                matched, "已掃描", "等待處理", "-", "-", "-", "-", "-", "-", ""
            ))
        self._update_stats()

    def update_result(self, idx: int, result: Any) -> None:
        from quotation.ui.viewmodels import STATUS_DISPLAY
        children = self._tree.get_children()
        if idx < len(children):
            item = children[idx]
            self._result_by_item[str(item)] = result
            st = result.status
            status_display = STATUS_DISPLAY.get(st, st)
            tags = []
            if st == "COMPLETE":
                tags = ["complete"]
            elif st in ("INCOMPLETE", "REVIEW_REQUIRED"):
                tags = ["unknown"]
            elif st in ("PARSE_FAILED", "QUOTE_FAILED", "DWG_CONVERSION_FAILED"):
                tags = ["fail"]

            hints = list(getattr(result, "errors", []) or [])
            if not hints:
                hints = list(getattr(result, "warnings", []) or [])
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
                "; ".join(hints[:1]),
            ), tags=tags)
            self._update_stats()

    def set_progress(self, current: int, total: int, text: str = "") -> None:
        fraction = current / total if total else 0
        percent = max(0, min(fraction * 100, 100))
        self._progress["maximum"] = 100
        self._progress["value"] = percent
        self._progress_percent.configure(text=f"{percent:.0f}%")
        self._progress_text.configure(text=text or f"{current}/{total}")

    def set_results(self, results: list[Any]) -> None:
        self._results = results
        self._result_by_item = {
            str(item): results[index]
            for index, item in enumerate(self._tree.get_children())
            if index < len(results)
        }

    def _update_stats(self) -> None:
        results = [result for result in self._results if result is not None]
        total = len(results)
        complete = sum(1 for r in results if r.status == "COMPLETE")
        review = sum(1 for r in results if r.status in ("INCOMPLETE", "REVIEW_REQUIRED"))
        failed = sum(1 for r in results if r.status in (
            "PARSE_FAILED", "QUOTE_FAILED", "UNSUPPORTED", "DWG_CONVERSION_FAILED"
        ))
        scanned = len(self._bundles)

        self._stat_labels.get("扫描文件", tk.Label()).configure(text=str(scanned))
        self._stat_labels.get("报价任务", tk.Label()).configure(text=str(total))
        self._stat_labels.get("报价完整", tk.Label()).configure(text=str(complete))
        self._stat_labels.get("需要确认", tk.Label()).configure(text=str(review))
        self._stat_labels.get("失败", tk.Label()).configure(text=str(failed))

    # --- Actions ---

    def _do_scan_dir(self) -> None:
        from tkinter import filedialog
        d = filedialog.askdirectory(title="選擇包含圖紙的資料夾")
        if d:
            self._progress.configure(style="Quote.Horizontal.TProgressbar")
            self.set_progress(0, 1, f"扫描中：{d}")
            self.update_idletasks()
            bundles = self._on_scan_dir(d, self._recursive.get())
            self._results = []
            self.set_bundles(bundles)
            self.set_progress(0, max(len(bundles), 1), f"扫描完成：{len(bundles)} 个任务")

    def _do_scan_files(self) -> None:
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="選擇圖紙檔案",
            filetypes=[("机械图纸", "*.dxf *.DXF *.dwg *.DWG *.slddrw *.SLDDRW *.sldprt *.SLDPRT"), ("所有文件", "*.*")]
        )
        if files:
            bundles = self._on_scan_files(list(files))
            self._results = []
            self.set_bundles(bundles)
            self._progress.configure(style="Quote.Horizontal.TProgressbar")
            self.set_progress(0, max(len(bundles), 1), f"扫描完成：{len(bundles)} 个任务")

    def _do_run_batch(self) -> None:
        if not self._bundles:
            messagebox.showwarning("提示", "請先掃描檔案")
            return
        self._results = []
        self._progress.configure(style="Quote.Horizontal.TProgressbar")
        self.set_progress(0, len(self._bundles), "准备批量报价…")
        self.update_idletasks()

        # Run in background via simple thread
        import threading
        def _progress(current: int, total: int, result: Any) -> None:
            self.after(
                0,
                lambda: self._on_batch_progress(current, total, result),
            )

        def _run() -> None:
            results = self._on_run_batch(
                self._bundles, self._use_ai.get(), _progress
            )
            self.after(0, lambda: self._on_batch_done(results))
        threading.Thread(target=_run, daemon=True).start()

    def _on_batch_progress(self, current: int, total: int, result: Any) -> None:
        index = getattr(result, "batch_index", None)
        if index is None:
            index = current - 1
        while len(self._results) <= index:
            self._results.append(None)
        self._results[index] = result
        self.update_result(index, result)
        self.set_progress(
            current,
            total,
            f"正在报价：{result.drawing_number}  ·  {current}/{total}",
        )

    def _on_batch_done(self, results: list[Any]) -> None:
        self._results = results
        for i, r in enumerate(results):
            self.update_result(i, r)
        complete = sum(1 for r in results if r.status == "COMPLETE")
        review = sum(1 for r in results if r.status in ("INCOMPLETE", "REVIEW_REQUIRED"))
        failed = sum(1 for r in results if r.status in (
            "PARSE_FAILED", "QUOTE_FAILED", "UNSUPPORTED", "DWG_CONVERSION_FAILED"
        ))
        self._progress_text.configure(
            text=f"完成: {complete} 完整, {review} 待確認, {failed} 失敗")
        self.set_progress(len(results), max(len(self._bundles), 1), self._progress_text.cget("text"))
        self._progress.configure(
            style=(
                "QuoteError.Horizontal.TProgressbar"
                if failed
                else "QuoteWarning.Horizontal.TProgressbar"
                if review
                else "QuoteSuccess.Horizontal.TProgressbar"
            )
        )

    def _show_batch_context_menu(self, event: tk.Event) -> None:
        row = self._tree.identify_row(event.y)
        if row:
            self._tree.selection_set(row)
            self._tree.focus(row)
            try:
                self._context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._context_menu.grab_release()

    def _show_selected_ai_detail(self, event: tk.Event | None = None) -> None:
        if event is not None:
            row = self._tree.identify_row(event.y)
            if row:
                self._tree.selection_set(row)
                self._tree.focus(row)
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个批量报价任务", parent=self)
            return
        item_id = str(selected[0])
        result = self._result_by_item.get(item_id)
        if result is None:
            messagebox.showinfo(
                "AI 分步细项", "该任务尚未完成报价，没有可查看的 AI 结果。", parent=self
            )
            return
        try:
            window = StructuredDetailWindow(
                self,
                f"详细报价与 AI 分步细项 — {result.drawing_number}",
                batch_ai_detail_sections(result),
            )
            self._detail_windows.add(window)
            window.bind(
                "<Destroy>",
                lambda destroy_event, current=window: (
                    self._detail_windows.discard(current)
                    if destroy_event.widget is current
                    else None
                ),
                add="+",
            )
            window.transient(self.winfo_toplevel())
            window.lift()
            window.focus_force()
        except Exception as exc:
            messagebox.showerror(
                "无法打开报价明细",
                f"明细数据读取失败：{exc}",
                parent=self,
            )

    def _do_export_selected(self) -> None:
        if self._on_export_selected is None:
            return
        from tkinter import filedialog
        if not self._results:
            messagebox.showwarning("提示", "没有可导出的报价结果")
            return
        p = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if p:
            self._on_export_selected(self._results, p)
            messagebox.showinfo("完成", f"已匯出: {p}")

    def _do_export_all(self) -> None:
        if self._on_export_all is None:
            return
        from tkinter import filedialog
        if not self._results:
            messagebox.showwarning("提示", "没有可导出的报价结果")
            return
        p = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if p:
            self._on_export_all(self._results, p)
            messagebox.showinfo("完成", f"已匯出: {p}")
