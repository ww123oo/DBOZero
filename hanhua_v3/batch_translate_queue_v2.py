from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from .runtime.auto_translate_v2 import translate

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "new_translations.tsv"
TRANSLATIONS_PATH = ROOT / "data" / "translations.tsv"


@dataclass(frozen=True)
class TranslationStats:
    selected: int
    filled: int
    empty_before: int
    empty_after: int
    reused_existing: int
    skipped: int


def _load_existing(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    result: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            source = (row.get("原文") or row.get("source_text") or "").strip()
            target = (row.get("填写中文") or row.get("zh_cn") or "").strip()
            if source and target and source not in result:
                result[source] = target
    return result


def _key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("文件") or row.get("file") or "").strip(), (row.get("原文") or row.get("source_text") or "").strip())


def translate_queue(
    *,
    queue_path: Path = QUEUE_PATH,
    out_path: Path | None = None,
    translations_path: Path = TRANSLATIONS_PATH,
    fill_all: bool = False,
    replace_existing: bool = False,
    ignore_existing_map: bool = False,
    only_keys: set[tuple[str, str]] | None = None,
) -> TranslationStats:
    queue_path = queue_path.resolve()
    out_path = (out_path or queue_path).resolve()
    with queue_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    source_col = "原文" if "原文" in fieldnames else "source_text"
    target_col = "填写中文" if "填写中文" in fieldnames else "zh_cn"
    if source_col not in fieldnames or target_col not in fieldnames:
        raise SystemExit("Translation queue must contain 原文/填写中文 or source_text/zh_cn")

    existing = {} if ignore_existing_map else _load_existing(translations_path)
    selected = filled = empty_before = empty_after = reused = skipped = 0

    for row in rows:
        if only_keys is not None and _key(row) not in only_keys:
            continue
        selected += 1
        source = row.get(source_col) or ""
        current = row.get(target_col) or ""
        if current.strip() and not replace_existing:
            skipped += 1
            continue
        if not current.strip():
            empty_before += 1

        stripped = source.strip()
        old = existing.get(stripped)
        if old and not ignore_existing_map:
            row[target_col] = old
            reused += 1
            filled += 1
            continue

        result = translate(stripped)
        # v2 intentionally refuses to invent translations for unknown text.
        # --fill-all means "use composed deterministic rules", not hallucinate.
        if result.changed and (fill_all or result.confidence >= 0.70):
            row[target_col] = result.translation
            filled += 1
        else:
            if not current.strip():
                empty_after += 1
            skipped += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return TranslationStats(selected, filled, empty_before, empty_after, reused, skipped)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DBO translation queue v2")
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--out", type=Path, default=QUEUE_PATH)
    parser.add_argument("--fill-all", action="store_true")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--ignore-existing-map", action="store_true")
    args = parser.parse_args(argv)
    stats = translate_queue(queue_path=args.queue, out_path=args.out, fill_all=args.fill_all, replace_existing=args.replace_existing, ignore_existing_map=args.ignore_existing_map)
    print(f"selected={stats.selected}")
    print(f"filled={stats.filled}")
    print(f"empty_before={stats.empty_before}")
    print(f"empty_after={stats.empty_after}")
    print(f"reused_existing={stats.reused_existing}")
    print(f"skipped={stats.skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
