#!/usr/bin/env python3
"""Clear tbl2 填写中文 that are longer (bytes) than 原文 — prevents fixed-field crash.

Keeps new_translations.tsv structure/columns intact. Only blanks unsafe rows.
Re-run after merging deltas if build/game crashes on tbl2.
"""
from __future__ import annotations

from pathlib import Path
import csv
import re
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1

    # backup once
    bak = target.with_suffix(".tsv.bak_before_tbl2_fix")
    if not bak.exists():
        bak.write_bytes(target.read_bytes())
        print("backup:", bak.name)

    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)

    cleared = 0
    kept = 0
    for r in rows:
        if "tbl2" not in (r.get("文件") or "").lower():
            continue
        en = (r.get("原文") or "").strip()
        zh = (r.get("填写中文") or "").strip()
        if not zh or not has_cjk(zh) or not en:
            continue
        se = len(en.encode("cp950", "replace"))
        tz = len(zh.encode("cp950", "replace"))
        gz = len(zh.encode("gbk", "replace"))
        if max(tz, gz) > se:
            r["填写中文"] = ""
            cleared += 1
        else:
            kept += 1

    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"OK: cleared {cleared} overlong tbl2 rows; kept {kept} safe CJK")
    print("  structure/columns unchanged; empty 填写中文 will fall back to English source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
