from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import ezdxf

from quotation.application.quotation_service import QuotationApplicationService
from quotation.infrastructure.rules.feature_price_calibration import (
    FeaturePriceCalibration,
    canonical_dimensions,
    extract_dimensions,
)


def _write_drawing(path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = ezdxf.new()
    model = document.modelspace()
    model.add_lwpolyline([(0, 0), (60, 0), (60, 70), (0, 70)], close=True)
    model.add_circle((30, 35), radius=3)
    model.add_text("A6061-T6", height=3).set_placement((0, 80))
    model.add_text("60*70*20", height=3).set_placement((0, 90))
    document.saveas(path)


def test_dimension_extraction_uses_drawing_text_not_identifier():
    result = extract_dimensions(["普通文件名", "60*70*20", "A6061-T6"])

    assert result is not None
    assert result[1] == (70.0, 60.0, 20.0)
    assert canonical_dimensions("φ250×15") == (250.0, 15.0, 1.0)


def test_published_model_forbids_identifier_matching():
    payload = json.loads(
        Path("data/feature-price-calibration-gcs-v1.0.json").read_text(encoding="utf-8")
    )

    assert payload["status"] == "ACTIVE_REVIEW_REQUIRED"
    assert payload["training_count"] == 62
    assert payload["prohibited_matching_fields"] == [
        "part_number",
        "drawing_number",
        "file_name",
    ]
    assert payload["validation"]["leave_one_out_wape_pct"] == 15.78


def test_feature_prediction_needs_material_and_dimensions():
    model = FeaturePriceCalibration()

    prediction = model.predict(texts=["A6061-T6", "60*70*20", "表面喷砂，阳极银色"])

    assert prediction is not None
    assert prediction.amount > 0
    assert prediction.material == "A6061-T6"
    assert model.predict(texts=["A6061-T6", "没有尺寸"]) is None


def test_quote_is_identical_after_file_rename_and_requires_review(tmp_path):
    first = tmp_path / "第一目录" / "未来零件-无料号.dxf"
    second = tmp_path / "第二目录" / "任意文件名.dxf"
    _write_drawing(first)
    _write_drawing(second)

    service = QuotationApplicationService()
    first_result = service.quote_single_file(first)
    second_result = service.quote_single_file(second)

    assert first_result.quote is not None
    assert second_result.quote is not None
    assert first_result.quote.total == second_result.quote.total
    assert len(first_result.quote.items) > 1
    assert not any(
        item.resolution_source == "FEATURE_CALIBRATION_MODEL"
        for item in first_result.quote.items
    )
    assert any(item.category == "material" for item in first_result.quote.items)
    assert any(item.category == "process" for item in first_result.quote.items)
    assert first_result.feature_summary["itemized_subtotal"].endswith("元")
    assert "不计入正式合计" in first_result.feature_summary["feature_calibration_reference"]
    assert first_result.status in {"COMPLETE", "REVIEW_REQUIRED"}
    assert first_result.tax is not None
    assert first_result.tax.tax_rate == Decimal("0.13")
    assert "不是正式价格" in first_result.warnings[-1]
    assert all("UC" not in (item.evidence or "") for item in first_result.quote.items)
