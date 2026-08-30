#!/usr/bin/env python3
"""Consolidate all data/*_delta.tsv into data/deltas/{term,ui,tbl}.tsv
and move originals to data/archive/legacy_deltas/.

Run once from repo root:
  python scripts/consolidate_deltas.py
"""
from __future__ import annotations

from pathlib import Path
import csv
import re
import shutil

root = Path(__file__).resolve().parents[1]
data = root / "data"
deltas_dir = data / "deltas"
arch = data / "archive" / "legacy_deltas"

TERM_PREFIX = ("term_", "place_")
TERM_NAMES = {"translations_to_merge.tsv", "place_name_fix_delta.tsv"}
UI_PREFIX = ("ui_", "lang0_", "length_fix")
TBL_PREFIX = ("tbl_batch", "tbl0_", "tbl_length")


def classify(name: str) -> str | None:
    if name in TERM_NAMES or name.startswith(TERM_PREFIX):
        return "term"
    if name.startswith(UI_PREFIX) or name in {"length_fix_delta.tsv"}:
        return "ui"
    if name.startswith(TBL_PREFIX) or name == "tbl_batch_delta.tsv":
        return "tbl"
    if name.endswith("_delta.tsv"):
        return "ui"  # misc deltas
    return None


def load_into(M: dict, path: Path) -> int:
    n = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            en = (r.get("原文") or "").strip()
            zh = (r.get("填写中文") or "").strip()
            if en and zh:
                M[en] = zh
                n += 1
    return n


def write_tsv(path: Path, M: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["原文", "填写中文"])
        for en, zh in M.items():
            w.writerow([en.replace("\n", "\\n"), zh.replace("\n", "\\n")])


def main() -> int:
    buckets = {"term": {}, "ui": {}, "tbl": {}}
    to_archive: list[Path] = []

    for p in sorted(data.glob("*.tsv")):
        if p.name in ("new_translations.tsv", "translations.tsv"):
            continue
        kind = classify(p.name)
        if not kind:
            continue
        n = load_into(buckets[kind], p)
        print(f"  {p.name} -> {kind} (+{n}, total {len(buckets[kind])})")
        to_archive.append(p)

    # also numbered batches already matched
    deltas_dir.mkdir(parents=True, exist_ok=True)
    for kind, M in buckets.items():
        out = deltas_dir / f"{kind}.tsv"
        write_tsv(out, M)
        print(f"wrote {out.relative_to(root)} keys={len(M)}")

    arch.mkdir(parents=True, exist_ok=True)
    for p in to_archive:
        dest = arch / p.name
        shutil.move(str(p), str(dest))
        print(f"archived {p.name}")

    # optional dirs
    for dname in ("tbl_batch3_chunks", "merge_parts"):
        d = data / dname
        if d.is_dir():
            dest = arch / dname
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(d), str(dest))
            print(f"archived dir {dname}")

    print("OK. data/ root should keep: new_translations.tsv, translations.tsv, gui_font.ini, deltas/, README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
