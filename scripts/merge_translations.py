#!/usr/bin/env python3
"""Merge translations_to_merge.tsv into data/new_translations.tsv by 原文."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
merge_path = root / "data" / "translations_to_merge.tsv"
target = root / "data" / "new_translations.tsv"

if not merge_path.exists():
    print("missing", merge_path)
    sys.exit(1)
if not target.exists():
    print("missing", target)
    sys.exit(1)

M = {}
with merge_path.open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        en = (r.get("原文") or "").strip()
        zh = (r.get("填写中文") or "").strip()
        if en and zh:
            M[en] = zh

rows = []
filled = 0
with target.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        en = (r.get("原文") or "").strip()
        cur = (r.get("填写中文") or "").strip()
        if en in M and (not cur or cur == en):
            r["填写中文"] = M[en]
            filled += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"merged {filled} rows from {len(M)} keys into {target}")
