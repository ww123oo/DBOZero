#!/usr/bin/env python3
"""Combine data/merge_parts/part*.tsv into data/translations_to_merge.tsv"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parts_dir = root / "data" / "merge_parts"
out = root / "data" / "translations_to_merge.tsv"
parts = sorted(parts_dir.glob("part*.tsv"))
if not parts:
    raise SystemExit(f"no parts in {parts_dir}")

lines = []
for i, p in enumerate(parts):
    rows = p.read_text(encoding="utf-8-sig").splitlines()
    if not rows:
        continue
    if i == 0:
        lines.extend(rows)
    else:
        lines.extend(rows[1:] if rows[0].startswith("原文") or "填写" in rows[0] else rows)

out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(lines)} lines) from {len(parts)} parts")
