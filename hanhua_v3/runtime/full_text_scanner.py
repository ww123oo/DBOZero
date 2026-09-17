# -*- coding: utf-8 -*-
"""Read-only scanner for DBO localization resources."""
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
LANG0_ENTRY_RE = re.compile(rb"(?m)^([A-Za-z_][A-Za-z0-9_.-]*)[ \t]*=[ \t]*\"")
XML_ATTR_RE = re.compile(
    r"(?P<name>[A-Za-z_][\w:.-]*)\s*=\s*(?P<quote>[\"'])(?P<value>(?:\\.|(?! (?P=quote) ).)*) (?P=quote)",
    re.X,
)
XML_TEXT_RE = re.compile(r">(?P<value>[^<\r\n]{3,})<")
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
                text = raw.decode("ascii")
            except UnicodeDecodeError:
                text = raw.decode("ascii", "ignore")
            if text and not text.isdigit():
                yield start, text, len(raw)
        i = max(i + 1, start + 1)


def _decode_lang0(raw: bytes) -> str:
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("gbk", errors="replace")


def _detect_lang0_value_encoding(raw: bytes) -> str:
    for enc in ("utf-8", "gbk"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "gbk"


def _lang0_end(data: bytes, start: int) -> int:
    pos = start
    while True:
        end = data.find(b'"', pos)
        if end < 0:
            return -1
        if end + 1 < len(data) and data[end + 1] == ord('"'):
            pos = end + 2
            continue
        return end


def scan_lang0_entries(path: Path) -> list[tuple[int, str, str, int]]:
    raw = path.read_bytes()
    hits: list[tuple[int, str, str, int]] = []
    for match in LANG0_ENTRY_RE.finditer(raw):
        key = match.group(1).decode("ascii")
        start = match.end()
        end = _lang0_end(raw, start)
        if end < 0:
            continue
        value_raw = raw[start:end].replace(b'""', b'"')
        value = _decode_lang0(value_raw)
        if not value or value.isdigit():
            continue
        hits.append((start, key, value, end - start))
    return hits


def unquote_dat(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        body = value[1:-1]
        body = body.replace("\\\\", "\\").replace("\\\"", "\"").replace("\\'", "'")
        body = body.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
        return body
    return value


def _decode_text_resource(raw: bytes) -> tuple[str | None, str]:
    for enc in ("utf-8-sig", "utf-8", "gb18030", "utf-16le", "utf-16"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None, ""


def scan_dat_entries(path: Path) -> list[tuple[int, str, str, int, str]]:
    """Return byte offset, key, value, encoded length and source encoding."""
    raw = path.read_bytes()
    text, encoding = _decode_text_resource(raw)
    if text is None:
        return []
    hits: list[tuple[int, str, str, int, str]] = []
    for match in DAT_ENTRY_RE.finditer(text):
        value = unquote_dat(match.group(2))
        if not value or value.isdigit():
            continue
        byte_offset = len(text[:match.start(2)].encode(encoding))
        if encoding == "utf-8-sig" and raw.startswith(b"\xef\xbb\xbf"):
            byte_offset += 3
        byte_length = len(match.group(2).encode(encoding))
        key = match.group(1)
        hits.append((byte_offset, key, value, byte_length, encoding))
    return hits


def _xml_candidates(path: Path, display_name: str | None = None) -> list["Hit"]:
    """Discover human-readable XML/RDF attribute and element values."""
    raw = path.read_bytes()
    text, encoding = _decode_text_resource(raw)
    if text is None:
        return []
    shown = display_name or path.name

    def byte_offset(char_index: int) -> int:
        return len(text[:char_index].encode(encoding)) + (
            3 if encoding == "utf-8-sig" and raw.startswith(b"\xef\xbb\xbf") else 0
        )

    hits: list[Hit] = []
    seen: set[tuple[int, str]] = set()
    for match in XML_ATTR_RE.finditer(text):
        value = match.group("value")
        if not value.strip() or value.strip().isdigit() or not any(ch.isalpha() for ch in value):
            continue
        start = byte_offset(match.start("value"))
        key = (start, value)
        if key in seen:
            continue
        seen.add(key)
        hits.append(Hit(shown, start, encoding, value, confidence(shown, start, value, encoding), len(value.encode(encoding)), "xml_attribute", match.group("name")))
    for match in XML_TEXT_RE.finditer(text):
        value = match.group("value").strip()
        if not value or value.isdigit() or not any(ch.isalpha() for ch in value):
            continue
        leading = len(match.group("value")) - len(match.group("value").lstrip())
        start = byte_offset(match.start("value") + leading)
        key = (start, value)
        if key in seen:
            continue
        seen.add(key)
        hits.append(Hit(shown, start, encoding, value, confidence(shown, start, value, encoding), len(value.encode(encoding)), "xml_text", ""))
    return hits


def confidence(file_name: str, offset: int, text: str, encoding: str) -> str:
    score = 0
    if len(text) >= 4:
        score += 1
    if any(c.isalpha() for c in text):
        score += 1
    if CJK_RE.search(text):
        score += 2
    if Path(file_name).name.lower() in WANTED_PACKS:
        score += 2
    if encoding == "utf-16le":
        score += 1
    if Path(file_name).suffix.lower() == ".dat":
        score += 1
    if offset < 16 and Path(file_name).name.lower().startswith("tbl"):
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
    id: str = ""


def files_to_scan(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        name = p.name.lower()
        if name in WANTED_PACKS or p.suffix.lower() in RESOURCE_EXTENSIONS:
            yield p


def scan_tbl2_structured(path: Path, display_name: str | None = None) -> list[Hit]:
    """Discover the observed tbl2 record form and retain its stable numeric ID."""
    data = path.read_bytes()
    shown = display_name or path.name
    hits: list[Hit] = []
    for record_pos in range(0, len(data) - 7):
        item_id = int.from_bytes(data[record_pos:record_pos + 4], "little")
        if item_id == 0 or data[record_pos + 4] != 0:
            continue
        units = int.from_bytes(data[record_pos + 5:record_pos + 7], "little")
        if units < 1 or units > 512:
            continue
        text_start = record_pos + 7
        text_end = text_start + units * 2
        if text_end > len(data):
            continue
        raw = data[text_start:text_end]
        try:
            text = raw.decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if not text or not any(ch.isalpha() for ch in text) or not all(printable(ch) for ch in text):
            continue
        hits.append(Hit(shown, text_start, "utf-16le", text, confidence(shown, text_start, text, "utf-16le"), len(raw), "tbl2_record", str(item_id)))
    return hits


def _overlaps(offset: int, length: int, intervals: list[tuple[int, int]]) -> bool:
    end = offset + max(length, 1)
    return any(offset < other_end and end > other_start for other_start, other_end in intervals)


def scan_file(path: Path, display_name: str | None = None) -> list[Hit]:
    data = path.read_bytes()
    shown = display_name or path.name
    hits: list[Hit] = []

    if path.name.lower() == "lang0.pak":
        for off, key, text, size in scan_lang0_entries(path):
            value_raw = data[off : off + size].replace(b'""', b'"')
            enc = _detect_lang0_value_encoding(value_raw)
            hits.append(Hit(shown, off, enc, text, confidence(shown, off, text, enc), size, "lang0_entry", key))
    if path.suffix.lower() == ".dat":
        for off, key, text, enc_size, enc in scan_dat_entries(path):
            hits.append(Hit(shown, off, enc, text, confidence(shown, off, text, enc), enc_size, "dat_entry", key))
    if path.suffix.lower() in {".rdf", ".xml"}:
        hits.extend(_xml_candidates(path, shown))
    if path.name.lower() == "tbl2.pak":
        hits.extend(scan_tbl2_structured(path, shown))

    occupied = [(hit.offset, hit.offset + hit.byte_length) for hit in hits if hit.byte_length]
    for off, text, chars in scan_utf16(data):
        size = chars * 2
        if _overlaps(off, size, occupied):
            continue
        hit = Hit(shown, off, "utf-16le", text, confidence(shown, off, text, "utf-16le"), size, "utf16", "")
        hits.append(hit)
        occupied.append((off, off + size))
    for off, text, size in scan_single_byte(data):
        if _overlaps(off, size, occupied):
            continue
        hit = Hit(shown, off, "ascii", text, confidence(shown, off, text, "ascii"), size, "single_byte", "")
        hits.append(hit)
        occupied.append((off, off + size))

    unique: dict[tuple[int, str, str, str], Hit] = {}
    for hit in hits:
        unique[(hit.offset, hit.text, hit.kind, hit.id)] = hit
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
        relative = path.relative_to(args.root).as_posix()
        all_hits.extend(scan_file(path, relative))
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["file", "offset", "encoding", "byte_length", "confidence", "kind", "id", "source_text", "translation"])
        for hit in all_hits:
            if levels[hit.confidence] < levels[args.min_confidence]:
                continue
            writer.writerow([hit.file_name, f"0x{hit.offset:X}", hit.encoding, hit.byte_length, hit.confidence, hit.kind, hit.id, hit.text, ""])
    print(f"Scanned files: {len(files)}")
    print(f"Text candidates: {len(all_hits)}")
    print(f"Output: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
