# -*- coding: utf-8 -*-
"""Read-only scanner for DBO text resources.

Scans lang0.pak, tbl0.pak, tbl1.pak, tbl2.pak and other resource files for
credible UTF-16LE/GBK/ASCII text. It writes a TSV inventory and NEVER modifies
the source files. This is the discovery stage for the full translation
pipeline; patchers can consume the offsets after the record structure has been
validated.
"""
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

TEXT_RE = re.compile(r"^[\x20-\x7e\t\r\n]+$")
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")

def printable(ch: str) -> bool:
    return ch in "\t\r\n" or (" " <= ch <= "~") or CJK_RE.search(ch) is not None

def scan_utf16(data: bytes, minimum: int = 3):
    i = 0
    n = len(data)
    while i + 2 <= n:
        start = i
        chars: list[str] = []
        while i + 2 <= n:
            unit = int.from_bytes(data[i:i+2], "little")
            try:
                ch = chr(unit)
            except ValueError:
                break
            if not printable(ch) or unit == 0:
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

def confidence(file_name: str, offset: int, text: str, encoding: str) -> str:
    score = 0
    if len(text) >= 4: score += 1
    if any(c.isalpha() for c in text): score += 1
    if CJK_RE.search(text): score += 2
    if file_name.lower() in {"lang0.pak", "tbl0.pak", "tbl1.pak", "tbl2.pak"}: score += 2
    if encoding == "utf-16le": score += 1
    if offset < 16 and file_name.lower().startswith("tbl"): score -= 1
    return "high" if score >= 5 else "medium" if score >= 3 else "low"

@dataclass
class Hit:
    file_name: str
    offset: int
    encoding: str
    text: str
    confidence: str
    byte_length: int

def files_to_scan(root: Path):
    wanted = {"lang0.pak", "tbl0.pak", "tbl1.pak", "tbl2.pak"}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        name = p.name.lower()
        if name in wanted or p.suffix.lower() in {".pak", ".rdf", ".xml", ".dat", ".bin"}:
            yield p

def scan_file(path: Path) -> list[Hit]:
    data = path.read_bytes()
    hits: list[Hit] = []
    for off, text, chars in scan_utf16(data):
        hits.append(Hit(path.name, off, "utf-16le", text, confidence(path.name, off, text, "utf-16le"), chars * 2))
    for off, text, size in scan_single_byte(data):
        hits.append(Hit(path.name, off, "gbk/ascii", text, confidence(path.name, off, text, "gbk/ascii"), size))
    hits.sort(key=lambda h: (h.offset, -h.byte_length))
    return hits

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan DBO resource files without modifying them")
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
        writer.writerow(["file", "offset", "encoding", "byte_length", "confidence", "source_text", "translation"])
        for hit in all_hits:
            if levels[hit.confidence] < levels[args.min_confidence]:
                continue
            writer.writerow([hit.file_name, f"0x{hit.offset:X}", hit.encoding, hit.byte_length, hit.confidence, hit.text, ""])
    print(f"Scanned files: {len(files)}")
    print(f"Text candidates: {len(all_hits)}")
    print(f"Output: {args.output.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
