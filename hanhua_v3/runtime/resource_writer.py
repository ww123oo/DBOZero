# -*- coding: utf-8 -*-
"""Safe writer for the DBO localization resource set.

The scanner discovers text; ``data/new_translations.tsv`` is the active work
queue.  This writer applies only rows with a non-empty translation and keeps
resource-specific safety rules separate:

* lang0.pak -> key/value GBK patcher
* tbl0/tbl1/tbl2.pak -> fixed UTF-16 field patcher
* XML/RDF/DAT -> exact byte-range replacement, applied from high offset to low

*.bin is deliberately rejected and never touched.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from . import lang0_gbk_patch as lang0
from . import tbl_utf16_patch as tbl

RESOURCE_EXTENSIONS = {".rdf", ".xml", ".dat"}
TBL_FILES = {"tbl0.pak", "tbl1.pak", "tbl2.pak"}
PAK_FILES = {"lang0.pak", *TBL_FILES}


class WriteError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueueRow:
    file: str
    locator: str
    source: str
    translation: str
    encoding: str
    kind: str


def read_queue(path: Path) -> list[QueueRow]:
    if not path.is_file():
        raise WriteError(f"Missing translation queue: {path}")
    rows: list[QueueRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row_no, row in enumerate(csv.DictReader(handle, delimiter="\t"), 2):
            source = (row.get("source_text") or "").strip()
            translation = (row.get("zh_cn") or "").strip()
            if not source or not translation:
                continue
            status = (row.get("status") or "").strip().lower()
            if status in {"skip", "ignored", "disabled"}:
                continue
            file_name = (row.get("file") or "").strip()
            if not file_name:
                continue
            rows.append(
                QueueRow(
                    file=file_name,
                    locator=(row.get("id") or "").strip(),
                    source=source,
                    translation=translation,
                    encoding=(row.get("encoding") or "").strip().lower(),
                    kind=(row.get("kind") or "").strip().lower(),
                )
            )
    return rows


def _find_resource(root: Path, name: str) -> Path:
    wanted = name.replace("\\", "/").strip()
    direct = root / wanted
    if direct.is_file():
        return direct
    matches = [p for p in root.rglob(Path(wanted).name) if p.is_file()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise WriteError(f"Resource not found: {name}")
    raise WriteError(f"Resource name is ambiguous: {name}")


def _encode(text: str, encoding: str) -> bytes:
    if encoding in {"utf-16le", "utf16", "utf-16"}:
        return text.encode("utf-16le")
    if encoding.startswith("gbk") or encoding in {"gb18030", "gb2312"}:
        return text.encode("gb18030" if encoding == "gb18030" else "gbk")
    if encoding in {"utf-8", "utf-8-sig", "ascii", ""}:
        return text.encode("utf-8")
    return text.encode(encoding)


def _offset(locator: str) -> int:
    value = locator.strip()
    if value.lower().startswith("offset:"):
        value = value.split(":", 1)[1]
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value)


def _patch_text_rows(data: bytes, rows: list[QueueRow]) -> tuple[bytes, int]:
    """Patch XML/RDF and plain DAT byte ranges without relying on mutable offsets."""
    patched = bytearray(data)
    operations: list[tuple[int, bytes, bytes, QueueRow]] = []
    for row in rows:
        try:
            offset = _offset(row.locator)
        except ValueError as exc:
            raise WriteError(f"Non-offset locator cannot patch generic resource: {row.locator!r}") from exc
        encoding = row.encoding
        if row.kind == "dat_entry":
            # Scanner offset points at the quoted DAT value (including the quote).
            enc = "gb18030" if encoding == "gb18030" else "utf-8"
            quoted_source = ("\"" + row.source.replace("\"", "\\\"") + "\"").encode(enc)
            raw_translation = ("\"" + row.translation.replace("\"", "\\\"") + "\"").encode(enc)
            old = data[offset:offset + len(quoted_source)]
            if old != quoted_source:
                # Some DAT files use single quotes; accept that exact form too.
                quoted_source = ("'" + row.source.replace("'", "\\'") + "'").encode(enc)
                raw_translation = ("'" + row.translation.replace("'", "\\'") + "'").encode(enc)
                old = data[offset:offset + len(quoted_source)]
            if old != quoted_source:
                raise WriteError(f"DAT source mismatch at 0x{offset:X}: {row.source!r}")
            operations.append((offset, old, raw_translation, row))
            continue

        old = _encode(row.source, encoding)
        new = _encode(row.translation, encoding)
        if data[offset:offset + len(old)] != old:
            raise WriteError(f"Source mismatch at 0x{offset:X} in {row.file}")
        operations.append((offset, old, new, row))

    changed = 0
    for offset, old, new, row in sorted(operations, key=lambda item: item[0], reverse=True):
        if patched[offset:offset + len(old)] != old:
            raise WriteError(f"Overlapping/invalid patch at 0x{offset:X} in {row.file}")
        patched[offset:offset + len(old)] = new
        changed += 1
    return bytes(patched), changed


def _write_one(path: Path, rows: list[QueueRow], output_root: Path) -> tuple[Path, int]:
    name = path.name.lower()
    output = output_root / path.relative_to(output_root.parent) if False else output_root / path.name
    original = path.read_bytes()

    if name == "lang0.pak":
        keyed: list[tuple[str, str]] = []
        skipped = 0
        for row in rows:
            if not row.locator or row.locator.lower().startswith("offset:"):
                skipped += 1
                continue
            keyed.append((row.locator, row.translation))
        if skipped:
            raise WriteError(f"lang0.pak has {skipped} rows without a key; scanner must provide lang0 keys")
        patched, stats = lang0.patch_lang0_bytes(original, keyed)
        changed = stats["changed"]
    elif name in TBL_FILES:
        overrides: list[tbl.TblOverride] = []
        for row in rows:
            try:
                off = _offset(row.locator) if row.locator else None
            except ValueError as exc:
                raise WriteError(f"Invalid tbl locator: {row.locator!r}") from exc
            overrides.append(tbl.TblOverride(name, off, row.source, row.translation))
        patched, stats = tbl.patch_tbl_bytes(original, overrides)
        changed = stats["changed"]
        if stats["missing"]:
            raise WriteError(f"{name}: {stats['missing']} translation rows did not match the original resource")
    elif path.suffix.lower() in RESOURCE_EXTENSIONS:
        patched, changed = _patch_text_rows(original, rows)
    else:
        raise WriteError(f"Unsupported resource type: {path}")

    if len(patched) != len(original) and name in PAK_FILES:
        raise WriteError(f"Fixed-size resource changed size: {name}")
    output_root.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)
    return output, changed


def write_queue(queue: Path, source_root: Path, output_root: Path) -> dict[str, int]:
    rows = read_queue(queue)
    if any(r.file.lower().endswith(".bin") for r in rows):
        raise WriteError(".bin is not a supported translation target and will never be written")

    grouped: dict[str, list[QueueRow]] = {}
    for row in rows:
        grouped.setdefault(row.file.replace("\\", "/").lower(), []).append(row)

    result: dict[str, int] = {}
    for key, file_rows in sorted(grouped.items()):
        path = _find_resource(source_root, key)
        output, changed = _write_one(path, file_rows, output_root)
        result[output.name] = changed
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write translated DBO localization resources safely")
    parser.add_argument("queue", type=Path, nargs="?", default=Path("data/new_translations.tsv"))
    parser.add_argument("--source-root", type=Path, required=True, help="Directory containing the original game resources")
    parser.add_argument("--output-root", type=Path, required=True, help="Directory for patched resources")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.dry_run:
        rows = read_queue(args.queue)
        print(f"translated rows: {len(rows)}")
        print("dry-run: no resource files were written")
        return 0

    stats = write_queue(args.queue, args.source_root, args.output_root)
    for name, changed in stats.items():
        print(f"{name}: changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
