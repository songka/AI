"""CAD Feature Validation — compare extracted features vs expected golden data."""

from __future__ import annotations

import json
from pathlib import Path

import ezdxf
import pytest

from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.parser.dimension_parser import parse_dimension

EXPECTED_DIR = Path(__file__).parent / "expected"

GOLDEN_PARTS = [
    ("UC1000005854", "S50C", "928*796*15", "表面鍍鉻", 4, "M6"),
    ("UC1000005855", "S50C", "1400*250*15", "熱處理", 2, None),
    ("UC1000005856", "S50C", "798*530*15", "熱處理", 4, "M8"),
    ("UC1000005857", "S50C", "1400*250*15", "熱處理", 2, "M8"),
    ("UC1002006858", "A6061-T6", "92*20*92", "表面噴砂陽極銀色", 2, None),
    ("UC1002009711", "A6061-T6", "φ250×15", "表面噴砂陽極銀色", 4, None),
    ("UC1002009712", "A6061-T6", "60*70*20", "表面噴砂陽極銀色", 2, None),
    ("UC1002009713", "A6061-T6", "60*30*10", "表面噴砂陽極銀色", 2, None),
    ("UC1002009718", "A6061-T6", "40*16*13", "表面噴砂陽極銀色", 1, None),
    ("UC1003000436", "普通鋼", "1400*1300*785", "表面噴塗,RAL9003", 8, "M8"),
    ("UC1004001529", "SPCC", "56*50*44", "表面噴塗,RAL9003", 0, None),
    ("UC1004001886", "SPCC", "1208*103.5*2", "表面噴塗,RAL9003", 4, None),
    ("UC1004001887", "SPCC", "794*200*15", "表面噴塗,RAL9003", 2, None),
    ("UC1004001888", "SPCC", "798*50*15", "表面噴塗,RAL9003", 2, None),
    ("UC1004001889", "SPCC", "1300*117.2*2", "表面噴塗,RAL9003", 2, "M6"),
    ("UC1004001890", "SPCC", "1300*117.2*88", "表面噴塗,RAL9003", 4, "M8"),
    ("UC1004001904", "SPCC", "818*200*21", "表面噴塗,RAL9003", 4, "M6"),
    ("UC1004001905", "SPCC", "818*200*21", "表面噴塗,RAL9003", 4, "M6"),
    ("UC1007000773", "SUS304", "80*90*2", None, 0, None),
    ("UC2020083221", "鋁型材", "40*40", "白色透明", 0, None),
]


def _gen_dxf(tmp_path, item, material, dims_raw, surface, min_holes, thread):
    dim_result = parse_dimension(dims_raw)
    length = dim_result.length or 100
    width = dim_result.width or length or 50
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    msp.add_line((0, 0), (length, 0))
    msp.add_line((length, 0), (length, width))
    msp.add_line((length, width), (0, width))
    msp.add_line((0, width), (0, 0))
    if min_holes > 0:
        spacing = length / (min_holes + 1)
        for i in range(min_holes):
            msp.add_circle((spacing * (i + 1), width / 2), radius=1.5)
    pad = 5.0
    if material:
        msp.add_text(material, height=5.0).set_placement((pad, width + pad))
    if surface:
        msp.add_text(surface, height=4.0).set_placement((pad, width + pad + 10))
    if thread and min_holes > 0:
        cx = length / (min_holes + 1)
        msp.add_text(thread, height=4.0).set_placement((cx, width / 2 + 8))
    path = tmp_path / f"{item}.dxf"
    doc.saveas(str(path))
    return path


