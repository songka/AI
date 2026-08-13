import csv
import sys
from collections import defaultdict


def read_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    if len(sys.argv) < 2:
        print("用法：python 检查IO表.py IO表样例.csv")
        return 1

    rows = read_rows(sys.argv[1])
    problems = []
    by_address = defaultdict(list)

    for row in rows:
        by_address[row.get("地址", "").strip()].append(row)

    for address, items in by_address.items():
        if address and len(items) > 1:
            names = "、".join(item.get("中文名称", "") for item in items)
            problems.append(["高", "地址重复", address, names, "多个点位使用同一地址", "重新分配地址", "电控工程师"])

    vague_words = ["传感器1", "传感器2", "气缸1", "气缸2", "备用点", "按钮1"]
    for row in rows:
        name = row.get("中文名称", "").strip()
        address = row.get("地址", "").strip()
        note = row.get("备注", "").strip()
        if name in vague_words or len(name) <= 3:
            problems.append(["中", "名称不清楚", address, name, "名称无法表达对象和动作", "改为对象+动作+状态", "电控工程师"])
        if not note:
            problems.append(["低", "备注不足", address, name, "备注为空，后续调试不易理解", "补充用途、异常处理或预留原因", "电控工程师"])

    writer = csv.writer(sys.stdout)
    writer.writerow(["风险等级", "问题类型", "地址", "中文名称", "问题说明", "修改建议", "需要谁确认"])
    writer.writerows(problems)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
