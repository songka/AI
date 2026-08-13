from types import SimpleNamespace

from quotation.ui import demo_app


class _FakeApp:
    instances = []

    def __init__(self, session=None, auth_service=None):
        self.session = session
        self.auth_service = auth_service
        self.mainloop_called = False
        self.window_title = None
        self.__class__.instances.append(self)

    def title(self, value):
        self.window_title = value

    def mainloop(self):
        self.mainloop_called = True


def test_desktop_defaults_to_no_login(monkeypatch):
    _FakeApp.instances.clear()
    monkeypatch.setattr(
        "quotation.application.settings_service.UserSettingsService.load",
        lambda _self: {"auth_enabled": False},
    )
    monkeypatch.setattr(demo_app, "DemoApp", _FakeApp)
    monkeypatch.setattr(
        "quotation.ui.auth_dialog.authenticate_desktop",
        lambda: (_ for _ in ()).throw(AssertionError("免登录模式不应打开登录窗口")),
    )

    demo_app.main()

    assert len(_FakeApp.instances) == 1
    assert _FakeApp.instances[0].session is None
    assert _FakeApp.instances[0].mainloop_called is True


def test_enabled_authentication_still_opens_without_login(monkeypatch):
    _FakeApp.instances.clear()
    monkeypatch.setattr(
        "quotation.application.settings_service.UserSettingsService.load",
        lambda _self: {"auth_enabled": True},
    )
    monkeypatch.setattr(demo_app, "DemoApp", _FakeApp)
    monkeypatch.setattr(
        "quotation.ui.auth_dialog.authenticate_desktop",
        lambda: (_ for _ in ()).throw(AssertionError("启动时不应强制登录")),
    )

    demo_app.main()

    assert _FakeApp.instances[0].session is None
    assert _FakeApp.instances[0].mainloop_called is True


def test_no_login_navigation_hides_privileged_approval_page():
    view = SimpleNamespace(_session=None)

    allowed = demo_app.DemoApp._allowed_nav_items(view)

    assert "新建报价" in allowed
    assert "价格管理" in allowed
    assert "管理员登录" in allowed
    assert "供应商管理" not in allowed
    assert "系统设置" not in allowed
    assert "价格审核" not in allowed
    assert "用户管理" not in allowed


def test_authenticated_navigation_only_shows_authorized_functions():
    view = SimpleNamespace(
        _session=SimpleNamespace(permissions=("quotation.view", "user.view"))
    )

    allowed = demo_app.DemoApp._allowed_nav_items(view)

    assert allowed == {"报价记录", "用户管理", "退出登录"}


def test_external_skill_settings_is_only_visible_with_system_config_permission():
    admin_view = SimpleNamespace(
        _session=SimpleNamespace(permissions=("system.config",))
    )
    engineer_view = SimpleNamespace(
        _session=SimpleNamespace(permissions=("quotation.view", "price.modify"))
    )

    assert "外接Skill设置" in demo_app.DemoApp._allowed_nav_items(admin_view)
    assert "外接Skill设置" not in demo_app.DemoApp._allowed_nav_items(engineer_view)


def test_user_management_rows_show_chinese_role_status_and_permissions():
    user = SimpleNamespace(
        user_id="U-1",
        username="sales001",
        display_name="业务员",
        role=SimpleNamespace(value="sales"),
        status=SimpleNamespace(value="active"),
        assigned_permissions=["quotation.view"],
        last_login_time=None,
    )

    class FakeAuth:
        def list_users(self, _actor):
            return [user]

        def get_user_permissions(self, _user):
            return ["quotation.view"]

        def permission_catalog(self, _actor):
            return {"quotation.view": {"name": "查看报价"}}

    view = SimpleNamespace(_user_context=lambda: (FakeAuth(), object()))

    rows = demo_app.DemoApp._load_users(view, "业务", "启用")

    assert rows[0]["role_display"] == "业务"
    assert rows[0]["status_display"] == "启用"
    assert rows[0]["permissions_display"] == "查看报价"
    assert rows[0]["permission_mode"] == "管理员单独分配"


def test_authentication_can_be_activated_without_restarting(monkeypatch):
    session = SimpleNamespace(
        display_name="管理员",
        role=SimpleNamespace(value="admin"),
    )
    service = object()
    context = SimpleNamespace(session=session, service=service)
    monkeypatch.setattr(
        "quotation.ui.auth_dialog.authenticate_desktop",
        lambda parent=None: context,
    )

    events = []
    view = SimpleNamespace(
        _session=None,
        _auth_service=None,
        _content=object(),
        _main=SimpleNamespace(destroy=lambda: events.append("destroy")),
        _configure_authenticated_services=lambda: events.append("configure"),
        title=lambda value: events.append(value),
        _build_ui=lambda: events.append("build"),
        update_idletasks=lambda: events.append("idle"),
        winfo_toplevel=lambda: "top-level-owner",
    )

    activated = demo_app.DemoApp._activate_authentication(view)

    assert activated is True
    assert view._session is session
    assert view._auth_service is service
    assert events[0] == "idle"
    assert events[1] == "configure"
    assert "管理员" in events[2]
    assert events[-2:] == ["destroy", "build"]


def test_authentication_startup_error_is_visible_in_gui(monkeypatch):
    monkeypatch.setattr(
        "quotation.ui.auth_dialog.authenticate_desktop",
        lambda parent=None: (_ for _ in ()).throw(FileNotFoundError("config/roles.yaml")),
    )
    errors = []
    view = SimpleNamespace(
        update_idletasks=lambda: None,
        winfo_toplevel=lambda: "top-level-owner",
    )
    monkeypatch.setattr(
        demo_app.messagebox,
        "showerror",
        lambda title, message, parent=None: errors.append((title, message, parent)),
    )

    activated = demo_app.DemoApp._activate_authentication(view)

    assert activated is False
    assert errors[0][0] == "管理员登录无法打开"
    assert "config/roles.yaml" in errors[0][1]
    assert errors[0][2] is view
