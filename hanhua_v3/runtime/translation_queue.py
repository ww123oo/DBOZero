# -*- coding: utf-8 -*-
"""Build and optionally sync the active DBO translation work queue.

Resource scan output is authoritative for discovery.  data/translations.tsv is
legacy reference data; data/new_translations.tsv is the active daily/update
queue.  This module never writes game resource files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

SCHEMA = (
    "surface", "file", "id", "source_text", "source_hash", "zh_cn",
    "status", "legacy_source", "legacy_row", "note",
)


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm_file(value: str) -> str:
    return (value or "").replace("\\", "/").strip().lower()


def _norm_id(value: str) -> str:
    return (value or "").strip()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            return []
        return [{name: (row.get(name) or "") for name in SCHEMA} for row in reader]


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def exact_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (_norm_file(row.get("file", "")), _norm_id(row.get("id", "")), row.get("source_text", "") or "")


def hash_key(row: dict[str, str]) -> tuple[str, str]:
    text = row.get("source_text", "") or ""
    digest = row.get("source_hash", "") or source_hash(text)
    return (_norm_file(row.get("file", "")), digest)


def surface_for(hit: dict[str, str]) -> str:
    file_name = _norm_file(hit.get("file", ""))
    kind = (hit.get("kind") or "").strip().lower()
    if kind == "dat_entry" or file_name.endswith(".dat"):
        return "dat"
    if file_name.endswith(".rdf"):
        return "rdf"
    if file_name.endswith(".xml"):
        return "xml"
    if file_name.endswith(".pak"):
        return "pak"
    return "scanner"


def locator_for(hit: dict[str, str]) -> str:
    value = _norm_id(hit.get("id", ""))
    if value:
        return value
    offset = _norm_id(hit.get("offset", ""))
    return f"offset:{offset}" if offset else ""


def candidate_from_hit(hit: dict[str, str]) -> dict[str, str] | None:
    source = (hit.get("source_text") or "").strip()
    if not source:
        return None
    return {
        "surface": surface_for(hit),
        "file": hit.get("file", ""),
        "id": locator_for(hit),
        "source_text": source,
        "source_hash": source_hash(source),
        "zh_cn": "",
        "status": "new",
        "legacy_source": "",
        "legacy_row": "",
        "note": "discovered by full_text_scanner",
    }


def build_queue(scan_tsv: Path, legacy_tsv: Path, daily_tsv: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    legacy = read_tsv(legacy_tsv)
    daily = read_tsv(daily_tsv)

    exact: dict[tuple[str, str, str], dict[str, str]] = {}
    hashes: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in legacy + daily:
        exact[exact_key(row)] = row
        hashes.setdefault(hash_key(row), []).append(row)

    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    with scan_tsv.open("r", encoding="utf-8-sig", newline="") as handle:
        for hit in csv.DictReader(handle, delimiter="\t"):
            row = candidate_from_hit(hit)
            if row is None:
                continue
            key = exact_key(row)
            if key in seen:
                continue
            seen.add(key)

            old = exact.get(key)
            if old is None:
                matches = hashes.get(hash_key(row), [])
                # Hash matching is allowed only when the same file identifies
                # exactly one historical/daily row.  Never match by text alone.
                if len(matches) == 1:
                    old = matches[0]

            if old is not None:
                # Human translation or an intentional status always wins.
                # A plain "new" row is also not duplicated if it already exists.
                continue

            candidates.append(row)
            exact[key] = row

    merged = list(daily)
    daily_keys = {exact_key(row) for row in merged}
    for row in candidates:
        if exact_key(row) not in daily_keys:
            merged.append(row)
            daily_keys.add(exact_key(row))
    return candidates, merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the DBO daily translation queue")
    parser.add_argument("scan", type=Path, help="translation_scan.tsv from scan_all_text.py")
    parser.add_argument("--legacy", type=Path, default=Path("data/translations.tsv"))
    parser.add_argument("--daily", type=Path, default=Path("data/new_translations.tsv"))
    parser.add_argument("-o", "--output", type=Path, default=Path("reports/internal/untranslated_candidates.tsv"))
    parser.add_argument("--sync-daily", action="store_true", help="append newly discovered entries to the active daily TSV")
    args = parser.parse_args(argv)

    if not args.scan.is_file():
        parser.error(f"scan file does not exist: {args.scan}")

    candidates, merged = build_queue(args.scan, args.legacy, args.daily)
    write_tsv(args.output, candidates)
    if args.sync_daily:
        write_tsv(args.daily, merged)

    print(f"new candidates: {len(candidates)}")
    print(f"candidate report: {args.output}")
    if args.sync_daily:
        print(f"daily queue updated: {args.daily}")
    else:
        print("daily queue unchanged; use --sync-daily to append discovered rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
