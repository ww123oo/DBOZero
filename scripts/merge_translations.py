#!/usr/bin/env python3
"""Merge delta TSVs into data/new_translations.tsv 填写中文."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"
merge_files = [
    root / "data" / "translations_to_merge.tsv",
    root / "data" / "ui_equip_delta.tsv",
    root / "data" / "ui_long_delta.tsv",
    root / "data" / "length_fix_delta.tsv",
    root / "data" / "ui_batch_delta.tsv",
    root / "data" / "ui_batch2_delta.tsv",
    root / "data" / "lang0_s2t_delta.tsv",
    root / "data" / "place_name_fix_delta.tsv",
    root / "data" / "tbl_batch_delta.tsv",
    root / "data" / "tbl_batch2_delta.tsv",
    root / "data" / "tbl_batch3_delta.tsv",
    root / "data" / "tbl_batch4_delta.tsv",
    root / "data" / "tbl_batch5_delta.tsv",
    root / "data" / "tbl_batch6_delta.tsv",
    root / "data" / "tbl_batch7_delta.tsv",
    root / "data" / "tbl_batch8_delta.tsv",
    root / "data" / "tbl_batch9_delta.tsv",
    root / "data" / "tbl_batch10_delta.tsv",
    root / "data" / "tbl_batch11_delta.tsv",
    root / "data" / "tbl_batch12_delta.tsv",
    root / "data" / "tbl_batch13_delta.tsv",
    root / "data" / "tbl_batch14_delta.tsv",
]

M = {}
for mp in merge_files:
    if not mp.exists():
        continue
    with mp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            en = (r.get("原文") or "").strip().replace("\\n", "\n")
            zh = (r.get("填写中文") or "").strip().replace("\\n", "\n")
            if en and zh:
                M[en] = zh
    print(f"loaded {mp.name}: keys {len(M)}")

if not M:
    print("no merge data")
    sys.exit(1)
if not target.exists():
    print("missing", target)
    sys.exit(1)

rows = []
filled = 0
with target.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        en = (r.get("原文") or "").strip()
        cur = (r.get("填写中文") or "").strip()
        if en in M:
            if cur != M[en]:
                r["填写中文"] = M[en]
                filled += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: data/new_translations.tsv updated {filled} from {len(M)} keys")
