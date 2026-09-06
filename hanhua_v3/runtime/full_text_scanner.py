# -*- coding: utf-8 -*-
"""Read-only scanner for DBO localization resources.

Supported discovery targets:
  lang0.pak, tbl0.pak, tbl1.pak, tbl2.pak, *.rdf, *.xml, *.dat

*.bin is intentionally excluded.  This module only discovers candidates; it
never modifies game resources.
"""
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")
DAT_ENTRY_RE = re.compile(
    r"(?m)^\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|[^\r\n]+)\s*$"
)
RESOURCE_EXTENSIONS = {".pak", ".rdf", ".xml", ".dat"}
WANTED_PACKS = {"lang0.pak", "tbl0.pak", "tbl1.pak", "tbl2.pak"}


def printable(ch: str) -> bool:
    return ch in "\t\r\n" or (" " <= ch <= "~") or CJK_RE.search(ch) is not None


def scan_utf16(data: bytes, minimum: int = 3):
    i = 0
    n = len(data)
    while i + 2 <= n:
        start = i
        chars: list[str] = []
        while i + 2 <= n:
            unit = int.from_bytes(data[i:i + 2], "little")
            if unit == 0 or unit > 0xFFFF:
                break
            ch = chr(unit)
            if not printable(ch):
                break
            chars.append(ch)
            i += 2
        if len(chars) >= minimum:
            yield start, "".join(chars), len(chars)
        i = max(i + 2, start + 2)


def scan_single_byte(data: bytes, minimum: int = 4):
    i = 0
    n = len(data)
    while i < n:
        start = i
        while i < n and (32 <= data[i] <= 126 or data[i] in (9, 10, 13)):
            i += 1
        if i - start >= minimum:
            raw = data[start:i]
            try:
                text = raw.decode("gbk")
            except UnicodeDecodeError:
                text = raw.decode("ascii", "ignore")
            if text and not text.isdigit():
                yield start, text, len(raw)
        i = max(i + 1, start + 1)


def unquote_dat(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        body = value[1:-1]
        return bytes(body, "utf-8").decode("unicode_escape")
    return value


def scan_dat_entries(path: Path) -> list[tuple[int, str, str, int]]:
    """Scan DBO DAT key=value resources without changing their syntax."""
    raw = path.read_bytes()
    text = None
    encoding = "utf-8"
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return []
    hits: list[tuple[int, str, str, int]] = []
    for match in DAT_ENTRY_RE.finditer(text):
        value = unquote_dat(match.group(2))
        if not value or value.isdigit():
            continue
        # Character offset is converted to a byte offset in the source file.
        byte_offset = len(text[:match.start(2)].encode(encoding))
        byte_length = len(match.group(2).encode(encoding))
        hits.append((byte_offset, value, encoding, byte_length))
    return hits


def confidence(file_name: str, offset: int, text: str, encoding: str) -> str:
    score = 0
    if len(text) >= 4:
        score += 1
    if any(c.isalpha() for c in text):
        score += 1
    if CJK_RE.search(text):
        score += 2
    if file_name.lower() in WANTED_PACKS:
        score += 2
    if encoding == "utf-16le":
        score += 1
    if file_name.lower().endswith(".dat"):
        score += 1
    if offset < 16 and file_name.lower().startswith("tbl"):
        score -= 1
    return "high" if score >= 5 else "medium" if score >= 3 else "low"


@dataclass
class Hit:
    file_name: str
    offset: int
    encoding: str
    text: str
    confidence: str
    byte_length: int
    kind: str = "raw"


def files_to_scan(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        name = p.name.lower()
        if name in WANTED_PACKS or p.suffix.lower() in RESOURCE_EXTENSIONS:
            yield p


def scan_file(path: Path) -> list[Hit]:
    data = path.read_bytes()
    hits: list[Hit] = []
    if path.suffix.lower() == ".dat":
        for off, text, enc, size in scan_dat_entries(path):
            hits.append(Hit(path.name, off, enc, text, confidence(path.name, off, text, enc), size, "dat_entry"))
    for off, text, chars in scan_utf16(data):
        hits.append(Hit(path.name, off, "utf-16le", text, confidence(path.name, off, text, "utf-16le"), chars * 2, "utf16"))
    for off, text, size in scan_single_byte(data):
        hits.append(Hit(path.name, off, "gbk/ascii", text, confidence(path.name, off, text, "gbk/ascii"), size, "single_byte"))
    # DAT entries are authoritative structured hits; remove exact duplicates
    # produced by the generic scanners.
    unique: dict[tuple[int, str, str], Hit] = {}
    for hit in hits:
        unique[(hit.offset, hit.text, hit.kind if hit.kind == "dat_entry" else "raw")] = hit
    return sorted(unique.values(), key=lambda h: (h.offset, -h.byte_length, h.kind))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan DBO translation resources without modifying them")
    parser.add_argument("root", type=Path, help="DBO root/resource directory to scan")
    parser.add_argument("-o", "--output", type=Path, default=Path("translation_scan.tsv"))
    parser.add_argument("--min-confidence", choices=("low", "medium", "high"), default="medium")
    args = parser.parse_args(argv)
    levels = {"low": 0, "medium": 1, "high": 2}
    all_hits: list[Hit] = []
    files = list(files_to_scan(args.root))
    for path in files:
        all_hits.extend(scan_file(path))
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["file", "offset", "encoding", "byte_length", "confidence", "kind", "source_text", "translation"])
        for hit in all_hits:
            if levels[hit.confidence] < levels[args.min_confidence]:
                continue
            writer.writerow([hit.file_name, f"0x{hit.offset:X}", hit.encoding, hit.byte_length, hit.confidence, hit.kind, hit.text, ""])
    print(f"Scanned files: {len(files)}")
    print(f"Text candidates: {len(all_hits)}")
    print(f"Output: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
