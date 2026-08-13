"""Generate full quote validation report for 20 Golden Dataset parts."""

from __future__ import annotations

import json, uuid
from pathlib import Path
import ezdxf

from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.quote_builder import QuoteBuilder
from quotation.infrastructure.parser.dimension_parser import parse_dimension
from quotation.domain.quote import PriceSource

DENSITY = {"S50C": 7.85, "A6061-T6": 2.70, "SPCC": 7.85, "SUS304": 7.93, "SKD11": 7.85, "普通鋼": 7.85}

# 20 Golden Dataset parts
PARTS = [
    ("UC1000005854", "S50C", "J003", "928*796*15", "表面鍍鉻", 1425.0, 4, "M6"),
    ("UC1000005855", "S50C", "J005", "1400*250*15", "熱處理", 712.0, 2, None),
    ("UC1000005856", "S50C", "J006", "798*530*15", "熱處理", 874.0, 4, "M8"),
    ("UC1000005857", "S50C", "J007", "1400*250*15", "熱處理", 693.0, 2, "M8"),
    ("UC1002006858", "A6061-T6", "J026", "92*20*92", "表面噴砂陽極銀色", 71.0, 2, None),
    ("UC1002009711", "A6061-T6", "R001", "φ250x15", "表面噴砂陽極銀色", 209.0, 4, None),
    ("UC1002009712", "A6061-T6", "R002", "60*70*20", "表面噴砂陽極銀色", 61.0, 2, None),
    ("UC1002009713", "A6061-T6", "R003", "60*30*10", "表面噴砂陽極銀色", 38.0, 2, None),
    ("UC1002009718", "A6061-T6", "R004", "40*16*13", "表面噴砂陽極銀色", 66.0, 1, None),
    ("UC1003000436", "普通鋼", "J001", "1400*1300*785", "表面噴塗,RAL9003", 7000.0, 8, "M8"),
    ("UC1004001529", "SPCC", "W002", "56*50*44", "表面噴塗,RAL9003", 16.0, 0, None),
    ("UC1004001886", "SPCC", "J036", "1208*103.5*2", "表面噴塗,RAL9003", 28.0, 4, None),
    ("UC1004001887", "SPCC", "F002", "794*200*15", "表面噴塗,RAL9003", 38.0, 2, None),
    ("UC1004001888", "SPCC", "J050", "798*50*15", "表面噴塗,RAL9003", 47.0, 2, None),
    ("UC1004001889", "SPCC", "J027", "1300*117.2*2", "表面噴塗,RAL9003", 38.0, 2, "M6"),
    ("UC1004001890", "SPCC", "J035", "1300*117.2*88", "表面噴塗,RAL9003", 95.0, 4, "M8"),
    ("UC1004001904", "SPCC", "F003", "818*200*21", "表面噴塗,RAL9003", 57.0, 4, "M6"),
    ("UC1004001905", "SPCC", "F001", "818*200*21", "表面噴塗,RAL9003", 57.0, 4, "M6"),
    ("UC1007000773", "SUS304", "J029", "80*90*2", None, 14.0, 0, None),
    ("UC2020083221", "鋁型材", "W001", "40*40", "白色透明", 2900.0, 0, None),
]

