# -*- coding: utf-8 -*-
"""
Build copy-only DBO Zero localization outputs from the v3 translation tables.

This reads:
- data/translations.tsv
- data/new_translations.tsv
- src_file/DBOZero

It writes:
- output/DBOZero
- output_taiwan/DBOZero

It never reads or writes the live game directory.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import re
import shutil
import struct
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

try:
    from hanhua_v3.runtime.build_progress import Progress as _BuildProgress
except Exception:  # pragma: no cover
    try:
        from build_progress import Progress as _BuildProgress
    except Exception:
        _BuildProgress = None
from typing import Callable

from hanhua_v3.policy import TBL_INTERNAL_TOKEN_DENYLIST, is_tbl_internal_token
from hanhua_v3.runtime import console_color, install_hanhua, lang0_gbk_patch, tbl_utf16_patch


ROOT = Path(__file__).resolve().parent


ACTIVE_STATUSES = {"", "accepted", "active", "ok", "keep"}
TAIWAN_FILES = set(install_hanhua.LOCALIZATION_FILES)
CORE_PACK_FILES = ("lang0.pak", "tbl0.pak", "tbl1.pak", "tbl2.pak")
OPTIONAL_PACK_FILES = ("gui0.pak",)
BUILD_CACHE_VERSION = 1
BUILD_MANIFEST_NAME = ".build_manifest.json"
BUILD_CODE_FILES = (
    Path("build_output.py"),
    Path("hanhua_v3/runtime/install_hanhua.py"),
    Path("hanhua_v3/runtime/lang0_gbk_patch.py"),
    Path("hanhua_v3/runtime/tbl_utf16_patch.py"),
)
GUI0_FONT_ALIASES = ("Default", "detail", "Lolita", "SimHei")
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc"}
UNQUOTED_LANG0_KEYS = {
    "DST_MAILSYSTEM_MAIL_MARKET",
    "DST_MARKET_ALLCATEGORY",
    "DST_MARKET_BUYTEXT",
    "DST_MARKET_CONSOLE_MACHINE",
    "DST_MARKET_EXP_BUFF",
    "DST_MARKET_NORMALTYPE",
    "DST_MARKET_REFRESH",
    "DST_MARKET_SELL_NOT",
    "DST_MARKET_TITLE",
    "DST_STATUS_STAT_CON",
    "DST_STATUS_STAT_DEX",
    "DST_STATUS_STAT_ENG",
    "DST_STATUS_STAT_FOC",
    "DST_STATUS_STAT_SOL",
    "DST_STATUS_STAT_STR",
}


class BuildError(RuntimeError):
    pass


def stable_json_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def existing_file_hash(path: Path) -> str:
    return file_hash(path) if path.is_file() else "<missing>"


def build_code_hash() -> str:
    return stable_json_hash(
        [
            (path.as_posix(), existing_file_hash(ROOT / path))
            for path in BUILD_CODE_FILES
        ]
    )


def load_build_manifest(out_dir: Path) -> dict:
    path = out_dir / BUILD_MANIFEST_NAME
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        except (OSError, json.JSONDecodeError):
            manifest = {}
    else:
        manifest = {}
    if not isinstance(manifest, dict) or manifest.get("version") != BUILD_CACHE_VERSION:
        manifest = {"version": BUILD_CACHE_VERSION, "targets": {}}
    if not isinstance(manifest.get("targets"), dict):
        manifest["targets"] = {}
    return manifest


def write_build_manifest(out_dir: Path, manifest: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / BUILD_MANIFEST_NAME).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def target_signature(
    *,
    sources: dict[str, Path],
    translation_hash: str,
    transform_sig: str,
    code_sig: str,
) -> str:
    return stable_json_hash(
        {
            "sources": {
                name: existing_file_hash(path)
                for name, path in sorted(sources.items())
            },
            "translation_hash": translation_hash,
            "transform_sig": transform_sig,
            "code_sig": code_sig,
        }
    )


def outputs_exist(paths: list[Path]) -> bool:
    return all(path.exists() and (not path.is_file() or path.stat().st_size > 0) for path in paths)


def maybe_build_target(
    *,
    manifest: dict,
    target_id: str,
    output_paths: list[Path],
    signature: str,
    force: bool,
    builder: Callable[[], dict[str, int]],
) -> dict[str, int]:
    targets = manifest.setdefault("targets", {})
    if not force and targets.get(target_id) == signature and outputs_exist(output_paths):
        return {"skipped": 1}
    stats = builder()
    targets[target_id] = signature
    return stats


def find_lang0_value_start_at_line(data: bytes, key: str) -> int:
    try:
        key_bytes = key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise lang0_gbk_patch.PatchError(f"lang0 key must be ASCII: {key}") from exc
    pattern = re.compile(rb"(?m)^" + re.escape(key_bytes) + rb"[ \t]*=[ \t]*\"")
    matches = list(pattern.finditer(data))
    if not matches:
        return -1
    if len(matches) > 1:
        raise lang0_gbk_patch.PatchError(f"Duplicate lang0 key pattern: {key}")
    return matches[0].end()


lang0_gbk_patch.find_lang0_value_start = find_lang0_value_start_at_line


@dataclass(frozen=True)
class TranslationSets:
    taiwan: dict[tuple[str, str], str]
    lang0: list[tuple[str, str, str]]
    tbl: list[tbl_utf16_patch.TblOverride]
    master_rows: int
    queue_rows: int
    warnings: list[str]


@dataclass(frozen=True)
class GuiFontOption:
    path: Path
    file_name: str
    family_name: str
    full_name: str
    postscript_name: str

    @property
    def face_name(self) -> str:
        return self.family_name or self.full_name or self.postscript_name or Path(self.file_name).stem

    def match_keys(self) -> set[str]:
        values = {
            self.file_name,
            Path(self.file_name).stem,
            self.family_name,
            self.full_name,
            self.postscript_name,
        }
        return {value.casefold() for value in values if value}


@dataclass(frozen=True)
class GuiFontPatch:
    file_name: str
    face_name: str


@dataclass(frozen=True)
class GuiFontSettings:
    font: str | None
    font_dir: Path | None
    font_name: str | None


@dataclass(frozen=True)
class BuildVariantJob:
    label: str
    out_dir: Path
    transform_sig: str
    ansi_encoding: str


def inside_repo(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"Output path must stay inside this workspace: {resolved}") from exc
    return resolved


def source_root(source_dir: Path) -> Path:
    resolved = source_dir.resolve()
    if (resolved / "DBOZero").is_dir():
        return resolved
    if resolved.name.lower() == "dbozero":
        return resolved.parent
    raise BuildError(f"Source dir must be src_file or a DBOZero folder: {source_dir}")


def require_source_layout(source_dir: Path) -> None:
    install_hanhua.require_source_layout(source_dir)


def clean_config_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def config_path(value: str | None) -> Path | None:
    cleaned = clean_config_value(value)
    if cleaned is None:
        return None
    path = Path(cleaned)
    if not path.is_absolute():
        path = ROOT / path
    return path


def load_gui_font_config(path: Path) -> GuiFontSettings:
    if not path.is_file():
        return GuiFontSettings(font=None, font_dir=None, font_name=None)

    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path, encoding="utf-8-sig")
    if not parser.has_section("gui0"):
        return GuiFontSettings(font=None, font_dir=None, font_name=None)

    return GuiFontSettings(
        font=clean_config_value(parser.get("gui0", "font", fallback=None)),
        font_dir=config_path(parser.get("gui0", "font_dir", fallback=None)),
        font_name=clean_config_value(parser.get("gui0", "font_name", fallback=None)),
    )


def resolve_gui_font_settings(args: argparse.Namespace) -> GuiFontSettings:
    config = load_gui_font_config(args.gui_font_config)
    return GuiFontSettings(
        font=args.gui_font if args.gui_font is not None else config.font,
        font_dir=args.gui_font_dir if args.gui_font_dir is not None else config.font_dir,
        font_name=args.gui_font_name if args.gui_font_name is not None else config.font_name,
    )


def read_u16be(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


def read_u32be(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def sfnt_table_offset(data: bytes) -> int:
    if data[:4] == b"ttcf":
        if len(data) < 16:
            raise BuildError("Invalid TTC font file")
        return read_u32be(data, 12)
    return 0


def decode_name_record(platform_id: int, raw: bytes) -> str:
    if platform_id in (0, 3):
        return raw.decode("utf-16-be", errors="replace")
    if platform_id == 1:
        return raw.decode("mac_roman", errors="replace")
    return raw.decode("utf-8", errors="replace")


def read_font_names(path: Path) -> dict[int, str]:
    data = path.read_bytes()
    base = sfnt_table_offset(data)
    if base + 12 > len(data):
        return {}

    table_count = read_u16be(data, base + 4)
    name_table_offset = -1
    for index in range(table_count):
        record = base + 12 + index * 16
        if record + 16 > len(data):
            break
        if data[record : record + 4] == b"name":
            name_table_offset = read_u32be(data, record + 8)
            break

    if name_table_offset < 0 or name_table_offset + 6 > len(data):
        return {}

    record_count = read_u16be(data, name_table_offset + 2)
    string_base = name_table_offset + read_u16be(data, name_table_offset + 4)
    names: dict[int, str] = {}
    for index in range(record_count):
        record = name_table_offset + 6 + index * 12
        if record + 12 > len(data):
            break
        platform_id = read_u16be(data, record)
        name_id = read_u16be(data, record + 6)
        length = read_u16be(data, record + 8)
        offset = read_u16be(data, record + 10)
        if name_id not in (1, 4, 6):
            continue
        raw = data[string_base + offset : string_base + offset + length]
        value = decode_name_record(platform_id, raw).replace("\x00", "").strip()
        if value and "\ufffd" not in value:
            names.setdefault(name_id, value)
    return names


def iter_font_files(font_dir: Path):
    if not font_dir.is_dir():
        return
    for path in sorted(font_dir.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file() and path.suffix.casefold() in FONT_EXTENSIONS:
            yield path


def collect_gui_font_options(source_dir: Path, extra_font_dir: Path | None) -> list[GuiFontOption]:
    dirs = [source_dir / "DBOZero" / "font"]
    if extra_font_dir is not None:
        dirs.append(extra_font_dir)

    options: list[GuiFontOption] = []
    seen: set[Path] = set()
    for font_dir in dirs:
        for path in iter_font_files(font_dir):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                names = read_font_names(path)
            except (OSError, struct.error, BuildError):
                names = {}
            options.append(
                GuiFontOption(
                    path=path,
                    file_name=path.name,
                    family_name=names.get(1, ""),
                    full_name=names.get(4, ""),
                    postscript_name=names.get(6, ""),
                )
            )
    return options


def print_gui_font_options(source_dir: Path, extra_font_dir: Path | None) -> None:
    options = collect_gui_font_options(source_dir, extra_font_dir)
    if not options:
        print("No GUI font files found. Copy DBOZero\\font into src_file\\DBOZero or pass --gui-font-dir.")
        return
    for option in options:
        print(
            f"{option.file_name}\tface={option.face_name}\t"
            f"family={option.family_name or '-'}\tfull={option.full_name or '-'}"
        )


def resolve_gui_font_patch(source_dir: Path, extra_font_dir: Path | None, query: str | None, face_name: str | None) -> GuiFontPatch | None:
    if not query:
        return None

    options = collect_gui_font_options(source_dir, extra_font_dir)
    query_key = query.casefold()
    matches = [option for option in options if query_key in option.match_keys()]

    if not matches and Path(query).suffix.casefold() in FONT_EXTENSIONS:
        file_name = Path(query).name
        return GuiFontPatch(file_name=file_name, face_name=face_name or Path(file_name).stem)

    if not matches:
        raise BuildError(f"Unknown GUI font {query!r}; run --list-gui-fonts with the same --gui-font-dir")

    exact = [option for option in matches if option.file_name.casefold() == query_key]
    selected = exact[0] if len(exact) == 1 else None
    if selected is None:
        if len(matches) == 1:
            selected = matches[0]
        else:
            names = ", ".join(option.file_name for option in matches)
            raise BuildError(f"Ambiguous GUI font {query!r}; use the exact file name. Matches: {names}")

    return GuiFontPatch(file_name=selected.file_name, face_name=face_name or selected.face_name)


def encode_gui0_token(value: str, label: str) -> bytes:
    try:
        return value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise BuildError(f"GUI font {label} must be ASCII for gui0.pak: {value!r}") from exc


def patch_gui0_font_defs(data: bytes, font_patch: GuiFontPatch | None) -> tuple[bytes, dict[str, int]]:
    if font_patch is None:
        return data, {"copied": 1, "font_aliases_changed": 0}

    file_name = encode_gui0_token(font_patch.file_name, "file name")
    face_name = encode_gui0_token(font_patch.face_name, "face name")
    patched = bytes(data)
    changed = 0

    for alias in GUI0_FONT_ALIASES:
        alias_bytes = re.escape(alias.encode("ascii"))
        pattern = re.compile(
            rb"(?m)^([ \t]*"
            + alias_bytes
            + rb"[ \t]*=[ \t]*)([^,\r\n;]+)([ \t]*,[ \t]*)([^;\r\n]*)(;?)"
        )

        def replace(match: re.Match[bytes]) -> bytes:
            semicolon = match.group(5) or b";"
            replacement = match.group(1) + file_name + match.group(3) + face_name + semicolon
            original_len = len(match.group(0))
            if len(replacement) > original_len:
                raise BuildError(
                    f"GUI font alias replacement for {alias!r} is too long for gui0.pak "
                    f"({len(replacement)} > {original_len})"
                )
            return replacement + (b" " * (original_len - len(replacement)))

        patched, count = pattern.subn(replace, patched, count=1)
        if count != 1:
            raise BuildError(f"Could not find gui0.pak font alias definition: {alias}")
        changed += count

    return patched, {"copied": 0, "font_aliases_changed": changed}


def write_gui0_pack(source_dir: Path, pack_dir: Path, font_patch: GuiFontPatch | None) -> dict[str, int]:
    source_gui0 = source_dir / "DBOZero" / "pack" / "gui0.pak"
    if not source_gui0.is_file():
        return {}
    patched, stats = patch_gui0_font_defs(source_gui0.read_bytes(), font_patch)
    (pack_dir / "gui0.pak").write_bytes(patched)
    return stats


def iter_dict_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 2):
            yield row_no, row


def is_active_status(status: str) -> bool:
    return status.strip().casefold() in ACTIVE_STATUSES


def lang0_value_len(text: str, encoding: str) -> int:
    return len(lang0_gbk_patch.encode_lang0_value(text, encoding))


def source_lang0_value_len(text: str) -> int:
    for encoding in ("gbk", "utf-8"):
        try:
            return lang0_value_len(text, encoding)
        except lang0_gbk_patch.PatchError:
            pass
    return len(text.encode("utf-8", errors="replace").replace(b'"', b'""'))


def queue_lang0_row_is_safe(item_id: str, source_text: str, translation: str, warnings: list[str], row_no: int) -> bool:
    old_specs = lang0_gbk_patch.printf_specs(source_text)
    new_specs = lang0_gbk_patch.printf_specs(translation)
    if old_specs != new_specs and not lang0_gbk_patch.printf_mismatch_allowed(item_id, old_specs, new_specs):
        warnings.append(f"new_translations.tsv:{row_no}: skipped printf mismatch for {item_id}: {old_specs} -> {new_specs}")
        return False

    source_len = source_lang0_value_len(source_text)
    simplified_len = lang0_value_len(install_hanhua.to_simplified(translation), "gbk")
    traditional_len = lang0_value_len(install_hanhua.to_traditional(translation), "cp950")
    if simplified_len > source_len or traditional_len > source_len:
        warnings.append(
            f"new_translations.tsv:{row_no}: too-long lang0 text for {item_id} "
            f"(source={source_len}, gbk={simplified_len}, cp950={traditional_len})"
        )
        return False
    return True


def read_master_translations(path: Path) -> tuple[dict[tuple[str, str], str], OrderedDict[tuple[str, str], str], OrderedDict[tuple[str, str, str], tbl_utf16_patch.TblOverride], int, list[str]]:
    taiwan: dict[tuple[str, str], str] = {}
    lang0: OrderedDict[tuple[str, str], str] = OrderedDict()
    tbl: OrderedDict[tuple[str, str, str], tbl_utf16_patch.TblOverride] = OrderedDict()
    warnings: list[str] = []
    used = 0

    if not path.is_file():
        raise BuildError(f"Missing translation table: {path}")

    for row_no, row in iter_dict_rows(path):
        if not is_active_status(row.get("status", "")):
            continue
        surface = (row.get("surface") or "").strip().casefold()
        file_name = (row.get("file") or "").strip()
        item_id = (row.get("id") or "").strip()
        source_text = row.get("source_text") or ""
        translation = row.get("zh_cn") or ""
        if not translation.strip():
            continue

        if surface == "taiwan":
            if file_name not in TAIWAN_FILES:
                warnings.append(f"translations.tsv:{row_no}: skipped unknown Taiwan file {file_name!r}")
                continue
            taiwan[(file_name, item_id)] = translation
            used += 1
        elif surface == "lang0":
            if file_name != "lang0.pak":
                warnings.append(f"translations.tsv:{row_no}: skipped unknown lang0 file {file_name!r}")
                continue
            lang0[(item_id, source_text)] = translation
            used += 1
        elif surface == "tbl":
            if file_name not in tbl_utf16_patch.TBL_FILES:
                warnings.append(f"translations.tsv:{row_no}: skipped unknown tbl file {file_name!r}")
                continue
            offset = tbl_utf16_patch.parse_offset(item_id, row_no)
            tbl[(file_name, item_id, source_text)] = tbl_utf16_patch.TblOverride(file_name, offset, source_text, translation)
            used += 1
        else:
            warnings.append(f"translations.tsv:{row_no}: skipped unknown surface {surface!r}")

    return taiwan, lang0, tbl, used, warnings


def read_queue_translations(
    path: Path,
    lang0: OrderedDict[tuple[str, str], str],
    tbl: OrderedDict[tuple[str, str, str], tbl_utf16_patch.TblOverride],
) -> tuple[int, list[str]]:
    warnings: list[str] = []
    used = 0
    if not path.is_file():
        return used, warnings

    for row_no, row in iter_dict_rows(path):
        file_name = (row.get("文件") or "").strip()
        item_id = (row.get("位置") or "").strip()
        source_text = row.get("原文") or ""
        translation = row.get("填写中文") or ""
        if not translation.strip():
            continue

        if file_name == "lang0.pak":
            if not queue_lang0_row_is_safe(item_id, source_text, translation, warnings, row_no):
                continue
            lang0[(item_id, source_text)] = translation
            used += 1
            continue

        if file_name in tbl_utf16_patch.TBL_FILES:
            offset = None if item_id in tbl_utf16_patch.ALL_OFFSETS else tbl_utf16_patch.parse_offset(item_id, row_no)
            for existing_key in list(tbl):
                if existing_key[0] == file_name and existing_key[2] == source_text:
                    del tbl[existing_key]
            tbl[(file_name, item_id, source_text)] = tbl_utf16_patch.TblOverride(file_name, offset, source_text, translation)
            used += 1
            continue

        warnings.append(f"new_translations.tsv:{row_no}: skipped unsupported file {file_name!r}")

    return used, warnings


def load_translation_sets(data_dir: Path) -> TranslationSets:
    taiwan, lang0, tbl, master_rows, warnings = read_master_translations(data_dir / "translations.tsv")
    queue_rows, queue_warnings = read_queue_translations(data_dir / "new_translations.tsv", lang0, tbl)
    warnings.extend(queue_warnings)
    return TranslationSets(
        taiwan=taiwan,
        lang0=[(key, source_text, translation) for (key, source_text), translation in lang0.items()],
        tbl=list(tbl.values()),
        master_rows=master_rows,
        queue_rows=queue_rows,
        warnings=warnings,
    )


def write_user_readme(out_dir: Path) -> None:
    text = """DBOZ 简中补丁 使用说明

