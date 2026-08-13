"""JSON serialization tests for all domain models.

Verifies that every domain model can be:
1. Serialized to JSON string (model_dump_json)
2. Serialized to Python dict (model_dump)
3. Deserialized from JSON string (model_validate_json)
4. Deserialized from Python dict (model_validate)
5. Round-trip preserves all data
"""

from __future__ import annotations

import json

import pytest

from quotation.domain.bom import BomEntry, BomSheet, ParsedPart
from quotation.domain.drawing import Drawing, DrawingFormat, ParseStatus, TextEntity
from quotation.domain.feature import (
    BoundingBox,
    Feature,
    FeatureSource,
    Hole,
)
from quotation.domain.issue import Issue, IssueReport, IssueSeverity, IssueStatus
from quotation.domain.material import MaterialProperties
from quotation.domain.quote import PriceSource, Quote, QuoteConfidence, QuoteItem
from quotation.domain.rule import (
    MaterialRule,
    MaterialStatus,
    ProcessRule,
    RuleSet,
    SurfacePricingMode,
    SurfaceRule,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _roundtrip(model_instance):
    """Generic round-trip test: model → json → model."""
    json_str = model_instance.model_dump_json()
    model_cls = type(model_instance)
    restored = model_cls.model_validate_json(json_str)
    # Compare dict representations (JSON-safe)
    assert model_instance.model_dump() == restored.model_dump()
    return restored


# ---------------------------------------------------------------------------
# Drawing serialization
# ---------------------------------------------------------------------------

class TestDrawingSerialization:
    @pytest.fixture
    def drawing(self):
        return Drawing(
            id="dwg-001",
            file_path="/path/to/UC1000005854-J003.DWG",
            file_name="UC1000005854-J003.DWG",
            source_format=DrawingFormat.DWG,
            drawing_number="UC1000005854",
            part_name="J003",
            revision="A",
            material_text="S50C",
            entity_count=269,
            entity_summary={"LINE": 245, "CIRCLE": 12},
            all_texts=[
                TextEntity(content="S50C", position_x=100.0, position_y=50.0, height=5.0)
            ],
            parse_status=ParseStatus.SUCCESS,
        )

    def test_to_json(self, drawing):
        data = drawing.model_dump()
        assert data["id"] == "dwg-001"
        assert data["source_format"] == "DWG"
        assert data["drawing_number"] == "UC1000005854"

    def test_from_json(self, drawing):
        json_str = drawing.model_dump_json()
        restored = Drawing.model_validate_json(json_str)
        assert restored.id == drawing.id
        assert restored.entity_count == 269

    def test_roundtrip(self, drawing):
        _roundtrip(drawing)

    def test_enum_serialization(self, drawing):
        """Enums must serialize as their string values, not object refs."""
        data = drawing.model_dump()
        assert data["source_format"] == "DWG"
        assert data["parse_status"] == "success"
        assert isinstance(data["source_format"], str)

    def test_text_entity_serialization(self):
        t = TextEntity(content="測試中文", position_x=0, position_y=0, height=3.0)
        data = t.model_dump()
        assert data["content"] == "測試中文"


# ---------------------------------------------------------------------------
# Feature serialization
# ---------------------------------------------------------------------------

class TestFeatureSerialization:
    @pytest.fixture
    def feature(self):
        return Feature(
            id="feat-001",
            drawing_id="dwg-001",
            bom_ref="UC1000005854",
            bounding_box=BoundingBox(min_x=0, min_y=0, max_x=928, max_y=796, max_z=15),
            overall_length=928.0,
            overall_width=796.0,
            overall_height=15.0,
            volume_mm3=11_070_720.0,
            surface_area_mm2=1_529_376.0,
            weight_kg=86.91,
            holes=[Hole(diameter=6.0, center_x=50, center_y=100, hole_type="tapped", thread_spec="M6")],
            hole_count=1,
            tapped_holes=1,
            threads=["M6"],
            contour_type="rectangular",
            material_text="S50C",
            material_normalized="S50C",
            surface_text="熱處理",
            surface_normalized="熱處理",
            tolerances=["平面度 0.05"],
            feature_source=FeatureSource.BOTH,
        )

    def test_to_json(self, feature):
        data = feature.model_dump()
        assert data["overall_length"] == 928.0
        assert data["material_normalized"] == "S50C"
        assert len(data["holes"]) == 1
        assert data["holes"][0]["diameter"] == 6.0

    def test_roundtrip(self, feature):
        restored = _roundtrip(feature)
        assert restored.weight_kg == 86.91
        assert restored.holes[0].thread_spec == "M6"

    def test_nested_objects_serialize(self, feature):
        data = feature.model_dump()
        assert "bounding_box" in data
        assert data["bounding_box"]["min_x"] == 0
        assert isinstance(data["bounding_box"], dict)

    def test_empty_lists(self):
        f = Feature(id="feat-empty", drawing_id="dwg-empty")
        data = f.model_dump()
        assert data["holes"] == []
        assert data["tolerances"] == []


# ---------------------------------------------------------------------------
# BOM serialization
# ---------------------------------------------------------------------------

class TestBomSerialization:
    def test_bom_entry_roundtrip(self):
        e = BomEntry(
            item="UC1000005854",
            description="原物料;加工件;S50C;J003;928*796*15;熱處理",
            level=2,
            unit_cost=1425.0,
            extended_cost=1425.0,
        )
        restored = _roundtrip(e)
        assert restored.unit_cost == 1425.0

    def test_parsed_part_roundtrip(self):
        p = ParsedPart(
            bom_item="UC1000005854",
            material="S50C",
            part_code="J003",
            dimensions_raw="928*796*15",
            surface_treatment="熱處理",
            drawing_ref="UC1000005854-J003.DWG",
        )
        restored = _roundtrip(p)
        assert restored.dimensions_raw == "928*796*15"

    def test_bom_sheet_roundtrip(self):
        sheet = BomSheet(
            source_file="BOM.xlsx",
            total_rows=2,
            project_name="GCS-雙滑台打磨設備",
            entries=[
                BomEntry(item="UC01", description="test1", unit_cost=100.0),
                BomEntry(item="UC02", description="test2", unit_cost=200.0),
            ],
            parsed_parts=[
                ParsedPart(bom_item="UC01", material="S50C"),
            ],
        )
        restored = _roundtrip(sheet)
        assert len(restored.entries) == 2
        assert restored.project_name == "GCS-雙滑台打磨設備"

    # -- New tests (Phase 2.0.1) —

    def test_bom_entry_source_tracking(self):
        """Round-trip preserves source_file, source_sheet, source_row."""
        e = BomEntry(
            item="UC1000005854",
            description="test",
            source_file="GCS-BOM.xlsx",
            source_sheet="工作表1",
            source_row=158,
        )
        restored = _roundtrip(e)
        assert restored.source_file == "GCS-BOM.xlsx"
        assert restored.source_sheet == "工作表1"
        assert restored.source_row == 158

    def test_parsed_part_all_fields(self):
        """Round-trip with all new ParsedPart fields."""
        p = ParsedPart(
            bom_item="UC1000005854",
            source_row=158,
            category="原材料",
            sub_type="加工件",
            material="S50C",
            part_code="J003",
            dimensions_raw="928*796*15",
            surface_treatment="熱處理",
            model_number=None,
            brand=None,
            spec=None,
            unit_cost=1425.0,
            quotation_source="BOM",
            is_quotable=True,
            is_matched=True,
            drawing_ref="UC1000005854-J003.DWG",
        )
        restored = _roundtrip(p)
        assert restored.category == "原材料"
        assert restored.sub_type == "加工件"
        assert restored.is_quotable is True
        assert restored.is_matched is True
        assert restored.quotation_source == "BOM"

    def test_bom_sheet_classification(self):
        """Round-trip preserves classification counts and matched_parts."""
        matched = [
            ParsedPart(
                bom_item="UC1000005854",
                sub_type="加工件",
                material="S50C",
                is_matched=True,
                drawing_ref="UC1000005854-J003.DWG",
            ),
        ]
        sheet = BomSheet(
            source_file="BOM.xlsx",
            total_rows=3,
            machined_count=82,
            electrical_count=140,
            mechanical_count=66,
            subassembly_count=28,
            matched_parts=matched,
            matched_drawings=1,
            unmatched_drawings=9,
        )
        restored = _roundtrip(sheet)
        assert restored.machined_count == 82
        assert restored.electrical_count == 140
        assert restored.mechanical_count == 66
        assert restored.subassembly_count == 28
        assert len(restored.matched_parts) == 1
        assert restored.matched_parts[0].is_matched is True


# ---------------------------------------------------------------------------
# Material serialization
# ---------------------------------------------------------------------------

class TestMaterialSerialization:
    def test_roundtrip(self):
        m = MaterialProperties(
            name="A6061-T6",
            density=2.70,
            category="鋁合金",
            grade="6061-T6",
            note="時效硬化鋁合金",
        )
        restored = _roundtrip(m)
        assert restored.density == 2.70
        assert restored.category == "鋁合金"


# ---------------------------------------------------------------------------
# Rule serialization
# ---------------------------------------------------------------------------

class TestRuleSerialization:
    def test_rule_set_roundtrip(self):
        rs = RuleSet(
            version="1.1",
            source="3.0報價表-R01",
            materials=[
                MaterialRule(
                    material_id="MAT_A6061",
                    material_name="A6061-T6",
                    aliases=["6061"],
                    unit_price=38.0,
                ),
                MaterialRule(
                    material_id="MAT_SPCC",
                    material_name="SPCC",
                    unit_price=0,
                    status=MaterialStatus.PENDING,
                    note="待確認",
                ),
            ],
            processes=[
                ProcessRule(process_id="PROC_CNC", process_name="CNC", rate=80.0),
            ],
            surfaces=[
                SurfaceRule(
                    surface_id="SURF_ANODIZE",
                    surface_name="陽極氧化",
                    pricing_mode=SurfacePricingMode.BY_AREA,
                    unit_price=0.15,
                    unit="dm2",
                    min_charge=30.0,
                    applicable_materials=["A6061-T6"],
                ),
            ],
        )
        restored = _roundtrip(rs)
        assert restored.material_count == 2
        assert restored.process_count == 1
        assert restored.surface_count == 1
        # Verify PENDING material preserved
        pending = [m for m in restored.materials if m.status == MaterialStatus.PENDING]
        assert len(pending) == 1
        assert pending[0].material_name == "SPCC"

    def test_enum_serialization(self):
        r = SurfaceRule(
            surface_id="SURF_TEST",
            surface_name="測試",
            pricing_mode=SurfacePricingMode.BY_AREA,
            unit_price=1.0,
            unit="dm2",
            applicable_materials=["A6061-T6"],
        )
        data = r.model_dump()
        assert data["pricing_mode"] == "by_area"


# ---------------------------------------------------------------------------
# Quote serialization
# ---------------------------------------------------------------------------

class TestQuoteSerialization:
    @pytest.fixture
    def quote(self):
        return Quote(
            id="q-001",
            drawing_id="dwg-001",
            feature_id="feat-001",
            part_number="UC1000005854",
            part_name="J003",
            material="S50C",
            items=[
                QuoteItem(
                    line_id="1",
                    category="material",
                    name="S50C 材料費",
                    quantity=86.91,
                    unit="kg",
                    unit_price=9.0,
                    amount=782.19,
                    source=PriceSource.C,
                    rule_id="MAT_S50C",
                    evidence="86.91kg × 9 CNY/kg = ¥782.19",
                    confidence=QuoteConfidence.HIGH,
                ),
                QuoteItem(
                    line_id="2",
                    category="surface",
                    name="SPCC 噴塗",
                    amount=0.0,
                    source=PriceSource.U,
                    confidence=QuoteConfidence.UNCERTAIN,
                    note="價格未設定",
                ),
            ],
        )

    def test_roundtrip(self, quote):
        restored = _roundtrip(quote)
        assert restored.total == pytest.approx(782.19, rel=0.01)
        assert restored.unknown_count == 1
        assert restored.source_summary == {"C": pytest.approx(782.19, rel=0.01), "U": 0.0}

    def test_price_source_serialization(self, quote):
        data = quote.model_dump()
        assert data["items"][0]["source"] == "C"
        assert isinstance(data["items"][0]["source"], str)

    def test_empty_quote(self):
        q = Quote(id="q-empty", drawing_id="dwg-empty")
        restored = _roundtrip(q)
        assert restored.total == 0.0


# ---------------------------------------------------------------------------
# Issue serialization
# ---------------------------------------------------------------------------

class TestIssueSerialization:
    def test_roundtrip(self):
        issue = Issue(
            id="iss-001",
            drawing_id="dwg-001",
            severity=IssueSeverity.WARNING,
            category="price_uncertain",
            title="價格偏差",
            description="系統 vs BOM 偏差 >15%",
            ai_suggestion="建議檢查工時估算",
            ai_confidence=0.85,
        )
        restored = _roundtrip(issue)
        assert restored.severity == IssueSeverity.WARNING
        assert restored.ai_confidence == 0.85

    def test_issue_report_roundtrip(self):
        report = IssueReport(
            quote_id="q-001",
            issues=[
                Issue(
                    id="iss-001",
                    severity=IssueSeverity.WARNING,
                    category="test",
                    title="w",
                    description="w",
                ),
                Issue(
                    id="iss-002",
                    severity=IssueSeverity.ERROR,
                    category="test",
                    title="e",
                    description="e",
                    status=IssueStatus.RESOLVED,
                ),
            ],
        )
        restored = _roundtrip(report)
        assert restored.total_issues == 2
        assert restored.error_count == 1
        assert restored.warning_count == 1
        assert restored.resolved_count == 1


# ---------------------------------------------------------------------------
# Cross-model integration
# ---------------------------------------------------------------------------

class TestCrossModelIntegration:
    """Verify that the complete quotation pipeline data can round-trip."""

    def test_full_pipeline_json(self):
        """Simulate a complete quotation pipeline output as JSON."""
        output = {
            "drawing": Drawing(
                id="dwg-001",
                file_path="/f.dxf",
                file_name="f.dxf",
                source_format=DrawingFormat.DXF,
                drawing_number="UC1000005854",
            ).model_dump(),
            "feature": Feature(
                id="feat-001",
                drawing_id="dwg-001",
                bom_ref="UC1000005854",
                overall_length=928.0,
                overall_width=796.0,
                overall_height=15.0,
                material_normalized="S50C",
            ).model_dump(),
            "bom_match": ParsedPart(
                bom_item="UC1000005854",
                material="S50C",
                unit_cost=1425.0,
            ).model_dump(),
            "quote": Quote(
                id="q-001",
                drawing_id="dwg-001",
                items=[
                    QuoteItem(
                        line_id="1",
                        category="material",
                        name="材料費",
                        amount=782.0,
                        source=PriceSource.C,
                        confidence=QuoteConfidence.HIGH,
                    ),
                ],
            ).model_dump(),
        }

        json_str = json.dumps(output, ensure_ascii=False, indent=2)
        assert "UC1000005854" in json_str
        assert "S50C" in json_str
        assert "782.0" in json_str

        # All models can be restored from their dicts
        Drawing.model_validate(output["drawing"])
        Feature.model_validate(output["feature"])
        ParsedPart.model_validate(output["bom_match"])
        Quote.model_validate(output["quote"])
