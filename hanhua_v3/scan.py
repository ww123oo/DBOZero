from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .policy import is_tbl_internal_token
from .runtime import install_hanhua


__all__ = [
    "CatalogEntry",
    "LegacyCandidate",
    "TranslationRow",
    "load_active_translations",
    "main",
    "scan_current_catalog",
]

ROOT = Path(__file__).resolve().parents[1]


TAIWAN_FILES = (
    "local_data.dat",
    "local_sync_data.dat",
    "table_text_all_data.rdf",
    "table_quest_text_data.rdf",
)

LEGACY_MANUAL_FILES = (
    "overrides.tsv",
    "lang0_overrides.tsv",
    "tbl_overrides.tsv",
)

LEGACY_CANDIDATE_FILES = (
    "untranslated.tsv",
    "taiwan_candidates.tsv",
    "taiwan_translated.tsv",
    "lang0_candidates.tsv",
    "tbl_candidates.tsv",
)

LOCAL_DATA_SHORT_UI_MAX_CHARS = 24
LOCAL_DATA_MESSAGE_KEY_RE = re.compile(
    r"(?:_MSG|MESSAGE|NOTICE|NOTIFY|INFO|GUIDE|HTML|DESC|DESCRIPTION|TOOLTIP|CONFIRM|ASK|FAIL|FAILED|SUCCESS|"
    r"ERROR|WARNING|ALERT|MAIL|COMMERCIAL|LOBBY|MARKET|FRIEND|QUEST|TUTORIAL|HELP|SYSTEM)"
)
LOCAL_DATA_RICH_TEXT_RE = re.compile(r"\[(?:/?font|br|align|metatag)\b", re.IGNORECASE)
PRINTF_RE = re.compile(r"%(?:\d+\$)?[+#0\- ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?[diuoxXfFeEgGaAcspn%]")


@dataclass(frozen=True)
class CatalogEntry:
    surface: str
    file_name: str
    item_id: str
    source_text: str
    source_origin: str
    location: str = ""
    encoding: str = ""
    note: str = ""


@dataclass(frozen=True)
class TranslationRow:
    surface: str
    file_name: str
    item_id: str
    source_text: str
    translation: str
    status: str
    legacy_source: str
    row_no: int
    note: str = ""


@dataclass(frozen=True)
class LegacyCandidate:
    surface: str
    file_name: str
    item_id: str
    source_text: str
    translation: str
    legacy_source: str
    row_no: int


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_root(source_dir: Path) -> Path:
    resolved = source_dir.resolve()
    if (resolved / "DBOZero").is_dir():
        return resolved / "DBOZero"
    if resolved.name.lower() == "dbozero":
        return resolved
    raise SystemExit(f"Invalid source dir: {source_dir}. Expected src_file or DBOZero.")


def language_dir(dbozero: Path) -> Path:
    return dbozero / "localize" / "Taiwan" / "language"


def pack_dir(dbozero: Path) -> Path:
    return dbozero / "pack"


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="surrogatepass")).hexdigest()


def short_hash(text: str) -> str:
    return sha1_text(text)[:12]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def has_cjk(text: str) -> bool:
    return any(
        "\u3400" <= ch <= "\u4dbf"
        or "\u4e00" <= ch <= "\u9fff"
        or "\uf900" <= ch <= "\ufaff"
        for ch in text
    )


def printf_specs(text: str) -> list[str]:
    return [spec for spec in PRINTF_RE.findall(text) if spec != "%%"]


def is_rich_or_multiline_text(text: str) -> bool:
    return bool(LOCAL_DATA_RICH_TEXT_RE.search(text) or "\n" in text or "\r" in text or "\\n" in text)


def is_message_like_key(item_id: str) -> bool:
    return bool(LOCAL_DATA_MESSAGE_KEY_RE.search(item_id.upper()))


def is_short_local_data_ui_reference(entry: CatalogEntry, translation: str) -> bool:
    text = translation
    if entry.surface != "lang0" or entry.file_name != "lang0.pak":
        return False
    if entry.source_text != entry.source_text.strip() and not entry.item_id.upper().startswith("DST_STATS_"):
        return False
    if text != text.strip():
        return False
    if not text or not has_cjk(text):
        return False
    if len(text) > LOCAL_DATA_SHORT_UI_MAX_CHARS:
        return False
    if is_message_like_key(entry.item_id) and not entry.item_id.upper().startswith("DST_STATS_"):
        return False
    if is_rich_or_multiline_text(entry.source_text) or is_rich_or_multiline_text(text):
        return False
    if printf_specs(entry.source_text) != printf_specs(text):
        return False
    return True


def looks_like_translation_candidate(text: str) -> bool:
    stripped = text.strip()
    if is_noise_text(stripped):
        return False
    if has_cjk(stripped):
        return False
    return re.search(r"[A-Za-z]", stripped) is not None


def is_noise_text(text: str) -> bool:
    stripped = normalize_text(text)
    if not stripped or len(stripped) <= 2:
        return True
    if stripped in {"@", "-", "_", "none", "null"}:
        return True
    if re.fullmatch(r"[\W_]+", stripped):
        return True
    if re.fullmatch(r"[\d\W_]+", stripped):
        return True
    if re.fullmatch(r"\[metatag\s*=\s*\d+\]\d*", stripped):
        return True
    if re.fullmatch(r"\[[a-z0-9_ -]+\]\d*", stripped):
        return True
    if re.fullmatch(r"[a-z]\d+[a-z0-9!?'+-]*", stripped):
        return True
    return False


def read_u32(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos : pos + 4], "little")


def read_u16(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos : pos + 2], "little")


def decode_best_effort(data: bytes, encodings: Iterable[str]) -> tuple[str, str]:
    for encoding in encodings:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    encoding = next(iter(encodings), "utf-8")
    return data.decode(encoding, errors="replace"), f"{encoding}-replace"


def read_kv_dat(path: Path) -> list[tuple[str, str]]:
    text, _encoding = decode_best_effort(path.read_bytes(), ("gbk", "utf-8"))
    rows: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("//", "#")) or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.startswith('"'):
            value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
            value = value.replace('""', '"')
        else:
            value = value.rstrip('"').replace('"', "")
        rows.append((key, value))
    return rows


def parse_lang0_pack(path: Path) -> list[tuple[str, str]]:
    text, _encoding = decode_best_effort(path.read_bytes(), ("utf-8", "gbk"))
    rows: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("//", "#")) or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not re.fullmatch(r"[A-Za-z0-9_]+", key):
            continue
        if value.startswith('"'):
            value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
            value = value.replace('""', '"')
        rows.append((key, value))
    return rows


def scan_kv_taiwan(dbozero: Path, file_name: str) -> list[CatalogEntry]:
    path = language_dir(dbozero) / file_name
    rows: list[CatalogEntry] = []
    for key, value in read_kv_dat(path):
        rows.append(
            CatalogEntry(
                surface="taiwan",
                file_name=file_name,
                item_id=key,
                source_text=value,
                source_origin="current_source",
                location=f"localize/Taiwan/language/{file_name}:{key}",
                encoding="gbk",
                note="taiwan source is reference text, not primary truth",
            )
        )
    return rows


