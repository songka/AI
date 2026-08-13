"""Generate the Golden Dataset JSON for regression tests."""

from __future__ import annotations

import json
from pathlib import Path

parts = [
    {"dwg_file":"UC1000005854-J003.DWG","bom_item":"UC1000005854","material":"S50C","part_code":"J003","dimensions_raw":"928*796*15","dimensions_parsed":{"length":928,"width":796,"height":15},"surface_treatment":"表面鍍鉻","historical_price":1425.0,"price_source":"BOM","source_bom_row":53,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1000005855-J005.DWG","bom_item":"UC1000005855","material":"S50C","part_code":"J005","dimensions_raw":"1400*250*15","dimensions_parsed":{"length":1400,"width":250,"height":15},"surface_treatment":"熱處理","historical_price":712.0,"price_source":"BOM","source_bom_row":54,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1000005856-J006.DWG","bom_item":"UC1000005856","material":"S50C","part_code":"J006","dimensions_raw":"798*530*15","dimensions_parsed":{"length":798,"width":530,"height":15},"surface_treatment":"熱處理","historical_price":874.0,"price_source":"BOM","source_bom_row":55,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1000005857-J007.DWG","bom_item":"UC1000005857","material":"S50C","part_code":"J007","dimensions_raw":"1400*250*15","dimensions_parsed":{"length":1400,"width":250,"height":15},"surface_treatment":"熱處理","historical_price":693.0,"price_source":"BOM","source_bom_row":56,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1002006858_J026.DWG","bom_item":"UC1002006858","material":"A6061-T6","part_code":"J026","dimensions_raw":"92*20*92","dimensions_parsed":{"length":92,"width":20,"height":92},"surface_treatment":"表面噴砂陽極銀色","historical_price":71.0,"price_source":"BOM","source_bom_row":60,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1002009711-R001.DWG","bom_item":"UC1002009711","material":"A6061-T6","part_code":"R001","dimensions_raw":"φ250×15","dimensions_parsed":{"length":250,"width":None,"height":15},"surface_treatment":"表面噴砂陽極銀色","historical_price":209.0,"price_source":"BOM","source_bom_row":70,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1002009712-R002.DWG","bom_item":"UC1002009712","material":"A6061-T6","part_code":"R002","dimensions_raw":"60*70*20","dimensions_parsed":{"length":60,"width":70,"height":20},"surface_treatment":"表面噴砂陽極銀色","historical_price":61.0,"price_source":"BOM","source_bom_row":71,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1002009713-R003.DWG","bom_item":"UC1002009713","material":"A6061-T6","part_code":"R003","dimensions_raw":"60*30*10","dimensions_parsed":{"length":60,"width":30,"height":10},"surface_treatment":"表面噴砂陽極銀色","historical_price":38.0,"price_source":"BOM","source_bom_row":72,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1002009718-R004.DWG","bom_item":"UC1002009718","material":"A6061-T6","part_code":"R004","dimensions_raw":"40*16*13","dimensions_parsed":{"length":40,"width":16,"height":13},"surface_treatment":"表面噴砂陽極銀色","historical_price":66.0,"price_source":"BOM","source_bom_row":73,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1003000436_J001.DWG","bom_item":"UC1003000436","material":"普通鋼","part_code":"J001","dimensions_raw":"1400*1300*785","dimensions_parsed":{"length":1400,"width":1300,"height":785},"surface_treatment":"表面噴塗,RAL9003","historical_price":7000.0,"price_source":"BOM","source_bom_row":80,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001529_W002.DWG","bom_item":"UC1004001529","material":"SPCC","part_code":"W002","dimensions_raw":"56*50*44","dimensions_parsed":{"length":56,"width":50,"height":44},"surface_treatment":"表面噴塗,RAL9003","historical_price":16.0,"price_source":"BOM","source_bom_row":90,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001886-J036.stp.DWG","bom_item":"UC1004001886","material":"SPCC","part_code":"J036","dimensions_raw":"1208*103.5*2","dimensions_parsed":{"length":1208,"width":103.5,"height":2},"surface_treatment":"表面噴塗,RAL9003","historical_price":28.0,"price_source":"BOM","source_bom_row":95,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001887-F002.DWG","bom_item":"UC1004001887","material":"SPCC","part_code":"F002","dimensions_raw":"794*200*15","dimensions_parsed":{"length":794,"width":200,"height":15},"surface_treatment":"表面噴塗,RAL9003","historical_price":38.0,"price_source":"BOM","source_bom_row":100,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001888-J050.DWG","bom_item":"UC1004001888","material":"SPCC","part_code":"J050","dimensions_raw":"798*50*15","dimensions_parsed":{"length":798,"width":50,"height":15},"surface_treatment":"表面噴塗,RAL9003","historical_price":47.0,"price_source":"BOM","source_bom_row":105,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001889_J027.DWG","bom_item":"UC1004001889","material":"SPCC","part_code":"J027","dimensions_raw":"1300*117.2*2","dimensions_parsed":{"length":1300,"width":117.2,"height":2},"surface_treatment":"表面噴塗,RAL9003","historical_price":38.0,"price_source":"BOM","source_bom_row":110,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001890-J035.DWG","bom_item":"UC1004001890","material":"SPCC","part_code":"J035","dimensions_raw":"1300*117.2*88","dimensions_parsed":{"length":1300,"width":117.2,"height":88},"surface_treatment":"表面噴塗,RAL9003","historical_price":95.0,"price_source":"BOM","source_bom_row":115,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001904-F003.DWG","bom_item":"UC1004001904","material":"SPCC","part_code":"F003","dimensions_raw":"818*200*21","dimensions_parsed":{"length":818,"width":200,"height":21},"surface_treatment":"表面噴塗,RAL9003","historical_price":57.0,"price_source":"BOM","source_bom_row":120,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1004001905-F001.DWG","bom_item":"UC1004001905","material":"SPCC","part_code":"F001","dimensions_raw":"818*200*21","dimensions_parsed":{"length":818,"width":200,"height":21},"surface_treatment":"表面噴塗,RAL9003","historical_price":57.0,"price_source":"BOM","source_bom_row":125,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC1007000773_J029.DWG","bom_item":"UC1007000773","material":"SUS304","part_code":"J029","dimensions_raw":"80*90*2","dimensions_parsed":{"length":80,"width":90,"height":2},"surface_treatment":None,"historical_price":14.0,"price_source":"BOM","source_bom_row":130,"project_name":"GCS","match_level":"L1","sub_type":"加工件"},
    {"dwg_file":"UC2020083221-W001.DWG","bom_item":"UC2020083221","material":"鋁型材","part_code":None,"dimensions_raw":"40*40","dimensions_parsed":{"length":40,"width":40,"height":None},"surface_treatment":"白色透明","historical_price":2900.0,"price_source":"BOM","source_bom_row":167,"project_name":"GCS","match_level":"L1","sub_type":"機構外購件"},
]

dataset = {
    "version": "1.0",
    "created_at": "2026-08-01",
    "source_bom": "GCS-雙滑台打磨設備-BOM.xlsx",
    "total_parts": 20,
    "materials": ["S50C", "A6061-T6", "普通鋼", "SPCC", "SUS304", "鋁型材"],
    "parts": parts,
}

out = Path("tests/regression/golden_dataset.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)
print(f"Golden Dataset saved: {out} ({len(parts)} parts)")
