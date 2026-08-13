from types import SimpleNamespace

from quotation.ui.demo_app import DemoApp
from quotation.ui.widgets import NavPanel


def test_price_approval_navigation_is_admin_only():
    admin_view = SimpleNamespace(
        _session=SimpleNamespace(
            permissions=("quotation.view", "price.view_cost", "rule.approve")
        )
    )
    engineer_view = SimpleNamespace(
        _session=SimpleNamespace(permissions=("quotation.view", "price.view_cost", "price.modify"))
    )

    assert "价格审核" in dict(NavPanel.NAV_ITEMS)
    assert "价格审核" in DemoApp._allowed_nav_items(admin_view)
    assert "价格审核" not in DemoApp._allowed_nav_items(engineer_view)


def test_price_approval_rows_use_chinese_labels():
    class FakeApproval:
        def list_items(self, _actor, *, status=None, query=None):
            assert status == "PENDING_REVIEW"
            assert query == "SUS"
            return [
                {
                    "price_record_id": "PR-TEST",
                    "material_code": "SUS304",
                    "tax_included": False,
                    "review_status_display": "待审核",
                }
            ]

    view = SimpleNamespace(
        _approval_context=lambda: (FakeApproval(), SimpleNamespace())
    )

    rows = DemoApp._load_price_approvals(view, "SUS", "待审核")

    assert rows[0]["target_name"] == "304 不锈钢"
    assert rows[0]["tax_display"] == "未税价"
    assert rows[0]["review_status_display"] == "待审核"