def scan_table_text_all(dbozero: Path) -> list[CatalogEntry]:
    file_name = "table_text_all_data.rdf"
    path = language_dir(dbozero) / file_name
    data = path.read_bytes()
    pos = 0
    rows: list[CatalogEntry] = []
    block_index = 0
    while pos < len(data):
        if pos + 9 > len(data):
            raise SystemExit(f"Invalid {file_name}: short block header at {pos}")
        table_id = read_u32(data, pos)
        block_size = read_u32(data, pos + 4)
        block_end = pos + 8 + block_size
        if block_end > len(data):
            raise SystemExit(f"Invalid {file_name}: block {block_index} exceeds file size")
        cols = data[pos + 8]
        pos += 9
        while pos < block_end:
            if pos + 4 > block_end:
                raise SystemExit(f"Invalid {file_name}: short record id in block {block_index}")
            key = read_u32(data, pos)
            pos += 4
            for col in range(cols):
                if pos + 2 > block_end:
                    raise SystemExit(f"Invalid {file_name}: short string length in block {block_index}")
                length = read_u16(data, pos)
                pos += 2
                raw = data[pos : pos + length * 2]
                pos += length * 2
                if len(raw) != length * 2:
                    raise SystemExit(f"Invalid {file_name}: short UTF-16LE text")
                text = raw.decode("utf-16le")
                item_id = f"{table_id}:{key}:{col}"
                rows.append(
                    CatalogEntry(
                        surface="taiwan",
                        file_name=file_name,
                        item_id=item_id,
                        source_text=text,
                        source_origin="current_source",
                        location=f"localize/Taiwan/language/{file_name}:{item_id}",
                        encoding="utf-16le",
                        note="taiwan rdf source is reference text, not primary truth",
                    )
                )
        block_index += 1
    return rows


def scan_table_quest(dbozero: Path) -> list[CatalogEntry]:
    file_name = "table_quest_text_data.rdf"
    path = language_dir(dbozero) / file_name
    data = path.read_bytes()
    if not data:
        raise SystemExit(f"Invalid {file_name}: empty file")
    pos = 1
    rows: list[CatalogEntry] = []
    while pos < len(data):
        if pos + 6 > len(data):
            raise SystemExit(f"Invalid {file_name}: short record at {pos}")
        key = read_u32(data, pos)
        pos += 4
        length = read_u16(data, pos)
        pos += 2
        raw = data[pos : pos + length * 2]
        pos += length * 2
        if len(raw) != length * 2:
            raise SystemExit(f"Invalid {file_name}: short UTF-16LE text")
        text = raw.decode("utf-16le")
        rows.append(
            CatalogEntry(
                surface="taiwan",
                file_name=file_name,
                item_id=str(key),
                source_text=text,
                source_origin="current_source",
                location=f"localize/Taiwan/language/{file_name}:{key}",
                encoding="utf-16le",
                note="taiwan quest source is reference text, not primary truth",
            )
        )
    return rows


TBL_SMALL_WORDS = frozenset({"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with"})
TBL_TEXT_RE = re.compile(r"[\[(A-Za-z0-9][A-Za-z0-9' \[\]()%°.,:/+&!?-]{3,}[A-Za-z0-9)\]%°.!?]")
TBL_COMPOUND_WORD_RE = re.compile(r"(?:[A-Z][a-z]{2,}){2,}")
TBL_ATTRIBUTE_WORDS = frozenset({"Elegant", "Funny", "Honest", "Strange", "Wild"})
TBL_UTF16_EXTRA_CHARS = frozenset("°[]")
TBL_FORCE_KEYWORDS = (
    "Recipe",
    "Black Dragon",
    "(Martial)",
    "(Spiritualist)",
    "(Warrior)",
    "(Dragon)",
    "(Might)",
    "(Wonder)",
    "(Namek Warrior)",
    "(Dragon Clan)",
    "(Might Majin)",
    "(Wonder Majin)",
    "Martial Artist",
    "Spiritualist",
    "Warrior",
    "Dragon Clan",
    "Might Majin",
    "Wonder Majin",
    "Namek Warrior",
)


def tbl_candidate_word(word: str) -> bool:
    letters = word.replace("'", "")
    if not letters.isalpha():
        return False
    if len(letters) > 2 and not any(ch in "aeiouyAEIOUY" for ch in letters):
        return False
    if letters.lower() in TBL_SMALL_WORDS:
        return True
    if letters.isupper():
        return len(letters) <= 4
    return letters[0].isupper() and letters[1:].islower()


def tbl_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if not TBL_TEXT_RE.fullmatch(text):
        return False

    has_parenthetical_variant = re.search(r"\([A-Za-z0-9' .+-]+\)", text) is not None
    validation_text = re.sub(r"\([A-Za-z0-9' .+-]+\)", " ", text)
    validation_text = re.sub(r"\[[A-Za-z0-9' .+%-]+\]", " ", validation_text)
    validation_text = re.sub(r"%[0-9]*[A-Za-z]", " ", validation_text)
    validation_text = validation_text.replace("%%", " ")
    validation_text = re.sub(r"[0-9°.,:/+&!?%-]+", " ", validation_text)
    words = [part for part in validation_text.split() if part]
    if not words:
        return False
    if len(words) >= 2:
        return all(tbl_candidate_word(word) for word in words)

    if has_parenthetical_variant and len(words[0]) >= 3:
        return tbl_candidate_word(words[0])

    return len(words[0]) >= 6 and (tbl_candidate_word(words[0]) or TBL_COMPOUND_WORD_RE.fullmatch(words[0]) is not None)


def tbl_property_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if text in TBL_ATTRIBUTE_WORDS:
        return True
    if not (text[0].isalpha() or text[0] == ","):
        return False
    lower = text.lower()
    return "element" in lower and ("attack" in lower or "defense" in lower)


def tbl_forced_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 96 or "\n" in text or "\r" in text:
        return False
    if text.startswith("((") or text[0].islower():
        return False
    if not (text[0].isalnum() or text[0] in "([]"):
        return False
    if re.match(r"^[a-z][0-9]", text):
        return False
    lower = text.lower()
    if "[metatag" in lower:
        return False
    if "50x" in lower or "divine" in lower or "hakai" in lower:
        return True
    return any(keyword in text for keyword in TBL_FORCE_KEYWORDS)


def tbl_shadow_sentence_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 160 or "\n" in text or "\r" in text:
        return False
    if not TBL_TEXT_RE.fullmatch(text):
        return False
    if not text[0].isupper() or text.startswith("(("):
        return False
    if not text.endswith((".", "!", "?")):
        return False
    lower = text.lower()
    if "[metatag" in lower:
        return False
    if "shadow sovereign" not in lower and "shadowsovereign" not in lower:
        return False
    words = re.findall(r"[A-Za-z]+", text)
    if len(words) < 6:
        return False
    for word in words:
        letters = word.replace("'", "")
        if len(letters) > 24:
            return False
        if len(letters) > 2 and not any(ch in "aeiouyAEIOUY" for ch in letters):
            return False
    return True


def tbl_item_description_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 220 or "\n" in text or "\r" in text:
        return False
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9' .,:;!?()&+\-/\[\]]+", text):
        return False
    lower = text.lower()
    if "[metatag" in lower:
        return False
    return (
        lower.startswith("a powerful ring obtained from ")
        or lower.startswith("a powerful earring obtained from ")
        or lower.startswith("a powerful necklace obtained from ")
        or lower.startswith("a sub-weapon touched by ")
        or lower.startswith("a dogi touched by ")
    )


def tbl_accepted_candidate_text(text: str) -> bool:
    return (
        tbl_candidate_text(text)
        or tbl_property_candidate_text(text)
        or tbl_forced_candidate_text(text)
        or tbl_shadow_sentence_candidate_text(text)
        or tbl_item_description_candidate_text(text)
    )


