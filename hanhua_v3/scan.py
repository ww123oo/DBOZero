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
from .runtime.full_text_scanner import scan_tbl2_structured


__all__ = [
    "CatalogEntry", "LegacyCandidate", "TranslationRow", "load_active_translations", "main", "scan_current_catalog",
]

ROOT = Path(__file__).resolve().parents[1]
TAIWAN_FILES = ("local_data.dat", "local_sync_data.dat", "table_text_all_data.rdf", "table_quest_text_data.rdf")
LEGACY_MANUAL_FILES = ("overrides.tsv", "lang0_overrides.tsv", "tbl_overrides.tsv")
LEGACY_CANDIDATE_FILES = ("untranslated.tsv", "taiwan_candidates.tsv", "taiwan_translated.tsv", "lang0_candidates.tsv", "tbl_candidates.tsv")
LOCAL_DATA_SHORT_UI_MAX_CHARS = 24
LOCAL_DATA_MESSAGE_KEY_RE = re.compile(r"(?:_MSG|MESSAGE|NOTICE|NOTIFY|INFO|GUIDE|HTML|DESC|DESCRIPTION|TOOLTIP|CONFIRM|ASK|FAIL|FAILED|SUCCESS|ERROR|WARNING|ALERT|MAIL|COMMERCIAL|LOBBY|MARKET|FRIEND|QUEST|TUTORIAL|HELP|SYSTEM)")
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
    kind: str = ""

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
    if (resolved / "DBOZero").is_dir(): return resolved / "DBOZero"
    if resolved.name.lower() == "dbozero": return resolved
    raise SystemExit(f"Invalid source dir: {source_dir}. Expected src_file or DBOZero.")

