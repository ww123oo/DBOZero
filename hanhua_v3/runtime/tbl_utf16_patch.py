# -*- coding: utf-8 -*-
"""Safe fixed-field patcher for DBO tbl0/tbl1/tbl2.

The patcher never inserts/deletes bytes.  It only replaces a UTF-16LE/GBK
string in an existing field and pads the remaining field with NUL bytes.
For tbl2 we additionally validate its observed record layout before writing.
"""
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

def tool_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def default_source_dir() -> Path:
    return tool_dir() / "src_file"

def dbo_root(source_dir: Path) -> Path:
    return source_dir / "DBOZero"

def tbl_path(source_dir: Path, file_name: str) -> Path:
    return dbo_root(source_dir) / "pack" / file_name

def parse_offset(value: str, row_no: int) -> int | None:
    value = value.strip()
    if value in ALL_OFFSETS:
        return None
    try:
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    except ValueError as exc:
        raise PatchError(f"Invalid offset at row {row_no}: {value}") from exc

def read_overrides(path: Path | None = None) -> list[TblOverride]:
    path = path or (tool_dir() / "tbl_overrides.tsv")
    if not path.exists():
        raise PatchError(f"Missing tbl overrides file: {path}")
    rows: list[TblOverride] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row_no, row in enumerate(csv.reader(handle, delimiter="\t"), 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            if row[0].strip().lower() == "file":
                continue
            if len(row) < 4:
                raise PatchError(f"Invalid tbl_overrides.tsv row {row_no}; need 4 columns")
            file_name = row[0].strip()
            if file_name not in TBL_FILES:
                raise PatchError(f"Unsupported tbl file at row {row_no}: {file_name}")
            if row[2] and row[3]:
                rows.append(TblOverride(file_name, parse_offset(row[1], row_no), row[2], row[3]))
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

def fixed_single_byte_replacement(source: bytes, translation: str, encoding: str = "gbk") -> bytes:
    try:
        replacement = translation.encode(encoding)
    except UnicodeEncodeError as exc:
        raise PatchError(f"Translation cannot be encoded as {encoding}: {translation!r}") from exc
    if len(replacement) > len(source):
        raise PatchError(f"Translation is too long for single-byte field: {translation!r}")
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
    """Validate the tbl2 record layout observed in the supplied client.

    Layout: uint32 id, uint8 type, uint16 little-endian UTF-16 code-unit
    length, followed immediately by UTF-16LE text.  The first record follows
    the same layout.  We deliberately reject an offset that is not a record
    field instead of guessing.
    """
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

def patch_one(data: bytes, row: TblOverride, file_name: str) -> tuple[bytes, bool, str]:
    patched = bytearray(data)
    source = utf16le(row.source_text)
    candidates: list[int]
    if row.offset is not None:
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

def patch_tbl_bytes(data: bytes, rows: list[TblOverride], single_byte_encoding: str = "gbk", missing_rows: list[tuple[TblOverride, str]] | None = None) -> tuple[bytes, dict[str, int]]:
    original = bytes(data)
    patched = original
    stats = {"rows": len(rows), "changed": 0, "missing": 0, "relocated": 0, "normalized": 0, "ambiguous": 0, "space_padded": 0}
    for row in rows:
        before = patched
        patched, ok, reason = patch_one(patched, row, row.file_name)
        if ok:
            stats["changed"] += 1
        else:
            stats["missing"] += 1
            if reason == "ambiguous_or_missing":
                stats["ambiguous"] += 1
            if missing_rows is not None:
                missing_rows.append((row, reason))
        if len(patched) != len(original):
            raise PatchError(f"Patch changed file size for {row.file_name}; refusing to write")
        if not ok and patched != before:
            raise PatchError("Internal patch error: failed patch mutated data")
    return patched, stats

def patch_tbl_pack(source_dir: Path, out_pack_dir: Path, rows: list[TblOverride], single_byte_encoding: str = "gbk") -> dict[str, dict[str, int]]:
    grouped = {name: [] for name in TBL_FILES}
    for row in rows:
        grouped[row.file_name].append(row)
    out_pack_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, dict[str, int]] = {}
    for file_name, file_rows in grouped.items():
        if not file_rows:
            continue
        source = tbl_path(source_dir, file_name)
        if not source.is_file():
            raise PatchError(f"Missing source tbl file: {source}")
        original = source.read_bytes()
        patched, values = patch_tbl_bytes(original, file_rows, single_byte_encoding)
        if len(original) != len(patched):
            raise PatchError(f"Size changed for {file_name}")
        (out_pack_dir / file_name).write_bytes(patched)
        stats[file_name] = values
    return stats

def command_plan(args: argparse.Namespace) -> int:
    rows = read_overrides(args.overrides)
    for file_name in TBL_FILES:
        file_rows = [r for r in rows if r.file_name == file_name]
        if not file_rows:
            continue
        source = tbl_path(args.source_dir.resolve(), file_name)
        if not source.is_file():
            raise PatchError(f"Missing source tbl file: {source}")
        _, stats = patch_tbl_bytes(source.read_bytes(), file_rows)
        print(f"{file_name}: rows={stats['rows']} would_change={stats['changed']} missing={stats['missing']} ambiguous={stats['ambiguous']}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DBO Zero safe tbl patcher")
    parser.add_argument("--source-dir", type=Path, default=default_source_dir())
    parser.add_argument("--overrides", type=Path, default=tool_dir() / "tbl_overrides.tsv")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return command_plan(args) if args.command == "plan" else 0
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