def tbl_queue_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 160 or "\n" in text or "\r" in text:
        return False
    if re.fullmatch(r"(?:Weapon|Armor)\([A-Z]\) \d{3}", text):
        return False
    if re.fullmatch(r"[A-Za-z]+(?:\([A-Z]\))? \d{3}", text):
        return False
    if re.fullmatch(r"[A-Z]{1,3}\d+(?:-\d+)?(?: Age| Pre)?", text):
        return False
    if (
        tbl_property_candidate_text(text)
        or tbl_forced_candidate_text(text)
        or tbl_shadow_sentence_candidate_text(text)
        or tbl_item_description_candidate_text(text)
    ):
        return True
    if not TBL_TEXT_RE.fullmatch(text):
        return False
    if re.search(r"\s", text):
        return tbl_candidate_text(text)
    words = re.findall(r"[A-Za-z][A-Za-z']*", text)
    if len(words) != 1:
        return False
    word = words[0]
    if len(word) < 4:
        return False
    if word.isupper():
        return False
    if not word[0].isupper():
        return False
    return tbl_candidate_word(word)


def normalize_tbl_candidate_text(text: str, strip_length_prefix: bool = False) -> tuple[str, int]:
    text = text.strip("\x00")
    leading_trimmed = text.lstrip()
    leading_shift = len(text) - len(leading_trimmed)
    text = leading_trimmed.rstrip()
    if not text:
        return "", 0
    if strip_length_prefix and len(text) > 1:
        prefix_len = ord(text[0])
        if prefix_len == len(text) - 1:
            candidate = text[1:]
            candidate_trimmed = candidate.lstrip()
            extra_shift = len(candidate) - len(candidate_trimmed)
            stripped = candidate_trimmed.rstrip()
            if tbl_accepted_candidate_text(stripped):
                return stripped, leading_shift + 1 + extra_shift
    if tbl_accepted_candidate_text(text):
        return text, leading_shift
    for char_shift in range(1, min(4, len(text))):
        candidate = text[char_shift:]
        candidate_trimmed = candidate.lstrip()
        extra_shift = len(candidate) - len(candidate_trimmed)
        stripped = candidate_trimmed.rstrip()
        if tbl_accepted_candidate_text(stripped):
            return stripped, leading_shift + char_shift + extra_shift
    return text, leading_shift


def is_tbl_utf16_candidate_char(ch: str) -> bool:
    code = ord(ch)
    return 0x20 <= code <= 0x7E or ch in TBL_UTF16_EXTRA_CHARS


def iter_utf16le_printable_runs(data: bytes, min_chars: int = 4):
    for alignment in (0, 1):
        run_start: int | None = None
        run_chars: list[str] = []
        pos = alignment
        while pos + 1 < len(data):
            ch = chr(data[pos] | (data[pos + 1] << 8))
            if is_tbl_utf16_candidate_char(ch):
                if run_start is None:
                    run_start = pos
                run_chars.append(ch)
            else:
                if run_start is not None and len(run_chars) >= min_chars:
                    yield run_start, "".join(run_chars)
                run_start = None
                run_chars = []
            pos += 2
        if run_start is not None and len(run_chars) >= min_chars:
            yield run_start, "".join(run_chars)


def scan_tbl_candidates(dbozero: Path) -> list[CatalogEntry]:
    rows: list[CatalogEntry] = []
    for file_name in ("tbl0.pak", "tbl1.pak", "tbl2.pak"):
        path = pack_dir(dbozero) / file_name
        data = path.read_bytes()
        for match in re.finditer(rb"[ -~]{4,}", data):
            text, char_shift = normalize_tbl_candidate_text(match.group().decode("ascii", errors="replace"))
            if not tbl_accepted_candidate_text(text):
                continue
            if is_noise_text(text):
                continue
            row_offset = match.start() + char_shift
            rows.append(
                CatalogEntry(
                    surface="tbl",
                    file_name=file_name,
                    item_id=f"0x{row_offset:08X}",
                    source_text=text,
                    source_origin="current_source_candidate_scan",
                    location=f"pack/{file_name}:0x{row_offset:08X}",
                    encoding="ascii_or_gbk",
                    note="tbl candidate from printable byte run",
                )
            )
        for offset, raw_text in iter_utf16le_printable_runs(data):
            text, char_shift = normalize_tbl_candidate_text(raw_text, strip_length_prefix=True)
            if not tbl_accepted_candidate_text(text):
                continue
            if is_noise_text(text):
                continue
            row_offset = offset + char_shift * 2
            rows.append(
                CatalogEntry(
                    surface="tbl",
                    file_name=file_name,
                    item_id=f"0x{row_offset:08X}",
                    source_text=text,
                    source_origin="current_source_candidate_scan",
                    location=f"pack/{file_name}:0x{row_offset:08X}",
                    encoding="utf-16le",
                    note="tbl candidate from UTF-16LE printable run",
                )
            )
    return rows


def scan_current_catalog(dbozero: Path) -> list[CatalogEntry]:
    rows: list[CatalogEntry] = []
    rows.extend(scan_kv_taiwan(dbozero, "local_data.dat"))
    rows.extend(scan_kv_taiwan(dbozero, "local_sync_data.dat"))
    rows.extend(scan_table_text_all(dbozero))
    rows.extend(scan_table_quest(dbozero))
    for key, value in parse_lang0_pack(pack_dir(dbozero) / "lang0.pak"):
        rows.append(
            CatalogEntry(
                surface="lang0",
                file_name="lang0.pak",
                item_id=key,
                source_text=value,
                source_origin="current_source",
                location=f"pack/lang0.pak:{key}",
                encoding="utf-8_or_gbk",
                note="lang0 UI/system source",
            )
        )
    rows.extend(scan_tbl_candidates(dbozero))
    return rows


def iter_tsv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 1):
            if not row:
                continue
            first = row[0].strip()
            if not first or first.startswith("#"):
                continue
            yield row_no, row


def load_manual_translations(root: Path) -> tuple[list[TranslationRow], list[str]]:
    rows: list[TranslationRow] = []
    warnings: list[str] = []

    path = first_existing(root / "legacy" / "translations" / "overrides.tsv", root / "overrides.tsv")
    if path is not None:
        for row_no, row in iter_tsv_rows(path):
            if len(row) < 3:
                warnings.append(f"{path.name}:{row_no}: ignored short row")
                continue
            file_name = row[0].strip()
            item_id = row[1].strip()
            if file_name.lower() == "file" and item_id.lower() == "id":
                continue
            source_text = row[2] if len(row) >= 4 else ""
            translation = row[3] if len(row) >= 4 else row[2]
            if not translation:
                continue
            rows.append(TranslationRow("taiwan", file_name, item_id, source_text, translation, "accepted", legacy_label(root, path), row_no))

    path = first_existing(root / "legacy" / "translations" / "lang0_overrides.tsv", root / "lang0_overrides.tsv")
    if path is not None:
        for row_no, row in iter_tsv_rows(path):
            if len(row) < 2:
                warnings.append(f"{path.name}:{row_no}: ignored short row")
                continue
            key = row[0].strip()
            if key.lower() == "key":
                continue
            source_text = row[1] if len(row) >= 3 else ""
            translation = row[2] if len(row) >= 3 else row[1]
            if not translation:
                continue
            rows.append(TranslationRow("lang0", "lang0.pak", key, source_text, translation, "accepted", legacy_label(root, path), row_no))

    path = first_existing(root / "legacy" / "translations" / "tbl_overrides.tsv", root / "tbl_overrides.tsv")
    if path is not None:
        for row_no, row in iter_tsv_rows(path):
            if len(row) < 4:
                warnings.append(f"{path.name}:{row_no}: ignored short row")
                continue
            file_name = row[0].strip()
            item_id = row[1].strip()
            if file_name.lower() == "file" and item_id.lower() == "id":
                continue
            source_text = row[2]
            translation = row[3]
            if not translation:
                continue
            rows.append(TranslationRow("tbl", file_name, item_id, source_text, translation, "accepted", legacy_label(root, path), row_no))

    return rows, warnings


