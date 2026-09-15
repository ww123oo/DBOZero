# -*- coding: utf-8 -*-
"""Safe fixed-field patcher for DBO tbl0/tbl1/tbl2."""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

TBL_FILES = ("tbl0.pak", "tbl1.pak", "tbl2.pak")
ALL_OFFSETS = {"", "*", "all", "ALL"}


class PatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class TblOverride:
    file_name: str
    offset: int | None
    source_text: str
    translation: str
    item_id: int | None = None


def tool_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def parse_offset(value: str, row_no: int) -> int | None:
    value = value.strip()
    if value in ALL_OFFSETS:
        return None
    try:
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    except ValueError as exc:
        raise PatchError(f"Invalid offset at row {row_no}: {value}") from exc


def parse_locator(value: str, row_no: int) -> tuple[int | None, int | None]:
    """Return (offset, stable_item_id). Supports *, hex/dec offset, and id:N."""
    value = (value or "").strip()
    if value in ALL_OFFSETS:
        return None, None
    if value.lower().startswith("id:"):
        try:
            return None, int(value.split(":", 1)[1].strip(), 0)
        except ValueError as exc:
            raise PatchError(f"Invalid stable ID at row {row_no}: {value}") from exc
    return parse_offset(value, row_no), None


def read_overrides(path: Path | None = None) -> list[TblOverride]:
    path = path or (tool_dir() / "tbl_overrides.tsv")
    if not path.exists():
        raise PatchError(f"Missing tbl overrides file: {path}")
    rows: list[TblOverride] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row_no, row in enumerate(csv.reader(handle, delimiter="\t"), 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            file_name = row[0].strip()
            if file_name not in TBL_FILES:
                raise PatchError(f"Unsupported tbl file at row {row_no}: {file_name}")
            if row[2] and row[3]:
                locator = row[1].strip()
                item_id = None
                if locator.lower().startswith("id:"):
                    try:
                        item_id = int(locator.split(":", 1)[1], 0)
                    except ValueError as exc:
                        raise PatchError(f"Invalid stable ID at row {row_no}: {locator}") from exc
                    offset = None
                else:
                    offset = parse_offset(locator, row_no)
                rows.append(TblOverride(file_name, offset, row[2], row[3], item_id))
    return rows


def utf16le(text: str, label: str = "Text") -> bytes:
    try:
        return text.encode("utf-16le")
    except UnicodeEncodeError as exc:
        raise PatchError(f"{label} cannot be encoded as UTF-16LE: {text!r}") from exc


def fixed_replacement(source_text: str, translation: str) -> bytes:
    source = utf16le(source_text, "Source text")
    replacement = utf16le(translation, "Translation")
    if len(replacement) > len(source):
        raise PatchError(f"Translation is too long: {source_text!r} -> {translation!r}")
    return replacement + b"\x00" * (len(source) - len(replacement))


def find_all(data: bytes, needle: bytes) -> list[int]:
    result: list[int] = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return result
        result.append(pos)
        start = pos + max(1, len(needle))


def tbl2_record_at(data: bytes, text_offset: int, source_text: str) -> bool:
    raw = utf16le(source_text)
    if text_offset < 7 or text_offset + len(raw) > len(data):
        return False
    length_pos = text_offset - 2
    type_pos = text_offset - 3
    record_pos = text_offset - 7
    units = int.from_bytes(data[length_pos:text_offset], "little")
    if units != len(source_text) or data[type_pos] != 0:
        return False
    if int.from_bytes(data[record_pos:record_pos + 4], "little") == 0:
        return False
    return bytes(data[text_offset:text_offset + len(raw)]) == raw


def find_tbl2_id_text(data: bytes, item_id: int, source_text: str) -> list[int]:
    """Find text offsets for a stable tbl2 ID in the observed record form."""
    raw = utf16le(source_text)
    hits: list[int] = []
    start = 0
    id_bytes = item_id.to_bytes(4, "little", signed=False)
    while True:
        record_pos = data.find(id_bytes, start)
        if record_pos < 0:
            break
        text_offset = record_pos + 7
        if tbl2_record_at(data, text_offset, source_text):
            hits.append(text_offset)
        start = record_pos + 1
    return hits


def patch_one(data: bytes, row: TblOverride, file_name: str) -> tuple[bytes, bool, str]:
    patched = bytearray(data)
    source = utf16le(row.source_text)
    if file_name == "tbl2.pak" and row.item_id is not None:
        candidates = find_tbl2_id_text(data, row.item_id, row.source_text)
        if len(candidates) != 1:
            return data, False, "stable_id_missing_or_ambiguous"
    elif row.offset is not None:
        candidates = [row.offset]
    else:
        candidates = find_all(data, source)
        if len(candidates) != 1:
            return data, False, "ambiguous_or_missing"
    for offset in candidates:
        if offset < 0 or offset + len(source) > len(patched):
            continue
        if bytes(patched[offset:offset + len(source)]) != source:
            continue
        if file_name == "tbl2.pak" and not tbl2_record_at(patched, offset, row.source_text):
            continue
        replacement = fixed_replacement(row.source_text, row.translation)
        patched[offset:offset + len(source)] = replacement
        return bytes(patched), True, "patched"
    return data, False, "source_mismatch_or_invalid_record"


def patch_tbl_bytes(
    data: bytes,
    rows: list[TblOverride],
    single_byte_encoding: str = "gbk",
    missing_rows: list[tuple[TblOverride, str]] | None = None,
) -> tuple[bytes, dict[str, int]]:
    original = bytes(data)
    patched = original
    stats = {
        "rows": len(rows),
        "changed": 0,
        "missing": 0,
        "relocated": 0,
        "normalized": 0,
        "ambiguous": 0,
        "space_padded": 0,
    }
    for row in rows:
        before = patched
        patched, ok, reason = patch_one(patched, row, row.file_name)
        if ok:
            stats["changed"] += 1
        else:
            stats["missing"] += 1
            if reason in {"ambiguous_or_missing", "stable_id_missing_or_ambiguous"}:
                stats["ambiguous"] += 1
            if missing_rows is not None:
                missing_rows.append((row, reason))
    return patched, stats


def tbl_path(source_dir: Path, file_name: str) -> Path:
    return source_dir / "pack" / file_name


def patch_tbl_file(
    source_dir: Path,
    out_pack_dir: Path,
    file_name: str,
    rows: list[TblOverride],
    single_byte_encoding: str = "gbk",
    progress=None,
) -> dict[str, int]:
    source = tbl_path(source_dir, file_name)
    if not source.is_file():
        raise PatchError(f"Missing source tbl file: {source}")
    data = source.read_bytes()
    file_rows = [row for row in rows if row.file_name == file_name]
    patched, stats = patch_tbl_bytes(data, file_rows, single_byte_encoding=single_byte_encoding)
    out_pack_dir.mkdir(parents=True, exist_ok=True)
    (out_pack_dir / file_name).write_bytes(patched)
    if progress is not None:
        progress.step(n=max(len(file_rows), 1))
    return stats


def patch_tbl_pack(
    source_dir: Path,
    out_pack_dir: Path,
    rows: list[TblOverride],
    single_byte_encoding: str = "gbk",
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for file_name in TBL_FILES:
        file_rows = [row for row in rows if row.file_name == file_name]
        if not file_rows and not tbl_path(source_dir, file_name).is_file():
            continue
        result[file_name] = patch_tbl_file(
            source_dir, out_pack_dir, file_name, rows, single_byte_encoding=single_byte_encoding
        )
    return result
