#!/usr/bin/env python3
"""Merge data/translations_to_merge.tsv and data/ui_equip_delta.tsv into data/new_translations.tsv 填写中文."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"
merge_files = [
    root / "data" / "translations_to_merge.tsv",
    root / "data" / "ui_equip_delta.tsv",
]
parts_dir = root / "data" / "merge_parts"

# Auto-combine part*.tsv if present
parts = sorted(parts_dir.glob("part*.tsv")) if parts_dir.exists() else []
if parts:
    lines = []
    for i, p in enumerate(parts):
        rows = p.read_text(encoding="utf-8-sig").splitlines()
        if not rows:
            continue
        if i == 0:
            lines.extend(rows)
        else:
            lines.extend(rows[1:] if ("原文" in rows[0] or "填写" in rows[0]) else rows)
    (root / "data" / "translations_to_merge.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"combined {len(parts)} parts")

M = {}
for mp in merge_files:
    if not mp.exists():
        continue
    with mp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            en = (r.get("原文") or "").strip()
            zh = (r.get("填写中文") or "").strip()
            if en and zh:
                M[en] = zh
    print(f"loaded {mp.name}: keys now {len(M)}")

if not M:
    print("no merge data found")
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
        if en in M and (not cur or cur == en):
            r["填写中文"] = M[en]
            filled += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: wrote data/new_translations.tsv, filled {filled} rows from {len(M)} keys")
