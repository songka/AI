from unittest.mock import MagicMock

import ezdxf
import pytest

from quotation.application.multi_agent_review import MultiAgentReviewOrchestrator
from quotation.application.quotation_service import (
    JobStatus,
    QuotationApplicationService,
)


def test_multi_agent_roles_are_kept_separate_and_supervised():
    client = MagicMock()
    client.analyze_drawing_notes.return_value = {
        "summary": "精密零件", "requirements": ["平面度0.01"],
        "risks": ["未注明检验方法"], "confidence": 0.8,
    }
    client.classify_processes.return_value = [{"code": "GRIND"}]
    client.classify_part_category.return_value = {
        "part_category": "MACHINING", "confidence": 0.9, "evidence": ["存在磨削特征"]
    }
    client.audit_itemized_quote.return_value = {
        "verdict": "REVIEW", "issues": ["磨削工时需确认"],
        "actions": ["人工确认"], "confidence": 0.8,
    }
    service = MultiAgentReviewOrchestrator(client)

    prior = service.analyze_before_pricing("A", ["平面度0.01"], {"孔数量": 0})
    result = service.audit_after_pricing("A", [], [], prior)

    assert set(result) == {
        "备注理解智能体", "零件分类智能体", "工艺规划智能体",
        "价格审核智能体", "风险汇总智能体",
    }
    assert result["风险汇总智能体"]["requires_human_review"] is True
    assert result["风险汇总智能体"]["verdict"] == "REVIEW"


def test_invalid_price_audit_can_retry_prerequisite_agents_once():
    client = MagicMock()
    client.begin_controlled_retry.return_value = True
    client.analyze_drawing_notes.return_value = {
        "summary": "重试成功", "requirements": [], "risks": [], "confidence": 0.9,
    }
    client.classify_processes.return_value = [{"code": "MILL"}]
    client.classify_part_category.return_value = {
        "part_category": "MACHINING", "confidence": 0.9, "evidence": ["铣削轮廓"]
    }
    service = MultiAgentReviewOrchestrator(client)

    assert service.audit_failed({
        "verdict": "REVIEW",
        "issues": ["价格审核未返回有效结果"],
        "confidence": 0.0,
    }) is True
    refreshed = service.retry_dependencies("A", ["铣削"], {"孔数量": 1})

    assert refreshed["备注理解智能体"]["summary"] == "重试成功"
    assert refreshed["零件分类智能体"]["part_category"] == "MACHINING"
    client.begin_controlled_retry.assert_called_once_with()


def test_plate_shaped_milled_part_is_not_reclassified_as_sheet_metal():
    category = MultiAgentReviewOrchestrator._reconcile_category(
        {
            "part_category": "SHEET_METAL",
            "confidence": 0.85,
            "evidence": ["板类零件，有厚度"],
        },
        [{"code": "MILL"}, {"code": "CNC"}],
        ["S50C", "50*28*17", "工件表面镀铬"],
    )

    assert category["part_category"] == "MACHINING"
    assert category["status"] == "CONSISTENCY_CORRECTED"
    assert "板状毛坯不等于钣金件" in category["evidence"][-1]


def test_explicit_bending_evidence_keeps_sheet_metal_category():
    category = MultiAgentReviewOrchestrator._reconcile_category(
        {"part_category": "SHEET_METAL", "confidence": 0.9},
        [{"code": "MILL"}],
        ["SPCC t=2", "折弯两处"],
    )

    assert category["part_category"] == "SHEET_METAL"


@pytest.mark.parametrize("wrong_category", ["WELDMENT", "FRAME_ASSEMBLY"])
def test_machined_part_rejects_unsupported_structure_category(wrong_category):
    category = MultiAgentReviewOrchestrator._reconcile_category(
        {"part_category": wrong_category, "confidence": 0.8, "evidence": ["按外形猜测"]},
        [{"code": "MILL"}],
        ["S50C", "50*28*17", "铣削轮廓"],
    )

    assert category["part_category"] == "MACHINING"
    assert category["status"] == "CONSISTENCY_CORRECTED"