def language_dir(dbozero: Path) -> Path: return dbozero / "localize" / "Taiwan" / "language"
def pack_dir(dbozero: Path) -> Path: return dbozero / "pack"
def sha1_text(text: str) -> str: return hashlib.sha1(text.encode("utf-8", errors="surrogatepass")).hexdigest()
def short_hash(text: str) -> str: return sha1_text(text)[:12]
def normalize_text(text: str) -> str: return re.sub(r"\s+", " ", text).strip().casefold()
def has_cjk(text: str) -> bool: return any("\u3400" <= ch <= "\u4dbf" or "\u4e00" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff" for ch in text)
def printf_specs(text: str) -> list[str]: return [spec for spec in PRINTF_RE.findall(text) if spec != "%%"]
def is_rich_or_multiline_text(text: str) -> bool: return bool(LOCAL_DATA_RICH_TEXT_RE.search(text) or "\n" in text or "\r" in text or "\\n" in text)
def is_message_like_key(item_id: str) -> bool: return bool(LOCAL_DATA_MESSAGE_KEY_RE.search(item_id.upper()))
def is_short_local_data_ui_reference(entry: CatalogEntry, translation: str) -> bool:
    if entry.surface != "lang0" or entry.file_name != "lang0.pak" or translation != translation.strip() or not translation or not has_cjk(translation) or len(translation) > LOCAL_DATA_SHORT_UI_MAX_CHARS: return False
    if is_message_like_key(entry.item_id) and not entry.item_id.upper().startswith("DST_STATS_"): return False
    if is_rich_or_multiline_text(entry.source_text) or is_rich_or_multiline_text(translation): return False
    return printf_specs(entry.source_text) == printf_specs(translation)
def looks_like_translation_candidate(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped and not is_noise_text(stripped) and not has_cjk(stripped) and re.search(r"[A-Za-z]", stripped))
def is_noise_text(text: str) -> bool:
    stripped = normalize_text(text)
    if not stripped or len(stripped) <= 2 or stripped in {"@", "-", "_", "none", "null"}: return True
    if re.fullmatch(r"[\W_]+", stripped) or re.fullmatch(r"[\d\W_]+", stripped): return True
    if re.fullmatch(r"\[metatag\s*=\s*\d+\]\d*", stripped) or re.fullmatch(r"\[[a-z0-9_ -]+\]\d*", stripped): return True
    return bool(re.fullmatch(r"[a-z]\d+[a-z0-9!?'+-]*", stripped))

def read_u32(data: bytes, pos: int) -> int: return int.from_bytes(data[pos:pos + 4], "little")
def read_u16(data: bytes, pos: int) -> int: return int.from_bytes(data[pos:pos + 2], "little")
def decode_best_effort(data: bytes, encodings: Iterable[str]) -> tuple[str, str]:
    for encoding in encodings:
        try: return data.decode(encoding), encoding
        except UnicodeDecodeError: pass
    encoding = next(iter(encodings), "utf-8")
    return data.decode(encoding, errors="replace"), f"{encoding}-replace"

def read_kv_dat(path: Path) -> list[tuple[str, str]]:
    text, _encoding = decode_best_effort(path.read_bytes(), ("gbk", "utf-8")); rows=[]
    for raw_line in text.splitlines():
        stripped=raw_line.strip()
        if not stripped or stripped.startswith(("//", "#")) or "=" not in raw_line: continue
        key,value=raw_line.split("=",1); key=key.strip(); value=value.strip()
        if not key: continue
        if value.startswith('"'):
            value=value[1:]
            if value.endswith('"'): value=value[:-1]
            value=value.replace('""','"')
        else: value=value.rstrip('"').replace('"','')
        rows.append((key,value))
    return rows

def parse_lang0_pack(path: Path) -> list[tuple[str, str]]:
    text,_encoding=decode_best_effort(path.read_bytes(),("utf-8","gbk")); rows=[]
    for raw_line in text.splitlines():
        stripped=raw_line.strip()
        if not stripped or stripped.startswith(("//","#")) or "=" not in raw_line: continue
        key,value=raw_line.split("=",1); key=key.strip(); value=value.strip()
        if not key or not re.fullmatch(r"[A-Za-z0-9_]+",key): continue
        if value.startswith('"'):
            value=value[1:]
            if value.endswith('"'): value=value[:-1]
            value=value.replace('""','"')
        rows.append((key,value))
    return rows

def scan_kv_taiwan(dbozero: Path, file_name: str) -> list[CatalogEntry]:
    return [CatalogEntry("taiwan",file_name,key,value,"current_source",f"localize/Taiwan/language/{file_name}:{key}","gbk","taiwan source is reference text, not primary truth") for key,value in read_kv_dat(language_dir(dbozero)/file_name)]

def scan_table_text_all(dbozero: Path) -> list[CatalogEntry]:
    file_name="table_text_all_data.rdf"; data=(language_dir(dbozero)/file_name).read_bytes(); pos=0; rows=[]; block_index=0
    while pos<len(data):
        if pos+9>len(data): raise SystemExit(f"Invalid {file_name}: short block header at {pos}")
        table_id=read_u32(data,pos); block_size=read_u32(data,pos+4); block_end=pos+8+block_size
        if block_end>len(data): raise SystemExit(f"Invalid {file_name}: block {block_index} exceeds file size")
        cols=data[pos+8]; pos+=9
        while pos<block_end:
            if pos+4>block_end: raise SystemExit(f"Invalid {file_name}: short record id in block {block_index}")
            key=read_u32(data,pos); pos+=4
            for col in range(cols):
                if pos+2>block_end: raise SystemExit(f"Invalid {file_name}: short string length in block {block_index}")
                length=read_u16(data,pos); pos+=2; raw=data[pos:pos+length*2]; pos+=length*2
                if len(raw)!=length*2: raise SystemExit(f"Invalid {file_name}: short UTF-16LE text")
                text=raw.decode("utf-16le"); item_id=f"{table_id}:{key}:{col}"
                rows.append(CatalogEntry("taiwan",file_name,item_id,text,"current_source",f"localize/Taiwan/language/{file_name}:{item_id}","utf-16le","taiwan rdf source is reference text, not primary truth"))
        block_index+=1
    return rows

def scan_table_quest(dbozero: Path) -> list[CatalogEntry]:
    file_name="table_quest_text_data.rdf"; data=(language_dir(dbozero)/file_name).read_bytes()
    if not data: raise SystemExit(f"Invalid {file_name}: empty file")
    pos=1; rows=[]
    while pos<len(data):
        if pos+6>len(data): raise SystemExit(f"Invalid {file_name}: short record at {pos}")
        key=read_u32(data,pos); pos+=4; length=read_u16(data,pos); pos+=2; raw=data[pos:pos+length*2]; pos+=length*2
        if len(raw)!=length*2: raise SystemExit(f"Invalid {file_name}: short UTF-16LE text")
        text=raw.decode("utf-16le"); rows.append(CatalogEntry("taiwan",file_name,str(key),text,"current_source",f"localize/Taiwan/language/{file_name}:{key}","utf-16le","taiwan quest source is reference text, not primary truth"))
    return rows

TBL_SMALL_WORDS=frozenset({"a","an","and","as","at","by","for","from","in","into","of","on","or","the","to","with"})
TBL_TEXT_RE=re.compile(r"[\[(A-Za-z0-9][A-Za-z0-9' \[\]()%°.,:/+&!?-]{3,}[A-Za-z0-9)\]%°.!?]")
TBL_COMPOUND_WORD_RE=re.compile(r"(?:[A-Z][a-z]{2,}){2,}")
TBL_ATTRIBUTE_WORDS=frozenset({"Elegant","Funny","Honest","Strange","Wild"})
TBL_UTF16_EXTRA_CHARS=frozenset("°[]")
TBL_FORCE_KEYWORDS=("Recipe","Black Dragon","(Martial)","(Spiritualist)","(Warrior)","(Dragon)","(Might)","(Wonder)","(Namek Warrior)","(Dragon Clan)","(Might Majin)","(Wonder Majin)","Martial Artist","Spiritualist","Warrior","Dragon Clan","Might Majin","Wonder Majin","Namek Warrior")
def tbl_candidate_word(word: str)->bool:
    letters=word.replace("'","")
    if not letters.isalpha(): return False
    if len(letters)>2 and not any(ch in "aeiouyAEIOUY" for ch in letters): return False
    if letters.lower() in TBL_SMALL_WORDS: return True
    if letters.isupper(): return len(letters)<=4
    return letters[0].isupper() and letters[1:].islower()
def tbl_candidate_text(text: str)->bool:
    text=text.strip()
    if not text or not TBL_TEXT_RE.fullmatch(text): return False
    validation=re.sub(r"\([A-Za-z0-9' .+-]+\)|\[[A-Za-z0-9' .+%-]+\]|%[0-9]*[A-Za-z]|%%|[0-9°.,:/+&!?%-]+"," ",text)
    words=[part for part in validation.split() if part]
    if not words: return False
    if len(words)>=2: return all(tbl_candidate_word(word) for word in words)
    return len(words[0])>=6 and (tbl_candidate_word(words[0]) or TBL_COMPOUND_WORD_RE.fullmatch(words[0]) is not None)
def tbl_property_candidate_text(text: str)->bool:
    text=text.strip()
    if not text: return False
    if text in TBL_ATTRIBUTE_WORDS: return True
    if not (text[0].isalpha() or text[0]==","): return False
    lower=text.lower(); return "element" in lower and ("attack" in lower or "defense" in lower)
def tbl_forced_candidate_text(text: str)->bool:
    text=text.strip()
    if not text or len(text)>96 or "\n" in text or "\r" in text or text.startswith("((") or text[0].islower(): return False
    if not (text[0].isalnum() or text[0] in "([]"): return False
    lower=text.lower()
    return "[metatag" not in lower and ("50x" in lower or "divine" in lower or "hakai" in lower or any(k in text for k in TBL_FORCE_KEYWORDS))
def tbl_shadow_sentence_candidate_text(text: str)->bool:
    text=text.strip()
    if not text or len(text)>160 or "\n" in text or "\r" in text or not TBL_TEXT_RE.fullmatch(text) or not text[0].isupper() or text.startswith("((") or not text.endswith((".","!","?")): return False
    lower=text.lower(); words=re.findall(r"[A-Za-z]+",text)
    return "[metatag" not in lower and ("shadow sovereign" in lower or "shadowsovereign" in lower) and len(words)>=6 and all(len(w.replace("'",""))<=24 and (len(w)<=2 or any(c in "aeiouyAEIOUY" for c in w)) for w in words)
def tbl_item_description_candidate_text(text: str)->bool:
    text=text.strip()
    if not text or len(text)>220 or "\n" in text or "\r" in text or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9' .,:;!?()&+\-/\[\]]+",text): return False
    lower=text.lower(); return "[metatag" not in lower and any(lower.startswith(p) for p in ("a powerful ring obtained from ","a powerful earring obtained from ","a powerful necklace obtained from ","a sub-weapon touched by ","a dogi touched by "))
def tbl_accepted_candidate_text(text: str)->bool: return tbl_candidate_text(text) or tbl_property_candidate_text(text) or tbl_forced_candidate_text(text) or tbl_shadow_sentence_candidate_text(text) or tbl_item_description_candidate_text(text)
def normalize_tbl_candidate_text(text: str, strip_length_prefix: bool=False)->tuple[str,int]:
    text=text.strip("\x00"); leading=text.lstrip(); shift=len(text)-len(leading); text=leading.rstrip()
    if not text: return "",0
    if strip_length_prefix and len(text)>1 and ord(text[0])==len(text)-1 and tbl_accepted_candidate_text(text[1:].strip()): return text[1:].strip(),shift+1
    if tbl_accepted_candidate_text(text): return text,shift
    for char_shift in range(1,min(4,len(text))):
        candidate=text[char_shift:].lstrip().rstrip();
        if tbl_accepted_candidate_text(candidate): return candidate,shift+char_shift+(len(text[char_shift:])-len(text[char_shift:].lstrip()))
    return text,shift
def is_tbl_utf16_candidate_char(ch: str)->bool: return 0x20<=ord(ch)<=0x7E or ch in TBL_UTF16_EXTRA_CHARS
def iter_utf16le_printable_runs(data: bytes,min_chars: int=4):
    for alignment in (0,1):
        run_start=None; run_chars=[]; pos=alignment
        while pos+1<len(data):
            ch=chr(data[pos]|(data[pos+1]<<8))
            if is_tbl_utf16_candidate_char(ch):
                if run_start is None: run_start=pos
                run_chars.append(ch)
            else:
                if run_start is not None and len(run_chars)>=min_chars: yield run_start,"".join(run_chars)
                run_start=None; run_chars=[]
            pos+=2
        if run_start is not None and len(run_chars)>=min_chars: yield run_start,"".join(run_chars)

def scan_tbl_candidates(dbozero: Path)->list[CatalogEntry]:
    rows=[]
    for file_name in ("tbl0.pak","tbl1.pak","tbl2.pak"):
        path=pack_dir(dbozero)/file_name; data=path.read_bytes()
        if file_name=="tbl2.pak":
            for hit in scan_tbl2_structured(path):
                rows.append(CatalogEntry("tbl",file_name,str(hit.id),hit.text,"current_source_structured",f"pack/{file_name}:0x{hit.offset:X}",hit.encoding,"stable tbl2 record ID",hit.kind))
        for match in re.finditer(rb"[ -~]{4,}",data):
            text,char_shift=normalize_tbl_candidate_text(match.group().decode("ascii",errors="replace"))
            if not tbl_accepted_candidate_text(text) or is_noise_text(text): continue
            row_offset=match.start()+char_shift
            rows.append(CatalogEntry("tbl",file_name,f"0x{row_offset:08X}",text,"current_source_candidate_scan",f"pack/{file_name}:0x{row_offset:08X}","ascii_or_gbk","tbl candidate from printable byte run"))
        for offset,raw_text in iter_utf16le_printable_runs(data):
            text,char_shift=normalize_tbl_candidate_text(raw_text,strip_length_prefix=True)
            if not tbl_accepted_candidate_text(text) or is_noise_text(text): continue
            row_offset=offset+char_shift*2
            rows.append(CatalogEntry("tbl",file_name,f"0x{row_offset:08X}",text,"current_source_candidate_scan",f"pack/{file_name}:0x{row_offset:08X}","utf-16le","tbl candidate from UTF-16LE printable run"))
    return rows

def scan_current_catalog(dbozero: Path)->list[CatalogEntry]:
    rows=[]
    rows.extend(scan_kv_taiwan(dbozero,"local_data.dat")); rows.extend(scan_kv_taiwan(dbozero,"local_sync_data.dat")); rows.extend(scan_table_text_all(dbozero)); rows.extend(scan_table_quest(dbozero))
    for key,value in parse_lang0_pack(pack_dir(dbozero)/"lang0.pak"):
        rows.append(CatalogEntry("lang0","lang0.pak",key,value,"current_source",f"pack/lang0.pak:{key}","utf-8_or_gbk","lang0 UI/system source"))
    rows.extend(scan_tbl_candidates(dbozero)); return rows

def iter_tsv_rows(path: Path):
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        for row_no,row in enumerate(csv.reader(handle,delimiter="\t"),1):
            if not row: continue
            first=row[0].strip()
            if not first or first.startswith("#"): continue
            yield row_no,row

def load_manual_translations(root: Path):
    rows=[]; warnings=[]
    path=first_existing(root/"legacy"/"translations"/"overrides.tsv",root/"overrides.tsv")
    if path:
        for row_no,row in iter_tsv_rows(path):
            if len(row)<3: warnings.append(f"{path.name}:{row_no}: ignored short row"); continue
            file_name=row[0].strip(); item_id=row[1].strip()
            if file_name.lower()=="file" and item_id.lower()=="id": continue
            source_text=row[2] if len(row)>=4 else ""; translation=row[3] if len(row)>=4 else row[2]
            if translation: rows.append(TranslationRow("taiwan",file_name,item_id,source_text,translation,"accepted",legacy_label(root,path),row_no))
    path=first_existing(root/"legacy"/"translations"/"lang0_overrides.tsv",root/"lang0_overrides.tsv")
    if path:
        for row_no,row in iter_tsv_rows(path):
            if len(row)<2: warnings.append(f"{path.name}:{row_no}: ignored short row"); continue
            key=row[0].strip()
            if key.lower()=="key": continue
            source_text=row[1] if len(row)>=3 else ""; translation=row[2] if len(row)>=3 else row[1]
            if translation: rows.append(TranslationRow("lang0","lang0.pak",key,source_text,translation,"accepted",legacy_label(root,path),row_no))
    path=first_existing(root/"legacy"/"translations"/"tbl_overrides.tsv",root/"tbl_overrides.tsv")
    if path:
        for row_no,row in iter_tsv_rows(path):
            if len(row)<4: warnings.append(f"{path.name}:{row_no}: ignored short row"); continue
            file_name=row[0].strip(); item_id=row[1].strip()
            if file_name.lower()=="file" and item_id.lower()=="id": continue
            if row[3]: rows.append(TranslationRow("tbl",file_name,item_id,row[2],row[3],"accepted",legacy_label(root,path),row_no))
    return rows,warnings

def load_translations_table(path: Path):
    rows=[]; warnings=[]
    if not path.exists(): return rows,warnings
    for row_no,row in iter_tsv_rows(path):
        if len(row)<7: warnings.append(f"{path.name}:{row_no}: ignored short row"); continue
        if row[0].strip().lower()=="surface": continue
        surface,file_name,item_id,source_text,source_hash,translation,status=row[:7]
        legacy_source=row[7].strip() if len(row)>=8 else legacy_label(repo_root(),path); legacy_row=0
        if len(row)>=9 and row[8].strip():
            try: legacy_row=int(row[8].strip())
            except ValueError: warnings.append(f"{path.name}:{row_no}: invalid legacy_row {row[8]!r}")
        note=row[9] if len(row)>=10 else ""
        if source_hash and source_hash!=short_hash(source_text): warnings.append(f"{path.name}:{row_no}: source_hash mismatch for {surface}/{file_name}/{item_id}")
        if translation: rows.append(TranslationRow(surface,file_name,item_id,source_text,translation,status or "accepted",legacy_source,legacy_row or row_no,note))
    return rows,warnings

def load_active_translations(root: Path,data_dir: Path):
    translations_path=data_dir/"translations.tsv"
    if translations_path.exists():
        rows,warnings=load_translations_table(translations_path); return rows,warnings,"data/translations.tsv"
    rows,warnings=load_manual_translations(root); return rows,warnings,"legacy bootstrap"
def first_existing(*paths: Path):
    for path in paths:
        if path.exists(): return path
    return None
def legacy_label(root: Path,path: Path)->str:
    try: return path.relative_to(root).as_posix()
    except ValueError: return path.name

def infer_surface_from_legacy_file(path_name: str,file_name: str)->str:
    if path_name=="lang0_candidates.tsv" or file_name=="lang0.pak": return "lang0"
    if path_name=="tbl_candidates.tsv" or file_name in {"tbl0.pak","tbl1.pak","tbl2.pak"}: return "tbl"
    return "taiwan"
