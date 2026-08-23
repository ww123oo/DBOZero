#!/usr/bin/env python3
"""把 data/translations_to_merge.tsv（或 merge_parts）合并进 data/new_translations.tsv 的「填写中文」列。"""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
parts_dir = root / "data" / "merge_parts"
merge_path = root / "data" / "translations_to_merge.tsv"
target = root / "data" / "new_translations.tsv"  # 最终写入这里

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
    merge_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"combined {len(parts)} parts -> {merge_path} ({len(lines)} lines)")

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

print(f"OK: 已写入 data/new_translations.tsv（填写中文），新增/补全 {filled} 行，对照表键 {len(M)} 个")
