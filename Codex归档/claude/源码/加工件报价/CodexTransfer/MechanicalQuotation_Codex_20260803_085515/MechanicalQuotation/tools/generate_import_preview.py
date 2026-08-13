"""Generate pricing import preview from Excel audit data."""

import json
from pathlib import Path

records = [
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C11R4","supplier":"通瑞","material":"A6061T6","spec":None,"price":28,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C12R4","supplier":"良伟","material":"A6061T6","spec":None,"price":35,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C15R4","supplier":"穩迪","material":"A6061T6","spec":None,"price":25,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C12R7","supplier":"良伟","material":"PC","spec":None,"price":60,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C14R11","supplier":"廣致誠","material":"SPCC","spec":"2mm","price":6.8,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C15R11","supplier":"穩迪","material":"SPCC","spec":"2mm","price":9,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C15R32","supplier":"穩迪","material":"鋁型材","spec":"30x30","price":30,"unit":"m","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C15R33","supplier":"穩迪","material":"鋁型材","spec":"40x40","price":48,"unit":"m","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"R31","supplier":None,"material":"鋁型材","spec":"20x30","price":None,"unit":"m","status":"UNKNOWN_PRICE"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C11R26","supplier":"通瑞","material":"鈹銅","spec":None,"price":180,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C12R26","supplier":"良伟","material":"鈹銅","spec":None,"price":130,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表1","source_cell":"C6R222","supplier":"INTERNAL_UNKNOWN","material":"鈹銅","spec":None,"price":220,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表1","source_cell":"C6R238","supplier":"捷密達","material":"鈹銅","spec":None,"price":170,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C12R29","supplier":"良伟","material":"亞克力","spec":None,"price":30,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表1","source_cell":"C6R228","supplier":"INTERNAL_UNKNOWN","material":"亞克力","spec":None,"price":28,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表1","source_cell":"C6R245","supplier":"捷密達","material":"亞克力","spec":None,"price":25,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C11R20","supplier":"通瑞","material":"SUJ2","spec":None,"price":25,"unit":"kg","status":"CONFLICT","conflict":"R22 also SUJ2=15 from same supplier (通瑞)"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C11R22","supplier":"通瑞","material":"SUJ2","spec":None,"price":15,"unit":"kg","status":"CONFLICT","conflict":"R20 also SUJ2=25 from same supplier (通瑞)"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表2","source_cell":"C12R30","supplier":"良伟","material":"隔熱板","spec":None,"price":650,"unit":"UNIT_CONFLICT","status":"UNIT_CONFLICT","conflict":"price=650/m2 but unit column=公斤"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表1","source_cell":"C6R226","supplier":"INTERNAL_UNKNOWN","material":"鐵","spec":None,"price":7,"unit":"kg","status":"IMPORT_READY"},
    {"source_file":"3.0報價表-R01.xlsx","source_sheet":"工作表1","source_cell":"C6R242","supplier":"捷密達","material":"鐵","spec":"S50C/S45C","price":5.5,"unit":"kg","status":"IMPORT_READY"},
]

# Summary
conflicts = [r for r in records if r["status"] == "CONFLICT"]
unit_conflicts = [r for r in records if r["status"] == "UNIT_CONFLICT"]
unknown = [r for r in records if r["status"] == "UNKNOWN_PRICE"]
ready = [r for r in records if r["status"] == "IMPORT_READY"]

output = {
    "total_records": len(records),
    "ready_to_import": len(ready),
    "conflicts": len(conflicts),
    "unit_conflicts": len(unit_conflicts),
    "unknown_prices": len(unknown),
    "records": records,
    "conflict_list": conflicts,
    "unit_conflict_list": unit_conflicts,
    "unknown_price_list": unknown,
    "suppliers_found": sorted(set(r["supplier"] for r in records if r["supplier"])),
    "materials_found": sorted(set(r["material"] for r in records if r["material"])),
}

Path("data").mkdir(exist_ok=True)
with open("data/pricing-import-preview.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"{len(records)} records -> data/pricing-import-preview.json")
print(f"  Ready: {len(ready)}, Conflicts: {len(conflicts)}, Unit conflicts: {len(unit_conflicts)}, Unknown: {len(unknown)}")
print(f"  Suppliers: {output['suppliers_found']}")
