#!/usr/bin/env python3
"""Replace 升階 with 進階 in Item Ascend related fills (and general 裝備升階)."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

REPL = [
    ("裝備升階", "裝備進階"),
    ("装备升阶", "裝備進階"),
    ("升階成功", "進階成功"),
    ("升阶成功", "進階成功"),
    ("升階失敗", "進階失敗"),
    ("升阶失败", "進階失敗"),
    ("無法升階", "無法進階"),
    ("无法升阶", "無法進階"),
    ("使其升階", "使其進階"),
    ("使其升阶", "使其進階"),
    ("現在嘗試升階", "現在嘗試進階"),
    ("现在尝试升阶", "現在嘗試進階"),
    ("下次升階", "下次進階"),
    ("下次升阶", "下次進階"),
    ("升階", "進階"),
    ("升阶", "進階"),
]

# Only touch rows that look ascend-related or contain 升階
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
        pos = (r.get("位置") or "")
        en = (r.get("原文") or "")
        touch = ("升階" in zh or "升阶" in zh or "ASCEND" in pos.upper()
                 or "ascend" in en.lower())
        if not touch:
            rows.append(r)
            continue
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
print(f"OK: 升階→進階 on {changed} rows")
