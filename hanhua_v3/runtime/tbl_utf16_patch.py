# -*- coding: utf-8 -*-
"""
DBO Zero tbl0/tbl1 fixed-field patcher.

This patcher preserves file size and all unrelated bytes. UTF-16LE replacements
must fit inside the original UTF-16LE string field. Exact-offset ASCII fields are
also supported with GBK replacements. Unused bytes are padded with NUL characters
so later binary offsets do not move and UI text does not gain visible trailing
spaces.

NOTE: tbl2.pak is intentionally not patched. The upstream DBOZero implementation
also limits this patcher to tbl0.pak and tbl1.pak. Patching tbl2.pak can make the
client crash when the modified game files are used, so tbl2 remains byte-for-byte
original while the supported tables are localized.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


__all__ = [
    "ALL_OFFSETS",
    "PatchError",
    "TBL_FILES",
    "TblOverride",
    "encoded_text_bytes",
    "find_all",
    "fixed_replacement",
    "fixed_single_byte_replacement",
    "has_length_prefix",
    "inside_length_prefixed_field",
    "length_prefixed_offsets",
    "length_prefixed_source_variants",
    "main",
    "parse_offset",
    "tool_dir",
]

# Keep this in sync with the upstream DBOZero patcher. tbl2.pak is deliberately
# excluded because modifying it has been observed to crash the client.
TBL_FILES = ("tbl0.pak", "tbl1.pak")
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
        raise PatchError(f"Invalid tbl_overrides.tsv offset at row {row_no}: {value}") from exc


def read_overrides(path: Path | None) -> list[TblOverride]:
    if path is None:
        path = tool_dir() / "tbl_overrides.tsv"
    if not path.exists():
        raise PatchError(f"Missing tbl overrides file: {path}")

    rows: list[TblOverride] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            if len(row) < 4:
                raise PatchError(f"Invalid tbl_overrides.tsv row {row_no}; need file, id, source_text, translation")
            file_name = row[0].strip()
            if file_name.lower() == "file":
                continue
            if file_name not in TBL_FILES:
                raise PatchError(f"Unsupported tbl file at row {row_no}: {file_name}")
            source_text = row[2]
            translation = row[3]
            if not source_text or not translation:
                continue
            rows.append(TblOverride(file_name, parse_offset(row[1], row_no), source_text, translation))
    return rows


def utf16le(text: str, label: str) -> bytes:
    try:
        return text.encode("utf-16le")
    except UnicodeEncodeError as exc:
        raise PatchError(f"{label} cannot be encoded as UTF-16LE: {text}") from exc


def encoded_text_bytes(text: str, label: str, encoding: str) -> bytes:
    try:
        return text.encode(encoding)
    except UnicodeEncodeError as exc:
        raise PatchError(f"{label} cannot be encoded as {encoding}: {text}") from exc