def load_translations_table(path: Path) -> tuple[list[TranslationRow], list[str]]:
    rows: list[TranslationRow] = []
    warnings: list[str] = []
    if not path.exists():
        return rows, warnings
    for row_no, row in iter_tsv_rows(path):
        if len(row) < 7:
            warnings.append(f"{path.name}:{row_no}: ignored short row")
            continue
        if row[0].strip().lower() == "surface":
            continue
        surface = row[0].strip()
        file_name = row[1].strip()
        item_id = row[2].strip()
        source_text = row[3]
        source_hash = row[4].strip()
        translation = row[5]
        status = row[6].strip() or "accepted"
        legacy_source = row[7].strip() if len(row) >= 8 else legacy_label(repo_root(), path)
        legacy_row = 0
        if len(row) >= 9 and row[8].strip():
            try:
                legacy_row = int(row[8].strip())
            except ValueError:
                warnings.append(f"{path.name}:{row_no}: invalid legacy_row {row[8]!r}")
        note = row[9] if len(row) >= 10 else ""
        if source_hash and source_hash != short_hash(source_text):
            warnings.append(f"{path.name}:{row_no}: source_hash mismatch for {surface}/{file_name}/{item_id}")
        if not translation:
            continue
        rows.append(TranslationRow(surface, file_name, item_id, source_text, translation, status, legacy_source, legacy_row or row_no, note))
    return rows, warnings


def load_active_translations(root: Path, data_dir: Path) -> tuple[list[TranslationRow], list[str], str]:
    translations_path = data_dir / "translations.tsv"
    if translations_path.exists():
        rows, warnings = load_translations_table(translations_path)
        return rows, warnings, "data/translations.tsv"
    rows, warnings = load_manual_translations(root)
    return rows, warnings, "legacy bootstrap"


def first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def legacy_label(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def infer_surface_from_legacy_file(path_name: str, file_name: str) -> str:
    if path_name == "lang0_candidates.tsv" or file_name == "lang0.pak":
        return "lang0"
    if path_name == "tbl_candidates.tsv" or file_name in {"tbl0.pak", "tbl1.pak", "tbl2.pak"}:
        return "tbl"
    return "taiwan"


def load_legacy_candidates(root: Path) -> tuple[list[LegacyCandidate], list[str]]:
    rows: list[LegacyCandidate] = []
    warnings: list[str] = []
    for path_name in LEGACY_CANDIDATE_FILES:
        path = first_existing(root / "legacy" / "candidates" / path_name, root / path_name)
        if path is None:
            continue
        for row_no, row in iter_tsv_rows(path):
            if len(row) < 3:
                warnings.append(f"{path.name}:{row_no}: ignored short row")
                continue
            file_name = row[0].strip()
            item_id = row[1].strip()
            if file_name.lower() == "file" and item_id.lower() == "id":
                continue
            source_text = row[2]
            translation = row[3] if len(row) >= 4 else ""
            if not source_text and not translation:
                continue
            surface = infer_surface_from_legacy_file(path_name, file_name)
            rows.append(LegacyCandidate(surface, file_name, item_id, source_text, translation, legacy_label(root, path), row_no))
    return rows, warnings


def build_exact_translation_indexes(translations: list[TranslationRow]):
    exact: dict[tuple[str, str, str], list[TranslationRow]] = defaultdict(list)
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]] = defaultdict(list)
    by_text: dict[str, list[TranslationRow]] = defaultdict(list)
    for row in translations:
        exact[(row.surface, row.file_name, row.item_id)].append(row)
        text_norm = normalize_text(row.source_text)
        if row.surface == "tbl" and row.item_id == "*" and text_norm:
            wildcard_by_source[(row.surface, row.file_name, text_norm)].append(row)
        if text_norm:
            by_text[text_norm].append(row)
    return exact, wildcard_by_source, by_text


def build_legacy_suggestion_index(legacy: list[LegacyCandidate]) -> dict[str, list[LegacyCandidate]]:
    by_text: dict[str, list[LegacyCandidate]] = defaultdict(list)
    for row in legacy:
        text_norm = normalize_text(row.source_text)
        if text_norm and row.translation:
            by_text[text_norm].append(row)
    return by_text


def build_local_data_reference_index(entries: list[CatalogEntry]) -> dict[str, str]:
    by_id: dict[str, str] = {}
    for entry in entries:
        if entry.surface != "taiwan" or entry.file_name != "local_data.dat":
            continue
        translation = install_hanhua.to_simplified(entry.source_text)
        if translation.strip() and has_cjk(translation):
            by_id[entry.item_id] = translation
    return by_id


def unique_join(values: Iterable[str], limit: int = 12) -> str:
    seen: list[str] = []
    for value in values:
        value = value.strip()
        if not value or value in seen:
            continue
        seen.append(value)
        if len(seen) >= limit:
            break
    return " | ".join(seen)


def preview_text(text: str, limit: int = 90) -> str:
    clean = text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", " ")
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def display_location(row: TranslationRow) -> str:
    return f"{row.surface}/{row.file_name}/{row.item_id} ({row.legacy_source}:{row.row_no})"


def display_catalog_location(entry: CatalogEntry) -> str:
    return f"{entry.surface}/{entry.file_name}/{entry.item_id}"


def suggested_conflict_action(source_text: str, rows: list[TranslationRow], variants: list[str]) -> str:
    source_norm = normalize_text(source_text)
    if is_noise_text(source_text):
        return "工具噪声：后续过滤，不需要人工处理。"
    if source_norm == "scouter":
        return "建议统一为“探测器”，旧的“史考特”应淘汰。"
    if source_norm == "namek":
        return "建议统一为“那美克”。"
    if source_norm == "whisper":
        return "建议聊天功能统一为“私聊”。"
    if source_norm == "no-bank":
        return "建议统一为“禁仓库”。"
    if source_norm == "all classes":
        return "建议统一为“全职业”。"
    if source_norm == "party only":
        return "建议统一为“仅队伍”。"
    if "zeni" in source_norm:
        return "建议货币统一为“索尼”，同时保留占位符。"
    if source_norm == "weapon":
        return "建议按场景区分：装备槽用“主武器”，泛称/市场用“武器”。"
    if source_norm in {"normal", "start", "block", "charge"}:
        return "这是多义词，不能全局替换；按 key 场景逐条确认。"
    if len(variants) == 2:
        return "二选一：确认一个主译法后写入 glossary 或逐 key 固定。"
    return "需要人工确认主译法，避免继续散落多种中文。"


def translation_summary(rows: Iterable[TranslationRow], limit: int = 8) -> str:
    return unique_join((f"{row.translation} [{row.surface}:{row.file_name}:{row.item_id}]" for row in rows), limit=limit)


