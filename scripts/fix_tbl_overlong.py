#!/usr/bin/env python3
"""Fix game crash: blank tbl0/1/2 填写中文 longer (bytes) than 原文.

Preserves new_translations.tsv columns and row count.
Only clears unsafe Chinese; English source used at build for empty cells.
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


def bytelen(s: str, enc: str) -> int:
    return len(s.encode(enc, "replace"))


def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1

    bak = target.with_suffix(".tsv.bak_before_tbl_overlong")
    if not bak.exists():
        bak.write_bytes(target.read_bytes())
        print("backup:", bak.name)

    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)

    if not fields or "填写中文" not in fields:
        print("bad columns", fields)
        return 1

    cleared = 0
    report: list[str] = []
    for r in rows:
        file_ = (r.get("文件") or "").lower()
        if not any(x in file_ for x in ("tbl0", "tbl1", "tbl2")):
            continue
        en = (r.get("原文") or "").strip()
        zh = (r.get("填写中文") or "").strip()
        if not zh or not has_cjk(zh) or not en:
            continue
        limit = max(bytelen(en, "cp950"), len(en.encode("ascii", "replace")))
        if max(bytelen(zh, "cp950"), bytelen(zh, "gbk")) > limit:
            r["填写中文"] = ""
            cleared += 1
            if len(report) < 30:
                report.append(f"{file_}\t{en[:40]}\twas:{zh[:30]}")

    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"OK: cleared {cleared} overlong tbl rows")
    print(f"  rows still {len(rows)}; columns {list(fields)}")
    for line in report:
        print(" ", line)
    if cleared >= 30:
        print(f"  ... and {cleared - 30} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
