"""Tests for QuotationApplicationService."""
from __future__ import annotations

from decimal import Decimal

from quotation.application.quotation_service import (
    JobStatus,
    QuotationApplicationService,
    TaxResult,
)
from quotation.domain.quote import PriceSource, QuoteConfidence, QuoteItem


class TestTaxResult:
    def test_17_percent_calculation(self):
        items = [
            QuoteItem(line_id="M1", category="material", name="S50C", amount=1000,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
        ]
        tax = TaxResult.calculate(items, Decimal("0.17"))
        assert tax.subtotal_excluding_tax == Decimal("1000.00")
        assert tax.tax_amount == Decimal("170.00")
        assert tax.total_including_tax == Decimal("1170.00")

    def test_unknown_excluded_from_base(self):
        items = [
            QuoteItem(line_id="M1", category="material", name="S50C", amount=1000,
                      source=PriceSource.C, confidence=QuoteConfidence.HIGH),
            QuoteItem(line_id="U1", category="process", name="Magic", amount=0,
                      source=PriceSource.U, confidence=QuoteConfidence.UNCERTAIN),
        ]
        tax = TaxResult.calculate(items, Decimal("0.17"))
        assert tax.subtotal_excluding_tax == Decimal("1000.00")

    def test_empty_items(self):
        tax = TaxResult.calculate([], Decimal("0.17"))
        assert tax.subtotal_excluding_tax == Decimal("0.00")
        assert tax.total_including_tax == Decimal("0.00")


class TestQuotationService:
    def test_service_initialization(self):
        svc = QuotationApplicationService()
        assert svc is not None

    def test_j003_demo_pipeline(self):
        svc = QuotationApplicationService()
        import ezdxf
        from pathlib import Path

        # Create a simple DXF like J003
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_line((0, 0), (928, 0))
        msp.add_line((928, 0), (928, 796))
        msp.add_line((928, 796), (0, 796))
        msp.add_line((0, 796), (0, 0))
        for i in range(4):
            msp.add_circle((200 + i * 150, 398), radius=3)
        msp.add_text("S50C", height=8).set_placement((10, 810))
        msp.add_text("6-M6", height=5).set_placement((200, 400))
        msp.add_text("表面鍍鉻", height=5).set_placement((10, 820))

        tmp = Path("demo_test_J003.dxf")
        doc.saveas(str(tmp))

        try:
            result = svc.quote_single_file(tmp)
            assert result.status in (JobStatus.COMPLETE, JobStatus.REVIEW_REQUIRED)
            assert result.quote is not None
            assert result.quote.part_number == "demo-test-j003"  # normalized
            assert result.tax is not None
        finally:
            tmp.unlink(missing_ok=True)

    def test_unsupported_format(self, tmp_path):
        txt = tmp_path / "test.txt"
        txt.write_text("hello")
        svc = QuotationApplicationService()
        result = svc.quote_single_file(txt)
        assert result.status == JobStatus.UNSUPPORTED
        assert result.errors == ["找不到可用的 DWG、DXF 或 SolidWorks 图纸"]

    def test_pdf_is_unsupported(self, tmp_path):
        pdf = tmp_path / "drawing.pdf"
        pdf.write_bytes(b"%PDF-test")
        result = QuotationApplicationService().quote_single_file(pdf)
        assert result.status == JobStatus.UNSUPPORTED
        assert result.quote is None

    def test_a023_uses_explicit_stock_dimensions_for_material_weight(self, tmp_path):
        import ezdxf

        path = tmp_path / "UC1000006481-A023.dxf"
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        model = doc.modelspace()
        # Simulate a drawing sheet/projection extent much larger than the part.
        model.add_lwpolyline([(0, 0), (375, 0), (375, 239), (0, 239)], close=True)
        model.add_text("50*28*17", height=4).set_placement((10, 220))
        model.add_text("S50C", height=4).set_placement((10, 210))
        doc.saveas(path)

        result = QuotationApplicationService().quote_single_file(path)

        assert result.quote is not None
        material = next(item for item in result.quote.items if item.category == "material")
        assert material.quantity == 0.18683
        assert result.feature_summary["material_dimensions"] == "50*28*17"
        assert result.feature_summary["weight_resolution"] == "CONFIRMED_PART_DIMENSION"

    def test_batch_processing(self):
        """Batch processes multiple bundles."""
        svc = QuotationApplicationService()
        import ezdxf
        from pathlib import Path

        # Create two simple DXF files
        paths = []
        for name, texts in [("BATCH-A", [("S50C", 10, 810, 8)]),
                            ("BATCH-B", [("SUS304", 10, 810, 8)])]:
            doc = ezdxf.new()
            doc.header["$INSUNITS"] = 4
            msp = doc.modelspace()
            msp.add_line((0, 0), (100, 0))
            msp.add_line((100, 0), (100, 50))
            msp.add_line((100, 50), (0, 50))
            msp.add_line((0, 50), (0, 0))
            for content, x, y, h in texts:
                msp.add_text(content, height=h).set_placement((x, y))
            p = Path(f"demo_test_{name}.dxf")
            doc.saveas(str(p))
            paths.append(p)

        try:
            from quotation.application.file_scanner import DrawingFile
            bundles = []
            for p in paths:
                df = DrawingFile.from_path(p)
                if df:
                    bundles.append(__import__('quotation.application.file_scanner', fromlist=['JobBundle']).JobBundle(
                        drawing_number=df.drawing_number, files=[df],
                        match_status=__import__('quotation.application.file_scanner', fromlist=['MatchStatus']).MatchStatus.UNMATCHED,
                    ))
            results = svc.quote_batch(bundles)
            assert len(results) == 2
            for r in results:
                assert r.status in (JobStatus.COMPLETE, JobStatus.REVIEW_REQUIRED)
        finally:
            for p in paths:
                p.unlink(missing_ok=True)

    def test_sheet_metal_without_holes_has_no_cnc_item(self, tmp_path):
        import ezdxf

        path = tmp_path / "J029.dxf"
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (80, 0), (80, 90), (0, 90)], close=True)
        msp.add_text("SUS304 鈑金", height=4).set_placement((5, 95))
        doc.saveas(path)

        result = QuotationApplicationService().quote_single_file(path)

        assert result.quote is not None
        assert result.feature_summary["quotation_route"] == "SHEET_METAL"
        assert not any(
            item.category == "process" and "CNC" in item.name
            for item in result.quote.items
        )

    def test_generic_stainless_with_inline_thickness_is_priced(self, tmp_path):
        import ezdxf

        path = tmp_path / "J029-inline-note.dxf"
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        model = doc.modelspace()
        model.add_lwpolyline([(0, 0), (100, 0), (100, 80), (0, 80)], close=True)
        model.add_text("4.材質為3mm厚度不鏽鋼；", height=4).set_placement((5, 90))
        doc.saveas(path)

        result = QuotationApplicationService().quote_single_file(path)

        assert result.quote is not None
        assert result.quote.material == "SUS304"
        material = next(item for item in result.quote.items if item.category == "material")
        assert material.source != PriceSource.U
        assert material.unit_price > 0
        assert "thickness_mm=3.0" in (material.evidence or "")

    def test_unresolved_weldment_weight_requires_review(self, tmp_path):
        import ezdxf

        path = tmp_path / "J001.dxf"
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (1400, 0), (1400, 1300), (0, 1300)], close=True)
        msp.add_text("普通鋼", height=5).set_placement((5, 1320))
        msp.add_text("機架", height=5).set_placement((5, 1340))
        msp.add_text("焊接", height=5).set_placement((5, 1360))
        doc.saveas(path)

        result = QuotationApplicationService().quote_single_file(path)

        assert result.status == JobStatus.REVIEW_REQUIRED
        assert result.unknown_item_count >= 1
        assert result.feature_summary["weight"] == "-"
        assert result.feature_summary["weight_resolution"] == "UNRESOLVED_WELDMENT_STRUCTURE"
        assert result.quote is not None
        material_item = next(item for item in result.quote.items if item.category == "material")
        assert material_item.source == PriceSource.U
        assert "BBOX" not in (material_item.evidence or "")
        welding_item = next(item for item in result.quote.items if "焊接加工" in item.name)
        assert welding_item.source == PriceSource.U
        assert welding_item.quantity == 1
        assert welding_item.unit == "项"