def legacy_suggestion_summary(rows: Iterable[LegacyCandidate], limit: int = 8) -> str:
    return unique_join((f"{row.translation} [{row.legacy_source}:{row.row_no}]" for row in rows if row.translation), limit=limit)


def exact_translations_for(
    entry: CatalogEntry,
    exact: dict[tuple[str, str, str], list[TranslationRow]],
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]],
) -> list[TranslationRow]:
    rows = list(exact.get((entry.surface, entry.file_name, entry.item_id), []))
    if entry.surface == "tbl":
        rows.extend(wildcard_by_source.get((entry.surface, entry.file_name, normalize_text(entry.source_text)), []))
    return rows


def write_tsv(path: Path, header: list[str], rows: Iterable[list[str]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def write_translations(path: Path, rows: list[TranslationRow]) -> int:
    return write_tsv(
        path,
        ["surface", "file", "id", "source_text", "source_hash", "zh_cn", "status", "legacy_source", "legacy_row", "note"],
        (
            [
                row.surface,
                row.file_name,
                row.item_id,
                row.source_text,
                short_hash(row.source_text),
                row.translation,
                row.status,
                row.legacy_source,
                str(row.row_no),
                row.note,
            ]
            for row in rows
        ),
    )


def write_catalog(
    path: Path,
    entries: list[CatalogEntry],
    exact: dict[tuple[str, str, str], list[TranslationRow]],
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]],
    translations_by_text: dict[str, list[TranslationRow]],
    legacy_by_text: dict[str, list[LegacyCandidate]],
) -> int:
    def rows():
        for entry in entries:
            text_norm = normalize_text(entry.source_text)
            exact_rows = exact_translations_for(entry, exact, wildcard_by_source)
            source_suggestions = translations_by_text.get(text_norm, [])
            legacy_suggestions = legacy_by_text.get(text_norm, [])
            if exact_rows:
                status = "accepted_exact"
            elif source_suggestions:
                status = "suggested_by_manual_overlap"
            elif legacy_suggestions:
                status = "suggested_by_legacy_candidate"
            elif looks_like_translation_candidate(entry.source_text):
                status = "needs_translation"
            else:
                status = "source_reference"
            yield [
                entry.surface,
                entry.file_name,
                entry.item_id,
                entry.source_text,
                short_hash(entry.source_text),
                status,
                translation_summary(exact_rows),
                translation_summary(source_suggestions),
                legacy_suggestion_summary(legacy_suggestions),
                entry.source_origin,
                entry.location,
                entry.encoding,
                entry.note,
            ]

    return write_tsv(
        path,
        [
            "surface",
            "file",
            "id",
            "source_text",
            "source_hash",
            "status",
            "exact_translation",
            "manual_overlap_suggestions",
            "legacy_candidate_suggestions",
            "source_origin",
            "location",
            "encoding",
            "note",
        ],
        rows(),
    )


def write_candidates(
    path: Path,
    entries: list[CatalogEntry],
    exact: dict[tuple[str, str, str], list[TranslationRow]],
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]],
    translations_by_text: dict[str, list[TranslationRow]],
    legacy_by_text: dict[str, list[LegacyCandidate]],
) -> int:
    def rows():
        catalog_surfaces_by_text: dict[str, set[str]] = defaultdict(set)
        for catalog_entry in entries:
            text_norm = normalize_text(catalog_entry.source_text)
            if text_norm:
                catalog_surfaces_by_text[text_norm].add(catalog_entry.surface)

        for entry in entries:
            if entry.surface == "taiwan":
                continue
            text_norm = normalize_text(entry.source_text)
            exact_rows = exact_translations_for(entry, exact, wildcard_by_source)
            if exact_rows:
                continue
            manual_suggestions = translations_by_text.get(text_norm, [])
            legacy_suggestions = legacy_by_text.get(text_norm, [])
            cross_surface = len(catalog_surfaces_by_text.get(text_norm, set())) > 1
            if manual_suggestions:
                status = "suggested_by_manual_overlap"
            elif legacy_suggestions and (entry.surface in {"lang0", "tbl"} or cross_surface):
                status = "suggested_by_legacy_candidate"
            elif entry.surface in {"lang0", "tbl"} and looks_like_translation_candidate(entry.source_text):
                status = "needs_translation"
            else:
                continue
            yield [
                entry.surface,
                entry.file_name,
                entry.item_id,
                entry.source_text,
                short_hash(entry.source_text),
                status,
                translation_summary(manual_suggestions),
                legacy_suggestion_summary(legacy_suggestions),
                entry.location,
                entry.note,
            ]

    return write_tsv(
        path,
        [
            "surface",
            "file",
            "id",
            "source_text",
            "source_hash",
            "status",
            "manual_overlap_suggestions",
            "legacy_candidate_suggestions",
            "location",
            "note",
        ],
        rows(),
    )


def translation_bytes_fit(entry: CatalogEntry, translation: str) -> str:
    if not translation:
        return ""
    if entry.surface == "lang0":
        try:
            return "ok" if len(translation.encode("gbk")) <= len(entry.source_text.encode("gbk", errors="replace")) else "too_long"
        except UnicodeEncodeError:
            return "encoding_error"
    if entry.surface == "tbl":
        encoding = entry.encoding.lower()
        try:
            if encoding == "utf-16le":
                return "ok" if len(translation.encode("utf-16le")) <= len(entry.source_text.encode("utf-16le")) else "too_long"
            return "ok" if len(translation.encode("gbk")) <= len(entry.source_text.encode("gbk", errors="replace")) else "too_long"
        except UnicodeEncodeError:
            return "encoding_error"
    return ""


def workbench_reason(
    entry: CatalogEntry,
    exact_rows: list[TranslationRow],
    manual_suggestions: list[TranslationRow],
    legacy_suggestions: list[LegacyCandidate],
) -> str:
    if exact_rows:
        if len({row.translation for row in exact_rows}) > 1:
            return "review_existing_conflict"
        if exact_rows[0].status in {"needs_review", "conflict"}:
            return "review_existing_marked"
        if entry.surface == "tbl" and translation_bytes_fit(entry, exact_rows[0].translation) == "too_long":
            return "review_existing_too_long"
        return ""
    if manual_suggestions:
        return "reuse_or_edit_existing_translation"
    if legacy_suggestions:
        return "check_legacy_candidate"
    if entry.surface in {"lang0", "tbl"} and looks_like_translation_candidate(entry.source_text):
        return "new_translation_needed"
    return ""


def write_workbench(
    path: Path,
    entries: list[CatalogEntry],
    exact: dict[tuple[str, str, str], list[TranslationRow]],
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]],
    translations_by_text: dict[str, list[TranslationRow]],
    legacy_by_text: dict[str, list[LegacyCandidate]],
) -> int:
    def rows():
        for entry in entries:
            if entry.surface == "taiwan":
                continue
            text_norm = normalize_text(entry.source_text)
            exact_rows = exact_translations_for(entry, exact, wildcard_by_source)
            manual_suggestions = translations_by_text.get(text_norm, [])
            legacy_suggestions = legacy_by_text.get(text_norm, [])
            reason = workbench_reason(entry, exact_rows, manual_suggestions, legacy_suggestions)
            if not reason:
                continue
            current_translation = exact_rows[0].translation if exact_rows else ""
            candidate_translation = ""
            if manual_suggestions:
                candidate_translation = manual_suggestions[0].translation
            elif legacy_suggestions:
                candidate_translation = legacy_suggestions[0].translation
            yield [
                reason,
                entry.surface,
                entry.file_name,
                entry.item_id,
                entry.source_text,
                short_hash(entry.source_text),
                current_translation,
                candidate_translation,
                "",
                translation_bytes_fit(entry, current_translation or candidate_translation),
                translation_summary(manual_suggestions, limit=5),
                legacy_suggestion_summary(legacy_suggestions, limit=5),
                entry.location,
                "Fill zh_cn_new only when you want to add or change this row.",
            ]

    return write_tsv(
        path,
        [
            "reason",
            "surface",
            "file",
            "id",
            "source_text",
            "source_hash",
            "current_zh_cn",
            "suggested_zh_cn",
            "zh_cn_new",
            "fit",
            "manual_overlap_suggestions",
            "legacy_candidate_suggestions",
            "location",
            "note",
        ],
        rows(),
    )