@pytest.fixture(scope="module")
def cad_results(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cad_val")
    geo_ext = GeometricExtractor()
    mfg_ext = ManufacturingExtractor()
    reader = DxfReader()
    results = []
    for item, material, dims, surface, min_holes, thread in GOLDEN_PARTS:
        dxf_path = _gen_dxf(tmp, item, material, dims, surface, min_holes, thread)
        ir = reader.read(dxf_path)
        geo = geo_ext.extract(ir.drawing.raw_entities)
        mfg = mfg_ext.extract(geo)
        exp_path = EXPECTED_DIR / f"{item}.json"
        expected = json.loads(exp_path.read_text(encoding="utf-8")) if exp_path.exists() else {}
        results.append({"item": item, "material": material, "dims": dims, "surface": surface,
                        "geo": geo, "mfg": mfg, "expected": expected})
    return results


class TestCadFeatureValidation:
    def test_all_bbox_present(self, cad_results):
        failures = [r["item"] for r in cad_results if r["geo"].bounding_box is None]
        assert len(failures) == 0, f"Missing: {failures}"

    def test_bbox_length(self, cad_results):
        failures = []
        for r in cad_results:
            b = r["geo"].bounding_box
            e = r["expected"].get("bounding_box", {})
            if b and e.get("length_min") and not (e["length_min"] <= b.length <= e["length_max"]):
                failures.append(f"{r['item']}: L={b.length:.0f}")
        assert len(failures) == 0, f"Length: {failures}"

    def test_bbox_width(self, cad_results):
        failures = []
        for r in cad_results:
            b = r["geo"].bounding_box
            e = r["expected"].get("bounding_box", {})
            if b and e.get("width_min") and not (e["width_min"] <= b.width <= e["width_max"]):
                failures.append(f"{r['item']}: W={b.width:.0f}")
        assert len(failures) == 0, f"Width: {failures}"

    def test_material(self, cad_results):
        failures = []
        for r in cad_results:
            em = r["expected"].get("material", {})
            if em.get("text_contains"):
                if r["mfg"].material is None:
                    failures.append(f"{r['item']}: not found")
                else:
                    raw = r["mfg"].material.raw_text.value or ""
                    if not any(kw in raw for kw in em["text_contains"]):
                        failures.append(f"{r['item']}: '{raw}' missing {em['text_contains']}")
        assert len(failures) == 0, f"Material: {failures}"

    def test_material_source(self, cad_results):
        for r in cad_results:
            if r["mfg"].material:
                assert r["mfg"].material.raw_text.source == "DRAWING_TEXT"

    def test_surface(self, cad_results):
        failures = []
        for r in cad_results:
            if r["expected"].get("surface_treatment", {}).get("present"):
                if r["mfg"].surface_treatment is None:
                    failures.append(r["item"])
        assert len(failures) == 0, f"Surface: {failures}"

    def test_holes(self, cad_results):
        failures = []
        for r in cad_results:
            exp_min = r["expected"].get("holes", {}).get("count_min", 0)
            actual = r["mfg"].total_holes
            if actual < exp_min:
                failures.append(f"{r['item']}: holes={actual} < {exp_min}")
        assert len(failures) == 0, f"Holes: {failures}"

    def test_threads(self, cad_results):
        failures = []
        for r in cad_results:
            et = r["expected"].get("threads", {})
            if et.get("present"):
                if len(r["mfg"].threads) == 0:
                    failures.append(f"{r['item']}: not found")
                elif et.get("spec_contains"):
                    if not any(et["spec_contains"] in (t.spec.value or "") for t in r["mfg"].threads):
                        failures.append(f"{r['item']}: spec mismatch")
        assert len(failures) == 0, f"Threads: {failures}"

    def test_confidence(self, cad_results):
        for r in cad_results:
            for h in r["mfg"].holes:
                assert h.confidence > 0
                assert h.diameter.confidence > 0
            for t in r["mfg"].threads:
                assert t.confidence > 0
                assert t.spec.confidence > 0

    def test_pass_rate(self, cad_results):
        passed = 0
        for r in cad_results:
            ok = True
            e = r["expected"]
            if r["geo"].bounding_box is None:
                ok = False
            if e.get("material", {}).get("text_contains") and r["mfg"].material is None:
                ok = False
            if e.get("holes", {}).get("count_min", 0) > 0 and r["mfg"].total_holes == 0:
                ok = False
            if e.get("threads", {}).get("present") and len(r["mfg"].threads) == 0:
                ok = False
            if ok:
                passed += 1
        rate = passed / len(cad_results) * 100
        assert rate >= 95, f"Pass rate {rate:.0f}%"