def test_full_quote_passes_itemized_prices_to_review_agent(tmp_path):
    drawing_path = tmp_path / "AI-REVIEW.dxf"
    document = ezdxf.new()
    modelspace = document.modelspace()
    modelspace.add_lwpolyline(
        [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
    )
    modelspace.add_text("S50C", height=5).set_placement((0, 55))
    document.saveas(drawing_path)

    client = MagicMock()
    client.extract_features.return_value = {}
    client.analyze_drawing_notes.return_value = {
        "summary": "一般机械零件",
        "requirements": [],
        "risks": [],
        "confidence": 0.9,
    }
    client.classify_processes.return_value = []
    client.audit_itemized_quote.return_value = {
        "verdict": "PASS",
        "issues": [],
        "actions": [],
        "confidence": 0.9,
    }

    result = QuotationApplicationService(ai_client=client).quote_single_file(
        drawing_path, use_ai=True
    )

    assert result.status in (JobStatus.COMPLETE, JobStatus.REVIEW_REQUIRED)
    assert not any("多智能体价格审核失败" in warning for warning in result.warnings)
    assert result.ai_suggestions["agents"]["风险汇总智能体"]["verdict"] == "PASS"
    audited_items = client.audit_itemized_quote.call_args.args[2]
    assert audited_items
    assert {"name", "category", "source", "amount"} <= set(audited_items[0])


def test_quote_retries_dependencies_rebuilds_process_price_and_reaudits(tmp_path):
    drawing_path = tmp_path / "AI-RETRY.dxf"
    document = ezdxf.new()
    modelspace = document.modelspace()
    modelspace.add_lwpolyline(
        [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
    )
    modelspace.add_circle((50, 25), radius=5)
    modelspace.add_text("S50C", height=5).set_placement((0, 55))
    document.saveas(drawing_path)

    class RecoveringClient:
        is_configured = True
        last_error = "AI服务连接失败：timed out"

        def __init__(self):
            self.retrying = False
            self.audit_calls = 0

        def extract_features(self, *_args, **_kwargs):
            return {}

        def estimate_unknown_costs(self, *_args, **_kwargs):
            return []

        def analyze_drawing_notes(self, *_args, **_kwargs):
            if self.retrying:
                return {
                    "summary": "普通孔板", "requirements": [], "risks": [], "confidence": 0.9,
                }
            return {
                "summary": "备注理解失败", "requirements": [],
                "risks": ["智能体未返回有效结果"], "confidence": 0.0,
            }

        def classify_processes(self, *_args, **_kwargs):
            if not self.retrying:
                return []
            return [{
                "code": "MILL", "process_name": "銑床", "estimated_hours": 1.0,
                "confidence": 0.9, "evidence": "普通孔板由铣床完成",
            }]

        def classify_part_category(self, *_args, **_kwargs):
            if not self.retrying:
                return {
                    "part_category": None, "confidence": 0.0,
                    "evidence": [], "status": "INVALID_RESULT",
                }
            return {
                "part_category": "MACHINING", "category_name": "加工件",
                "confidence": 0.9, "evidence": ["孔与铣削轮廓"], "status": "SUCCESS",
            }

        def audit_itemized_quote(self, *_args, **_kwargs):
            self.audit_calls += 1
            if not self.retrying:
                return {
                    "verdict": "REVIEW", "issues": ["价格审核未返回有效结果"],
                    "actions": [], "confidence": 0.0,
                }
            return {"verdict": "PASS", "issues": [], "actions": [], "confidence": 0.9}

        def begin_controlled_retry(self):
            self.retrying = True
            self.last_error = None
            return True

    client = RecoveringClient()
    result = QuotationApplicationService(ai_client=client).quote_single_file(
        drawing_path, use_ai=True
    )

    assert result.ai_suggestions["dependency_retry"]["status"] == "RECOVERED"
    assert result.ai_suggestions["agents"]["价格审核智能体"]["verdict"] == "PASS"
    assert result.feature_summary["part_category_source"] == "BUILTIN_DEEPSEEK_SKILL_RETRY"
    assert any(item.name == "銑床 加工費" for item in result.quote.items)
    assert not any(item.name.startswith("CNC ") for item in result.quote.items)
    assert client.audit_calls == 2


def test_ai_replaces_automatic_cnc_with_mill_for_simple_hole_part(tmp_path):
    drawing_path = tmp_path / "SIMPLE-MILL.dxf"
    document = ezdxf.new()
    modelspace = document.modelspace()
    modelspace.add_lwpolyline(
        [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
    )
    modelspace.add_circle((50, 25), radius=5)
    modelspace.add_text("S50C", height=5).set_placement((0, 55))
    document.saveas(drawing_path)

    client = MagicMock()
    client.extract_features.return_value = {}
    client.analyze_drawing_notes.return_value = {
        "summary": "普通平板孔加工",
        "requirements": [],
        "risks": [],
        "confidence": 0.9,
    }
    client.classify_processes.return_value = [{
        "code": "MILL",
        "process_name": "銑床",
        "estimated_hours": 1.0,
        "confidence": 0.9,
        "evidence": "普通平面与常规孔，三轴铣床足够",
    }]
    client.audit_itemized_quote.return_value = {
        "verdict": "REVIEW",
        "issues": [],
        "actions": ["确认铣床工时"],
        "confidence": 0.9,
    }

    result = QuotationApplicationService(ai_client=client).quote_single_file(
        drawing_path, use_ai=True
    )

    process_names = [
        item.name for item in result.quote.items if item.category == "process"
    ]
    assert "銑床 加工費" in process_names
    assert not any(name.startswith("CNC ") for name in process_names)
    mill_item = next(item for item in result.quote.items if item.name == "銑床 加工費")
    assert mill_item.unit_price == 40
    assert mill_item.amount == 40
    assert any("普通铣床足以完成" in warning for warning in result.warnings)


def test_explicit_cnc_requirement_is_not_replaced_by_mill(tmp_path):
    drawing_path = tmp_path / "EXPLICIT-CNC.dxf"
    document = ezdxf.new()
    modelspace = document.modelspace()
    modelspace.add_lwpolyline(
        [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
    )
    modelspace.add_circle((50, 25), radius=5)
    modelspace.add_text("S50C CNC加工", height=5).set_placement((0, 55))
    document.saveas(drawing_path)

    client = MagicMock()
    client.extract_features.return_value = {}
    client.analyze_drawing_notes.return_value = {
        "summary": "图纸要求 CNC",
        "requirements": ["CNC加工"],
        "risks": [],
        "confidence": 0.9,
    }
    client.classify_processes.return_value = [{
        "code": "MILL",
        "process_name": "銑床",
        "estimated_hours": 1.0,
        "confidence": 0.9,
        "evidence": "普通铣床建议",
    }]
    client.audit_itemized_quote.return_value = {
        "verdict": "REVIEW",
        "issues": [],
        "actions": [],
        "confidence": 0.9,
    }

    result = QuotationApplicationService(ai_client=client).quote_single_file(
        drawing_path, use_ai=True
    )

    process_names = [
        item.name for item in result.quote.items if item.category == "process"
    ]
    assert any(name.startswith("CNC ") for name in process_names)
    assert "銑床 加工費" not in process_names
    assert any("明确要求 CNC" in warning for warning in result.warnings)


def test_ai_process_alternatives_use_hours_times_rate_to_choose_lower_cost(tmp_path):
    drawing_path = tmp_path / "COST-OPTIMIZED-MILL.dxf"
    document = ezdxf.new()
    modelspace = document.modelspace()
    modelspace.add_lwpolyline(
        [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
    )
    modelspace.add_circle((50, 25), radius=5)
    modelspace.add_text("S50C", height=5).set_placement((0, 55))
    document.saveas(drawing_path)

    client = MagicMock()
    client.extract_features.return_value = {}
    client.analyze_drawing_notes.return_value = {
        "summary": "普通平板孔加工",
        "requirements": [],
        "risks": [],
        "confidence": 0.9,
    }
    client.classify_processes.return_value = [
        {
            "code": "CNC",
            "process_name": "CNC",
            "estimated_hours": 0.8,
            "confidence": 0.9,
            "evidence": "CNC 可完成",
        },
        {
            "code": "MILL",
            "process_name": "銑床",
            "estimated_hours": 1.0,
            "confidence": 0.9,
            "evidence": "普通铣床也可完成",
        },
    ]
    client.audit_itemized_quote.return_value = {
        "verdict": "REVIEW",
        "issues": [],
        "actions": ["确认候选工时"],
        "confidence": 0.9,
    }

    result = QuotationApplicationService(ai_client=client).quote_single_file(
        drawing_path, use_ai=True
    )

    process_names = [
        item.name for item in result.quote.items if item.category == "process"
    ]
    assert "銑床 加工費" in process_names
    assert not any(name.startswith("CNC ") for name in process_names)
    assert any(
        "CNC 64.00元、铣床 40.00元" in warning and "采用成本较低的銑床" in warning
        for warning in result.warnings
    )
    geometry = client.classify_processes.call_args.args[2]
    assert geometry["可用工艺小时费率"]["CNC"]["每小时工价"] == 80
    assert geometry["可用工艺小时费率"]["銑床"]["每小时工价"] == 40