def run_part(item, material, code, dims_raw, surface, hist_price, min_holes, thread):
    dims = parse_dimension(dims_raw)
    length = dims.length or 100
    width = dims.width or length or 50

    doc = ezdxf.new(); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
    msp.add_line((0, 0), (length, 0)); msp.add_line((length, 0), (length, width))
    msp.add_line((length, width), (0, width)); msp.add_line((0, width), (0, 0))
    if min_holes > 0:
        for i in range(min_holes):
            msp.add_circle((length/(min_holes+1)*(i+1), width/2), radius=3)
    msp.add_text(material, height=5).set_placement((5, width+5))
    if surface:
        msp.add_text(surface, height=4).set_placement((5, width+15))
    if thread and min_holes > 0:
        msp.add_text(f"{min_holes}-{thread}" if min_holes > 1 else thread, height=4).set_placement((length/(min_holes+1), width/2+8))
    if code and code != "W001":
        msp.add_text(code, height=3).set_placement((5, width+25))
    path = Path(f"val_{item}.dxf")
    doc.saveas(str(path))

    reader = DxfReader(); ir = reader.read(path)
    geo = GeometricExtractor().extract(ir.drawing.raw_entities)
    mfg = ManufacturingExtractor().extract(geo)
    qf = QuotationMapper().map(mfg, geo)

    # Override weight from BOM dimensions if available (golden data has thickness)
    if dims_raw and qf.machining:
        dims = parse_dimension(dims_raw)
        thickness = dims.height or 15
        material = qf.machining[0].material
        density_map = {"S50C": 7.85, "A6061-T6": 2.70, "SPCC": 7.85, "SUS304": 7.93, "SKD11": 7.85, "普通鋼": 7.85}
        density = density_map.get(material or "", 7.85)
        l = dims.length or (geo.bounding_box.length if geo.bounding_box else 100)
        w = dims.width or (geo.bounding_box.width if geo.bounding_box else 50)
        h = dims.height or thickness
        vol = l * w * h
        weight = round(vol * density / 1_000_000, 3)
        qf.machining[0].weight_kg = weight

    resolver = PricingResolver()
    items = []
    for mq in qf.machining: items.extend(resolver.resolve_machining(mq))
    for fq in qf.frames: items.extend(resolver.resolve_frame(fq))
    for aq in qf.assemblies: items.extend(resolver.resolve_assembly(aq))

    builder = QuoteBuilder()
    quote = builder.build(f"Q-{item}", f"DWG-{item}", item, code, material, items,
                          feature_confidence=mfg.material.confidence if mfg.material else None,
                          price_version=resolver.price_version)
    path.unlink(missing_ok=True)

    # Analyze issues
    issues = []
    if quote.unknown_count > 0: issues.append("C: price rule missing")
    if mfg.material is None: issues.append("B: material not detected")
    if not mfg.holes and min_holes > 0: issues.append("B: holes not detected")
    if mfg.surface_treatment is None and surface: issues.append("B: surface not detected")
    dev = (quote.total - hist_price) / hist_price * 100 if hist_price > 0 else 0
    if abs(dev) > 30: issues.append(f"A: price deviation {dev:+.0f}%")

    return {
        "item": item, "code": code, "material": material, "dims": dims_raw, "surface": surface,
        "historical_price": hist_price,
        "feature": {
            "bbox": f"{geo.bounding_box.length:.0f}x{geo.bounding_box.width:.0f}" if geo.bounding_box else "none",
            "holes_detected": mfg.total_holes, "holes_expected": min_holes,
            "material_detected": mfg.material.normalized.value if mfg.material and mfg.material.normalized.value else (mfg.material.raw_text.value if mfg.material else None),
            "surface_detected": mfg.surface_treatment.raw_text.value if mfg.surface_treatment else None,
        },
        "quote_items": [{"name": i.name, "amount": i.amount, "source": i.source.value} for i in quote.items],
        "total": quote.total, "status": quote.quotation_status,
        "unknown_count": quote.unknown_count,
        "deviation_pct": round(dev, 1),
        "issues": issues or ["OK"],
        "cost_completion": quote.source_summary.get("cost_completion", 100),
    }

# Run all
results = []
for args in PARTS:
    try:
        r = run_part(*args)
    except Exception as e:
        r = {"item": args[0], "error": str(e), "issues": ["D: pipeline error"]}
    results.append(r)
    print(f"  {args[0]}: {r.get('total', 0):.0f} CNY (hist={args[5]}) dev={r.get('deviation_pct', 0):+.1f}% {r.get('issues', [])}")

# Summary
total_ok = sum(1 for r in results if r.get("issues") == ["OK"])
total_has_unknown = sum(1 for r in results if r.get("unknown_count", 0) > 0)
avg_dev = sum(abs(r.get("deviation_pct", 0)) for r in results) / len(results)

summary = {
    "total_parts": len(results),
    "ok_parts": total_ok,
    "parts_with_unknown": total_has_unknown,
    "avg_abs_deviation": round(avg_dev, 1),
    "issue_breakdown": {},
    "parts": results,
}

for r in results:
    for issue in r.get("issues", []):
        cat = issue.split(":")[0] if ":" in issue else issue
        summary["issue_breakdown"][cat] = summary["issue_breakdown"].get(cat, 0) + 1

with open("docs/full-quote-validation-report.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"\nSummary: {total_ok}/{len(results)} OK, avg_dev={avg_dev:.1f}%, {total_has_unknown} with unknown")
print(f"Issues: {summary['issue_breakdown']}")
