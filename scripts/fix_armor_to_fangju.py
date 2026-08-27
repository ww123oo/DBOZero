#!/usr/bin/env python3
"""Replace 盔甲 → 防具 in 填写中文; upgrade stones use 強化石; light S2T on touched rows."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# Order matters: longer phrases first
REPLACEMENTS = [
    ("高级盔甲升级石", "高級防具強化石"),
    ("史诗盔甲升级石", "史詩防具強化石"),
    ("盔甲升级石", "防具強化石"),
    ("盔甲降级石", "防具降級石"),
    ("盔甲券", "防具券"),
    ("盔甲石", "防具石"),
    ("盔甲商人", "防具商人"),
    ("盔甲制作", "防具製作"),
    ("盔甲升级", "防具強化"),
    ("盔甲", "防具"),
]

S2T_EXTRA = [
    ("升级", "升級"),
    ("降级", "降級"),
    ("高级", "高級"),
    ("史诗", "史詩"),
    ("制作", "製作"),
    ("创建", "建立"),
    ("赛亚人", "賽亞人"),
    ("贝吉塔", "達爾"),
    ("布罗利", "布羅利"),
    ("异次元", "異次元"),
    ("武器和防具", "武器和防具"),
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
        if "盔甲" not in zh and "升级石" not in zh:
            rows.append(r)
            continue
        new = zh
        for a, b in REPLACEMENTS:
            new = new.replace(a, b)
        # only light S2T on rows we already touched
        if new != zh:
            for a, b in S2T_EXTRA:
                new = new.replace(a, b)
        if new != zh:
            r["填写中文"] = new
            changed += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: replaced 盔甲→防具 in {changed} rows")
