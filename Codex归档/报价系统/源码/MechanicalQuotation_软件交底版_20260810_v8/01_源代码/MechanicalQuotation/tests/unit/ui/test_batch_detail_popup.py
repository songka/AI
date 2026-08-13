from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from quotation.domain.quote import PriceSource, QuoteConfidence, QuoteItem
from quotation.ui.widgets import batch_ai_detail_sections
from quotation.ui.widgets import BatchQuotePage


class _Tree:
    def selection(self):
        return ("batch-3",)

    def identify_row(self, _y):
        return "batch-3"

    def selection_set(self, _row):
        pass

    def focus(self, _row):
        pass


class _Window:
    def bind(self, *_args, **_kwargs):
        pass

    def transient(self, *_args):
        pass

    def lift(self):
        pass

    def focus_force(self):
        pass


def test_batch_detail_uses_row_to_result_mapping_instead_of_completion_order():
    result = SimpleNamespace(
        drawing_number="ROW-3",
        status="COMPLETE",
        ai_used=True,
        ai_suggestions={},
        warnings=[],
        errors=[],
    )
    page = SimpleNamespace(
        _tree=_Tree(),
        _result_by_item={"batch-3": result},
        _detail_windows=set(),
        winfo_toplevel=lambda: None,
    )

    with patch("quotation.ui.widgets.StructuredDetailWindow", return_value=_Window()) as window:
        BatchQuotePage._show_selected_ai_detail(page)

    assert window.call_args.args[2][0][0] == "执行概况"
    assert "ROW-3" in window.call_args.args[1]


def test_batch_detail_supports_decimal_values_and_contains_formal_quote_lines():
    quote_item = QuoteItem(
        line_id="L-1",
        category="process",
        name="磨床 加工费",
        quantity=1.2,
        unit="hour",
        unit_price=50,
        amount=60,
        source=PriceSource.C,
        confidence=QuoteConfidence.MEDIUM,
        evidence="hours=1.2, rate=50",
    )
    result = SimpleNamespace(
        drawing_number="D-1",
        status="REVIEW_REQUIRED",
        ai_used=True,
        ai_suggestions={"agents": {"价格审核智能体": {"amount": Decimal("60.00")}}},
        warnings=[],
        errors=[],
        quote=SimpleNamespace(items=[quote_item]),
    )

    sections = batch_ai_detail_sections(result)

    assert [section[0] for section in sections[:2]] == ["执行概况", "正式报价明细"]
    assert sections[1][2][0]["name"] == "磨床 加工费"


def test_batch_detail_distinguishes_deepseek_roles_from_internal_summary():
    result = SimpleNamespace(
        drawing_number="D-2",
        status="REVIEW_REQUIRED",
        ai_used=True,
        ai_suggestions={
            "agents": {
                "工艺规划智能体": [{"process_name": "銑床"}],
                "风险汇总智能体": {"verdict": "REVIEW"},
            }
        },
        warnings=[],
        errors=[],
        quote=SimpleNamespace(items=[]),
    )

    sections = batch_ai_detail_sections(result)
    agent_section = next(section for section in sections if section[0] == "AI 角色（4+1）")
    executors = {row["agent"]: row["executor"] for row in agent_section[2]}

    assert executors["工艺规划智能体"] == "内置 DeepSeek"
    assert executors["风险汇总智能体"] == "内部规则汇总"


def test_batch_ai_items_show_skill_agent_and_process_execution():
    result = SimpleNamespace(
        drawing_number="D-3",
        status="REVIEW_REQUIRED",
        ai_used=True,
        ai_suggestions={
            "price_estimates": [{
                "line_id": "AI-1", "unit_price": 20, "quantity": 1,
                "amount": 20, "confidence": 0.7, "reason": "缺少正式价格",
            }],
            "skill_debug_trace": [{
                "step": "UNKNOWN_ESTIMATION",
                "step_name_zh": "待确认项 AI 估价",
                "provider": "外接估价 Skill",
                "provider_type": "FOLDER",
                "agent": "外接估价智能体",
                "process_codes": ["MILL"],
                "status": "成功",
                "duration_ms": 12,
                "output": {},
            }],
        },
        warnings=[],
        errors=[],
        quote=SimpleNamespace(items=[]),
    )

    sections = batch_ai_detail_sections(result)
    estimates = next(section for section in sections if section[0] == "AI 估价")[2]
    traces = next(section for section in sections if section[0] == "Skill 调试")[2]

    assert estimates[0]["skill"] == "外接估价 Skill"
    assert estimates[0]["agent"] == "外接估价智能体"
    assert traces[0]["provider_type"] == "FOLDER"
    assert traces[0]["processes"] == "MILL"


def test_batch_ai_items_keep_external_skill_agent_when_debug_is_off():
    result = SimpleNamespace(
        drawing_number="D-4",
        status="REVIEW_REQUIRED",
        ai_used=True,
        ai_suggestions={
            "price_estimates": [{"line_id": "AI-2", "reason": "待确认"}],
            "external_skills": [{
                "selected_steps": ["UNKNOWN_ESTIMATION"],
                "skill": {"name_zh": "外接参考估价 Skill"},
                "agent": {"name_zh": "外接估价 Agent"},
            }],
        },
        warnings=[],
        errors=[],
        quote=SimpleNamespace(items=[]),
    )

    sections = batch_ai_detail_sections(result)
    estimate = next(section for section in sections if section[0] == "AI 估价")[2][0]

    assert estimate["skill"] == "外接参考估价 Skill"
    assert estimate["agent"] == "外接估价 Agent"
