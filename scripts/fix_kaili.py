#!/usr/bin/env python3
"""凱裡 → 凱里 (place); keep 凱莉 for clothes if intended."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

if not target.exists():
    print("missing", target)
    sys.exit(1)

rows = []
changed = 0
with target.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        zh = r.get("填写中文") or ""
        new = zh.replace("凱裡", "凱里").replace("凯里", "凱里")
        # clothes name stays 凱莉 if present as full name for Kairi Clothes
        if new != zh:
            r["填写中文"] = new
            changed += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"OK: 凱裡→凱里 on {changed} rows")
