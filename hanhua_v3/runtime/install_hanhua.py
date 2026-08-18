# -*- coding: utf-8 -*-
"""
DBO Zero Simplified Chinese patch builder/installer.

This tool builds Simplified Chinese language files from the user's own Taiwan
localization files. It does not patch executables, DLLs, anti-cheat files, or
the pack archives.
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Callable


LOCALIZATION_FILES = (
    "local_data.dat",
    "local_sync_data.dat",
    "table_text_all_data.rdf",
    "table_quest_text_data.rdf",
)

LCMAP_SIMPLIFIED_CHINESE = 0x02000000
LCMAP_TRADITIONAL_CHINESE = 0x04000000
LCID_CHINESE_SIMPLIFIED = 0x0804
LCID_CHINESE_TRADITIONAL = 0x0404


TAIWAN_SIMPLIFY_FIXUPS = (
    ("伺服器", "服务器"),
    ("滑鼠", "鼠标"),
    ("點選", "点击"),
    ("鑑定", "鉴定"),
    ("膠囊", "胶囊"),
    ("登錄", "登录"),
    ("帳號", "账号"),
    ("帳戶", "账户"),
    ("資料", "资料"),
    ("品質", "品质"),
    ("訊息", "信息"),
    ("視窗", "窗口"),
    ("頭銜", "头衔"),
    ("獎勵", "奖励"),
    ("獲得", "获得"),
    ("後", "后"),
    ("於", "于"),
    ("與", "与"),
    ("為", "为"),
    ("這", "这"),
    ("個", "个"),
    ("來", "来"),
    ("對", "对"),
    ("時", "时"),
    ("會", "会"),
    ("應", "应"),
    ("無", "无"),
    ("開", "开"),
    ("關", "关"),
    ("點", "点"),
    ("選", "选"),
    ("擇", "择"),
    ("刪", "删"),
    ("單", "单"),
    ("稱", "称"),
    ("獲", "获"),
    ("顯", "显"),
    ("裝", "装"),
    ("備", "备"),
    ("級", "级"),
    ("擊", "击"),
    ("龍", "龙"),
    ("雙", "双"),
    ("體", "体"),
    ("復", "复"),
    ("數", "数"),
    ("隨", "随"),
    ("狀", "状"),
    ("臺", "台"),
    ("買", "买"),
    ("賣", "卖"),
    ("實", "实"),
    ("際", "际"),
    ("資", "资"),
    ("確", "确"),
    ("認", "认"),
    ("設", "设"),
    ("當", "当"),
    ("經", "经"),
    ("驗", "验"),
    ("倉", "仓"),
    ("庫", "库"),
    ("標", "标"),
    ("籤", "签"),
    ("參", "参"),
    ("動", "动"),
    ("樓", "楼"),
    ("層", "层"),
    ("進", "进"),
    ("過", "过"),
    ("預", "预"),
    ("賽", "赛"),
    ("決", "决"),
    ("勝", "胜"),
    ("負", "负"),
    ("間", "间"),
    ("請", "请"),
    ("幫", "帮"),
    ("憐", "怜"),
    ("離", "离"),
    ("續", "续"),
    ("優", "优"),
    ("轉", "转"),
    ("職", "职"),
    ("強", "强"),
    ("輔", "辅"),
    ("滅", "灭"),
    ("壞", "坏"),
    ("氣", "气"),
    ("癒", "愈"),
    ("萬", "万"),
    ("圖", "图"),
    ("號", "号"),
    ("餘", "余"),
    ("發", "发"),
    ("髮", "发"),
    ("沖", "冲"),
    ("衝", "冲"),
    ("網", "网"),
    ("頁", "页"),
    ("務", "务"),
    ("啟", "启"),
    ("閉", "闭"),
    ("遞", "递"),
    ("遺", "遗"),
    ("達", "达"),
    ("遠", "远"),
)


class PatchError(RuntimeError):
    pass


def tool_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_game_dir() -> Path:
    return Path.cwd()


def default_source_dir() -> Path:
    return tool_dir() / "src_file"


def is_game_dir(path: Path) -> bool:
    return (path / "DBOZero").is_dir()


def auto_detect_game_dir() -> Path | None:
    bases: list[Path] = []
    for base in (tool_dir(), Path.cwd()):
        try:
            resolved = base.resolve()
        except OSError:
            resolved = base
        bases.append(resolved)
        bases.extend(resolved.parents)

    seen: set[str] = set()
    candidates: list[Path] = []
    for base in bases:
        key = str(base).lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(base)
        candidates.append(base / "DBO Zero 2.0")
        candidates.append(base / "DBOZero")
        try:
            for child in base.iterdir():
                if child.is_dir() and "dbo" in child.name.lower():
                    candidates.append(child)
        except OSError:
            pass

    checked: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        key = str(resolved).lower()
        if key in checked:
            continue
        checked.add(key)
        if is_game_dir(resolved):
            return resolved
    return None


def dbo_root(game_dir: Path) -> Path:
    return game_dir / "DBOZero"


def taiwan_language_dir(game_dir: Path) -> Path:
    return dbo_root(game_dir) / "localize" / "Taiwan" / "language"


def target_language_dir(game_dir: Path, folder: str) -> Path:
    return dbo_root(game_dir) / "localize" / folder / "language"


def validate_target_folder(folder: str) -> str:
    folder = folder.strip()
    if not folder or any(ch in folder for ch in '\\/:*?"<>|'):
        raise PatchError(f"Invalid target folder name: {folder!r}")
    return folder


def require_file(path: Path) -> None:
    if not path.is_file():
        raise PatchError(f"Missing required file: {path}")


def require_game_layout(game_dir: Path) -> None:
    root = dbo_root(game_dir)
    if not root.is_dir():
        raise PatchError(f"Game directory does not contain DBOZero: {game_dir}")
    for name in LOCALIZATION_FILES:
        require_file(taiwan_language_dir(game_dir) / name)
    require_file(root / "pack" / "lang0.pak")
    require_file(root / "ConfigOptions.xml")


def require_source_layout(source_dir: Path) -> None:
    root = dbo_root(source_dir)
    if not root.is_dir():
        raise PatchError(f"Source directory does not contain DBOZero: {source_dir}")
    for name in LOCALIZATION_FILES:
        require_file(taiwan_language_dir(source_dir) / name)
    require_file(root / "pack" / "lang0.pak")
    for name in ("tbl0.pak", "tbl1.pak"):
        require_file(root / "pack" / name)


def require_tbl_layout(source_dir: Path) -> None:
    root = dbo_root(source_dir)
    if not root.is_dir():
        raise PatchError(f"Source directory does not contain DBOZero: {source_dir}")
    for name in ("tbl0.pak", "tbl1.pak"):
        require_file(root / "pack" / name)


@lru_cache(maxsize=100000)
def to_simplified(text: str) -> str:
    if not text:
        return text
    if os.name != "nt":
        return apply_taiwan_fixups(text)
    kernel32 = ctypes.windll.kernel32
    src_len = len(text)
    needed = kernel32.LCMapStringW(
        LCID_CHINESE_SIMPLIFIED,
        LCMAP_SIMPLIFIED_CHINESE,
        text,
        src_len,
        None,
        0,
    )
    if needed <= 0:
        return apply_taiwan_fixups(text)
    buf = ctypes.create_unicode_buffer(needed)
    written = kernel32.LCMapStringW(
        LCID_CHINESE_SIMPLIFIED,
        LCMAP_SIMPLIFIED_CHINESE,
        text,
        src_len,
        buf,
        needed,
    )
    if written <= 0:
        return apply_taiwan_fixups(text)
    return apply_taiwan_fixups(buf.value)


@lru_cache(maxsize=100000)
def to_traditional(text: str) -> str:
    if not text:
        return text
    if os.name != "nt":
        return apply_traditional_fixups(text)
    kernel32 = ctypes.windll.kernel32
    src_len = len(text)
    needed = kernel32.LCMapStringW(
        LCID_CHINESE_TRADITIONAL,
        LCMAP_TRADITIONAL_CHINESE,
        text,
        src_len,
        None,
        0,
    )
    if needed <= 0:
        return apply_traditional_fixups(text)
    buf = ctypes.create_unicode_buffer(needed)
    written = kernel32.LCMapStringW(
        LCID_CHINESE_TRADITIONAL,
        LCMAP_TRADITIONAL_CHINESE,
        text,
        src_len,
        buf,
        needed,
    )
    if written <= 0:
        return apply_traditional_fixups(text)
    return apply_traditional_fixups(buf.value)


def apply_taiwan_fixups(text: str) -> str:
    fixed = text
    for old, new in TAIWAN_SIMPLIFY_FIXUPS:
        fixed = fixed.replace(old, new)
    return fixed


def apply_traditional_fixups(text: str) -> str:
    fixed = text
    for old, new in TAIWAN_SIMPLIFY_FIXUPS:
        fixed = fixed.replace(new, old)
    return fixed


def decode_text(path: Path, encoding: str) -> str:
    return path.read_bytes().decode(encoding)


def read_kv_dat(path: Path, encoding: str, allow_invalid: bool = False) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line_no, raw_line in enumerate(decode_text(path, encoding).splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("//", "#")):
            continue
        if "=" not in raw_line:
            if allow_invalid:
                continue
            raise PatchError(f"Invalid key/value line in {path}:{line_no}")
        key, value = raw_line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            if allow_invalid:
                continue
            raise PatchError(f"Invalid quoted value in {path}:{line_no}")
        if value.startswith('"'):
            value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
        else:
            # One known client line is not wrapped and contains a stray quote.
            # Normalize it so the generated file returns to the normal KEY="text" shape.
            value = value.rstrip('"').replace('"', "")
        rows.append((key, value))
    return rows


def write_kv_dat(path: Path, rows: list[tuple[str, str]], encoding: str = "gbk") -> None:
    text = "".join(f'{key}="{make_encodable(value, encoding)}"\r\n' for key, value in rows)
    path.write_bytes(text.encode(encoding, errors="replace"))


COMMON_ENCODING_REPLACEMENTS = {
    "\u2022": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00a0": " ",
    "\u2248": "~",
}


def make_encodable(text: str, encoding: str) -> str:
    if encoding.lower().replace("_", "-") in {"utf-8", "utf8"}:
        return text
    normalized = "".join(COMMON_ENCODING_REPLACEMENTS.get(ch, ch) for ch in text)
    try:
        normalized.encode(encoding)
        return normalized
    except UnicodeEncodeError:
        chars = []
        for ch in normalized:
            try:
                ch.encode(encoding)
                chars.append(ch)
            except UnicodeEncodeError:
                chars.append("?")
        return "".join(chars)


def read_overrides(path: Path | None) -> dict[tuple[str, str], str]:
    if path is None or not path.exists():
        bundled = bundled_overrides_path()
        if bundled is None:
            return {}
        path = bundled
    if not path.exists():
        return {}
    overrides: dict[tuple[str, str], str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            if len(row) < 3:
                raise PatchError(f"Invalid overrides.tsv row {row_no}; need file, id, text")
            file_name, item_id, text = row[0].strip(), row[1].strip(), row[2]
            if file_name.lower() == "file" and item_id.lower() == "id":
                continue
            if len(row) >= 4:
                text = row[3]
            if text == "":
                continue
            overrides[(file_name, item_id)] = text
    return overrides


def bundled_overrides_path() -> Path | None:
    if not getattr(sys, "frozen", False):
        return None
    bundle_root = Path(getattr(sys, "_MEIPASS", ""))
    candidate = bundle_root / "overrides.tsv"
    if candidate.exists():
        return candidate
    return None


def override_value(
    overrides: dict[tuple[str, str], str],
    file_name: str,
    item_id: str,
    current: str,
    *aliases: str,
) -> str:
    keys = [(file_name, item_id)]
    keys.extend((file_name, alias) for alias in aliases)
    for key in keys:
        if key in overrides:
            return overrides[key]
    return current


def append_override_only_rows(
    rows: list[tuple[str, str]],
    existing_keys: set[str],
    overrides: dict[tuple[str, str], str],
    file_name: str,
    text_transform: Callable[[str], str] = to_simplified,
) -> int:
    appended = 0
    for override_file, item_id in overrides:
        if override_file != file_name or item_id in existing_keys:
            continue
        rows.append((item_id, text_transform(overrides[(override_file, item_id)])))
        existing_keys.add(item_id)
        appended += 1
    return appended


def convert_local_data(
    game_dir: Path,
    dst_dir: Path,
    overrides: dict[tuple[str, str], str],
    text_transform: Callable[[str], str] = to_simplified,
    ansi_encoding: str = "gbk",
) -> dict[str, int]:
    source = taiwan_language_dir(game_dir) / "local_data.dat"
    english = dbo_root(game_dir) / "pack" / "lang0.pak"
    tw_rows = read_kv_dat(source, "gbk")
    en_rows = read_kv_dat_auto(english, ("utf-8", "gbk"), allow_invalid=True)

    tw_keys = {key for key, _ in tw_rows}
    output_keys: set[str] = set()
    output_rows: list[tuple[str, str]] = []
    override_hits = 0

    for key, value in tw_rows:
        converted = text_transform(value)
        final = text_transform(override_value(overrides, "local_data.dat", key, converted))
        if final != converted:
            override_hits += 1
        output_rows.append((key, final))
        output_keys.add(key)

    missing_rows = 0
    for key, value in en_rows:
        if key in tw_keys:
            continue
        converted = text_transform(value)
        final = text_transform(override_value(overrides, "local_data.dat", key, converted))
        if final != converted:
            override_hits += 1
        output_rows.append((key, final))
        output_keys.add(key)
        missing_rows += 1

    extra_override_rows = append_override_only_rows(output_rows, output_keys, overrides, "local_data.dat", text_transform)
    override_hits += extra_override_rows

    write_kv_dat(dst_dir / "local_data.dat", output_rows, encoding=ansi_encoding)
    return {
        "taiwan_keys": len(tw_rows),
        "english_keys": len(en_rows),
        "english_fallback_keys": missing_rows,
        "extra_override_keys": extra_override_rows,
        "override_hits": override_hits,
        "output_keys": len(output_rows),
    }



def lang0_override_value(
    overrides: dict[tuple[str, str], str],
    item_id: str,
    current: str,
) -> tuple[str, bool]:
    for file_name in ("lang0.pak", "pack/lang0.pak", "pack\\lang0.pak", "local_data.dat"):
        key = (file_name, item_id)
        if key in overrides:
            return overrides[key], True
    return current, False


def read_kv_dat_auto(path: Path, encodings: tuple[str, ...], allow_invalid: bool = False) -> list[tuple[str, str]]:
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return read_kv_dat(path, encoding, allow_invalid=allow_invalid)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise PatchError(f"Cannot decode {path}: {last_error}") from last_error
    raise PatchError(f"No encodings configured for {path}")


def read_taiwan_language_kv(
    game_dir: Path,
    file_name: str,
    allow_invalid: bool = False,
) -> list[tuple[str, str]]:
    path = taiwan_language_dir(game_dir) / file_name
    if file_name == "local_sync_data.dat":
        return read_kv_dat_auto(path, ("utf-8", "gbk"), allow_invalid=allow_invalid)
    return read_kv_dat(path, "gbk", allow_invalid=allow_invalid)


def decode_text_auto(path: Path, encodings: tuple[str, ...]) -> tuple[str, str]:
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return decode_text(path, encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise PatchError(f"Cannot decode {path}: {last_error}") from last_error
    raise PatchError(f"No encodings configured for {path}")


def split_line_ending(raw_line: str) -> tuple[str, str]:
    if raw_line.endswith("\r\n"):
        return raw_line[:-2], "\r\n"
    if raw_line.endswith("\n"):
        return raw_line[:-1], "\n"
    return raw_line, ""


def parse_kv_line(raw_line: str) -> tuple[str, str] | None:
    line, _ = split_line_ending(raw_line)
    stripped = line.strip()
    if not stripped or stripped.startswith(("//", "#")) or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if value.startswith('"'):
        value = value[1:]
        if value.endswith('"'):
            value = value[:-1]
    else:
        value = value.rstrip('"').replace('"', "")
    return key, value


def convert_pack_lang0(
    game_dir: Path,
    dst_path: Path,
    overrides: dict[tuple[str, str], str],
) -> dict[str, int]:
    source = dbo_root(game_dir) / "pack" / "lang0.pak"
    lang_text, _ = decode_text_auto(source, ("utf-8", "gbk"))
    lang_lines = lang_text.splitlines(keepends=True)
    taiwan_rows = dict(read_kv_dat(taiwan_language_dir(game_dir) / "local_data.dat", "gbk"))

    output_lines: list[str] = []
    source_keys = 0
    preserved_lines = 0
    taiwan_key_hits = 0
    override_hits = 0
    for raw_line in lang_lines:
        parsed = parse_kv_line(raw_line)
        if parsed is None:
            output_lines.append(raw_line)
            preserved_lines += 1
            continue
        source_keys += 1
        key, value = parsed
        if key in taiwan_rows:
            converted = to_simplified(taiwan_rows[key])
            if converted != value:
                taiwan_key_hits += 1
        else:
            converted = to_simplified(value)
        final, used_override = lang0_override_value(overrides, key, converted)
        if used_override:
            override_hits += 1
        _, ending = split_line_ending(raw_line)
        output_lines.append(f'{key}="{final}"{ending}')

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes("".join(output_lines).encode("utf-8"))
    return {
        "source_keys": source_keys,
        "preserved_lines": preserved_lines,
        "encoding": "utf-8",
        "taiwan_key_hits": taiwan_key_hits,
        "override_hits": override_hits,
        "output_lines": len(output_lines),
    }
def convert_local_sync(
    game_dir: Path,
    dst_dir: Path,
    overrides: dict[tuple[str, str], str],
    text_transform: Callable[[str], str] = to_simplified,
    ansi_encoding: str = "gbk",
) -> dict[str, int]:
    rows = read_taiwan_language_kv(game_dir, "local_sync_data.dat")
    out_rows: list[tuple[str, str]] = []
    override_hits = 0
    for key, value in rows:
        converted = text_transform(value)
        final = text_transform(override_value(overrides, "local_sync_data.dat", key, converted))
        if final != converted:
            override_hits += 1
        out_rows.append((key, final))
    # The client renders these key/value messages through an ANSI path.
    write_kv_dat(dst_dir / "local_sync_data.dat", out_rows, encoding=ansi_encoding)
    return {"keys": len(out_rows), "override_hits": override_hits}


def read_u32(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos : pos + 4], "little")


def read_u16(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos : pos + 2], "little")


def put_u32(value: int) -> bytes:
    return int(value).to_bytes(4, "little")


def put_u16(value: int) -> bytes:
    if value > 0xFFFF:
        raise PatchError(f"Text is too long for RDF length field: {value}")
    return int(value).to_bytes(2, "little")


def convert_rdf_text(value: str, text_transform: Callable[[str], str] = to_simplified) -> str:
    return text_transform(value)


def convert_table_text_all(
    game_dir: Path,
    dst_dir: Path,
    overrides: dict[tuple[str, str], str],
    text_transform: Callable[[str], str] = to_simplified,
) -> dict[str, int]:
    file_name = "table_text_all_data.rdf"
    data = (taiwan_language_dir(game_dir) / file_name).read_bytes()
    pos = 0
    output = bytearray()
    blocks = 0
    records = 0
    strings = 0
    override_hits = 0

    while pos < len(data):
        if pos + 9 > len(data):
            raise PatchError(f"Invalid {file_name}: short block header at {pos}")
        table_id = read_u32(data, pos)
        block_size = read_u32(data, pos + 4)
        block_end = pos + 8 + block_size
        if block_end > len(data):
            raise PatchError(f"Invalid {file_name}: block {blocks} exceeds file size")
        cols = data[pos + 8]
        if cols < 1 or cols > 16:
            raise PatchError(f"Invalid {file_name}: bad column count {cols} at block {blocks}")
        pos += 9

        payload = bytearray()
        while pos < block_end:
            if pos + 4 > block_end:
                raise PatchError(f"Invalid {file_name}: short record id in block {blocks}")
            key = read_u32(data, pos)
            pos += 4
            payload += put_u32(key)
            for col in range(cols):
                if pos + 2 > block_end:
                    raise PatchError(f"Invalid {file_name}: short string length in block {blocks}")
                length = read_u16(data, pos)
                pos += 2
                raw = data[pos : pos + length * 2]
                if len(raw) != length * 2:
                    raise PatchError(f"Invalid {file_name}: short UTF-16 text in block {blocks}")
                pos += length * 2
                text = raw.decode("utf-16le")
                converted = convert_rdf_text(text, text_transform)
                item_id = f"{table_id}:{key}"
                final = text_transform(
                    override_value(
                        overrides,
                        file_name,
                        item_id,
                        converted,
                        str(key),
                        f"{table_id}:{key}:{col}",
                    )
                )
                if final != converted:
                    override_hits += 1
                encoded = final.encode("utf-16le")
                payload += put_u16(len(encoded) // 2)
                payload += encoded
                strings += 1
            records += 1

        output += put_u32(table_id)
        output += put_u32(1 + len(payload))
        output.append(cols)
        output += payload
        blocks += 1

    (dst_dir / file_name).write_bytes(output)
    return {
        "blocks": blocks,
        "records": records,
        "strings": strings,
        "override_hits": override_hits,
    }


def convert_table_quest(
    game_dir: Path,
    dst_dir: Path,
    overrides: dict[tuple[str, str], str],
    text_transform: Callable[[str], str] = to_simplified,
) -> dict[str, int]:
    file_name = "table_quest_text_data.rdf"
    data = (taiwan_language_dir(game_dir) / file_name).read_bytes()
    if not data:
        raise PatchError(f"Invalid {file_name}: empty file")
    output = bytearray(data[:1])
    pos = 1
    records = 0
    override_hits = 0

    while pos < len(data):
        if pos + 6 > len(data):
            raise PatchError(f"Invalid {file_name}: short record at {pos}")
        key = read_u32(data, pos)
        pos += 4
        length = read_u16(data, pos)
        pos += 2
        raw = data[pos : pos + length * 2]
        if len(raw) != length * 2:
            raise PatchError(f"Invalid {file_name}: short UTF-16 text at record {records}")
        pos += length * 2
        text = raw.decode("utf-16le")
        converted = convert_rdf_text(text, text_transform)
        final = text_transform(override_value(overrides, file_name, str(key), converted))
        if final != converted:
            override_hits += 1
        encoded = final.encode("utf-16le")
        output += put_u32(key)
        output += put_u16(len(encoded) // 2)
        output += encoded
        records += 1

    (dst_dir / file_name).write_bytes(output)
    return {"records": records, "override_hits": override_hits}


def build_payload(
    game_dir: Path,
    out_language_dir: Path,
    overrides: dict[tuple[str, str], str],
    text_transform: Callable[[str], str] = to_simplified,
    ansi_encoding: str = "gbk",
) -> dict[str, dict[str, int]]:
    out_language_dir.mkdir(parents=True, exist_ok=True)
    stats = {
        "local_data.dat": convert_local_data(game_dir, out_language_dir, overrides, text_transform, ansi_encoding),
        "local_sync_data.dat": convert_local_sync(game_dir, out_language_dir, overrides, text_transform, ansi_encoding),
        "table_text_all_data.rdf": convert_table_text_all(game_dir, out_language_dir, overrides, text_transform),
        "table_quest_text_data.rdf": convert_table_quest(game_dir, out_language_dir, overrides, text_transform),
    }
    return stats


def has_cjk(text: str) -> bool:
    return any(
        ("\u3400" <= ch <= "\u9fff")
        or ("\uf900" <= ch <= "\ufaff")
        for ch in text
    )


def untranslated_candidate(text: str) -> bool:
    if not text:
        return False
    if text.startswith(("http://", "https://")):
        return False
    if has_cjk(text):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]{3,}", text))


def scan_table_text_all(game_dir: Path) -> dict[str, int]:
    data = (taiwan_language_dir(game_dir) / "table_text_all_data.rdf").read_bytes()
    pos = 0
    blocks = records = strings = candidates = 0
    while pos < len(data):
        table_id = read_u32(data, pos)
        block_size = read_u32(data, pos + 4)
        block_end = pos + 8 + block_size
        cols = data[pos + 8]
        pos += 9
        while pos < block_end:
            _key = read_u32(data, pos)
            pos += 4
            for _ in range(cols):
                length = read_u16(data, pos)
                pos += 2
                text = data[pos : pos + length * 2].decode("utf-16le")
                pos += length * 2
                strings += 1
                if untranslated_candidate(text):
                    candidates += 1
            records += 1
        blocks += 1
    return {"blocks": blocks, "records": records, "strings": strings, "candidate_untranslated": candidates}


def scan_table_quest(game_dir: Path) -> dict[str, int]:
    data = (taiwan_language_dir(game_dir) / "table_quest_text_data.rdf").read_bytes()
    pos = 1
    records = candidates = 0
    while pos < len(data):
        _key = read_u32(data, pos)
        pos += 4
        length = read_u16(data, pos)
        pos += 2
        text = data[pos : pos + length * 2].decode("utf-16le")
        pos += length * 2
        if untranslated_candidate(text):
            candidates += 1
        records += 1
    return {"records": records, "candidate_untranslated": candidates}


def collect_table_text_rows(game_dir: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    file_name = "table_text_all_data.rdf"
    data = (taiwan_language_dir(game_dir) / file_name).read_bytes()
    pos = 0
    while pos < len(data):
        table_id = read_u32(data, pos)
        block_size = read_u32(data, pos + 4)
        block_end = pos + 8 + block_size
        cols = data[pos + 8]
        pos += 9
        while pos < block_end:
            key = read_u32(data, pos)
            pos += 4
            for col in range(cols):
                length = read_u16(data, pos)
                pos += 2
                text = data[pos : pos + length * 2].decode("utf-16le")
                pos += length * 2
                if untranslated_candidate(text):
                    rows.append([file_name, f"{table_id}:{key}:{col}", text])
    return rows


def collect_table_quest_rows(game_dir: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    file_name = "table_quest_text_data.rdf"
    data = (taiwan_language_dir(game_dir) / file_name).read_bytes()
    pos = 1
    while pos < len(data):
        key = read_u32(data, pos)
        pos += 4
        length = read_u16(data, pos)
        pos += 2
        text = data[pos : pos + length * 2].decode("utf-16le")
        pos += length * 2
        if untranslated_candidate(text):
            rows.append([file_name, str(key), text])
    return rows


def collect_kv_untranslated_rows(game_dir: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    tw = dict(read_kv_dat(taiwan_language_dir(game_dir) / "local_data.dat", "gbk"))
    en = read_kv_dat_auto(dbo_root(game_dir) / "pack" / "lang0.pak", ("utf-8", "gbk"), allow_invalid=True)
    for key, value in en:
        if key not in tw:
            rows.append(["local_data.dat", key, value])
    for file_name in ("local_data.dat", "local_sync_data.dat"):
        for key, value in read_taiwan_language_kv(game_dir, file_name):
            if untranslated_candidate(value):
                rows.append([file_name, key, value])
    return rows


def collect_kv_taiwan_translated_rows(game_dir: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for file_name in ("local_data.dat", "local_sync_data.dat"):
        for key, value in read_taiwan_language_kv(game_dir, file_name):
            if has_cjk(value):
                rows.append([file_name, key, value, to_simplified(value)])
    return rows


def collect_table_text_translated_rows(game_dir: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    file_name = "table_text_all_data.rdf"
    data = (taiwan_language_dir(game_dir) / file_name).read_bytes()
    pos = 0
    while pos < len(data):
        table_id = read_u32(data, pos)
        block_size = read_u32(data, pos + 4)
        block_end = pos + 8 + block_size
        cols = data[pos + 8]
        pos += 9
        while pos < block_end:
            key = read_u32(data, pos)
            pos += 4
            for col in range(cols):
                length = read_u16(data, pos)
                pos += 2
                text = data[pos : pos + length * 2].decode("utf-16le")
                pos += length * 2
                if has_cjk(text):
                    rows.append([file_name, f"{table_id}:{key}:{col}", text, convert_rdf_text(text)])
    return rows


def collect_table_quest_translated_rows(game_dir: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    file_name = "table_quest_text_data.rdf"
    data = (taiwan_language_dir(game_dir) / file_name).read_bytes()
    pos = 1
    while pos < len(data):
        key = read_u32(data, pos)
        pos += 4
        length = read_u16(data, pos)
        pos += 2
        text = data[pos : pos + length * 2].decode("utf-16le")
        pos += length * 2
        if has_cjk(text):
            rows.append([file_name, str(key), text, convert_rdf_text(text)])
    return rows


def export_untranslated(game_dir: Path, out_path: Path) -> int:
    rows = [["file", "id", "source_text", "translation"]]
    rows.extend(collect_kv_untranslated_rows(game_dir))
    rows.extend(collect_table_text_rows(game_dir))
    rows.extend(collect_table_quest_rows(game_dir))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows)
    return len(rows) - 1


def export_taiwan_translated(game_dir: Path, out_path: Path) -> int:
    rows = [["file", "id", "source_text", "translation"]]
    rows.extend(collect_kv_taiwan_translated_rows(game_dir))
    rows.extend(collect_table_text_translated_rows(game_dir))
    rows.extend(collect_table_quest_translated_rows(game_dir))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows)
    return len(rows) - 1


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


def tbl_accepted_candidate_text(text: str) -> bool:
    return (
        tbl_candidate_text(text)
        or tbl_property_candidate_text(text)
        or tbl_forced_candidate_text(text)
        or tbl_shadow_sentence_candidate_text(text)
    )


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


def collect_tbl_candidate_rows(source_dir: Path) -> list[list[str]]:
    root = source_dir / "DBOZero" / "pack"
    rows: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for file_name in ("tbl0.pak", "tbl1.pak"):
        path = root / file_name
        data = path.read_bytes()

        for match in re.finditer(rb"[ -~]{4,}", data):
            text, char_shift = normalize_tbl_candidate_text(match.group().decode("ascii", errors="replace"))
            if not tbl_accepted_candidate_text(text):
                continue
            row_offset = match.start() + char_shift
            key = (
                (file_name, f"0x{row_offset:08X}", text)
                if tbl_property_candidate_text(text) or tbl_forced_candidate_text(text)
                else (file_name, text)
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append([file_name, f"0x{row_offset:08X}", text, ""])

        for offset, raw_text in iter_utf16le_printable_runs(data):
            text, char_shift = normalize_tbl_candidate_text(raw_text, strip_length_prefix=True)
            if not tbl_accepted_candidate_text(text):
                continue
            row_offset = offset + char_shift * 2
            key = (
                (file_name, f"0x{row_offset:08X}", text)
                if tbl_property_candidate_text(text) or tbl_forced_candidate_text(text)
                else (file_name, text)
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append([file_name, f"0x{row_offset:08X}", text, ""])

    return rows


def export_tbl_candidates(source_dir: Path, out_path: Path) -> int:
    rows = [["file", "id", "source_text", "translation"]]
    rows.extend(collect_tbl_candidate_rows(source_dir))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerows(rows)
    return len(rows) - 1


def backup_paths(game_dir: Path) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return dbo_root(game_dir) / "hanhua_backup" / stamp


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    elif src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def activate_language(game_dir: Path, folder: str) -> None:
    folder = validate_target_folder(folder)
    root = dbo_root(game_dir)
    config = root / "ConfigOptions.xml"
    text = config.read_text(encoding="utf-8")
    replacement = f'<localize folder="{folder}" />'
    new_text, count = re.subn(r'<localize\s+folder="[^"]*"\s*/>', replacement, text, count=1)
    if count == 0:
        new_text = text.replace("</config_options>", f"\t{replacement}\r\n</config_options>")
    with config.open("w", encoding="utf-8", newline="") as handle:
        handle.write(new_text)
    (root / "selected_language.txt").write_text(f"{folder}\r\n", encoding="ascii")


def running_game_processes() -> list[str]:
    if os.name != "nt":
        return []
    names = {"DboClient.exe", "Launcher Zero.exe", "Updater.exe", "Register.exe"}
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            encoding="mbcs",
            errors="replace",
        )
    except OSError:
        return []
    running = []
    for line in result.stdout.splitlines():
        if not line.startswith('"'):
            continue
        proc = line.split('","', 1)[0].strip('"')
        if proc in names:
            running.append(proc)
    return sorted(set(running))


def install(game_dir: Path, overrides_path: Path | None, activate: bool, target_folder: str = "China") -> Path:
    target_folder = validate_target_folder(target_folder)
    require_game_layout(game_dir)
    running = running_game_processes()
    if running:
        raise PatchError(
            "Game/launcher processes are still running: "
            + ", ".join(running)
            + ". Close them before installing."
        )

    overrides = read_overrides(overrides_path)
    root = dbo_root(game_dir)
    backup = backup_paths(game_dir)
    backup.mkdir(parents=True, exist_ok=False)
    copy_if_exists(root / "ConfigOptions.xml", backup / "ConfigOptions.xml")
    copy_if_exists(root / "selected_language.txt", backup / "selected_language.txt")
    copy_if_exists(root / "localize" / target_folder, backup / target_folder)

    with tempfile.TemporaryDirectory(prefix="dbo_hanhua_") as temp_name:
        temp_language = Path(temp_name) / target_folder / "language"
        stats = build_payload(game_dir, temp_language, overrides)
        target_folder_path = root / "localize" / target_folder
        if target_folder_path.exists():
            shutil.rmtree(target_folder_path)
        shutil.copytree(Path(temp_name) / target_folder, target_folder_path)
        if activate:
            activate_language(game_dir, target_folder)
        report_lines = ["DBO Zero Simplified Chinese patch installed.", ""]
        report_lines.extend(format_stats(stats))
        report_lines.append("")
        report_lines.append(f"Target folder: {target_folder}")
        report_lines.append(f"Activated: {'yes' if activate else 'no'}")
        (backup / "install_report.txt").write_text("\n".join(report_lines), encoding="utf-8")

    return backup


def restore(game_dir: Path, backup_dir: Path) -> None:
    root = dbo_root(game_dir)
    if not backup_dir.is_dir():
        raise PatchError(f"Backup directory does not exist: {backup_dir}")
    copy_if_exists(backup_dir / "ConfigOptions.xml", root / "ConfigOptions.xml")
    copy_if_exists(backup_dir / "selected_language.txt", root / "selected_language.txt")
    copy_if_exists(backup_dir / "pack" / "lang0.pak", root / "pack" / "lang0.pak")
    for folder in ("China", "Taiwan"):
        backup_folder_path = backup_dir / folder
        if not backup_folder_path.exists():
            continue
        target_folder_path = root / "localize" / folder
        if target_folder_path.exists():
            shutil.rmtree(target_folder_path)
        shutil.copytree(backup_folder_path, target_folder_path)


def format_stats(stats: dict[str, dict[str, int]]) -> list[str]:
    lines: list[str] = []
    for name, values in stats.items():
        joined = ", ".join(f"{key}={value}" for key, value in values.items())
        lines.append(f"{name}: {joined}")
    return lines


def command_plan(args: argparse.Namespace) -> int:
    game_dir = args.game_dir.resolve()
    target_folder = validate_target_folder(args.target_folder)
    require_game_layout(game_dir)
    tw_rows = read_kv_dat(taiwan_language_dir(game_dir) / "local_data.dat", "gbk")
    en_rows = read_kv_dat_auto(dbo_root(game_dir) / "pack" / "lang0.pak", ("utf-8", "gbk"), allow_invalid=True)
    tw_keys = {key for key, _ in tw_rows}
    local_sync_rows = read_taiwan_language_kv(game_dir, "local_sync_data.dat")
    table_stats = scan_table_text_all(game_dir)
    quest_stats = scan_table_quest(game_dir)
    print(f"Game dir: {game_dir}")
    print(f"Target language folder: {target_language_dir(game_dir, target_folder)}")
    print("No files were changed by plan mode.")
    print("")
    print(f"local_data.dat Taiwan keys: {len(tw_rows)}")
    print(f"pack\\lang0.pak English keys: {len(en_rows)}")
    print(f"English fallback keys to append: {len([key for key, _ in en_rows if key not in tw_keys])}")
    print(f"local_sync_data.dat keys: {len(local_sync_rows)}")
    print(
        "table_text_all_data.rdf: "
        + ", ".join(f"{key}={value}" for key, value in table_stats.items())
    )
    print(
        "table_quest_text_data.rdf: "
        + ", ".join(f"{key}={value}" for key, value in quest_stats.items())
    )
    overrides = read_overrides(args.overrides)
    print(f"Overrides loaded: {len(overrides)}")
    return 0


def command_build(args: argparse.Namespace) -> int:
    game_dir = args.game_dir.resolve()
    require_game_layout(game_dir)
    overrides = read_overrides(args.overrides)
    stats = build_payload(game_dir, args.out.resolve(), overrides)
    print(f"Built payload at: {args.out.resolve()}")
    for line in format_stats(stats):
        print(line)
    return 0


def command_selftest(args: argparse.Namespace) -> int:
    game_dir = args.game_dir.resolve()
    require_game_layout(game_dir)
    overrides = read_overrides(args.overrides)
    target_folder = validate_target_folder(args.target_folder)
    with tempfile.TemporaryDirectory(prefix="dbo_hanhua_selftest_") as temp_name:
        temp_root = Path(temp_name)
        stats = build_payload(game_dir, temp_root / target_folder / "language", overrides)
    print("Selftest build completed in a temporary folder; no game files were changed.")
    for line in format_stats(stats):
        print(line)
    return 0


def command_export(args: argparse.Namespace) -> int:
    game_dir = args.game_dir.resolve()
    require_source_layout(game_dir)
    count = export_untranslated(game_dir, args.out.resolve())
    print(f"Exported {count} rows to: {args.out.resolve()}")
    return 0


def command_export_taiwan(args: argparse.Namespace) -> int:
    game_dir = args.game_dir.resolve()
    require_source_layout(game_dir)
    count = export_taiwan_translated(game_dir, args.out.resolve())
    print(f"Exported {count} Taiwan translated rows to: {args.out.resolve()}")
    return 0


def command_export_tbl(args: argparse.Namespace) -> int:
    source_dir = args.source_dir.resolve()
    require_tbl_layout(source_dir)
    count = export_tbl_candidates(source_dir, args.out.resolve())
    print(f"Exported {count} tbl candidate rows to: {args.out.resolve()}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    target_folder = validate_target_folder(args.target_folder)
    backup = install(args.game_dir.resolve(), args.overrides, not args.no_activate, target_folder)
    print("Installed Simplified Chinese patch.")
    print(f"Backup: {backup}")
    if args.no_activate:
        print("Language was not activated because --no-activate was used.")
    else:
        print(f"Language folder set to {target_folder}.")
    return 0


def command_wizard(args: argparse.Namespace) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except Exception as exc:
        print(f"ERROR: Cannot open folder picker: {exc}", file=sys.stderr)
        return 2

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    target_folder = validate_target_folder(args.target_folder)

    try:
        game_dir: Path | None = None
        explicit = args.game_dir.resolve()
        if is_game_dir(explicit):
            game_dir = explicit
        else:
            detected = auto_detect_game_dir()
            if detected and messagebox.askyesno(
                "DBOZ 简中补丁",
                "检测到游戏目录：\n\n"
                f"{detected}\n\n"
                "是否安装到这个目录？",
                parent=root,
            ):
                game_dir = detected

        while game_dir is None:
            selected = filedialog.askdirectory(
                title="选择 DBO Zero 2.0 游戏文件夹（里面要有 DBOZero 文件夹）",
                parent=root,
            )
            if not selected:
                return 1
            candidate = Path(selected).resolve()
            if is_game_dir(candidate):
                game_dir = candidate
                break
            messagebox.showerror(
                "选择错误",
                "这个文件夹不对。\n\n"
                "请选择 DBO Zero 2.0 游戏根目录，里面应该能看到 DBOZero 文件夹。",
                parent=root,
            )

        if not messagebox.askyesno(
            "确认安装",
            "安装前请关闭游戏和启动器。\n\n"
            f"游戏目录：\n{game_dir}\n\n"
            + (
                "补丁会备份原 Taiwan 繁中目录，然后把 Taiwan 中文替换为简中。\n"
                "之后在启动器里选择 CN 中文即可使用简中。\n\n"
                if target_folder.lower() == "taiwan"
                else f"补丁会新增 {target_folder} 简中目录，并切换游戏配置。\n\n"
            )
            + "现在开始安装？",
            parent=root,
        ):
            return 1

        root.config(cursor="watch")
        root.update()
        backup = install(game_dir, args.overrides, activate=True, target_folder=target_folder)
        root.config(cursor="")
        messagebox.showinfo(
            "安装完成",
            "简中补丁安装完成。\n\n"
            + (
                "现在可以在启动器里选择 CN 中文进入游戏。\n\n"
                if target_folder.lower() == "taiwan"
                else "如果启动器切换语言后简中失效，重新运行本工具即可。\n\n"
            )
            + f"备份位置：\n{backup}",
            parent=root,
        )
        return 0
    except PatchError as exc:
        root.config(cursor="")
        messagebox.showerror("安装失败", str(exc), parent=root)
        return 2
    finally:
        root.destroy()


def command_restore(args: argparse.Namespace) -> int:
    restore(args.game_dir.resolve(), args.backup.resolve())
    print(f"Restored from backup: {args.backup.resolve()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DBO Zero Simplified Chinese patch installer")
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=default_game_dir(),
        help="Path to the DBO Zero 2.0 game directory. The directory must contain DBOZero.",
    )
    parser.add_argument(
        "--overrides",
        type=Path,
        default=tool_dir() / "overrides.tsv",
        help="Optional manual translation override TSV.",
    )
    parser.add_argument(
        "--target-folder",
        default="China",
        help="Localization folder to install into. Use Taiwan for launcher-compatible CN mode.",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="Inspect inputs and print what would be generated. No writes.")

    build = sub.add_parser("build", help="Build language files into a chosen output folder.")
    build.add_argument("--out", type=Path, required=True, help="Output language folder path.")

    sub.add_parser("selftest", help="Build into a temporary folder and delete it after validation.")

    export = sub.add_parser("export", help="Export untranslated/fallback text candidates to TSV.")
    export.add_argument("--out", type=Path, default=tool_dir() / "untranslated.tsv")

    export_taiwan = sub.add_parser("export-taiwan", help="Export translated Taiwan text rows to TSV.")
    export_taiwan.add_argument("--out", type=Path, default=tool_dir() / "taiwan_translated.tsv")

    export_tbl = sub.add_parser("export-tbl", help="Export reference-only tbl0/tbl1 English text candidates to TSV.")
    export_tbl.add_argument("--source-dir", type=Path, default=default_source_dir(), help="Folder containing source DBOZero files. Default: ./src_file")
    export_tbl.add_argument("--out", type=Path, default=tool_dir() / "tbl_candidates.tsv")

    install_cmd = sub.add_parser("install", help="Build, backup, install, and activate localization.")
    install_cmd.add_argument("--no-activate", action="store_true", help="Install files but do not switch config.")

    sub.add_parser("wizard", help="Open a folder picker and run the installer for normal users.")

    restore_cmd = sub.add_parser("restore", help="Restore ConfigOptions/selected_language/localize folder from a backup folder.")
    restore_cmd.add_argument("--backup", type=Path, required=True, help="Backup directory created by install.")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            return command_plan(args)
        if args.command == "build":
            return command_build(args)
        if args.command == "selftest":
            return command_selftest(args)
        if args.command == "export":
            return command_export(args)
        if args.command == "export-taiwan":
            return command_export_taiwan(args)
        if args.command == "export-tbl":
            return command_export_tbl(args)
        if args.command == "install":
            return command_install(args)
        if args.command == "wizard":
            return command_wizard(args)
        if args.command == "restore":
            return command_restore(args)
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
