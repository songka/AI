import argparse
import csv
from collections import defaultdict

REQUIRED = ["station", "device", "signal_type", "address", "tag", "description"]


def main():
    parser = argparse.ArgumentParser(description="Check a CSV IO table for basic quality issues.")
    parser.add_argument("csv_path")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    fields = rows[0].keys() if rows else []
    missing_columns = [c for c in REQUIRED if c not in fields]
    findings = []

    for col in missing_columns:
        findings.append(("missing_column", col, "Required column is absent."))

    address_map = defaultdict(list)
    tag_map = defaultdict(list)
    for index, row in enumerate(rows, start=2):
        for col in REQUIRED:
            if col in row and not str(row.get(col, "")).strip():
                findings.append(("missing_field", f"row {index}:{col}", "Required field is blank."))
        address = str(row.get("address", "")).strip()
        tag = str(row.get("tag", "")).strip()
        if address:
            address_map[address].append(index)
        if tag:
            tag_map[tag].append(index)

    for address, line_numbers in address_map.items():
        if len(line_numbers) > 1:
            findings.append(("duplicate_address", address, f"Rows {line_numbers} share the same address."))

    for tag, line_numbers in tag_map.items():
        if len(line_numbers) > 1:
            findings.append(("duplicate_tag", tag, f"Rows {line_numbers} share the same tag."))

    print("issue_type,evidence,note")
    for item in findings:
        print(",".join(f'"{str(part).replace(chr(34), chr(34)+chr(34))}"' for part in item))


if __name__ == "__main__":
    main()
