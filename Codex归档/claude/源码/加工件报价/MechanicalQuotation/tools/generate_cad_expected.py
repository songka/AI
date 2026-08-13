"""Generate expected_feature.json files from Golden Dataset for CAD validation."""

from __future__ import annotations

import json
from pathlib import Path

GOLDEN = Path("tests/regression/golden_dataset.json")
OUT_DIR = Path("tests/regression/cad_feature/expected")

# 20 parts with expected CAD features
PARTS = [
    # (bom_item, material_text, dims_raw, surface_text, min_holes, thread_hint)
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


def generate():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for item, material, dims, surface, min_holes, thread in PARTS:
        # Parse dimensions
        from quotation.infrastructure.parser.dimension_parser import parse_dimension
        dim_result = parse_dimension(dims)
        length = dim_result.length or 0
        width = dim_result.width or 0
        height = dim_result.height or 0

        expected = {
            "bom_item": item,
            "bounding_box": {
                "length_min": length * 0.90,
                "length_max": length * 1.10,
                "width_min": (width or length) * 0.90,
                "width_max": (width or length) * 1.10,
                "height_min": height * 0.90 if height > 0 else 0,
                "height_max": height * 1.10 if height > 0 else 0,
            },
            "material": {
                "text_contains": [material] if material and material not in ("鋁型材",) else [],
                "source": "DRAWING_TEXT",
                "confidence_min": 0.5,
            },
            "surface_treatment": {
                "present": surface is not None,
                "source": "DRAWING_TEXT",
            },
            "holes": {
                "count_min": min_holes,
            },
            "threads": {
                "present": thread is not None,
                "spec_contains": thread,
            } if thread else {"present": False},
        }

        out_path = OUT_DIR / f"{item}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(expected, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(PARTS)} expected feature files in {OUT_DIR}")


if __name__ == "__main__":
    generate()
