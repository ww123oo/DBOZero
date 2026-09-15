# -*- coding: utf-8 -*-
"""Attach tbl2 stable IDs (id:N) to data/new_translations.tsv by scanning pack/tbl2.pak.

Only rewrites rows where file is tbl2.pak and locator is * / empty.
Matching is by exact source_text. Ambiguous texts stay *.

Usage:
  python scripts/attach_tbl2_stable_ids.py
  python scripts/attach_tbl2_stable_ids.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def iter_tbl2_records(data: bytes) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    n = len(data)
    for record_pos in range(0, n - 7):
        item_id = int.from_bytes(data[record_pos : record_pos + 4], "little")
        if item_id == 0:
            continue
        if data[record_pos + 4] != 0:
            continue
        units = int.from_bytes(data[record_pos + 5 : record_pos + 7], "little")
        if units <= 0 or units > 4096:
            continue
        text_start = record_pos + 7
        byte_len = units * 2
        if text_start + byte_len > n:
            continue
        raw = data[text_start : text_start + byte_len]
        try:
            text = raw.decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if len(text) != units:
            continue
        hits.append((item_id, text))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tsv", type=Path, default=ROOT / "data" / "new_translations.tsv")
    parser.add_argument(
        "--tbl2",
        type=Path,
        default=ROOT / "src_file" / "DBOZero" / "pack" / "tbl2.pak",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.tbl2.is_file():
        raise SystemExit(f"missing tbl2: {args.tbl2}")
    if not args.tsv.is_file():
        raise SystemExit(f"missing tsv: {args.tsv}")

    data = args.tbl2.read_bytes()
    records = iter_tbl2_records(data)
    by_text: dict[str, list[int]] = {}
    for item_id, text in records:
        by_text.setdefault(text, []).append(item_id)
    for text, ids in list(by_text.items()):
        by_text[text] = sorted(set(ids))

    print(f"tbl2 validated records: {len(records)}")
    print(f"unique texts: {len(by_text)}")

    with args.tsv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    col_file = "文件" if "文件" in fieldnames else "file"
    col_id = "位置" if "位置" in fieldnames else "id"
    col_src = "原文" if "原文" in fieldnames else "source_text"

    attached = ambiguous = missing = skipped = 0
    for row in rows:
        if (row.get(col_file) or "").strip().lower() != "tbl2.pak":
            continue
        loc = (row.get(col_id) or "").strip()
        if loc.startswith("id:"):
            skipped += 1
            continue
        if loc and loc not in {"*", "all", "ALL"}:
            skipped += 1
            continue
        src = row.get(col_src) or ""
        ids = by_text.get(src)
        if not ids:
            missing += 1
            continue
        if len(ids) != 1:
            ambiguous += 1
            continue
        row[col_id] = f"id:{ids[0]}"
        attached += 1

    print(f"attached id:N: {attached}")
    print(f"ambiguous (left *): {ambiguous}")
    print(f"missing text in pak: {missing}")
    print(f"skipped (already located): {skipped}")

    if args.dry_run:
        print("dry-run: not writing")
        return 0

    bak = args.tsv.with_suffix(args.tsv.suffix + ".bak_before_tbl2_ids")
    if not bak.exists():
        shutil.copy2(args.tsv, bak)
        print(f"backup: {bak}")

    with args.tsv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