QUEUE_HEADER = ["来源", "文件", "位置", "原文", "参考译文", "填写中文", "长度状态"]


def queue_key(file_name: str, item_id: str, source_text: str) -> tuple[str, str, str]:
    return (file_name, item_id, source_text)


def load_existing_translation_queue(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    rows: dict[tuple[str, str, str], dict[str, str]] = {}
    if not path.is_file():
        return rows

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            return rows
        for row in reader:
            file_name = (row.get("文件") or "").strip()
            item_id = (row.get("位置") or "").strip()
            source_text = row.get("原文") or ""
            if not file_name or not item_id or not source_text:
                continue
            key = queue_key(file_name, item_id, source_text)
            previous = rows.get(key)
            if previous is None or (row.get("填写中文") or "").strip():
                rows[key] = row
    return rows


def write_new_translation_queue(
    path: Path,
    entries: list[CatalogEntry],
    exact: dict[tuple[str, str, str], list[TranslationRow]],
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]],
    legacy_by_text: dict[str, list[LegacyCandidate]],
    existing_queue: dict[tuple[str, str, str], dict[str, str]] | None = None,
) -> int:
    existing_queue = existing_queue or {}
    local_data_by_id = build_local_data_reference_index(entries)

    def rows():
        emitted_tbl_sources: set[tuple[str, str]] = set()
        for entry in entries:
            if entry.surface not in {"lang0", "tbl"}:
                continue
            if entry.surface == "tbl" and is_tbl_internal_token(entry.file_name, entry.source_text):
                continue
            if exact_translations_for(entry, exact, wildcard_by_source):
                continue
            if not looks_like_translation_candidate(entry.source_text):
                continue
            text_norm = normalize_text(entry.source_text)
            legacy_suggestions = legacy_by_text.get(text_norm, [])
            legacy_suggestion = legacy_suggestions[0].translation if legacy_suggestions else ""
            local_data_suggestion = local_data_by_id.get(entry.item_id, "")
            if local_data_suggestion and not is_short_local_data_ui_reference(entry, local_data_suggestion):
                local_data_suggestion = ""
            suggested = local_data_suggestion or legacy_suggestion
            old_row = existing_queue.get(queue_key(entry.file_name, entry.item_id, entry.source_text), {})
            if not old_row and entry.surface == "tbl" and entry.encoding == "utf-16le":
                old_row = existing_queue.get(queue_key(entry.file_name, "*", entry.source_text), {})
            filled = old_row.get("填写中文") or ""
            if local_data_suggestion:
                simplified_filled = install_hanhua.to_simplified(filled)
                if filled and simplified_filled == local_data_suggestion:
                    filled = local_data_suggestion
                elif not filled and translation_bytes_fit(entry, local_data_suggestion) == "ok":
                    filled = local_data_suggestion
            old_suggested = old_row.get("参考译文") or ""
            if entry.surface == "tbl" and not (filled or suggested or tbl_queue_candidate_text(entry.source_text)):
                continue
            if entry.surface == "tbl" and entry.encoding != "utf-16le" and not (filled or suggested):
                continue
            item_id = entry.item_id
            note = ""
            if entry.surface == "tbl" and entry.encoding == "utf-16le":
                tbl_source_key = (entry.file_name, normalize_text(entry.source_text))
                if tbl_source_key in emitted_tbl_sources:
                    continue
                emitted_tbl_sources.add(tbl_source_key)
                item_id = "*"
                note = "wildcard_utf16"
            length_status = note or translation_bytes_fit(entry, filled or suggested)
            if not length_status:
                length_status = "untranslated"
            yield [
                "UI" if entry.surface == "lang0" else "TBL",
                entry.file_name,
                item_id,
                entry.source_text,
                suggested or old_suggested,
                filled,
                length_status,
            ]

    return write_tsv(path, QUEUE_HEADER, rows())


def write_tbl_internal_queue(
    path: Path,
    entries: list[CatalogEntry],
    exact: dict[tuple[str, str, str], list[TranslationRow]],
    wildcard_by_source: dict[tuple[str, str, str], list[TranslationRow]],
    legacy_by_text: dict[str, list[LegacyCandidate]],
) -> int:
    def rows():
        for entry in entries:
            if entry.surface != "tbl":
                continue
            if exact_translations_for(entry, exact, wildcard_by_source):
                continue
            if not looks_like_translation_candidate(entry.source_text):
                continue
            text_norm = normalize_text(entry.source_text)
            legacy_suggestions = legacy_by_text.get(text_norm, [])
            suggested = legacy_suggestions[0].translation if legacy_suggestions else ""
            yield [
                "TBL",
                entry.file_name,
                entry.item_id,
                entry.source_text,
                suggested,
                "",
                translation_bytes_fit(entry, suggested),
            ]

    return write_tsv(path, QUEUE_HEADER, rows())


def write_overlap_by_text(
    path: Path,
    entries: list[CatalogEntry],
    translations_by_text: dict[str, list[TranslationRow]],
) -> int:
    groups: dict[str, list[CatalogEntry]] = defaultdict(list)
    for entry in entries:
        text_norm = normalize_text(entry.source_text)
        if text_norm:
            groups[text_norm].append(entry)

    def rows():
        for text_norm, group in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
            surfaces = sorted({entry.surface for entry in group})
            if len(surfaces) < 2:
                continue
            translation_rows = translations_by_text.get(text_norm, [])
            yield [
                group[0].source_text,
                short_hash(group[0].source_text),
                str(len(group)),
                str(len(surfaces)),
                ",".join(surfaces),
                unique_join((f"{entry.surface}:{entry.file_name}:{entry.item_id}" for entry in group), limit=24),
                translation_summary(translation_rows, limit=12),
            ]

    return write_tsv(
        path,
        ["source_text_sample", "source_hash", "occurrences", "surface_count", "surfaces", "locations", "manual_translations"],
        rows(),
    )


def write_overlap_by_id(path: Path, entries: list[CatalogEntry]) -> int:
    groups: dict[str, list[CatalogEntry]] = defaultdict(list)
    for entry in entries:
        if entry.item_id:
            groups[entry.item_id].append(entry)

    def rows():
        for item_id, group in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
            surfaces = sorted({entry.surface for entry in group})
            if len(surfaces) < 2:
                continue
            yield [
                item_id,
                str(len(group)),
                str(len(surfaces)),
                ",".join(surfaces),
                unique_join((f"{entry.surface}:{entry.file_name}:{entry.source_text}" for entry in group), limit=24),
            ]

    return write_tsv(path, ["id", "occurrences", "surface_count", "surfaces", "texts"], rows())


