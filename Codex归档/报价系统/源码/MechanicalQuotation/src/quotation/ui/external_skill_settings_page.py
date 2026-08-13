"""Administrator-only external Skill routing settings page."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from quotation.application.external_skill_settings import (
    BUILTIN_AGENTS,
    BUILTIN_SKILLS,
    PROCESS_NAMES_ZH,
    PROCESS_ROUTABLE_STEPS,
    CATEGORY_NAMES_ZH,
    STEP_NAMES_ZH,
    CategorySkillRouting,
    ExternalSkillDefinition,
    ExternalSkillRoutingConfig,
    ExternalSkillSettingsService,
    AgentDefinition,
    AgentSourceType,
    PartCategory,
    ProcessCode,
    ProcessSkillRouting,
    PRE_CATEGORY_STEPS,
    SkillRoutingMode,
    SkillSourceType,
    SkillStep,
    StepRoute,
)
from quotation.domain.user import User
from quotation.infrastructure.external_skill.client import ExternalSkillClient
from quotation.application.external_skill_command import ExternalSkillCommandRunner
from quotation.ui.widgets import (
    CARD_BG, CONTENT_BG, HEADER_BG, HEADER_FG, StructuredDetailWindow, _font,
)


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
        self._agents = list(self._config.agents)
        self._mode = tk.StringVar(value=self._config.mode.value)
        self._endpoint = tk.StringVar()
        self._full_skill = tk.StringVar()
        self._excel_export_skill = tk.StringVar(value="内置 Excel 导出")
        self._step_vars = {step: tk.StringVar(value="内置系统（自动）") for step in SkillStep}
        self._step_agent_vars = {
            step: tk.StringVar(value="按执行资源默认") for step in SkillStep
        }
        self._process_code = tk.StringVar(value=PROCESS_NAMES_ZH[ProcessCode.CNC])
        self._active_process_code = ProcessCode.CNC
        self._process_route_dirty = False
        self._process_step_vars = {
            step: tk.StringVar(value="继承类别路由") for step in PROCESS_ROUTABLE_STEPS
        }
        self._process_agent_vars = {
            step: tk.StringVar(value="按执行资源默认") for step in PROCESS_ROUTABLE_STEPS
        }
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

        fixed_footer = tk.Frame(self, bg=CONTENT_BG)
        fixed_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(6, 14))

        # Keep the complete administrator form reachable at 1024x600.
        viewport = tk.Frame(self, bg=CONTENT_BG)
        viewport.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(viewport, bg=CONTENT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(viewport, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas, bg=CONTENT_BG)
        content_window = canvas.create_window((0, 0), window=content, anchor=tk.NW)
        content.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(content_window, width=event.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.bind(
            "<Enter>",
            lambda _event: canvas.bind_all(
                "<MouseWheel>",
                lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"),
            ),
        )
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))

        registry = tk.LabelFrame(
            content, text=" Skill 注册与能力检测 ", bg=CARD_BG, font=_font(10, True)
        )
        registry.pack(fill=tk.X, padx=18, pady=(14, 8))
        endpoint_row = tk.Frame(registry, bg=CARD_BG)
        endpoint_row.pack(fill=tk.X, padx=10, pady=(8, 4))
        tk.Label(endpoint_row, text="HTTP 地址或 Skill 文件夹：", bg=CARD_BG).pack(
            side=tk.LEFT
        )
        tk.Entry(endpoint_row, textvariable=self._endpoint).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )
        action_row = tk.Frame(registry, bg=CARD_BG)
        action_row.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Button(action_row, text="选择本地/公共槽文件夹", command=self._browse_folder).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(action_row, text="检测 Skill", command=self._discover).pack(side=tk.LEFT, padx=5)
        tk.Button(action_row, text="载入一组 Skill", command=self._discover_group).pack(side=tk.LEFT, padx=5)
        tk.Button(action_row, text="检测外挂智能体", command=self._discover_agent).pack(side=tk.LEFT, padx=5)
        self._remove_button = tk.Button(
            action_row,
            text="移除选中资源",
            command=self._remove,
            bg="#fff5f5",
            fg="#b03a2e",
            activebackground="#fadbd8",
            activeforeground="#922b21",
            disabledforeground="#aab7b8",
        )
        self._remove_button.pack(side=tk.LEFT, padx=5)

        self._registry_notebook = ttk.Notebook(registry, height=150)
        self._registry_notebook.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._resource_trees: dict[str, ttk.Treeview] = {}
        for tab_key, tab_name in (
            ("builtin_skill", f"内置 Skill（{len(BUILTIN_SKILLS)}）"),
            ("external_skill", "外接 Skill"),
            ("builtin_agent", f"内置智能体（{len(BUILTIN_AGENTS)}）"),
            ("external_agent", "外接智能体"),
        ):
            page = tk.Frame(self._registry_notebook, bg=CARD_BG)
            self._registry_notebook.add(page, text=tab_name)
            columns = ("resource_id", "name", "version", "mode", "steps", "endpoint")
            tree = ttk.Treeview(page, columns=columns, show="headings", height=5)
            for key, label, width in [
                ("resource_id", "资源 ID", 210),
                ("name", "中文名称", 210),
                ("version", "版本", 80),
                ("mode", "参与能力", 120),
                ("steps", "可参与步骤", 330),
                ("endpoint", "位置 / 服务地址", 330),
            ]:
                tree.heading(key, text=label)
                tree.column(key, width=width, anchor=tk.W)
            yscroll = ttk.Scrollbar(page, orient=tk.VERTICAL, command=tree.yview)
            xscroll = ttk.Scrollbar(page, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            tree.grid(row=0, column=0, sticky=tk.NSEW)
            yscroll.grid(row=0, column=1, sticky=tk.NS)
            xscroll.grid(row=1, column=0, sticky=tk.EW)
            page.rowconfigure(0, weight=1)
            page.columnconfigure(0, weight=1)
            tree.bind(
                "<Double-1>",
                lambda event, current_tree=tree: self._show_skill_capabilities(
                    event, tree=current_tree
                ),
            )
            tree.bind(
                "<Return>",
                lambda event, current_tree=tree: self._show_skill_capabilities(
                    event, tree=current_tree
                ),
            )
            tree.bind(
                "<space>",
                lambda event, current_tree=tree: self._show_skill_capabilities(
                    event, tree=current_tree
                ),
            )
            tree.bind("<<TreeviewSelect>>", self._update_remove_button_state, add="+")
            self._resource_trees[tab_key] = tree
        # Kept as an alias for older UI tests/extensions; selection is resolved across all tabs.
        self._tree = self._resource_trees["external_skill"]
        tk.Label(
            registry,
            text="提示：用上方四页切换资源；双击或按 Enter/空格可看能力、正文和文件结构，非文本文件只展示类型与大小。",
            bg=CARD_BG,
            fg="#566573",
            font=_font(9),
        ).pack(anchor=tk.W, padx=10, pady=(0, 8))

        routing = tk.LabelFrame(
            content, text=" 参与方式与步骤路由 ", bg=CARD_BG, font=_font(10, True)
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
        tk.Label(full_row, text="Excel 导出 Skill：", bg=CARD_BG, width=20, anchor=tk.W).pack(
            side=tk.LEFT, padx=(24, 0)
        )
        self._excel_export_box = ttk.Combobox(
            full_row,
            textvariable=self._excel_export_skill,
            state="readonly",
            width=42,
        )
        self._excel_export_box.pack(side=tk.LEFT)

        tk.Label(
            routing,
            text=(
                "每个步骤：上栏选择 Skill（或内置系统），下栏选择执行智能体；"
                "第 1、2 步固定使用全局路由，完成分类后第 3～11 步才按零件类别路由"
            ),
            bg=CARD_BG,
            fg="#1a5276",
            font=_font(10, True),
        ).pack(anchor=tk.W, padx=18, pady=(8, 2))
        self._step_boxes: dict[SkillStep, ttk.Combobox] = {}
        self._step_agent_boxes: dict[SkillStep, ttk.Combobox] = {}
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
                tk.Label(
                    frame, text="报价 Skill", bg="#f8fbfd", fg="#566573", anchor=tk.W
                ).pack(fill=tk.X)
                box.pack(fill=tk.X)
                self._step_boxes[step] = box
                agent_box = ttk.Combobox(
                    frame,
                    textvariable=self._step_agent_vars[step],
                    state="readonly",
                    width=17,
                )
                tk.Label(
                    frame, text="执行智能体", bg="#f8fbfd", fg="#566573", anchor=tk.W
                ).pack(fill=tk.X, pady=(4, 0))
                agent_box.pack(fill=tk.X, pady=(3, 0))
                self._step_agent_boxes[step] = agent_box
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

        process_frame = tk.LabelFrame(
            routing,
            text=" 第三层：具体工艺路由（第6步工时、第7步计价、第10步审核、第11步建议） ",
            bg="#f8fbfd",
            fg="#1a5276",
            padx=8,
            pady=8,
        )
        process_frame.pack(fill=tk.X, padx=16, pady=(8, 6))
        process_head = tk.Frame(process_frame, bg="#f8fbfd")
        process_head.pack(fill=tk.X)
        tk.Label(process_head, text="具体工艺：", bg="#f8fbfd").pack(side=tk.LEFT)
        self._process_box = ttk.Combobox(
            process_head,
            textvariable=self._process_code,
            state="readonly",
            width=18,
            values=list(PROCESS_NAMES_ZH.values()),
        )
        self._process_box.pack(side=tk.LEFT, padx=(0, 8))
        self._process_box.bind("<<ComboboxSelected>>", self._load_process_route)
        self._process_apply_button = tk.Button(
            process_head, text="应用该工艺路由", command=self._apply_process_route
        )
        self._process_apply_button.pack(side=tk.LEFT, padx=4)
        self._process_remove_button = tk.Button(
            process_head,
            text="删除该工艺覆盖",
            command=self._remove_process_route,
            bg="#fff5f5",
            fg="#b03a2e",
            activebackground="#fadbd8",
            activeforeground="#922b21",
            disabledforeground="#aab7b8",
        )
        self._process_remove_button.pack(side=tk.LEFT, padx=4)
        self._process_hint_label = tk.Label(
            process_head,
            text="请先选择具体零件类别；未设置的步骤继承类别路由",
            bg="#f8fbfd",
            fg="#566573",
        )
        self._process_hint_label.pack(side=tk.LEFT, padx=10)
        self._process_step_boxes: dict[SkillStep, ttk.Combobox] = {}
        self._process_agent_boxes: dict[SkillStep, ttk.Combobox] = {}
        process_body = tk.Frame(process_frame, bg="#f8fbfd")
        process_body.pack(fill=tk.X, pady=(6, 0))
        for step in sorted(PROCESS_ROUTABLE_STEPS, key=lambda item: list(SkillStep).index(item)):
            cell = tk.LabelFrame(
                process_body,
                text=f" {STEP_NAMES_ZH[step]} ",
                bg="#ffffff",
                padx=5,
                pady=5,
            )
            cell.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            provider_box = ttk.Combobox(
                cell,
                textvariable=self._process_step_vars[step],
                state="readonly",
                width=22,
            )
            tk.Label(
                cell, text="报价 Skill", bg="#ffffff", fg="#566573", anchor=tk.W
            ).pack(fill=tk.X)
            provider_box.pack(fill=tk.X)
            provider_box.bind(
                "<<ComboboxSelected>>", self._mark_process_route_dirty, add="+"
            )
            agent_box = ttk.Combobox(
                cell,
                textvariable=self._process_agent_vars[step],
                state="readonly",
                width=22,
            )
            tk.Label(
                cell, text="执行智能体", bg="#ffffff", fg="#566573", anchor=tk.W
            ).pack(fill=tk.X, pady=(4, 0))
            agent_box.pack(fill=tk.X, pady=(3, 0))
            agent_box.bind(
                "<<ComboboxSelected>>", self._mark_process_route_dirty, add="+"
            )
            self._process_step_boxes[step] = provider_box
            self._process_agent_boxes[step] = agent_box

        footer = fixed_footer
        self._status = tk.Label(footer, bg=CONTENT_BG, fg="#566573")
        self._status.pack(side=tk.LEFT)
        self._save_button = tk.Button(
            footer,
            text="保存并发布到 SMB 公共槽",
            command=self._save,
            bg="#2471a3",
            fg="#ffffff",
            activebackground="#1a5276",
            activeforeground="#ffffff",
            disabledforeground="#d5d8dc",
            font=_font(10, True),
            padx=14,
            pady=6,
        )
        self._save_button.pack(side=tk.RIGHT)
        self._registry_notebook.bind(
            "<<NotebookTabChanged>>", self._update_remove_button_state
        )
        self._refresh_skill_widgets()
        self._update_remove_button_state()

    def _skill_label(self, skill: ExternalSkillDefinition) -> str:
        return f"Skill｜{skill.name_zh} [{skill.skill_id}]"

    def _agent_label(self, agent: AgentDefinition) -> str:
        prefix = "内置智能体" if agent.source_type == AgentSourceType.BUILTIN else "外挂智能体"
        return f"{prefix}｜{agent.name_zh} [{agent.agent_id}]"

    def _all_agents(self) -> list[AgentDefinition]:
        return [*BUILTIN_AGENTS, *self._agents]

    def _skill_id_from_label(self, label: str) -> str | None:
        for skill in self._skills:
            if self._skill_label(skill) == label:
                return skill.skill_id
        return None

    def _provider_id_from_label(self, label: str) -> str | None:
        return self._skill_id_from_label(label)

    def _agent_id_from_label(self, label: str) -> str | None:
        for agent in self._all_agents():
            if self._agent_label(agent) == label:
                return agent.agent_id
        return None

    def _resource_label(self, provider: str) -> str:
        skill = next((item for item in self._skills if item.skill_id == provider), None)
        if skill:
            return self._skill_label(skill)
        agent = next((item for item in self._all_agents() if item.agent_id == provider), None)
        return self._agent_label(agent) if agent else "内置系统（自动）"

    def _refresh_skill_widgets(self) -> None:
        for tree in self._resource_trees.values():
            tree.delete(*tree.get_children())
        for skill, tree, prefix in (
            *(
                (item, self._resource_trees["builtin_skill"], "builtin-skill")
                for item in BUILTIN_SKILLS
            ),
            *(
                (item, self._resource_trees["external_skill"], "skill")
                for item in self._skills
            ),
        ):
            tree.insert(
                "",
                tk.END,
                iid=f"{prefix}:{skill.skill_id}",
                values=(
                    skill.skill_id,
                    skill.name_zh,
                    skill.skill_version,
                    " / ".join(
                        item for item in (
                            "分步",
                            "整套" if skill.supports_full_quotation else "",
                            "Excel导出" if skill.supports_excel_export else "",
                            f"命令{len(skill.command_capabilities)}"
                            if skill.command_capabilities else "",
                        ) if item
                    ),
                    "、".join(STEP_NAMES_ZH[step] for step in skill.supported_steps),
                    skill.endpoint,
                ),
            )
        for agent in BUILTIN_AGENTS:
            self._resource_trees["builtin_agent"].insert(
                "",
                tk.END,
                iid=f"agent:{agent.agent_id}",
                values=(
                    agent.agent_id,
                    agent.name_zh,
                    agent.agent_version,
                    "智能体",
                    "、".join(STEP_NAMES_ZH[step] for step in agent.supported_steps),
                    agent.endpoint,
                ),
            )
        for agent in self._agents:
            self._resource_trees["external_agent"].insert(
                "",
                tk.END,
                iid=f"agent:{agent.agent_id}",
                values=(
                    agent.agent_id,
                    agent.name_zh,
                    agent.agent_version,
                    "智能体",
                    "、".join(STEP_NAMES_ZH[step] for step in agent.supported_steps),
                    agent.endpoint,
                ),
            )
        self._full_box["values"] = [
            self._skill_label(skill) for skill in self._skills if skill.supports_full_quotation
        ]
        export_values = ["内置 Excel 导出"] + [
            self._skill_label(skill) for skill in self._skills if skill.supports_excel_export
        ]
        self._excel_export_box["values"] = export_values
        selected_export = next(
            (
                self._skill_label(skill)
                for skill in self._skills
                if skill.skill_id == self._config.excel_export_skill_id
                and skill.supports_excel_export
            ),
            "内置 Excel 导出",
        )
        if (
            self._excel_export_skill.get() not in export_values
            or (
                self._config.excel_export_skill_id is not None
                and self._excel_export_skill.get() == "内置 Excel 导出"
            )
        ):
            self._excel_export_skill.set(selected_export)
        for step, box in self._step_boxes.items():
            box["values"] = ["内置系统（自动）"] + [
                self._skill_label(skill)
                for skill in self._skills
                if step in skill.supported_steps
            ]
            self._step_agent_boxes[step]["values"] = ["按执行资源默认"] + [
                self._agent_label(agent)
                for agent in self._all_agents()
                if step in agent.supported_steps
            ]
        for step, box in self._process_step_boxes.items():
            box["values"] = ["继承类别路由"] + list(self._step_boxes[step]["values"])
        self._refresh_process_options()
        self._load_process_route()
        self._toggle_mode()
        self._update_remove_button_state()

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
            display_route = route
            if self._active_category is not None and step in PRE_CATEGORY_STEPS:
                display_route = self._route_drafts[None]
                assert display_route is not None
            selected_route = (
                StepRoute(provider=display_route.full_skill_id or "builtin")
                if display_route.mode == SkillRoutingMode.FULL_QUOTATION
                else display_route.step_routes.get(step, StepRoute())
            )
            legacy_agent = next(
                (
                    item
                    for item in self._all_agents()
                    if item.agent_id == selected_route.provider
                ),
                None,
            )
            self._step_vars[step].set(
                "内置系统（自动）"
                if legacy_agent is not None
                else self._resource_label(selected_route.provider)
            )
            selected_agent_id = selected_route.agent_id or (
                legacy_agent.agent_id if legacy_agent else None
            )
            agent = next(
                (item for item in self._all_agents() if item.agent_id == selected_agent_id),
                None,
            )
            self._step_agent_vars[step].set(
                self._agent_label(agent) if agent else "按执行资源默认"
            )
        self._load_process_route()
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
        existing = self._route_drafts.get(self._active_category)
        process_routes = existing.process_routes if existing is not None else {}
        if mode == SkillRoutingMode.DISTRIBUTED:
            routes = {
                step: StepRoute(
                    provider=self._provider_id_from_label(variable.get()) or "builtin",
                    agent_id=self._agent_id_from_label(self._step_agent_vars[step].get()),
                )
                for step, variable in self._step_vars.items()
                if self._active_category is None or step not in PRE_CATEGORY_STEPS
            }
        self._route_drafts[self._active_category] = CategorySkillRouting(
            mode=mode,
            full_skill_id=full_skill_id,
            step_routes=routes,
            process_routes=process_routes,
        )

    def _switch_category(self, _event=None) -> None:
        self._capture_active_process_route()
        label = self._category.get()
        self._active_category = next(
            (category for category, name in CATEGORY_NAMES_ZH.items() if name == label),
            None,
        )
        self._load_active_route()

    def _selected_process_code(self) -> ProcessCode:
        return next(
            code for code, name in PROCESS_NAMES_ZH.items()
            if name == self._process_code.get()
        )

    def _refresh_process_options(self) -> None:
        if not hasattr(self, "_process_step_boxes"):
            return
        process = self._selected_process_code()
        for step in PROCESS_ROUTABLE_STEPS:
            self._process_step_boxes[step]["values"] = [
                "继承类别路由",
                "内置系统（自动）",
                *(
                    self._skill_label(skill)
                    for skill in self._skills
                    if step in skill.supported_steps
                    and (
                        not skill.supported_processes
                        or process in skill.supported_processes
                    )
                ),
            ]
            self._process_agent_boxes[step]["values"] = [
                "按执行资源默认",
                *(
                    self._agent_label(agent)
                    for agent in self._all_agents()
                    if step in agent.supported_steps
                    and (
                        not agent.supported_processes
                        or process in agent.supported_processes
                    )
                ),
            ]

    def _load_process_route(self, _event=None) -> None:
        if not hasattr(self, "_process_step_boxes"):
            return
        if _event is not None:
            self._capture_active_process_route()
        self._active_process_code = self._selected_process_code()
        self._refresh_process_options()
        route = self._route_drafts.get(self._active_category)
        if route is None:
            route = self._route_drafts.get(None)
        process_route = None
        if route is not None:
            process_route = route.process_routes.get(self._selected_process_code())
        for step in PROCESS_ROUTABLE_STEPS:
            selected = (
                process_route.step_routes.get(step) if process_route is not None else None
            )
            if selected is None:
                self._process_step_vars[step].set("继承类别路由")
                self._process_agent_vars[step].set("按执行资源默认")
            else:
                legacy_agent = next(
                    (
                        item
                        for item in self._all_agents()
                        if item.agent_id == selected.provider
                    ),
                    None,
                )
                self._process_step_vars[step].set(
                    "内置系统（自动）"
                    if legacy_agent is not None
                    else self._resource_label(selected.provider)
                )
                selected_agent_id = selected.agent_id or (
                    legacy_agent.agent_id if legacy_agent else None
                )
                agent = next(
                    (item for item in self._all_agents() if item.agent_id == selected_agent_id),
                    None,
                )
                self._process_agent_vars[step].set(
                    self._agent_label(agent) if agent else "按执行资源默认"
                )
        self._process_route_dirty = False

    def _mark_process_route_dirty(self, _event=None) -> None:
        self._process_route_dirty = True

    def _capture_active_process_route(self, *, force: bool = False) -> None:
        if not hasattr(self, "_process_step_boxes"):
            return
        if self._mode.get() != SkillRoutingMode.DISTRIBUTED.value:
            self._capture_active_route()
            return
        if (
            self._active_category is not None
            and self._inherit_global.get()
            and not self._process_route_dirty
            and not force
        ):
            self._capture_active_route()
            return
        if self._active_category is not None and self._inherit_global.get():
            global_route = self._route_drafts[None]
            assert global_route is not None
            self._route_drafts[self._active_category] = global_route.model_copy(deep=True)
            self._inherit_global.set(False)
        else:
            self._capture_active_route()
        route = self._route_drafts[self._active_category]
        assert route is not None
        step_routes = {}
        for step in PROCESS_ROUTABLE_STEPS:
            label = self._process_step_vars[step].get()
            if label == "继承类别路由":
                continue
            step_routes[step] = StepRoute(
                provider=self._provider_id_from_label(label) or "builtin",
                agent_id=self._agent_id_from_label(self._process_agent_vars[step].get()),
            )
        process_routes = dict(route.process_routes)
        code = self._active_process_code
        if step_routes:
            process_routes[code] = ProcessSkillRouting(step_routes=step_routes)
        else:
            process_routes.pop(code, None)
        self._route_drafts[self._active_category] = route.model_copy(
            update={"process_routes": process_routes}
        )
        self._process_route_dirty = False

    def _apply_process_route(self) -> None:
        self._capture_active_process_route(force=True)
        code = self._active_process_code
        scope = (
            CATEGORY_NAMES_ZH[self._active_category]
            if self._active_category is not None
            else "全局默认"
        )
        self._status.configure(
            text=f"已暂存 {scope} / {PROCESS_NAMES_ZH[code]} 路由"
        )

    def _remove_process_route(self) -> None:
        route = self._route_drafts.get(self._active_category)
        if route is None:
            return
        process_routes = dict(route.process_routes)
        process_routes.pop(self._selected_process_code(), None)
        self._route_drafts[self._active_category] = route.model_copy(
            update={"process_routes": process_routes}
        )
        self._load_process_route()

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
        for step, box in self._step_boxes.items():
            category_global_step = (
                self._active_category is not None and step in PRE_CATEGORY_STEPS
            )
            box.configure(
                state="disabled"
                if full or inherited or category_global_step
                else "readonly"
            )
            self._step_agent_boxes[step].configure(state=box.cget("state"))
        process_state = (
            "readonly"
            if not full
            else "disabled"
        )
        process_enabled = process_state == "readonly"
        self._process_box.configure(state=process_state)
        self._process_apply_button.configure(
            state="normal" if process_enabled else "disabled"
        )
        self._process_remove_button.configure(
            state="normal" if process_enabled else "disabled"
        )
        if full:
            hint = "整套报价模式不拆分具体工艺；切换到分步报价后可设置"
        elif self._active_category is None:
            hint = "这里设置所有零件类别共用的工艺默认；具体类别可再单独覆盖"
        elif inherited:
            hint = "可直接设置；应用后该类别将建立工艺覆盖，其他步骤保持当前全局设置"
        else:
            hint = "未设置的工艺或步骤自动继承全局/类别路由；多工艺可调用多个 Skill"
        self._process_hint_label.configure(text=hint)
        for step in PROCESS_ROUTABLE_STEPS:
            self._process_step_boxes[step].configure(state=process_state)
            self._process_agent_boxes[step].configure(state=process_state)

    def _discover(self) -> None:
        try:
            skill = self._client.discover(self._endpoint.get())
            self._skills = [item for item in self._skills if item.skill_id != skill.skill_id]
            self._skills.append(skill)
            self._refresh_skill_widgets()
            steps = "、".join(STEP_NAMES_ZH[step] for step in skill.supported_steps)
            mode = "支持整套报价，也可按声明步骤参与" if skill.supports_full_quotation else "仅支持分步参与"
            messagebox.showinfo(
                "检测成功",
                f"已读取：{skill.name_zh} {skill.skill_version}\n{mode}\n支持步骤：{steps}",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Skill 检测失败", str(exc), parent=self)

    def _discover_group(self) -> None:
        selected = filedialog.askdirectory(
            title="选择包含多个 Skill 子文件夹的目录", parent=self
        )
        if not selected:
            return
        try:
            discovered = self._client.discover_group(selected)
            discovered_ids = {item.skill_id for item in discovered}
            self._skills = [
                item for item in self._skills if item.skill_id not in discovered_ids
            ]
            self._skills.extend(discovered)
            self._endpoint.set(selected)
            self._refresh_skill_widgets()
            self._registry_notebook.select(self._resource_trees["external_skill"].master)
            messagebox.showinfo(
                "Skill 组载入成功",
                f"已载入 {len(discovered)} 个 Skill。\n"
                "请在路由区按步骤或具体工艺选择，保存后发布到公共槽。",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Skill 组载入失败", str(exc), parent=self)

    def _discover_agent(self) -> None:
        try:
            agent = self._client.discover_agent(self._endpoint.get())
            self._agents = [
                item for item in self._agents if item.agent_id != agent.agent_id
            ]
            self._agents.append(agent)
            self._refresh_skill_widgets()
            steps = "、".join(STEP_NAMES_ZH[step] for step in agent.supported_steps)
            processes = "、".join(
                PROCESS_NAMES_ZH[process] for process in agent.supported_processes
            ) or "不限具体工艺"
            messagebox.showinfo(
                "智能体检测成功",
                f"已读取：{agent.name_zh} {agent.agent_version}\n"
                f"支持步骤：{steps}\n支持工艺：{processes}",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("智能体检测失败", str(exc), parent=self)

    def _browse_folder(self) -> None:
        selected = filedialog.askdirectory(
            title="选择本地或 SMB 公共槽 Skill 文件夹", parent=self
        )
        if selected:
            self._endpoint.set(selected)

    def _remove(self) -> None:
        resource_key = self._selected_resource_key()
        if not resource_key:
            messagebox.showinfo("提示", "请先选择一个 Skill 或外挂智能体", parent=self)
            return
        if resource_key.startswith("builtin-skill:"):
            messagebox.showinfo("提示", "内置 Skill 不能移除。", parent=self)
            return
        resource_kind, resource_id = resource_key.split(":", 1)
        references = self._resource_references(resource_id, resource_kind)
        if references:
            messagebox.showwarning(
                "资源正在使用",
                "该资源仍被以下配置引用，不能移除：\n\n"
                + "\n".join(f"• {item}" for item in references)
                + "\n\n请先修改并应用相关路由。",
                parent=self,
            )
            return
        if not messagebox.askyesno(
            "确认移除",
            "确定从当前配置中移除选中的外接资源吗？\n保存并发布前不会影响其他电脑。",
            parent=self,
        ):
            return
        if resource_key.startswith("skill:"):
            skill_id = resource_key.removeprefix("skill:")
            self._skills = [item for item in self._skills if item.skill_id != skill_id]
        elif resource_key.startswith("agent:"):
            agent_id = resource_key.removeprefix("agent:")
            if any(item.agent_id == agent_id for item in BUILTIN_AGENTS):
                messagebox.showinfo("提示", "内置智能体不能移除。", parent=self)
                return
            self._agents = [item for item in self._agents if item.agent_id != agent_id]
        self._refresh_skill_widgets()

    def _resource_references(self, resource_id: str, resource_kind: str) -> list[str]:
        self._capture_active_process_route()
        references: list[str] = []
        if resource_kind == "skill" and (
            self._skill_id_from_label(self._excel_export_skill.get()) == resource_id
        ):
            references.append("Excel 导出 Skill")
        if resource_kind == "agent":
            for skill in self._skills:
                for step, agent_id in skill.step_agent_routes.items():
                    if agent_id == resource_id:
                        references.append(
                            f"Skill“{skill.name_zh}”的{STEP_NAMES_ZH[step]}执行智能体"
                        )
        for category, route in self._route_drafts.items():
            if route is None:
                continue
            scope = "全局默认" if category is None else CATEGORY_NAMES_ZH[category]
            if resource_kind == "skill" and route.full_skill_id == resource_id:
                references.append(f"{scope} / 整套报价 Skill")
            for step, step_route in route.step_routes.items():
                if resource_kind == "skill" and step_route.provider == resource_id:
                    references.append(f"{scope} / {STEP_NAMES_ZH[step]} Skill")
                if resource_kind == "agent" and (
                    step_route.agent_id == resource_id or step_route.provider == resource_id
                ):
                    references.append(f"{scope} / {STEP_NAMES_ZH[step]}执行智能体")
            for process, process_route in route.process_routes.items():
                process_name = PROCESS_NAMES_ZH[process]
                for step, step_route in process_route.step_routes.items():
                    if resource_kind == "skill" and step_route.provider == resource_id:
                        references.append(
                            f"{scope} / {process_name} / {STEP_NAMES_ZH[step]} Skill"
                        )
                    if resource_kind == "agent" and (
                        step_route.agent_id == resource_id
                        or step_route.provider == resource_id
                    ):
                        references.append(
                            f"{scope} / {process_name} / {STEP_NAMES_ZH[step]}执行智能体"
                        )
        return list(dict.fromkeys(references))

    def _selected_resource_key(self, tree: ttk.Treeview | None = None) -> str | None:
        if tree is not None:
            candidates = [tree]
        else:
            current_tab = self._registry_notebook.select()
            candidates = [
                candidate
                for candidate in self._resource_trees.values()
                if str(candidate.master) == current_tab
            ]
        for candidate in candidates:
            if candidate is None:
                continue
            selected = candidate.selection()
            if selected:
                return str(selected[0])
        return None

    def _update_remove_button_state(self, _event=None) -> None:
        if not hasattr(self, "_remove_button"):
            return
        current_tab = self._registry_notebook.select()
        external_tabs = {
            str(self._resource_trees["external_skill"].master),
            str(self._resource_trees["external_agent"].master),
        }
        removable = current_tab in external_tabs and self._selected_resource_key() is not None
        self._remove_button.configure(state=tk.NORMAL if removable else tk.DISABLED)

    def _show_skill_capabilities(
        self, _event=None, *, tree: ttk.Treeview | None = None
    ) -> None:
        resource_key = self._selected_resource_key(tree)
        if not resource_key:
            return
        if resource_key.startswith("agent:"):
            self._show_agent_capabilities(resource_key.removeprefix("agent:"))
            return
        builtin = resource_key.startswith("builtin-skill:")
        skill_id = resource_key.split(":", 1)[1]
        skill_pool = BUILTIN_SKILLS if builtin else self._skills
        skill = next((item for item in skill_pool if item.skill_id == skill_id), None)
        if skill is None:
            return
        capability_rows = [
            {"field": "Skill ID", "value": skill.skill_id},
            {"field": "名称", "value": skill.name_zh},
            {"field": "版本", "value": skill.skill_version},
            {
                "field": "运行方式",
                "value": (
                    "内置系统"
                    if skill.source_type == SkillSourceType.BUILTIN
                    else "HTTP 服务"
                    if skill.source_type == SkillSourceType.HTTP
                    else "文件夹 Skill"
                ),
            },
            {"field": "整套报价", "value": "支持" if skill.supports_full_quotation else "不支持"},
            {"field": "Excel 导出", "value": "支持" if skill.supports_excel_export else "不支持"},
            {"field": "导出命令", "value": " ".join(skill.excel_export_command) or "—"},
            {"field": "环境要求", "value": "、".join(skill.execution_requirements) or "无额外声明"},
            {"field": "可执行命令数", "value": len(skill.command_capabilities)},
            {"field": "可参与步骤数", "value": len(skill.supported_steps)},
            {"field": "位置", "value": skill.endpoint},
        ]
        step_rows = [
            {
                "index": index,
                "code": step.value,
                "name": STEP_NAMES_ZH[step],
                "usage": "可在分步路由中选择",
            }
            for index, step in enumerate(skill.supported_steps, 1)
        ]
        command_rows = [
            {
                "command_id": item.command_id,
                "kind": item.kind.value,
                "tasks": "、".join(task.value for task in item.task_types),
                "requirements": "、".join(item.requirements) or "无",
                "environment": (
                    "可用"
                    if all(
                        ExternalSkillCommandRunner.requirement_ok(requirement)
                        for requirement in item.requirements
                    )
                    else "缺少：" + "、".join(
                        requirement
                        for requirement in item.requirements
                        if not ExternalSkillCommandRunner.requirement_ok(requirement)
                    )
                ),
                "timeout": item.timeout_seconds,
                "command": " ".join(item.command),
            }
            for item in skill.command_capabilities
        ]
        try:
            content = self._client.read_skill_content(skill)
        except Exception as exc:
            content = f"内容读取失败：{exc}"
        file_rows = (
            self._client.list_folder_files(skill.endpoint)
            if skill.source_type == SkillSourceType.FOLDER
            else [{
                "path": "内置资源" if builtin else "远端资源",
                "type": "不可枚举",
                "size": "—",
                "usage": "内置内容随程序发布" if builtin else "HTTP 服务不公开服务器文件结构",
            }]
        )
        StructuredDetailWindow(
            self,
            f"Skill 能力详情 — {skill.name_zh}",
            [
                ("能力概况", [("field", "字段", 210), ("value", "内容", 740)], capability_rows),
                ("支持步骤", [
                    ("index", "序号", 60), ("code", "步骤代码", 230),
                    ("name", "功能名称", 220), ("usage", "使用方式", 400),
                ], step_rows),
                ("可执行命令", [
                    ("command_id", "Command ID", 150), ("kind", "类型", 90),
                    ("tasks", "任务", 230), ("requirements", "环境要求", 180),
                    ("environment", "本机检查", 130),
                    ("timeout", "超时(秒)", 80), ("command", "命令模板", 420),
                ], command_rows),
                ("文件结构", [
                    ("path", "相对路径", 420), ("type", "文件类型", 150),
                    ("size", "大小(字节)", 110), ("usage", "展示/使用说明", 420),
                ], file_rows),
                ("Skill 内容", [
                    ("resource", "资源", 180), ("content", "完整内容（双击查看）", 900),
                ], [{"resource": skill.endpoint, "content": content}]),
            ],
        )

    def _show_agent_capabilities(self, agent_id: str) -> None:
        agent = next(
            (item for item in self._all_agents() if item.agent_id == agent_id), None
        )
        if agent is None:
            return
        try:
            content = self._client.read_agent_content(agent)
        except Exception as exc:
            content = f"内容读取失败：{exc}"
        file_rows = (
            self._client.list_folder_files(agent.endpoint)
            if agent.source_type == AgentSourceType.FOLDER
            else [{
                "path": "内置资源" if agent.source_type == AgentSourceType.BUILTIN else "远端资源",
                "type": "不可枚举",
                "size": "—",
                "usage": (
                    "内置内容随程序发布"
                    if agent.source_type == AgentSourceType.BUILTIN
                    else "HTTP 服务不公开服务器文件结构"
                ),
            }]
        )
        capability_rows = [
            {"field": "智能体 ID", "value": agent.agent_id},
            {"field": "名称", "value": agent.name_zh},
            {"field": "来源", "value": agent.source_type.value},
            {"field": "版本", "value": agent.agent_version},
            {"field": "说明", "value": agent.description_zh or "—"},
            {
                "field": "支持步骤",
                "value": "、".join(STEP_NAMES_ZH[item] for item in agent.supported_steps),
            },
            {
                "field": "支持工艺",
                "value": "、".join(
                    PROCESS_NAMES_ZH[item] for item in agent.supported_processes
                ) or "不限具体工艺",
            },
            {"field": "位置", "value": agent.endpoint},
        ]
        StructuredDetailWindow(
            self,
            f"智能体详情 — {agent.name_zh}",
            [
                ("能力清单", [("field", "字段", 210), ("value", "内容", 760)], capability_rows),
                ("文件结构", [
                    ("path", "相对路径", 420), ("type", "文件类型", 150),
                    ("size", "大小(字节)", 110), ("usage", "展示/使用说明", 420),
                ], file_rows),
                ("智能体内容", [
                    ("resource", "资源", 180), ("content", "完整内容（双击查看）", 900),
                ], [{"resource": agent.endpoint, "content": content}]),
            ],
        )

    def _save(self) -> None:
        self._save_button.configure(state=tk.DISABLED)
        self._status.configure(text="正在发布配置…", fg="#1a5276")
        self.update_idletasks()
        try:
            self._capture_active_process_route()
            global_route = self._route_drafts[None]
            assert global_route is not None
            category_routes = {
                category: route
                for category, route in self._route_drafts.items()
                if category is not None and route is not None
            }
            candidate = ExternalSkillRoutingConfig(
                schema_version="2.0",
                config_version=self._config.config_version,
                mode=global_route.mode,
                skills=self._skills,
                agents=self._agents,
                full_skill_id=global_route.full_skill_id,
                step_routes=global_route.step_routes,
                process_routes=global_route.process_routes,
                category_routes=category_routes,
                debug_mode=self._debug_mode.get(),
                excel_export_skill_id=self._skill_id_from_label(
                    self._excel_export_skill.get()
                ),
            )
            self._config = self._service.save(self._actor, candidate)
            self._skills = list(self._config.skills)
            self._agents = list(self._config.agents)
            self._refresh_skill_widgets()
            self._status.configure(
                text=f"已发布配置版本 {self._config.config_version} 到 SMB 公共槽",
                fg="#1e8449",
            )
            messagebox.showinfo("保存完成", "所有电脑同步后将使用相同 Skill 路由", parent=self)
        except Exception as exc:
            self._status.configure(text=f"发布失败：{exc}", fg="#c0392b")
            messagebox.showerror("保存失败", str(exc), parent=self)
        finally:
            self._save_button.configure(state=tk.NORMAL)
