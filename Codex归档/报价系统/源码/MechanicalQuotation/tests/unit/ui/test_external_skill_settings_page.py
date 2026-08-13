from types import SimpleNamespace

from quotation.application.external_skill_settings import (
    AgentDefinition,
    AgentSourceType,
    CategorySkillRouting,
    ExternalSkillRoutingConfig,
    PROCESS_NAMES_ZH,
    PROCESS_ROUTABLE_STEPS,
    PartCategory,
    ProcessCode,
    SkillRoutingMode,
    SkillStep,
    StepRoute,
)
from quotation.ui import external_skill_settings_page as page_module
from quotation.ui.external_skill_settings_page import ExternalSkillSettingsPage


class _Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Widget:
    def __init__(self):
        self.options = {}

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def __setitem__(self, key, value):
        self.options[key] = value


def _bare_page():
    return ExternalSkillSettingsPage.__new__(ExternalSkillSettingsPage)


def test_capture_active_process_route_keeps_unapplied_controls():
    page = _bare_page()
    page._process_step_boxes = {step: object() for step in PROCESS_ROUTABLE_STEPS}
    page._mode = _Var(SkillRoutingMode.DISTRIBUTED.value)
    page._active_category = None
    page._inherit_global = _Var(False)
    page._active_process_code = ProcessCode.CNC
    page._process_route_dirty = True
    page._route_drafts = {None: CategorySkillRouting()}
    page._process_step_vars = {
        step: _Var("外接工时") if step == SkillStep.TIME_ESTIMATION else _Var("继承类别路由")
        for step in PROCESS_ROUTABLE_STEPS
    }
    page._process_agent_vars = {step: _Var("按执行资源默认") for step in PROCESS_ROUTABLE_STEPS}
    page._capture_active_route = lambda: None
    page._provider_id_from_label = lambda label: "vendor.time" if label == "外接工时" else None
    page._agent_id_from_label = lambda _label: None

    page._capture_active_process_route()

    saved = page._route_drafts[None].process_routes[ProcessCode.CNC]
    assert saved.step_routes[SkillStep.TIME_ESTIMATION].provider == "vendor.time"


def test_process_dropdown_captures_previous_process_before_loading_next():
    page = _bare_page()
    page._process_step_boxes = {step: _Widget() for step in PROCESS_ROUTABLE_STEPS}
    page._process_agent_boxes = {step: _Widget() for step in PROCESS_ROUTABLE_STEPS}
    page._process_step_vars = {step: _Var("") for step in PROCESS_ROUTABLE_STEPS}
    page._process_agent_vars = {step: _Var("") for step in PROCESS_ROUTABLE_STEPS}
    page._process_code = _Var(PROCESS_NAMES_ZH[ProcessCode.LATHE])
    page._active_process_code = ProcessCode.CNC
    page._active_category = None
    page._route_drafts = {None: CategorySkillRouting()}
    page._skills = []
    page._all_agents = lambda: []
    captured = []
    page._capture_active_process_route = lambda: captured.append(page._active_process_code)

    page._load_process_route(object())

    assert captured == [ProcessCode.CNC]
    assert page._active_process_code == ProcessCode.LATHE


