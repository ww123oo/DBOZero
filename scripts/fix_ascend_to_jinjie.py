#!/usr/bin/env python3
"""Never use 升階 — always 進階 in 填写中文."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

REPL = [
    ("裝備升階", "裝備進階"),
    ("装备升阶", "裝備進階"),
    ("升階", "進階"),
    ("升阶", "進階"),
]

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
        new = zh
        for a, b in REPL:
            new = new.replace(a, b)
        if new != zh:
            r["填写中文"] = new
            changed += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"OK: 升階/升阶 → 進階 on {changed} rows")
