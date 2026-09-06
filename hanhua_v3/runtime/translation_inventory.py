# -*- coding: utf-8 -*-
"""Bridge full-text scan results into the daily new_translations.tsv queue.

This module deliberately does not modify game resources.  It only compares
scanner output with the existing translation tables and produces candidates.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

SCHEMA = (
    "surface",
    "file",
    "id",
    "source_text",
    "source_hash",
    "zh_cn",
    "status",
    "legacy_source",
    "legacy_row",
    "note",
)


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("file") or "").replace("\\", "/").lower(),
        row.get("id") or "",
        row.get("source_text") or "",
    )


def build_inventory(scan_tsv: Path, legacy_tsv: Path, new_tsv: Path) -> list[dict[str, str]]:
    """Return new/changed candidates while preserving existing daily entries."""
    legacy = _read_tsv(legacy_tsv)
    daily = _read_tsv(new_tsv)
    known = {_key(row): row for row in legacy}
    known.update({_key(row): row for row in daily})

    candidates: list[dict[str, str]] = []
    with scan_tsv.open("r", encoding="utf-8-sig", newline="") as f:
        for hit in csv.DictReader(f, delimiter="\t"):
            source = (hit.get("source_text") or "").strip()
            if not source:
                continue
            row = {
                "surface": "scanner",
                "file": hit.get("file", ""),
                "id": hit.get("id", ""),
                "source_text": source,
                "source_hash": "",
                "zh_cn": "",
                "status": "new",
                "legacy_source": "",
                "legacy_row": "",
                "note": "discovered by full_text_scanner",
            }
            k = _key(row)
            old = known.get(k)
            if old:
                # Keep a previously entered translation/status; scanner metadata
                # is intentionally not allowed to overwrite human translation data.
                if old.get("zh_cn") or old.get("status") not in ("", "new"):
                    continue
            candidates.append(row)
            known[k] = row
    return candidates


def write_candidates(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build new translation candidates from a full scan")
    parser.add_argument("scan", type=Path, help="translation_scan.tsv produced by scan_all_text.py")
    parser.add_argument("--legacy", type=Path, default=Path("data/translations.tsv"))
    parser.add_argument("--daily", type=Path, default=Path("data/new_translations.tsv"))
    parser.add_argument("-o", "--output", type=Path, default=Path("reports/internal/untranslated_candidates.tsv"))
    args = parser.parse_args()
    rows = build_inventory(args.scan, args.legacy, args.daily)
    write_candidates(rows, args.output)
    print(f"new candidates: {len(rows)}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