安装：
1. 关闭游戏和启动器。
2. 自己备份游戏里的 DBOZero 文件夹，至少备份：
   DBOZero\\localize\\Taiwan
   DBOZero\\pack\\lang0.pak
   DBOZero\\pack\\tbl0.pak
   DBOZero\\pack\\tbl1.pak
   DBOZero\\pack\\gui0.pak
3. 把本目录里的 DBOZero 文件夹复制到游戏根目录。
4. 提示覆盖时选“是”。
5. 启动器选择 CN 中文。

说明：
- 本补丁不含安装器。
- 本补丁会覆盖 Taiwan 语言文件、lang0.pak、tbl0.pak、tbl1.pak、tbl2.pak、gui0.pak。
- 出问题就用你自己的备份覆盖回去。
"""
    (out_dir / "使用说明.txt").write_text(text, encoding="utf-8")


def write_taiwan_user_readme(out_dir: Path) -> None:
    text = """DBOZ 台灣繁中補丁 使用說明

安裝：
1. 關閉遊戲和啟動器。
2. 自己備份遊戲裡的 DBOZero 資料夾，至少備份：
   DBOZero\\localize\\Taiwan
   DBOZero\\pack\\lang0.pak
   DBOZero\\pack\\tbl0.pak
   DBOZero\\pack\\tbl1.pak
   DBOZero\\pack\\gui0.pak