# ============================================================================
# W001 regression: unknown items preserved
# ============================================================================

class TestW001UnknownPreservation:
    def test_w001_acrylic_unknown_preserved(self):
        """White acrylic item must be preserved as source=U, not lost or set to 0."""
        import ezdxf
        from pathlib import Path
        from quotation.application.quotation_service import QuotationApplicationService

        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        msp.add_line((0, 0), (1300, 0))
        msp.add_line((1300, 0), (1300, 1300))
        msp.add_line((1300, 1300), (0, 1300))
        msp.add_line((0, 1300), (0, 0))
        texts = [("鋁型材 40x40", 10, 1320, 6), ("防護圍欄", 10, 1340, 6),
                 ("門組件", 10, 1360, 5), ("白色透明亞克力", 10, 1380, 4),
                 ("合頁", 10, 1400, 4), ("角碼", 10, 1460, 4)]
        for c, x, y, h in texts:
            msp.add_text(c, height=h).set_placement((x, y))
        tmp = Path("_test_w001.dxf")
        doc.saveas(str(tmp))

        try:
            svc = QuotationApplicationService()
            result = svc.quote_single_file(tmp)

            assert result.quote is not None
            # Must have unknown items
            assert result.unknown_item_count >= 1
            # Must NOT be COMPLETE
            assert result.status != "COMPLETE"
            # Must have cost_completion < 100%
            assert result.cost_completion < 100.0
        finally:
            tmp.unlink(missing_ok=True)

    def test_ai_estimate_is_included_and_forces_review(self):
        """A valid AI estimate contributes to totals but cannot look approved."""
        from quotation.application.quotation_service import QuotationApplicationService
        from quotation.infrastructure.ai.deepseek_client import DeepSeekClient
        from unittest.mock import MagicMock

        mock_client = MagicMock(spec=DeepSeekClient)
        mock_client.extract_features.return_value = {
            "material_candidate": "S50C",
            "confidence": 0.8,
            "missing_fields": [],
            "surface_treatment_candidate": None,
            "heat_treatment_candidate": None,
            "thickness_candidate": None,
            "warnings": [],
        }
        mock_client.estimate_unknown_costs.side_effect = lambda **kwargs: [{
            "line_id": kwargs["items"][0]["line_id"],
            "unit_price": 100.0,
            "quantity": 1.0,
            "unit": "项",
            "amount": 100.0,
            "reason": "同类结构参考，仅供人工确认",
            "confidence": 0.4,
        }]

        svc = QuotationApplicationService(ai_client=mock_client)
        import ezdxf
        from pathlib import Path
        doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        msp.add_line((0, 0), (1300, 0)); msp.add_line((1300, 0), (1300, 1300))
        msp.add_line((1300, 1300), (0, 1300)); msp.add_line((0, 1300), (0, 0))
        texts = [("鋁型材 40x40", 10, 1320, 6), ("白色透明亞克力", 10, 1380, 4)]
        for c, x, y, h in texts:
            msp.add_text(c, height=h).set_placement((x, y))
        tmp = Path("_test_ai_w001.dxf")
        doc.saveas(str(tmp))

        try:
            result = svc.quote_single_file(tmp, use_ai=True)
            # AI price is included but the quote must remain review-required.
            assert result.status == "REVIEW_REQUIRED"
            # AI should be recorded as used
            assert result.ai_used is True
            estimated = [
                item for item in result.quote.items
                if item.ai_estimated_amount is not None
            ]
            assert estimated
            assert estimated[0].source == PriceSource.AI
            assert estimated[0].ai_estimated_amount == 100.0
            assert estimated[0].unit_price == 100.0
            assert estimated[0].amount == 100.0
            assert "已计入" in (estimated[0].note or "")
            assert result.tax is not None
            assert float(result.tax.subtotal_excluding_tax) == result.quote.total
            assert result.quote.quotation_status == "REVIEW_REQUIRED"
            payload = result._item_to_dict(estimated[0])
            assert payload["price_status"] == "AI_REFERENCE"
            assert payload["requires_review"] is True
            assert payload["included_in_quotation"] is True
            assert payload["ai_reference"]["estimated_amount"] == 100.0
        finally:
            tmp.unlink(missing_ok=True)
