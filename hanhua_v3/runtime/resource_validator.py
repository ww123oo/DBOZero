# -*- coding: utf-8 -*-
"""Deterministic validator for generated DBO localization resources.

The validator checks repository/toolchain invariants only. It never starts the
 game and never assumes in-game verification is available.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import lang0_gbk_patch as lang0
from . import tbl_utf16_patch as tbl
from .resource_writer import QueueRow

PAK_FILES = {"lang0.pak", "tbl0.pak", "tbl1.pak", "tbl2.pak"}


class ValidationError(RuntimeError):
    """Raised when a generated resource violates a deterministic invariant."""


@dataclass(frozen=True)
class ValidationSummary:
    files: int
    queued_rows: int
    validated_rows: int
    untouched_files: int


def _resolve_resource(root: Path, name: str) -> Path:
    normalized = name.replace("\\", "/").strip()
    direct = root / normalized
    if direct.is_file():
        return direct
    matches = [p for p in root.rglob(Path(normalized).name) if p.is_file()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValidationError(f"Resource not found: {name}")
    raise ValidationError(f"Resource name is ambiguous: {name}")


def _encode_text(text: str, encoding: str) -> bytes:
    normalized = (encoding or "utf-8").strip().lower().replace("_", "-")
    if normalized in {"utf8", "utf-8", "utf-8-sig"}:
        return text.encode("utf-8")
    if normalized in {"gbk", "gb18030", "gb2312", "gbk/ascii"}:
        return text.encode("gb18030" if normalized == "gb18030" else "gbk")
    if normalized in {"utf-16", "utf-16le", "utf16"}:
        return text.encode("utf-16le")
    return text.encode(encoding)


def _validate_lang0(data: bytes, row: QueueRow) -> None:
    if not row.locator or row.locator.lower().startswith("offset:"):
        raise ValidationError(f"lang0.pak row requires a key locator: {row.locator!r}")
    try:
        start = lang0.find_lang0_value_start(data, row.locator)
        if start < 0:
            raise ValidationError(f"lang0 key missing from output: {row.locator}")
        end = lang0.find_lang0_value_end(data, start, row.locator)
        actual = lang0.decode_lang0_value(lang0.unescape_lang0_value(data[start:end]))
    except lang0.PatchError as exc:
        raise ValidationError(str(exc)) from exc
    if actual != row.translation:
        raise ValidationError(
            f"lang0 translation mismatch for {row.locator}: "
            f"expected {row.translation!r}, got {actual!r}"
        )


def _tbl_override(row: QueueRow, file_name: str) -> tbl.TblOverride:
    locator = (row.locator or "").strip()
    if file_name == "tbl2.pak":
        if locator.lower().startswith("id:"):
            try:
                return tbl.TblOverride(
                    file_name,
                    None,
                    row.translation,
                    row.translation,
                    int(locator.split(":", 1)[1].strip(), 0),
                )
            except ValueError as exc:
                raise ValidationError(f"Invalid tbl2 stable ID: {locator!r}") from exc
        if row.kind == "tbl2_record":
            try:
                return tbl.TblOverride(
                    file_name, None, row.translation, row.translation, int(locator, 0)
                )
            except ValueError as exc:
                raise ValidationError(f"Invalid tbl2 record ID: {locator!r}") from exc

    try:
        offset = tbl.parse_offset(
            locator[7:] if locator.lower().startswith("offset:") else locator,
            0,
        )
    except tbl.PatchError as exc:
        raise ValidationError(str(exc)) from exc
    return tbl.TblOverride(file_name, offset, row.translation, row.translation)


def _validate_tbl(data: bytes, row: QueueRow, file_name: str) -> None:
    override = _tbl_override(row, file_name)
    _patched, stats = tbl.patch_tbl_bytes(data, [override])
    if stats["missing"]:
        raise ValidationError(
            f"{file_name} translation record could not be located in output: "
            f"{row.locator or '<no locator>'} / {row.translation!r}"
        )


def _escaped_dat_candidates(source: str, translation: str, encoding: str) -> list[tuple[bytes, bytes]]:
    enc = "gb18030" if encoding == "gb18030" else "utf-8"
    source_escaped = source.replace("\\", "\\\\").replace('"', '\\"')
    translation_escaped = translation.replace("\\", "\\\\").replace('"', '\\"')
    single_source = source.replace("\\", "\\\\").replace("'", "\\'")
    single_translation = translation.replace("\\", "\\\\").replace("'", "\\'")
    return [
        (
            f'"{source_escaped}"'.encode(enc),
            f'"{translation_escaped}"'.encode(enc),
        ),
        (
            f"'{single_source}'".encode(enc),
            f"'{single_translation}'".encode(enc),
        ),
    ]


def _validate_text_resource(data: bytes, row: QueueRow) -> None:
    file_name = row.file.replace("\\", "/").lower()
    if row.kind == "dat_entry" or file_name.endswith(".dat"):
        encoding = "gb18030" if row.encoding.lower() == "gb18030" else "utf-8"
        for _old, new in _escaped_dat_candidates(row.source, row.translation, encoding):
            if new in data:
                return
        raise ValidationError(
            f"DAT translation not found in output: {row.file} / {row.locator or '<no locator>'}"
        )

    try:
        needle = _encode_text(row.translation, row.encoding)
    except UnicodeEncodeError as exc:
        raise ValidationError(
            f"Translation cannot be encoded as {row.encoding or 'utf-8'}: {row.translation!r}"
        ) from exc
    if needle not in data:
        raise ValidationError(
            f"Translation bytes not found in output: {row.file} / {row.locator or '<no locator>'}"
        )


def validate_build(source_root: Path, output_root: Path, rows: list[QueueRow]) -> ValidationSummary:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    if not source_root.is_dir():
        raise ValidationError(f"Source root not found: {source_root}")
    if not output_root.is_dir():
        raise ValidationError(f"Output root not found: {output_root}")

    source_files = {
        p.relative_to(source_root).as_posix(): p
        for p in source_root.rglob("*")
        if p.is_file()
    }
    output_files = {
        p.relative_to(output_root).as_posix(): p
        for p in output_root.rglob("*")
        if p.is_file()
    }
    if source_files.keys() != output_files.keys():
        missing = sorted(source_files.keys() - output_files.keys())
        extra = sorted(output_files.keys() - source_files.keys())
        raise ValidationError(f"Output tree mismatch: missing={missing[:8]}, extra={extra[:8]}")

    for relative, source in source_files.items():
        output = output_files[relative]
        if Path(relative).name.lower() in PAK_FILES and source.stat().st_size != output.stat().st_size:
            raise ValidationError(
                f"Fixed-size PAK changed size: {relative} "
                f"({source.stat().st_size} -> {output.stat().st_size})"
            )

    grouped: dict[str, list[QueueRow]] = {}
    for row in rows:
        grouped.setdefault(row.file.replace("\\", "/").lower(), []).append(row)

    validated = 0
    touched_files = 0
    for requested_name, file_rows in sorted(grouped.items()):
        source_path = _resolve_resource(source_root, requested_name)
        output_path = _resolve_resource(output_root, requested_name)
        if source_path.name.lower() in PAK_FILES:
            touched_files += 1
            original = output_path.read_bytes()
            name = source_path.name.lower()
            for row in file_rows:
                if name == "lang0.pak":
                    _validate_lang0(original, row)
                else:
                    _validate_tbl(original, row, name)
                validated += 1
        else:
            touched_files += 1
            original = output_path.read_bytes()
            for row in file_rows:
                _validate_text_resource(original, row)
                validated += 1

    untouched = len(source_files) - touched_files
    return ValidationSummary(
        files=len(output_files),
        queued_rows=len(rows),
        validated_rows=validated,
        untouched_files=max(untouched, 0),
    )
