# -*- coding: utf-8 -*-
"""Merge full resource discovery into the human translation queue.

The existing v3 queue remains the user-facing TSV. This bridge adds resources
that the older structured catalog does not cover yet: all XML/RDF/DAT files and
stable-ID tbl2 records. It never touches game files.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .full_text_scanner import scan_file, files_to_scan

HEADER = ["来源", "文件", "位置", "原文", "参考译文", "填写中文", "长度状态"]


def _candidate(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 220:
        return False
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return False
    return any(ch.isalpha() for ch in text)


def _row_key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("文件") or "").strip().lower(), (row.get("原文") or "").strip())


def _read(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def merge_queue(queue: Path, source_root: Path) -> tuple[int, int]:
    rows = _read(queue)
    fieldnames = list(HEADER)
    if rows and any(name not in rows[0] for name in HEADER):
        fieldnames = HEADER
    stable_tbl2: dict[tuple[str, str], dict[str, str]] = {}
    discovered: list[dict[str, str]] = []

    for path in files_to_scan(source_root):
        name = path.name.lower()
        if path.suffix.lower() not in {".dat", ".xml", ".rdf"} and name != "tbl2.pak":
            continue
        for hit in scan_file(path):
            if not _candidate(hit.text):
                continue
            if name == "tbl2.pak" and hit.kind == "tbl2_record":
                stable_tbl2[(name, hit.text)] = {
                    "来源": "TBL",
                    "文件": path.name,
                    "位置": f"id:{hit.id}",
                    "原文": hit.text,
                    "参考译文": "",
                    "填写中文": "",
                    "长度状态": "untranslated",
                }
            elif path.suffix.lower() in {".dat", ".xml", ".rdf"}:
                discovered.append({
                    "来源": path.suffix.lower().lstrip("." ).upper(),
                    "文件": path.name,
                    "位置": f"offset:0x{hit.offset:X}",
                    "原文": hit.text,
                    "参考译文": "",
                    "填写中文": "",
                    "长度状态": "untranslated",
                })

    # Replace old tbl2 rows for the same source with stable-ID rows.
    output: list[dict[str, str]] = []
    replaced_keys: set[tuple[str, str]] = set()
    for row in rows:
        key = _row_key(row)
        stable = stable_tbl2.get(key)
        if stable:
            stable["填写中文"] = row.get("填写中文") or ""
            stable["参考译文"] = row.get("参考译文") or ""
            stable["长度状态"] = row.get("长度状态") or "untranslated"
            output.append(stable)
            replaced_keys.add(key)
        else:
            output.append({name: row.get(name, "") for name in HEADER})

    existing = {_row_key(row) for row in output}
    for row in stable_tbl2.values():
        key = _row_key(row)
        if key not in existing:
            output.append(row)
            existing.add(key)
    for row in discovered:
        key = _row_key(row)
        if key not in existing:
            output.append(row)
            existing.add(key)

    queue.parent.mkdir(parents=True, exist_ok=True)
    with queue.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    return len(output), len(output) - len(rows)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Merge full resource discovery into data/new_translations.tsv")
    parser.add_argument("queue", type=Path, default=Path("data/new_translations.tsv"), nargs="?")
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args(argv)
    total, added = merge_queue(args.queue, args.source_root)
    print(f"queue rows: {total}")
    print(f"full-resource rows added/replaced: {added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