def write_translation_conflicts(path: Path, translations: list[TranslationRow]) -> int:
    rows_out: list[list[str]] = []
    by_text: dict[str, list[TranslationRow]] = defaultdict(list)
    by_target: dict[tuple[str, str, str], list[TranslationRow]] = defaultdict(list)
    for row in translations:
        text_norm = normalize_text(row.source_text)
        if text_norm:
            by_text[text_norm].append(row)
        by_target[(row.surface, row.file_name, row.item_id)].append(row)

    for text_norm, rows in by_text.items():
        if is_noise_text(rows[0].source_text):
            continue
        translations_seen = sorted({row.translation for row in rows if row.translation})
        if len(translations_seen) > 1:
            rows_out.append(
                [
                    "same_source_text",
                    rows[0].source_text,
                    short_hash(rows[0].source_text),
                    str(len(rows)),
                    unique_join(translations_seen, limit=24),
                    unique_join((f"{row.surface}:{row.file_name}:{row.item_id}:{row.legacy_source}:{row.row_no}" for row in rows), limit=24),
                ]
            )

    for target, rows in by_target.items():
        translations_seen = sorted({row.translation for row in rows if row.translation})
        if len(translations_seen) > 1:
            rows_out.append(
                [
                    "same_target",
                    f"{target[0]}:{target[1]}:{target[2]}",
                    "",
                    str(len(rows)),
                    unique_join(translations_seen, limit=24),
                    unique_join((f"{row.legacy_source}:{row.row_no}" for row in rows), limit=24),
                ]
            )

    return write_tsv(
        path,
        ["conflict_type", "key_or_source_text", "source_hash", "rows", "translation_variants", "locations"],
        rows_out,
    )


def write_review_conflicts(path: Path, translations: list[TranslationRow]) -> int:
    by_text: dict[str, list[TranslationRow]] = defaultdict(list)
    for row in translations:
        text_norm = normalize_text(row.source_text)
        if text_norm and not is_noise_text(row.source_text):
            by_text[text_norm].append(row)

    conflicts: list[tuple[str, list[TranslationRow], list[str]]] = []
    for _text_norm, rows in by_text.items():
        variants = sorted({row.translation for row in rows if row.translation})
        if len(variants) > 1:
            conflicts.append((rows[0].source_text, rows, variants))

    conflicts.sort(key=lambda item: (len(item[2]), len(item[1]), item[0].casefold()), reverse=True)

    lines = [
        "# Translation Conflicts Review",
        "",
        "这个文件给人看。它只列同一原文出现多个中文译法的情况。",
        "",
        f"Total conflicts: {len(conflicts)}",
        "",
    ]
    for index, (source_text, rows, variants) in enumerate(conflicts, 1):
        lines.extend(
            [
                f"## {index}. {preview_text(source_text)}",
                "",
                f"- 原文 hash: `{short_hash(source_text)}`",
                f"- 出现位置: {len(rows)}",
                f"- 现有译法: {unique_join(variants, limit=20)}",
                f"- 建议处理: {suggested_conflict_action(source_text, rows, variants)}",
                "",
                "位置：",
            ]
        )
        for row in rows[:12]:
            lines.append(f"- `{display_location(row)}` -> {preview_text(row.translation, 80)}")
        if len(rows) > 12:
            lines.append(f"- ... 还有 {len(rows) - 12} 处")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8-sig")
    return len(conflicts)


def write_review_overlaps(
    path: Path,
    entries: list[CatalogEntry],
    translations_by_text: dict[str, list[TranslationRow]],
    limit: int = 80,
) -> int:
    groups: dict[str, list[CatalogEntry]] = defaultdict(list)
    for entry in entries:
        text_norm = normalize_text(entry.source_text)
        if text_norm and not is_noise_text(entry.source_text):
            groups[text_norm].append(entry)

    overlap_groups: list[tuple[str, list[CatalogEntry], list[TranslationRow]]] = []
    for text_norm, group in groups.items():
        surfaces = {entry.surface for entry in group}
        if len(surfaces) < 2:
            continue
        manual_rows = translations_by_text.get(text_norm, [])
        if not manual_rows and len(group) < 3:
            continue
        overlap_groups.append((group[0].source_text, group, manual_rows))

    overlap_groups.sort(
        key=lambda item: (
            0 if item[2] else 1,
            -len({entry.surface for entry in item[1]}),
            -len(item[1]),
            item[0].casefold(),
        )
    )
    shown = overlap_groups[:limit]

    lines = [
        "# Cross-Surface Overlaps Review",
        "",
        "这个文件给人看。它列出同一原文同时出现在 Taiwan/lang0/tbl 多个表面的情况。",
        "优先看带现有手工译法的条目，因为这些最容易造成重复翻译或译法不一致。",
        "",
        f"Total overlap groups: {len(overlap_groups)}",
        f"Shown: {len(shown)}",
        "",
    ]
    for index, (source_text, group, manual_rows) in enumerate(shown, 1):
        surfaces = sorted({entry.surface for entry in group})
        lines.extend(
            [
                f"## {index}. {preview_text(source_text)}",
                "",
                f"- 原文 hash: `{short_hash(source_text)}`",
                f"- 表面: {', '.join(surfaces)}",
                f"- 出现次数: {len(group)}",
                f"- 现有手工译法: {translation_summary(manual_rows, limit=10) or '无'}",
                "",
                "代表位置：",
            ]
        )
        for entry in group[:10]:
            lines.append(f"- `{display_catalog_location(entry)}`")
        if len(group) > 10:
            lines.append(f"- ... 还有 {len(group) - 10} 处")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8-sig")
    return len(shown)


