"""Administrator-only external Skill routing settings page."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from quotation.application.external_skill_settings import (
    CATEGORY_NAMES_ZH,
    STEP_NAMES_ZH,
    CategorySkillRouting,
    ExternalSkillDefinition,
    ExternalSkillRoutingConfig,
    ExternalSkillSettingsService,
    PartCategory,
    SkillRoutingMode,
    SkillStep,
    StepRoute,
)
from quotation.domain.user import User
from quotation.infrastructure.external_skill.client import ExternalSkillClient
from quotation.ui.widgets import CARD_BG, CONTENT_BG, HEADER_BG, HEADER_FG, _font


class ExternalSkillSettingsPage(tk.Frame):
    def __init__(
        self,
        parent,
        service: ExternalSkillSettingsService,
        actor: User,
        client: ExternalSkillClient | None = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=CONTENT_BG, **kwargs)
        self._service = service
        self._actor = actor
        self._client = client or ExternalSkillClient()
        self._config = service.get(actor)
        self._skills = list(self._config.skills)
        self._mode = tk.StringVar(value=self._config.mode.value)
        self._endpoint = tk.StringVar()
        self._full_skill = tk.StringVar()
        self._step_vars = {step: tk.StringVar(value="内置系统") for step in SkillStep}
        self._category = tk.StringVar(value="全局默认")
        self._inherit_global = tk.BooleanVar(value=False)
        self._debug_mode = tk.BooleanVar(value=self._config.debug_mode)
        self._active_category: PartCategory | None = None
        self._route_drafts: dict[PartCategory | None, CategorySkillRouting | None] = {
            None: self._config.route_for()
        }
        self._route_drafts.update(self._config.category_routes)
        self._build()
        self._load_selection()

    def _build(self) -> None:
        header = tk.Frame(self, bg=HEADER_BG, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="  外接报价 Skill 设置（管理员）",
            font=_font(14, True),
            bg=HEADER_BG,
            fg=HEADER_FG,
        ).pack(side=tk.LEFT, pady=10)

        registry = tk.LabelFrame(
            self, text=" Skill 注册与能力检测 ", bg=CARD_BG, font=_font(10, True)
        )
        registry.pack(fill=tk.X, padx=18, pady=(14, 8))
        row = tk.Frame(registry, bg=CARD_BG)
        row.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(row, text="HTTP 地址或 Skill 文件夹：", bg=CARD_BG).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self._endpoint, width=56).pack(side=tk.LEFT, padx=5)
        tk.Button(row, text="选择本地/公共槽文件夹", command=self._browse_folder).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(row, text="检测并添加/更新", command=self._discover).pack(side=tk.LEFT, padx=5)
        tk.Button(row, text="移除选中 Skill", command=self._remove).pack(side=tk.LEFT, padx=5)

        columns = ("skill_id", "name", "source", "version", "full", "steps", "endpoint")
        self._tree = ttk.Treeview(registry, columns=columns, show="headings", height=4)
        for key, label, width in [
            ("skill_id", "Skill ID", 140),
            ("name", "中文名称", 130),
            ("source", "来源", 90),
            ("version", "版本", 80),
            ("full", "整套报价", 80),
            ("steps", "支持步骤数", 90),
            ("endpoint", "服务地址", 330),
        ]:
            self._tree.heading(key, text=label)
            self._tree.column(key, width=width, anchor=tk.W)
        self._tree.pack(fill=tk.X, padx=10, pady=(0, 10))

        routing = tk.LabelFrame(
            self, text=" 参与方式与步骤路由 ", bg=CARD_BG, font=_font(10, True)
        )
        routing.pack(fill=tk.BOTH, expand=True, padx=18, pady=8)
        modes = tk.Frame(routing, bg=CARD_BG)
        modes.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(modes, text="零件类别：", bg=CARD_BG).pack(side=tk.LEFT, padx=(0, 4))
        self._category_box = ttk.Combobox(
            modes,
            textvariable=self._category,
            state="readonly",
            width=14,
            values=["全局默认"] + list(CATEGORY_NAMES_ZH.values()),
        )
        self._category_box.pack(side=tk.LEFT, padx=(0, 10))
        self._category_box.bind("<<ComboboxSelected>>", self._switch_category)
        self._inherit_box = ttk.Checkbutton(
            modes,
            text="该类别继承全局默认",
            variable=self._inherit_global,
            command=self._toggle_inherit,
        )
        self._inherit_box.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(
            modes,
            text="调试模式（报价后查看每步输入输出）",
            variable=self._debug_mode,
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            modes,
            text="整套报价（只能选择一个外接 Skill）",
            variable=self._mode,
            value=SkillRoutingMode.FULL_QUOTATION.value,
            command=self._toggle_mode,
        ).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(
            modes,
            text="分步报价（每一步可选择内置或一个外接 Skill）",
            variable=self._mode,
            value=SkillRoutingMode.DISTRIBUTED.value,
            command=self._toggle_mode,
        ).pack(side=tk.LEFT, padx=6)

        full_row = tk.Frame(routing, bg=CARD_BG)
        full_row.pack(fill=tk.X, padx=16, pady=4)
        tk.Label(full_row, text="整套报价 Skill：", bg=CARD_BG, width=20, anchor=tk.W).pack(side=tk.LEFT)
        self._full_box = ttk.Combobox(
            full_row, textvariable=self._full_skill, state="readonly", width=48
        )
        self._full_box.pack(side=tk.LEFT)

        tk.Label(
            routing,
            text="分布式 Agent 执行流程（文件夹 Skill 由程序内置 DeepSeek 执行）",
            bg=CARD_BG,
            fg="#1a5276",
            font=_font(10, True),
        ).pack(anchor=tk.W, padx=18, pady=(8, 2))
        self._step_boxes: dict[SkillStep, ttk.Combobox] = {}
        pipeline = tk.Frame(routing, bg=CARD_BG)
        pipeline.pack(fill=tk.X, padx=16, pady=5)
        steps = list(SkillStep)
        for phase_index, phase_steps in enumerate((steps[:5], steps[5:])):
            row_frame = tk.Frame(pipeline, bg=CARD_BG)
            row_frame.pack(fill=tk.X, pady=3)
            for offset, step in enumerate(phase_steps):
                index = phase_index * 5 + offset
                frame = tk.LabelFrame(
                    row_frame,
                    text=f" {index + 1}. {STEP_NAMES_ZH[step]} ",
                    bg="#f8fbfd",
                    fg="#1a5276",
                    padx=5,
                    pady=5,
                )
                frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                box = ttk.Combobox(
                    frame, textvariable=self._step_vars[step], state="readonly", width=17
                )
                box.pack(fill=tk.X)
                self._step_boxes[step] = box
                if offset < len(phase_steps) - 1:
                    tk.Label(
                        row_frame, text="➜", bg=CARD_BG, fg="#2874a6", font=_font(16, True)
                    ).pack(side=tk.LEFT, padx=3)
            if phase_index == 0:
                tk.Label(
                    pipeline,
                    text="↓ 继续下一阶段",
                    bg=CARD_BG,
                    fg="#2874a6",
                    font=_font(10, True),
                ).pack(anchor=tk.CENTER, pady=1)

        footer = tk.Frame(self, bg=CONTENT_BG)
        footer.pack(fill=tk.X, padx=18, pady=(0, 14))
        self._status = tk.Label(footer, bg=CONTENT_BG, fg="#566573")
        self._status.pack(side=tk.LEFT)
        tk.Button(footer, text="保存并发布到 SMB 公共槽", command=self._save).pack(side=tk.RIGHT)
        self._refresh_skill_widgets()

    def _skill_label(self, skill: ExternalSkillDefinition) -> str:
        return f"{skill.name_zh} [{skill.skill_id}]"

    def _skill_id_from_label(self, label: str) -> str | None:
        for skill in self._skills:
            if self._skill_label(skill) == label:
                return skill.skill_id
        return None

    def _refresh_skill_widgets(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for skill in self._skills:
            self._tree.insert(
                "",
                tk.END,
                iid=skill.skill_id,
                values=(
                    skill.skill_id,
                    skill.name_zh,
                    "HTTP 服务"
                    if skill.source_type.value == "HTTP"
                    else "文件夹提示词（内置AI）",
                    skill.skill_version,
                    "是" if skill.supports_full_quotation else "否",
                    len(skill.supported_steps),
                    skill.endpoint,
                ),
            )
        self._full_box["values"] = [
            self._skill_label(skill) for skill in self._skills if skill.supports_full_quotation
        ]
        for step, box in self._step_boxes.items():
            box["values"] = ["内置系统"] + [
                self._skill_label(skill)
                for skill in self._skills
                if step in skill.supported_steps
            ]
        self._toggle_mode()

    def _load_selection(self) -> None:
        self._load_active_route()
        self._status.configure(
            text=f"配置版本 {self._config.config_version}；读取来源：{self._service.store.last_source}"
        )

    def _load_active_route(self) -> None:
        route = self._route_drafts.get(self._active_category)
        inherited = self._active_category is not None and route is None
        if route is None:
            route = self._route_drafts[None]
        assert route is not None
        self._inherit_global.set(inherited)
        self._mode.set(route.mode.value)
        self._full_skill.set("")
        if route.full_skill_id:
            skill = next(
                (item for item in self._skills if item.skill_id == route.full_skill_id),
                None,
            )
            if skill:
                self._full_skill.set(self._skill_label(skill))
        for step in SkillStep:
            provider = (
                route.full_skill_id or "builtin"
                if route.mode == SkillRoutingMode.FULL_QUOTATION
                else route.step_routes.get(step, StepRoute()).provider
            )
            skill = next((item for item in self._skills if item.skill_id == provider), None)
            self._step_vars[step].set(self._skill_label(skill) if skill else "内置系统")
        self._toggle_mode()

    def _capture_active_route(self) -> None:
        if self._active_category is not None and self._inherit_global.get():
            self._route_drafts[self._active_category] = None
            return
        mode = SkillRoutingMode(self._mode.get())
        full_skill_id = (
            self._skill_id_from_label(self._full_skill.get())
            if mode == SkillRoutingMode.FULL_QUOTATION
            else None
        )
        routes = {}
        if mode == SkillRoutingMode.DISTRIBUTED:
            routes = {
                step: StepRoute(
                    provider=self._skill_id_from_label(variable.get()) or "builtin"
                )
                for step, variable in self._step_vars.items()
            }
        self._route_drafts[self._active_category] = CategorySkillRouting(
            mode=mode,
            full_skill_id=full_skill_id,
            step_routes=routes,
        )

    def _switch_category(self, _event=None) -> None:
        self._capture_active_route()
        label = self._category.get()
        self._active_category = next(
            (category for category, name in CATEGORY_NAMES_ZH.items() if name == label),
            None,
        )
        self._load_active_route()

    def _toggle_inherit(self) -> None:
        if self._active_category is None:
            self._inherit_global.set(False)
        elif self._inherit_global.get():
            self._route_drafts[self._active_category] = None
        elif not self._inherit_global.get() and self._route_drafts.get(self._active_category) is None:
            global_route = self._route_drafts[None]
            self._route_drafts[self._active_category] = global_route.model_copy(deep=True)
        self._load_active_route()

    def _toggle_mode(self) -> None:
        inherited = self._active_category is not None and self._inherit_global.get()
        self._inherit_box.configure(state="disabled" if self._active_category is None else "normal")
        full = self._mode.get() == SkillRoutingMode.FULL_QUOTATION.value
        self._full_box.configure(state="readonly" if full and not inherited else "disabled")
        for box in self._step_boxes.values():
            box.configure(state="disabled" if full or inherited else "readonly")

    def _discover(self) -> None:
        try:
            skill = self._client.discover(self._endpoint.get())
            self._skills = [item for item in self._skills if item.skill_id != skill.skill_id]
            self._skills.append(skill)
            self._refresh_skill_widgets()
            messagebox.showinfo("检测成功", f"已读取：{skill.name_zh} {skill.skill_version}", parent=self)
        except Exception as exc:
            messagebox.showerror("Skill 检测失败", str(exc), parent=self)

    def _browse_folder(self) -> None:
        selected = filedialog.askdirectory(
            title="选择本地或 SMB 公共槽 Skill 文件夹", parent=self
        )
        if selected:
            self._endpoint.set(selected)

    def _remove(self) -> None:
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个 Skill", parent=self)
            return
        skill_id = selected[0]
        self._skills = [item for item in self._skills if item.skill_id != skill_id]
        self._refresh_skill_widgets()

    def _save(self) -> None:
        try:
            self._capture_active_route()
            global_route = self._route_drafts[None]
            assert global_route is not None
            category_routes = {
                category: route
                for category, route in self._route_drafts.items()
                if category is not None and route is not None
            }
            candidate = ExternalSkillRoutingConfig(
                config_version=self._config.config_version,
                mode=global_route.mode,
                skills=self._skills,
                full_skill_id=global_route.full_skill_id,
                step_routes=global_route.step_routes,
                category_routes=category_routes,
                debug_mode=self._debug_mode.get(),
            )
            self._config = self._service.save(self._actor, candidate)
            self._status.configure(
                text=f"已发布配置版本 {self._config.config_version} 到 SMB 公共槽"
            )
            messagebox.showinfo("保存完成", "所有电脑同步后将使用相同 Skill 路由", parent=self)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self)
