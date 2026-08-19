from __future__ import annotations

import csv
import io
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .batch_translate_queue import is_internal_identifier


__all__ = [
    "CATALOG_PATH",
    "QUEUE_PATH",
    "ROOT",
    "RecoveryError",
    "RecoveryStats",
    "TRANSLATIONS_PATH",
    "exact_queue_key",
    "git_tsv",
    "master_key",
    "read_tsv",
    "recover_from_git",
    "stable_key",
    "write_tsv_atomic",
]

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "new_translations.tsv"
TRANSLATIONS_PATH = ROOT / "data" / "translations.tsv"
CATALOG_PATH = ROOT / "reports" / "internal" / "catalog_current.tsv"


class RecoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class RecoveryStats:
    references: tuple[str, ...]
    queue_filled: int
    master_added: int
    missing_current_source: int
    conflicts: int


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def git_tsv(ref: str, relative_path: str) -> list[dict[str, str]]:
    command = [
        "git",
        "-c",
        f"safe.directory={ROOT.as_posix()}",
        "show",
        f"{ref}:{relative_path}",
    ]
    try:
        run_kwargs: dict = {
            "cwd": ROOT,
            "check": True,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if os.name == "nt":
            run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        payload = subprocess.run(command, **run_kwargs).stdout
        text = payload.decode("utf-8-sig")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        raise RecoveryError(f"無法讀取 Git 翻譯資料：{ref}:{relative_path}") from exc
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def stable_key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("文件") or row.get("file") or "").strip(), (row.get("原文") or row.get("source_text") or "").strip())


def exact_queue_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("文件") or row.get("file") or "").strip(),
        (row.get("位置") or row.get("id") or "").strip(),
        (row.get("原文") or row.get("source_text") or "").strip(),
    )


def master_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("surface") or "").strip(),
        (row.get("file") or "").strip(),
        (row.get("source_text") or "").strip(),
    )


def write_tsv_atomic(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    temporary = path.with_name(f".{path.name}.recover.tmp")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def recover_from_git(refs: list[str], *, dry_run: bool = False) -> RecoveryStats:
    if not refs:
        raise RecoveryError("至少需要一個 Git 引用")
    queue_fields, queue_rows = read_tsv(QUEUE_PATH)
    master_fields, master_rows = read_tsv(TRANSLATIONS_PATH)
    _catalog_fields, catalog_rows = read_tsv(CATALOG_PATH)

    queue_exact_candidates: dict[tuple[str, str, str], tuple[str, str]] = {}
    queue_stable_candidates: dict[tuple[str, str], dict[str, str]] = {}
    master_candidates: dict[tuple[str, str, str], tuple[dict[str, str], str]] = {}
    conflicts: list[tuple[str, str, str, str, str]] = []

    for ref in refs:
        for row in git_tsv(ref, "data/new_translations.tsv"):
            translation = (row.get("填写中文") or "").strip()
            exact_key = exact_queue_key(row)
            source_key = stable_key(row)
            if not translation or not all(exact_key) or not all(source_key) or is_internal_identifier(source_key[1]):
                continue
            existing = queue_exact_candidates.get(exact_key)
            if existing and existing[0] != translation:
                conflicts.append((exact_key[0], exact_key[2], existing[0], translation, ref))
            else:
                queue_exact_candidates.setdefault(exact_key, (translation, ref))
            queue_stable_candidates.setdefault(source_key, {}).setdefault(translation, ref)

        for row in git_tsv(ref, "data/translations.tsv"):
            translation = (row.get("zh_cn") or "").strip()
            key = master_key(row)
            if not translation or not all(key):
                continue
            existing = master_candidates.get(key)
            if existing and (existing[0].get("zh_cn") or "").strip() != translation:
                conflicts.append((key[1], key[2], (existing[0].get("zh_cn") or "").strip(), translation, ref))
                continue
            master_candidates.setdefault(key, (row, ref))

    queue_by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in queue_rows:
        queue_by_key.setdefault(stable_key(row), []).append(row)

    queue_filled = 0
    for row in queue_rows:
        if (row.get("填写中文") or "").strip():
            continue
        candidate = queue_exact_candidates.get(exact_queue_key(row))
        if not candidate:
            variants = queue_stable_candidates.get(stable_key(row), {})
            if len(variants) == 1:
                translation, ref = next(iter(variants.items()))
                candidate = (translation, ref)
        if candidate:
            row["填写中文"] = candidate[0]
            queue_filled += 1

    current_master_keys = {master_key(row) for row in master_rows}
    catalog_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in catalog_rows:
        key = master_key(row)
        if all(key):
            catalog_by_key.setdefault(key, row)

    master_added = 0
    missing_current_source = 0
    for key, (reference_row, ref) in master_candidates.items():
        if key in current_master_keys:
            continue
        catalog_row = catalog_by_key.get(key)
        if not catalog_row:
            missing_current_source += 1
            continue

        surface, file_name, source_text = key
        translation = (reference_row.get("zh_cn") or "").strip()
        if surface != "taiwan":
            current_queue_rows = queue_by_key.get((file_name, source_text), [])
            for queue_row in current_queue_rows:
                if not (queue_row.get("填写中文") or "").strip():
                    queue_row["填写中文"] = translation
                    queue_filled += 1
            continue

        master_rows.append(
            {
                "surface": surface,
                "file": file_name,
                "id": catalog_row.get("id") or "",
                "source_text": source_text,
                "source_hash": catalog_row.get("source_hash") or "",
                "zh_cn": translation,
                "status": "accepted",
                "legacy_source": f"git:{ref}",
                "legacy_row": reference_row.get("legacy_row") or "",
                "note": "recovered_from_git_history",
            }
        )
        current_master_keys.add(key)
        master_added += 1

    if not dry_run:
        write_tsv_atomic(QUEUE_PATH, queue_fields, queue_rows)
        if master_added:
            write_tsv_atomic(TRANSLATIONS_PATH, master_fields, master_rows)

    ambiguous_sources = sum(len(variants) > 1 for variants in queue_stable_candidates.values())
    return RecoveryStats(tuple(refs), queue_filled, master_added, missing_current_source, len(conflicts) + ambiguous_sources)