def test_save_refreshes_agents_from_persisted_config(monkeypatch):
    persisted_agent = AgentDefinition(
        agent_id="vendor.time-agent",
        name_zh="工时智能体",
        source_type=AgentSourceType.FOLDER,
        endpoint="C:/skills/time-agent",
        supported_steps=[SkillStep.TIME_ESTIMATION],
    )
    persisted = ExternalSkillRoutingConfig(agents=[persisted_agent])

    class _Service:
        def save(self, _actor, _candidate):
            return persisted

    page = _bare_page()
    page._service = _Service()
    page._actor = object()
    page._config = ExternalSkillRoutingConfig()
    page._skills = []
    page._agents = []
    page._route_drafts = {None: CategorySkillRouting()}
    page._debug_mode = _Var(False)
    page._excel_export_skill = _Var("内置 Excel 导出")
    page._save_button = _Widget()
    page._status = _Widget()
    page.update_idletasks = lambda: None
    page._capture_active_process_route = lambda: None
    page._skill_id_from_label = lambda _label: None
    page._refresh_skill_widgets = lambda: None
    monkeypatch.setattr(page_module.messagebox, "showinfo", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(page_module.messagebox, "showerror", lambda *_args, **_kwargs: None)

    page._save()

    assert page._agents == [persisted_agent]


def _inherited_page():
    page = _bare_page()
    page._process_step_boxes = {step: _Widget() for step in PROCESS_ROUTABLE_STEPS}
    page._process_agent_boxes = {step: _Widget() for step in PROCESS_ROUTABLE_STEPS}
    page._process_step_vars = {step: _Var("继承类别路由") for step in PROCESS_ROUTABLE_STEPS}
    page._process_agent_vars = {step: _Var("按执行资源默认") for step in PROCESS_ROUTABLE_STEPS}
    page._mode = _Var(SkillRoutingMode.DISTRIBUTED.value)
    page._active_category = PartCategory.MACHINING
    page._inherit_global = _Var(True)
    page._active_process_code = ProcessCode.CNC
    page._process_route_dirty = False
    page._route_drafts = {
        None: CategorySkillRouting(),
        PartCategory.MACHINING: None,
        PartCategory.SHEET_METAL: None,
    }
    page._capture_active_route = lambda: None
    return page


def test_save_does_not_turn_unmodified_inherited_process_into_override(monkeypatch):
    page = _inherited_page()
    page._service = type("Service", (), {"save": lambda _self, _actor, candidate: candidate})()
    page._actor = object()
    page._config = ExternalSkillRoutingConfig()
    page._skills = []
    page._agents = []
    page._debug_mode = _Var(False)
    page._excel_export_skill = _Var("内置 Excel 导出")
    page._save_button = _Widget()
    page._status = _Widget()
    page.update_idletasks = lambda: None
    page._skill_id_from_label = lambda _label: None
    page._refresh_skill_widgets = lambda: None
    monkeypatch.setattr(page_module.messagebox, "showinfo", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(page_module.messagebox, "showerror", lambda *_args, **_kwargs: None)

    page._save()

    assert page._route_drafts[PartCategory.MACHINING] is None
    assert PartCategory.MACHINING not in page._config.category_routes


def test_category_switch_keeps_unmodified_inherited_route_as_none():
    page = _inherited_page()
    page._category = _Var("钣金件")
    page._load_active_route = lambda: None

    page._switch_category()

    assert page._route_drafts[PartCategory.MACHINING] is None


def test_process_switch_keeps_unmodified_inherited_route_as_none():
    page = _inherited_page()
    page._process_code = _Var(PROCESS_NAMES_ZH[ProcessCode.LATHE])
    page._skills = []
    page._all_agents = lambda: []

    page._load_process_route(object())

    assert page._route_drafts[PartCategory.MACHINING] is None
    assert page._active_process_code == ProcessCode.LATHE


def test_referenced_skill_is_blocked_before_remove_confirmation(monkeypatch):
    page = _bare_page()
    page._skills = [object()]
    page._agents = []
    page._route_drafts = {
        None: CategorySkillRouting(
            step_routes={SkillStep.TIME_ESTIMATION: StepRoute(provider="vendor.time")}
        )
    }
    page._excel_export_skill = _Var("内置 Excel 导出")
    page._skill_id_from_label = lambda _label: None
    page._capture_active_process_route = lambda: None
    page._selected_resource_key = lambda: "skill:vendor.time"
    warnings = []
    monkeypatch.setattr(
        page_module.messagebox,
        "showwarning",
        lambda _title, message, **_kwargs: warnings.append(message),
    )
    monkeypatch.setattr(
        page_module.messagebox,
        "askyesno",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not confirm")),
    )

    page._remove()

    assert warnings and "工时估算" in warnings[0]
    assert len(page._skills) == 1


def test_referenced_agent_is_blocked_before_remove_confirmation(monkeypatch):
    page = _bare_page()
    page._skills = []
    page._agents = [object()]
    page._route_drafts = {
        None: CategorySkillRouting(
            step_routes={
                SkillStep.TIME_ESTIMATION: StepRoute(agent_id="vendor.time-agent")
            }
        )
    }
    page._excel_export_skill = _Var("内置 Excel 导出")
    page._skill_id_from_label = lambda _label: None
    page._capture_active_process_route = lambda: None
    page._selected_resource_key = lambda: "agent:vendor.time-agent"
    warnings = []
    monkeypatch.setattr(
        page_module.messagebox,
        "showwarning",
        lambda _title, message, **_kwargs: warnings.append(message),
    )
    monkeypatch.setattr(
        page_module.messagebox,
        "askyesno",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not confirm")),
    )

    page._remove()

    assert warnings and "执行智能体" in warnings[0]
    assert len(page._agents) == 1


def test_unreferenced_skill_can_still_be_confirmed_and_removed(monkeypatch):
    page = _bare_page()
    page._skills = [SimpleNamespace(skill_id="vendor.unused")]
    page._agents = []
    page._route_drafts = {None: CategorySkillRouting()}
    page._excel_export_skill = _Var("内置 Excel 导出")
    page._skill_id_from_label = lambda _label: None
    page._capture_active_process_route = lambda: None
    page._selected_resource_key = lambda: "skill:vendor.unused"
    page._refresh_skill_widgets = lambda: None
    monkeypatch.setattr(page_module.messagebox, "askyesno", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        page_module.messagebox,
        "showwarning",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected warning")),
    )

    page._remove()

    assert page._skills == []
