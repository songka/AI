import argparse
import csv
from collections import defaultdict

REQUIRED = ["工位", "设备", "信号类型", "地址", "变量名", "说明"]


def quote(value):
    text = str(value).replace('"', '""')
    return f'"{text}"'


def main():
    parser = argparse.ArgumentParser(description="检查中文 IO 表中的基础质量问题。")
    parser.add_argument("csv_path")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    fields = rows[0].keys() if rows else []
    findings = []

    for col in REQUIRED:
        if col not in fields:
            findings.append(("缺少必需列", col, "IO 表缺少这个必需字段。"))

    address_map = defaultdict(list)
    name_map = defaultdict(list)

    for index, row in enumerate(rows, start=2):
        for col in REQUIRED:
            if col in row and not str(row.get(col, "")).strip():
                findings.append(("必填字段为空", f"第 {index} 行：{col}", "这个字段不能为空。"))

        address = str(row.get("地址", "")).strip()
        name = str(row.get("变量名", "")).strip()
        if address:
            address_map[address].append(index)
        if name:
            name_map[name].append(index)

    for address, line_numbers in address_map.items():
        if len(line_numbers) > 1:
            findings.append(("地址重复", address, f"第 {line_numbers} 行使用了同一个地址。"))

    for name, line_numbers in name_map.items():
        if len(line_numbers) > 1:
            findings.append(("变量名重复", name, f"第 {line_numbers} 行使用了同一个变量名。"))

    print("问题类型,证据,备注")
    for item in findings:
        print(",".join(quote(part) for part in item))


if __name__ == "__main__":
    main()