def write_next_steps(
    path: Path,
    queue_count: int,
) -> None:
    lines = [
        "# 翻译工作说明",
        "",
        "老大，以后做翻译只看这两个文件。",
        "",
        "## 1. 补新内容",
        "",
        "打开：`data/new_translations.tsv`",
        "",
        "只填这一列：",
        "",
        "- `填写中文`: 你只填这一列",
        "",
        "其他列只是参考：",
        "",
        "- `来源`: UI 表示 lang0，TBL 表示 tbl0.pak / tbl1.pak / tbl2.pak",
        "- `文件`: 来源文件",
        "- `位置`: key 或 offset",
        "- `原文`: 游戏原文",
        "- `参考译文`: 旧资料里找到的参考译法",
        "- `长度状态`: `ok` 表示长度可用，`untranslated` 表示尚未填写，`too_long` 表示可能放不进固定长度字段",
        "",
        f"当前待填行数：{queue_count}",
        "",
        "这个表包含 UI/lang0 和 TBL 待翻译内容。TBL 行很多，建议优先按 `来源`、`文件` 或关键词筛选。",
        "",
        "## 2. 改旧翻译",
        "",
        "打开：`data/translations.tsv`",
        "",
        "只改这一列：",
        "",
        "- `zh_cn`: 当前中文译文",
        "",
        "TBL 里为了长度把“那美克”写成“那美”这种情况可以保留。",
        "",
        "## 3. 生成补丁",
        "",
        "翻译改完后，在当前目录运行：",
        "",
        "```powershell",
        "dboc build",
        "```",
        "",
        "它会重新生成：",
        "",
        "- `output/DBOZero`: 大陆简中 GBK 版",
        "- `output_taiwan/DBOZero`: 台湾繁中 CP950 版",
        "",
        "发简中补丁就打包 `output`。",
        "",
        "发台湾繁中补丁就打包 `output_taiwan`。",
        "",
        "不要把 `src_file`、`data`、`legacy`、`reports` 一起发出去。",
        "",
        "## 4. 检查结果",
        "",
        "生成后至少确认这些文件存在：",
        "",
        "- `output/DBOZero/localize/Taiwan/language/local_data.dat`",
        "- `output/DBOZero/pack/lang0.pak`",
        "- `output/DBOZero/pack/tbl0.pak`",
        "- `output/DBOZero/pack/tbl1.pak`",
        "- `output_taiwan/DBOZero/localize/Taiwan/language/local_data.dat`",
        "- `output_taiwan/DBOZero/pack/lang0.pak`",
        "- `output_taiwan/DBOZero/pack/tbl0.pak`",
        "- `output_taiwan/DBOZero/pack/tbl1.pak`",
        "",
        "`dboc build` 只读 `src_file/DBOZero`，不会动真实游戏目录。",
        "",
        "## 5. 其他文件",
        "",
        "平时不用看。",
        "",
        "`reports/internal/` 里是工具内部生成物，平时不用看。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def write_summary(
    path: Path,
    entries: list[CatalogEntry],
    translations: list[TranslationRow],
    legacy: list[LegacyCandidate],
    warnings: list[str],
    generated_counts: dict[str, int],
) -> None:
    by_surface: dict[str, int] = defaultdict(int)
    by_file: dict[str, int] = defaultdict(int)
    translations_by_surface: dict[str, int] = defaultdict(int)
    for entry in entries:
        by_surface[entry.surface] += 1
        by_file[f"{entry.surface}/{entry.file_name}"] += 1
    for row in translations:
        translations_by_surface[row.surface] += 1

    lines = [
        "# hanhua v3 scan summary",
        "",
        "This scan is read-only. It does not modify game files or generated output.",
        "",
        "## Current catalog",
        "",
    ]
    for surface, count in sorted(by_surface.items()):
        lines.append(f"- {surface}: {count}")
    lines.extend(["", "## Current files", ""])
    for file_key, count in sorted(by_file.items()):
        lines.append(f"- {file_key}: {count}")
    lines.extend(["", "## Imported manual translations", ""])
    for surface, count in sorted(translations_by_surface.items()):
        lines.append(f"- {surface}: {count}")
    lines.extend(
        [
            f"- total: {len(translations)}",
            "",
            "## Imported legacy candidates",
            "",
            f"- total: {len(legacy)}",
            "",
            "## Generated files",
            "",
        ]
    )
    for name, count in generated_counts.items():
        lines.append(f"- {name}: {count} rows")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:200]:
            lines.append(f"- {warning}")
        if len(warnings) > 200:
            lines.append(f"- ... {len(warnings) - 200} more warnings")
    lines.extend(
        [
            "",
            "## Policy notes",
            "",
            "- Taiwan text is now reference material, not the primary translation source.",
            "- Same-key local_data.dat text is promoted only for short lang0 UI labels after simplified-Chinese conversion; rich/long/message-like lang0 rows and TBL rows keep their own workflow.",
            "- Manual translations imported from legacy override TSV files are marked accepted.",
            "- Candidate suggestions from old candidate TSV files are reference-only.",
            "- Existing translations in data/translations.tsv are treated as the editable v3 master table.",
            "- Use data/new_translations.tsv for new translations and data/translations.tsv for accepted translation edits.",
            "- TBL entries are scanned from the current source snapshot and must be reconciled after every game update.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def run(args: argparse.Namespace) -> None:
    root = repo_root()
    dbozero = source_root(args.source_dir)
    data_dir = args.data_dir.resolve()
    report_dir = args.report_dir.resolve()

    entries = scan_current_catalog(dbozero)
    translations, manual_warnings, translation_source = load_active_translations(root, data_dir)
    legacy, legacy_warnings = load_legacy_candidates(root)
    warnings = manual_warnings + legacy_warnings

    exact, wildcard_by_source, translations_by_text = build_exact_translation_indexes(translations)
    legacy_by_text = build_legacy_suggestion_index(legacy)

    generated_counts: dict[str, int] = {}
    translations_path = data_dir / "translations.tsv"
    if not translations_path.exists():
        generated_counts["data/translations.tsv"] = write_translations(translations_path, translations)
    else:
        generated_counts["data/translations.tsv"] = len(translations)
    existing_queue = load_existing_translation_queue(data_dir / "new_translations.tsv")
    internal_report_dir = report_dir / "internal"
    generated_counts["reports/internal/catalog_current.tsv"] = write_catalog(
        internal_report_dir / "catalog_current.tsv",
        entries,
        exact,
        wildcard_by_source,
        translations_by_text,
        legacy_by_text,
    )
    generated_counts["reports/internal/workbench.tsv"] = write_workbench(
        internal_report_dir / "workbench.tsv",
        entries,
        exact,
        wildcard_by_source,
        translations_by_text,
        legacy_by_text,
    )
    generated_counts["data/new_translations.tsv"] = write_new_translation_queue(
        data_dir / "new_translations.tsv",
        entries,
        exact,
        wildcard_by_source,
        legacy_by_text,
        existing_queue,
    )
    generated_counts["reports/internal/tbl_internal_candidates.tsv"] = write_tbl_internal_queue(
        internal_report_dir / "tbl_internal_candidates.tsv",
        entries,
        exact,
        wildcard_by_source,
        legacy_by_text,
    )
    generated_counts["reports/internal/candidates_unified.tsv"] = write_candidates(
        internal_report_dir / "candidates_unified.tsv",
        entries,
        exact,
        wildcard_by_source,
        translations_by_text,
        legacy_by_text,
    )
    generated_counts["reports/internal/overlaps_by_text.tsv"] = write_overlap_by_text(
        internal_report_dir / "overlaps_by_text.tsv",
        entries,
        translations_by_text,
    )
    generated_counts["reports/internal/overlaps_by_id.tsv"] = write_overlap_by_id(internal_report_dir / "overlaps_by_id.tsv", entries)
    generated_counts["reports/internal/translation_conflicts.tsv"] = write_translation_conflicts(
        internal_report_dir / "translation_conflicts.tsv",
        translations,
    )
    generated_counts["reports/internal/review_conflicts.md"] = write_review_conflicts(
        internal_report_dir / "review_conflicts.md",
        translations,
    )
    generated_counts["reports/internal/review_overlaps.md"] = write_review_overlaps(
        internal_report_dir / "review_overlaps.md",
        entries,
        translations_by_text,
    )
    write_next_steps(
        report_dir / "what_to_do_next.md",
        generated_counts["data/new_translations.tsv"],
    )
    generated_counts["reports/what_to_do_next.md"] = 1
    write_summary(internal_report_dir / "scan_summary.md", entries, translations, legacy, warnings, generated_counts)

    print("hanhua v3 scan completed")
    print(f"current catalog entries: {len(entries)}")
    print(f"active translations: {len(translations)} from {translation_source}")
    print(f"legacy candidates imported: {len(legacy)}")
    for name, count in generated_counts.items():
        print(f"{name}: {count}")
    if warnings:
        print(f"warnings: {len(warnings)}")


def build_parser() -> argparse.ArgumentParser:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Scan DBO Zero localization sources into unified v3 tables.")
    parser.add_argument("--source-dir", type=Path, default=root / "src_file", help="Path to src_file or DBOZero.")
    parser.add_argument("--data-dir", type=Path, default=root / "data", help="Output directory for unified data TSV files.")
    parser.add_argument("--report-dir", type=Path, default=root / "reports", help="Output directory for reports.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