3. 把本目錄裡的 DBOZero 資料夾複製到遊戲根目錄。
4. 提示覆蓋時選「是」。
5. 啟動器選擇 CN 中文。

說明：
- 本目錄是給台灣 Big5/CP950 環境使用的繁中版。
- 出問題就用你自己的備份覆蓋回去。
"""
    (out_dir / "使用说明_台湾繁中.txt").write_text(text, encoding="utf-8")


def transform_lang0(rows: list[tuple[str, str, str]], transform: Callable[[str], str]) -> list[tuple[str, str, str]]:
    return [(key, source_text, transform(text)) for key, source_text, text in rows]


def write_build_missing_report(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.unlink(missing_ok=True)
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def find_lang0_line_value_ranges(data: bytes, key: str) -> list[tuple[int, int]]:
    try:
        key_bytes = key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise lang0_gbk_patch.PatchError(f"lang0 key must be ASCII: {key}") from exc
    pattern = re.compile(rb"(?m)^" + re.escape(key_bytes) + rb"[ \t]*=[ \t]*\"")
    ranges: list[tuple[int, int]] = []
    for match in pattern.finditer(data):
        start = match.end()
        end = find_lang0_value_end(data, start, key)
        ranges.append((start, end))
    return ranges


def find_lang0_value_end(data: bytes, start: int, key: str) -> int:
    pos = start
    while pos < len(data):
        value = data[pos]
        if value in (ord("\r"), ord("\n")):
            break
        if value == ord("\\") and pos + 1 < len(data):
            pos += 2
            continue
        if value == ord('"'):
            if pos + 1 < len(data) and data[pos + 1] == ord('"'):
                pos += 2
                continue
            return pos
        pos += 1
    raise lang0_gbk_patch.PatchError(f"Closing quote not found for {key}")


def normalize_lang0_source_text(text: str) -> str:
    return text.replace('\\"', '"')


def patch_lang0_bytes_by_source(
    data: bytes,
    rows: list[tuple[str, str, str]],
    encoding: str,
    missing_rows: list[tuple[str, str, str, str]] | None = None,
) -> tuple[bytes, dict[str, int]]:
    source = bytes(data)
    patched = bytearray(data)
    changed = 0
    missing = 0
    space_padded = 0

    for key, source_text, text in rows:
        matches = find_lang0_line_value_ranges(source, key)
        if not matches:
            missing += 1
            if missing_rows is not None:
                missing_rows.append((key, source_text, text, "key_not_found"))
            continue

        selected: tuple[int, int] | None = None
        selected_old_value = ""
        selected_old_raw = b""
        expected_source_text = normalize_lang0_source_text(source_text)
        for start, end in matches:
            old_raw = source[start:end]
            old_value = lang0_gbk_patch.decode_lang0_value(
                lang0_gbk_patch.unescape_lang0_value(old_raw).replace(b'\\"', b'"')
            )
            if source_text and old_value != expected_source_text:
                continue
            if selected is not None:
                raise lang0_gbk_patch.PatchError(f"Duplicate lang0 key/source pattern: {key} = {source_text!r}")
            selected = (start, end)
            selected_old_value = old_value
            selected_old_raw = old_raw

        if selected is None and not source_text and len(matches) == 1:
            selected = matches[0]
            selected_old_value = lang0_gbk_patch.decode_lang0_value(
                lang0_gbk_patch.unescape_lang0_value(source[selected[0] : selected[1]])
            )
            selected_old_raw = source[selected[0] : selected[1]]

        if selected is None:
            missing += 1
            if missing_rows is not None:
                missing_rows.append((key, source_text, text, "key_found_but_source_changed"))
            continue

        old_specs = lang0_gbk_patch.printf_specs(selected_old_value)
        new_specs = lang0_gbk_patch.printf_specs(text)
        if old_specs != new_specs and not lang0_gbk_patch.printf_mismatch_allowed(key, old_specs, new_specs):
            raise lang0_gbk_patch.PatchError(f"Printf placeholder mismatch for {key}: {old_specs} -> {new_specs}")

        start, end = selected
        if key in UNQUOTED_LANG0_KEYS:
            stat_text = text
            if encoding.lower() in {"cp950", "big5"}:
                stat_text = install_hanhua.to_traditional(stat_text)
            raw_value = lang0_gbk_patch.encoded_text_bytes(stat_text, encoding)
            old_field_len = end - start + 2
            if len(raw_value) > old_field_len:
                raise lang0_gbk_patch.PatchError(
                    f"Unquoted lang0 text is too long for fixed lang0 field: {key} "
                    f"({len(raw_value)} bytes > {old_field_len} bytes): {stat_text!r}"
                )
            pad_len = old_field_len - len(raw_value)
            patched[start - 1 : end + 1] = raw_value + (b" " * pad_len)
            if pad_len:
                space_padded += 1
            changed += 1
            continue

        if b'\\"' in selected_old_raw:
            normalized_text = normalize_lang0_source_text(text)
            new_value = lang0_gbk_patch.encoded_text_bytes(normalized_text, encoding).replace(b'"', b'\\"')
        else:
            new_value = lang0_gbk_patch.encode_lang0_value(text, encoding)
        old_len = end - start
        if len(new_value) > old_len:
            raise lang0_gbk_patch.PatchError(
                f"Translation is too long for fixed lang0 field: {key} "
                f"({len(new_value)} bytes > {old_len} bytes): {selected_old_value!r} -> {text!r}"
            )
        pad_len = old_len - len(new_value)
        patched[start : end + 1] = new_value + b'"' + (b" " * pad_len)
        if pad_len:
            space_padded += 1
        changed += 1

    return bytes(patched), {"rows": len(rows), "changed": changed, "missing": missing, "space_padded": space_padded}


def transform_tbl(rows: list[tbl_utf16_patch.TblOverride], transform: Callable[[str], str]) -> list[tbl_utf16_patch.TblOverride]:
    return [
        tbl_utf16_patch.TblOverride(row.file_name, row.offset, row.source_text, transform(row.translation))
        for row in rows
        if not is_tbl_internal_token(row.file_name, row.source_text)
    ]


def group_tbl_translations(rows: list[tbl_utf16_patch.TblOverride]) -> dict[str, list[tbl_utf16_patch.TblOverride]]:
    grouped: dict[str, list[tbl_utf16_patch.TblOverride]] = {name: [] for name in tbl_utf16_patch.TBL_FILES}
    for row in rows:
        grouped.setdefault(row.file_name, []).append(row)
    return grouped


def hash_taiwan_rows(rows: dict[tuple[str, str], str]) -> str:
    return stable_json_hash(sorted((file_name, item_id, text) for (file_name, item_id), text in rows.items()))


def hash_lang0_rows(rows: list[tuple[str, str, str]]) -> str:
    return stable_json_hash(rows)


def hash_tbl_rows(rows: list[tbl_utf16_patch.TblOverride]) -> str:
    return stable_json_hash(
        [
            {
                "file": row.file_name,
                "offset": row.offset,
                "source": row.source_text,
                "translation": row.translation,
            }
            for row in rows
        ]
    )


def patch_tbl_file(
    source_dir: Path,
    pack_dir: Path,
    file_name: str,
    rows: list[tbl_utf16_patch.TblOverride],
    single_byte_encoding: str,
) -> dict[str, int]:
    source = tbl_utf16_patch.tbl_path(source_dir, file_name)
    if not source.is_file():
        raise tbl_utf16_patch.PatchError(f"Missing source tbl file: {source}")
    pack_dir.mkdir(parents=True, exist_ok=True)
    if not rows:
        shutil.copy2(source, pack_dir / file_name)
        return {"rows": 0, "copied": 1}
    missing_rows: list[tuple[tbl_utf16_patch.TblOverride, str]] = []
    patched, stats = tbl_utf16_patch.patch_tbl_bytes(
        source.read_bytes(),
        rows,
        single_byte_encoding,
        missing_rows=missing_rows,
    )
    (pack_dir / file_name).write_bytes(patched)
    write_build_missing_report(
        ROOT / "reports" / "internal" / f"build_missing_{file_name}_{single_byte_encoding}.tsv",
        ["file", "location", "source_text", "translation", "reason"],
        [
            [
                row.file_name,
                "*" if row.offset is None else f"0x{row.offset:08X}",
                row.source_text,
                row.translation,
                reason,
            ]
            for row, reason in missing_rows
        ],
    )
    return stats


def copy_missing_pack_files(source_dir: Path, pack_dir: Path) -> None:
    source_pack = source_dir / "DBOZero" / "pack"
    for name in CORE_PACK_FILES:
        target = pack_dir / name
        if not target.exists():
            shutil.copy2(source_pack / name, target)
    for name in OPTIONAL_PACK_FILES:
        source = source_pack / name
        target = pack_dir / name
        if source.is_file() and not target.exists():
            shutil.copy2(source, target)


def build_one(
    source_dir: Path,
    out_dir: Path,
    translations: TranslationSets,
    *,
    clean: bool,
    force: bool,
    text_transform: Callable[[str], str],
    transform_sig: str,
    ansi_encoding: str,
    readme_writer: Callable[[Path], None],
    gui_font: GuiFontPatch | None,
) -> dict[str, dict[str, int]]:
    out_dir = inside_repo(out_dir)
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)

    language_dir = out_dir / "DBOZero" / "localize" / "Taiwan" / "language"
    pack_dir = out_dir / "DBOZero" / "pack"
    language_dir.mkdir(parents=True, exist_ok=True)
    pack_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_build_manifest(out_dir)
    code_sig = build_code_hash()
    stats: dict[str, dict[str, int]] = {}
    progress = _BuildProgress(9, label=ansi_encoding) if _BuildProgress else None

    def _p(msg: str) -> None:
        if progress is not None:
            progress.step(msg)
        else:
            print(f"  · {msg}", flush=True)

    taiwan_sources = {
        name: source_dir / "DBOZero" / "localize" / "Taiwan" / "language" / name
        for name in install_hanhua.LOCALIZATION_FILES
    }
    taiwan_signature = target_signature(
        sources=taiwan_sources,
        translation_hash=hash_taiwan_rows(translations.taiwan),
        transform_sig=transform_sig,
        code_sig=code_sig,
    )
    taiwan_output_paths = [language_dir / name for name in install_hanhua.LOCALIZATION_FILES]
    taiwan_stats = maybe_build_target(
        manifest=manifest,
        target_id="DBOZero/localize/Taiwan/language",
        output_paths=taiwan_output_paths,
        signature=taiwan_signature,
        force=force,
        builder=lambda: install_hanhua.build_payload(
            source_dir,
            language_dir,
            translations.taiwan,
            text_transform,
            ansi_encoding,
        ),
    )
    if set(taiwan_stats) == {"skipped"}:
        stats["localize/Taiwan/language"] = taiwan_stats
    else:
        stats.update(taiwan_stats)
    _p("localize/Taiwan/language")

    lang0_rows = transform_lang0(translations.lang0, text_transform)
    source_lang0 = lang0_gbk_patch.lang0_path(source_dir)
    lang0_signature = target_signature(
        sources={"pack/lang0.pak": source_lang0},
        translation_hash=hash_lang0_rows(lang0_rows),
        transform_sig=transform_sig,
        code_sig=code_sig,
    )

    def build_lang0() -> dict[str, int]:
        missing_rows: list[tuple[str, str, str, str]] = []
        patched_lang0, lang0_stats = patch_lang0_bytes_by_source(
            source_lang0.read_bytes(),
            lang0_rows,
            ansi_encoding,
            missing_rows=missing_rows,
        )
        (pack_dir / "lang0.pak").write_bytes(patched_lang0)
        write_build_missing_report(
            ROOT / "reports" / "internal" / f"build_missing_lang0.pak_{ansi_encoding}.tsv",
            ["file", "location", "source_text", "translation", "reason"],
            [["lang0.pak", key, source_text, text, reason] for key, source_text, text, reason in missing_rows],
        )
        return lang0_stats

    stats["pack/lang0.pak"] = maybe_build_target(
        manifest=manifest,
        target_id="DBOZero/pack/lang0.pak",
        output_paths=[pack_dir / "lang0.pak"],
        signature=lang0_signature,
        force=force,
        builder=build_lang0,
    )
    _p("pack/lang0.pak")

    tbl_rows = transform_tbl(translations.tbl, text_transform)
    tbl_groups = group_tbl_translations(tbl_rows)
    for file_name in tbl_utf16_patch.TBL_FILES:
        source_tbl = tbl_utf16_patch.tbl_path(source_dir, file_name)
        file_rows = tbl_groups.get(file_name, [])
        signature = target_signature(
            sources={f"pack/{file_name}": source_tbl},
            translation_hash=hash_tbl_rows(file_rows),
            transform_sig=transform_sig,
            code_sig=code_sig,
        )
        stats[f"pack/{file_name}"] = maybe_build_target(
            manifest=manifest,
            target_id=f"DBOZero/pack/{file_name}",
            output_paths=[pack_dir / file_name],
            signature=signature,
            force=force,
            builder=lambda file_name=file_name, file_rows=file_rows: patch_tbl_file(
                source_dir,
                pack_dir,
                file_name,
                file_rows,
                ansi_encoding,
            ),
        )
        _p(f"pack/{file_name}")

    gui0_stats = {}
    source_gui0 = source_dir / "DBOZero" / "pack" / "gui0.pak"
    if source_gui0.is_file():
        gui0_signature = target_signature(
            sources={"pack/gui0.pak": source_gui0},
            translation_hash=stable_json_hash(
                None if gui_font is None else {"file_name": gui_font.file_name, "face_name": gui_font.face_name}
            ),
            transform_sig=transform_sig,
            code_sig=code_sig,
        )
        gui0_stats = maybe_build_target(
            manifest=manifest,
            target_id="DBOZero/pack/gui0.pak",
            output_paths=[pack_dir / "gui0.pak"],
            signature=gui0_signature,
            force=force,
            builder=lambda: write_gui0_pack(source_dir, pack_dir, gui_font),
        )
    if source_gui0.is_file() or gui0_stats:
        _p("pack/gui0.pak")
    copy_missing_pack_files(source_dir, pack_dir)
    _p("copy pack files")

    readme_writer(out_dir)
    _p("write README")
    if gui0_stats:
        stats["pack/gui0.pak"] = gui0_stats
    write_build_manifest(out_dir, manifest)
    _p("write manifest")
    if progress is not None:
        progress.done("完成")
    return stats


def format_stats(stats: dict[str, dict[str, int]]) -> list[str]:
    lines: list[str] = []
    for name, values in stats.items():
        joined = ", ".join(f"{key}={value}" for key, value in values.items())
        lines.append(f"{name}: {joined}")
    return lines


def validate_basic(source_dir: Path, out_dir: Path, label: str, ansi_encoding: str) -> None:
    language_dir = out_dir / "DBOZero" / "localize" / "Taiwan" / "language"
    pack_dir = out_dir / "DBOZero" / "pack"
    for name in install_hanhua.LOCALIZATION_FILES:
        if not (language_dir / name).is_file():
            raise BuildError(f"{label} missing language file: {name}")
    for name in CORE_PACK_FILES:
        source = source_dir / "DBOZero" / "pack" / name
        target = pack_dir / name
        if not target.is_file():
            raise BuildError(f"{label} missing pack file: {name}")
        if source.stat().st_size != target.stat().st_size:
            raise BuildError(f"{label} {name} size changed: {source.stat().st_size} -> {target.stat().st_size}")
    for name in OPTIONAL_PACK_FILES:
        source = source_dir / "DBOZero" / "pack" / name
        if not source.is_file():
            continue
        target = pack_dir / name
        if not target.is_file():
            raise BuildError(f"{label} missing pack file: {name}")
        if target.stat().st_size <= 0:
            raise BuildError(f"{label} empty pack file: {name}")
    for name in ("local_data.dat", "local_sync_data.dat"):
        (language_dir / name).read_bytes().decode(ansi_encoding)
    for file_name, token in TBL_INTERNAL_TOKEN_DENYLIST:
        source_data = (source_dir / "DBOZero" / "pack" / file_name).read_bytes()
        output_data = (pack_dir / file_name).read_bytes()
        needle = token.encode("utf-16le")
        source_count = source_data.count(needle)
        output_count = output_data.count(needle)
        if output_count != source_count:
            raise BuildError(
                f"{label} changed internal title-effect token {file_name}/{token}: "
                f"source={source_count}, output={output_count}"
            )


def run_build_variant(
    job: BuildVariantJob,
    source_dir: Path,
    translations: TranslationSets,
    clean: bool,
    force: bool,
    gui_font: GuiFontPatch | None,
) -> tuple[str, Path, str, dict[str, dict[str, int]]]:
    if job.label == "mainland":
        text_transform = install_hanhua.to_simplified
        readme_writer = write_user_readme
    elif job.label == "taiwan":
        text_transform = install_hanhua.to_traditional
        readme_writer = write_taiwan_user_readme
    else:
        raise BuildError(f"Unknown build variant: {job.label}")

    print(f"=== 開始構建 {job.label} ({job.ansi_encoding}) → {job.out_dir}", flush=True)
    stats = build_one(
        source_dir,
        job.out_dir,
        translations,
        clean=clean,
        force=force,
        text_transform=text_transform,
        transform_sig=job.transform_sig,
        ansi_encoding=job.ansi_encoding,
        readme_writer=readme_writer,
        gui_font=gui_font,
    )
    print(f"=== 完成 {job.label} ===", flush=True)
    return job.label, job.out_dir, job.ansi_encoding, stats


def run_build_jobs(
    jobs: list[BuildVariantJob],
    source_dir: Path,
    translations: TranslationSets,
    *,
    clean: bool,
    force: bool,
    gui_font: GuiFontPatch | None,
    parallel: bool,
) -> list[tuple[str, Path, str, dict[str, dict[str, int]]]]:
    if not parallel or len(jobs) <= 1:
        return [run_build_variant(job, source_dir, translations, clean, force, gui_font) for job in jobs]

    results: dict[str, tuple[str, Path, str, dict[str, dict[str, int]]]] = {}
    with ProcessPoolExecutor(max_workers=len(jobs)) as executor:
        future_to_job = {
            executor.submit(run_build_variant, job, source_dir, translations, clean, force, gui_font): job
            for job in jobs
        }
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            results[job.label] = future.result()
    return [results[job.label] for job in jobs]


def build_all(args: argparse.Namespace) -> int:
    source_dir = source_root(args.source_dir)
    gui_settings = resolve_gui_font_settings(args)
    if args.list_gui_fonts:
        print_gui_font_options(source_dir, gui_settings.font_dir)
        return 0

    require_source_layout(source_dir)
    translations = load_translation_sets(args.data_dir)
    gui_font = resolve_gui_font_patch(source_dir, gui_settings.font_dir, gui_settings.font, gui_settings.font_name)
    blocking_warnings = [
        warning
        for warning in translations.warnings
        if "too-long lang0 text" in warning or "skipped printf mismatch" in warning
    ]
    if blocking_warnings:
        for warning in blocking_warnings[:50]:
            print(f"ERROR: {warning}")
        if len(blocking_warnings) > 50:
            print(f"ERROR: {len(blocking_warnings) - 50} more blocking translation errors hidden")
        raise BuildError(
            "lang0 translations must fit the original field length and keep placeholders; fix data/new_translations.tsv"
        )

    for warning in translations.warnings[:20]:
        print(f"WARNING: {warning}")
    if len(translations.warnings) > 20:
        print(f"WARNING: {len(translations.warnings) - 20} more warnings hidden")

    jobs: list[BuildVariantJob] = []
    if args.variant in ("all", "mainland"):
        jobs.append(BuildVariantJob(
            label="mainland",
            out_dir=inside_repo(args.out),
            transform_sig="mainland-gbk",
            ansi_encoding="gbk",
        ))

    if args.variant in ("all", "taiwan"):
        jobs.append(BuildVariantJob(
            label="taiwan",
            out_dir=inside_repo(args.taiwan_out),
            transform_sig="taiwan-cp950",
            ansi_encoding="cp950",
        ))

    built = run_build_jobs(
        jobs,
        source_dir,
        translations,
        clean=args.force and not args.no_clean,
        force=args.force,
        gui_font=gui_font,
        parallel=args.variant == "all" and not args.no_parallel,
    )

    if not args.no_validate:
        for label, out_dir, ansi_encoding, _stats in built:
            validate_basic(source_dir, out_dir, label, ansi_encoding)

    print(f"Loaded master translations: {translations.master_rows}")
    print(f"Loaded filled queue rows: {translations.queue_rows}")
    for label, out_dir, _ansi_encoding, stats in built:
        print(f"Built {label}: {console_color.path(str(out_dir))}")
        for line in format_stats(stats):
            print(line)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DBO Zero output and output_taiwan from v3 translation tables.")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "src_file")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--out", type=Path, default=ROOT / "output")
    parser.add_argument("--taiwan-out", type=Path, default=ROOT / "output_taiwan")
    parser.add_argument("--variant", choices=("all", "mainland", "taiwan"), default="all")
    parser.add_argument("--no-parallel", action="store_true", help="Build mainland and Taiwan variants sequentially.")
    parser.add_argument("--force", action="store_true", help="Rebuild every target and refresh the incremental manifest.")
    parser.add_argument("--no-incremental", action="store_true", dest="force", help="Alias for --force.")
    parser.add_argument("--no-clean", action="store_true", help="Do not delete old output folders when forcing a rebuild.")
    parser.add_argument("--no-validate", action="store_true", help="Skip basic generated-file checks.")
    parser.add_argument("--gui-font-config", type=Path, default=ROOT / "data" / "gui_font.ini")
    parser.add_argument("--gui-font-dir", type=Path, help="Optional DBOZero\\font directory used for GUI font choices.")
    parser.add_argument("--list-gui-fonts", action="store_true", help="List GUI font choices and exit.")
    parser.add_argument("--gui-font", help="GUI font to write into gui0.pak, matched by file name, stem, family, or full name.")
    parser.add_argument("--gui-font-name", help="Override the internal font face name written into gui0.pak.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        return build_all(parse_args(argv))
    except (
        BuildError,
        install_hanhua.PatchError,
        lang0_gbk_patch.PatchError,
        tbl_utf16_patch.PatchError,
        UnicodeDecodeError,
    ) as exc:
        print(console_color.error(f"ERROR: {exc}"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
