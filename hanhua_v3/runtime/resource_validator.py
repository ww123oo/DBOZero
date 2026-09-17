# -*- coding: utf-8 -*-
"""Deterministic validator for generated DBO localization resources.

The validator checks toolchain and resource-format invariants only. It never
starts the game and never requires in-game verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import lang0_gbk_patch as lang0
from . import tbl_utf16_patch as tbl
from .resource_writer import QueueRow, _patch_generic_pak_rows, _patch_text_rows


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
    wanted = "/".join(Path(normalized).parts).casefold()
    casefold_matches = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.relative_to(root).as_posix().casefold() == wanted
    ]
    if len(casefold_matches) == 1:
        return casefold_matches[0]
    matches = [p for p in root.rglob(Path(normalized).name) if p.is_file()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValidationError(f"Resource not found: {name}")
    raise ValidationError(f"Resource name is ambiguous: {name}")


def _validate_lang0(source: bytes, output: bytes, rows: list[QueueRow]) -> None:
    # Field-level semantic check catches malformed key/value escaping.
    for row in rows:
        if not row.locator or row.locator.lower().startswith("offset:"):
            raise ValidationError(f"lang0.pak row requires a key locator: {row.locator!r}")
        try:
            start = lang0.find_lang0_value_start(output, row.locator)
            if start < 0:
                raise ValidationError(f"lang0 key missing from output: {row.locator}")
            end = lang0.find_lang0_value_end(output, start, row.locator)
            actual = lang0.decode_lang0_value(lang0.unescape_lang0_value(output[start:end]))
        except lang0.PatchError as exc:
            raise ValidationError(str(exc)) from exc
        if actual != row.translation:
            raise ValidationError(
                f"lang0 translation mismatch for {row.locator}: "
                f"expected {row.translation!r}, got {actual!r}"
            )

    # Strong check: rebuild from the pristine source using the only encodings
    # supported by the current lang0 writer and require byte-for-byte equality.
    expected_variants: list[tuple[str, bytes]] = []
    for encoding in ("utf-8", "gbk"):
        try:
            expected, _stats = lang0.patch_lang0_bytes(
                source,
                [(row.locator, row.translation) for row in rows],
                encoding=encoding,
            )
        except (lang0.PatchError, UnicodeEncodeError):
            continue
        expected_variants.append((encoding, expected))
    if not any(expected == output for _encoding, expected in expected_variants):
        raise ValidationError("lang0 output differs from deterministic patch result")


def _tbl2_id(locator: str, kind: str) -> int:
    value = locator.strip()
    try:
        if value.lower().startswith("id:"):
            return int(value.split(":", 1)[1].strip(), 0)
        if kind == "tbl2_record":
            return int(value, 0)
    except ValueError as exc:
        raise ValidationError(f"Invalid tbl2 stable ID: {locator!r}") from exc
    raise ValidationError("tbl2.pak rows must use a stable id:N locator")


def _validate_tbl2(data: bytes, source: bytes, rows: list[QueueRow]) -> None:
    overrides: list[tbl.TblOverride] = []
    for row in rows:
        item_id = _tbl2_id(row.locator, row.kind)
        try:
            translated = row.translation.encode("utf-16le")
            original = row.source.encode("utf-16le")
        except UnicodeEncodeError as exc:
            raise ValidationError(f"tbl2 text cannot be encoded as UTF-16LE: {row.source!r}") from exc
        if len(translated) > len(original):
            raise ValidationError(
                f"tbl2 translation is longer than its fixed field: {row.source!r} -> {row.translation!r}"
            )

        id_bytes = item_id.to_bytes(4, "little", signed=False)
        expected_field = translated + b"\x00" * (len(original) - len(translated))
        hits: list[int] = []
        start = 0
        while True:
            record_pos = data.find(id_bytes, start)
            if record_pos < 0:
                break
            if record_pos + 7 > len(data):
                break
            if data[record_pos + 4] != 0:
                start = record_pos + 1
                continue
            units = int.from_bytes(data[record_pos + 5 : record_pos + 7], "little")
            if units < 1 or record_pos + 7 + units * 2 > len(data):
                start = record_pos + 1
                continue
            field = data[record_pos + 7 : record_pos + 7 + units * 2]
            if len(field) == len(original) and field == expected_field:
                hits.append(record_pos)
            start = record_pos + 1
        if len(hits) != 1:
            raise ValidationError(
                f"tbl2 output record is missing or ambiguous: id:{item_id}, "
                f"expected_text={row.translation!r}, matches={len(hits)}"
            )
        overrides.append(tbl.TblOverride("tbl2.pak", None, row.source, row.translation, item_id))

    try:
        expected, _stats = tbl.patch_tbl_bytes(source, overrides)
    except (tbl.PatchError, ValueError) as exc:
        raise ValidationError(f"tbl2 reconstruction failed: {exc}") from exc
    if expected != data:
        raise ValidationError("tbl2 output differs from deterministic patch result")


def _validate_tbl_fixed_field(data: bytes, row: QueueRow, file_name: str) -> None:
    locator = (row.locator or "").strip()
    if not locator or locator.lower().startswith("id:"):
        raise ValidationError(f"{file_name} row requires an offset locator")
    try:
        offset = tbl.parse_offset(
            locator[7:] if locator.lower().startswith("offset:") else locator,
            0,
        )
        if offset is None:
            raise ValidationError(f"{file_name} does not permit wildcard locators")
        expected = tbl.fixed_replacement(row.source, row.translation)
    except tbl.PatchError as exc:
        raise ValidationError(str(exc)) from exc
    if data[offset : offset + len(expected)] != expected:
        raise ValidationError(
            f"{file_name} output field mismatch at 0x{offset:X}: {row.translation!r}"
        )


def _validate_generic_pak(data: bytes, source: bytes, rows: list[QueueRow], file_name: str) -> None:
    try:
        expected, _changed = _patch_generic_pak_rows(source, rows, file_name)
    except Exception as exc:
        raise ValidationError(f"Invalid {file_name} translation rows: {exc}") from exc
    if expected != data:
        raise ValidationError(f"{file_name} output differs from deterministic fixed-field patch result")


def _validate_text_resource(data: bytes, source: bytes, rows: list[QueueRow]) -> None:
    try:
        expected, _changed = _patch_text_rows(source, rows, rows[0].file.replace("\\", "/").lower())
    except Exception as exc:
        raise ValidationError(f"Text resource reconstruction failed: {exc}") from exc
    if expected != data:
        raise ValidationError(f"{rows[0].file} output differs from deterministic text patch result")


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

    for relative, source_path in source_files.items():
        output_path = output_files[relative]
        if Path(relative).suffix.lower() == ".pak" and source_path.stat().st_size != output_path.stat().st_size:
            raise ValidationError(
                f"Fixed-size PAK changed size: {relative} "
                f"({source_path.stat().st_size} -> {output_path.stat().st_size})"
            )

    grouped: dict[str, list[QueueRow]] = {}
    for row in rows:
        grouped.setdefault(row.file.replace("\\", "/").lower(), []).append(row)

    validated = 0
    touched_files: set[str] = set()
    for requested_name, file_rows in sorted(grouped.items()):
        source_path = _resolve_resource(source_root, requested_name)
        output_path = _resolve_resource(output_root, requested_name)
        name = source_path.name.lower()
        touched_files.add(requested_name)
        source_data = source_path.read_bytes()
        output_data = output_path.read_bytes()

        if name == "lang0.pak":
            _validate_lang0(source_data, output_data, file_rows)
        elif name == "tbl2.pak":
            _validate_tbl2(output_data, source_data, file_rows)
        elif name in {"tbl0.pak", "tbl1.pak"}:
            for row in file_rows:
                _validate_tbl_fixed_field(output_data, row, name)
        elif name.endswith(".pak"):
            _validate_generic_pak(output_data, source_data, file_rows, name)
        else:
            _validate_text_resource(output_data, source_data, file_rows)
        validated += len(file_rows)

    return ValidationSummary(
        files=len(output_files),
        queued_rows=len(rows),
        validated_rows=validated,
        untouched_files=max(len(source_files) - len(touched_files), 0),
    )
