__all__ = [
    "ALLOWED_PRINTF_MISMATCHES",
    "PatchError",
    "PRINTF_SPEC_RE",
    "auto_detect_game_dir",
    "backup_lang0",
    "build_parser",
    "decode_lang0_value",
    "encode_lang0_value",
    "encoded_text_bytes",
    "find_lang0_value_end",
    "find_lang0_value_start",
    "install",
    "is_game_dir",
    "lang0_path",
    "main",
    "tool_dir",
]

# -*- coding: utf-8 -*-
"""
DBO Zero lang0.pak fixed-size single-value patcher.

This dev tool intentionally patches only quoted values in pack/lang0.pak.
It preserves file size and all unrelated bytes because lang0.pak also contains
metadata records after the visible key/value text.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


class PatchError(RuntimeError):
    pass


PRINTF_SPEC_RE = re.compile(r"%(?:\d+\$)?[+#0\- ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?[diuoxXfFeEgGaAcspn%]")
ALLOWED_PRINTF_MISMATCHES = {
    "DST_INVENTORY_SORT_SUCCESS": (("%s",), ()),
    "DST_ITEM_REMOTE_SELL": (("% o", "%s", "%s"), ("%s", "%s")),
}


def tool_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", tool_dir()))
    return tool_dir()


def default_game_dir() -> Path:
    return Path.cwd()


def dbo_root(game_dir: Path) -> Path:
    return game_dir / "DBOZero"


def lang0_path(game_dir: Path) -> Path:
    return dbo_root(game_dir) / "pack" / "lang0.pak"


def is_game_dir(path: Path) -> bool:
    return (path / "DBOZero" / "pack" / "lang0.pak").is_file()


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


def read_overrides(path: Path | None) -> list[tuple[str, str]]:
    if path is None:
        for candidate in (tool_dir() / "lang0_overrides.tsv", bundled_dir() / "lang0_overrides.tsv"):
            if candidate.exists():
                path = candidate
                break
    if path is None or not path.exists():
        raise PatchError("Missing lang0_overrides.tsv")

    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            if len(row) < 2:
                raise PatchError(f"Invalid lang0_overrides.tsv row {row_no}; need key and text")
            key = row[0].strip()
            if key.lower() == "key":
                continue
            text = row[2] if len(row) >= 3 else row[1]
            if not text:
                continue
            if "\r" in text or "\n" in text:
                raise PatchError(f"Unsupported newline in translation for {key}")
            rows.append((key, text))
    if not rows:
        raise PatchError("No usable rows in lang0_overrides.tsv")
    return rows


def encoded_text_bytes(text: str, encoding: str) -> bytes:
    try:
        return text.encode(encoding)
    except UnicodeEncodeError as exc:
        raise PatchError(f"Text cannot be encoded as {encoding}: {text}") from exc


def decode_lang0_value(raw: bytes) -> str:
    for encoding in ("utf-8", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("gbk", errors="replace")


def unescape_lang0_value(raw: bytes) -> bytes:
    return raw.replace(b'""', b'"')


def encode_lang0_value(text: str, encoding: str = "gbk") -> bytes:
    return encoded_text_bytes(text, encoding).replace(b'"', b'""')


def find_lang0_value_end(data: bytes, start: int, key: str) -> int:
    pos = start
    while True:
        end = data.find(b'"', pos)
        if end < 0:
            raise PatchError(f"Closing quote not found for {key}")
        if end + 1 < len(data) and data[end + 1] == ord('"'):
            pos = end + 2
            continue
        return end


def printf_specs(text: str) -> list[str]:
    return [spec for spec in PRINTF_SPEC_RE.findall(text) if spec != "%%"]


def printf_mismatch_allowed(key: str, old_specs: list[str], new_specs: list[str]) -> bool:
    return ALLOWED_PRINTF_MISMATCHES.get(key) == (tuple(old_specs), tuple(new_specs))



def find_lang0_value_start(data: bytes, key: str) -> int:
    try:
        key_bytes = key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise PatchError(f"lang0 key must be ASCII: {key}") from exc
    pattern = re.compile(re.escape(key_bytes) + rb"[ \t]*=[ \t]*\"")
    matches = list(pattern.finditer(data))
    if not matches:
        return -1
    if len(matches) > 1:
        raise PatchError(f"Duplicate lang0 key pattern: {key}")
    return matches[0].end()


def patch_lang0_bytes(data: bytes, rows: list[tuple[str, str]], encoding: str = "gbk") -> tuple[bytes, dict[str, int]]:
    patch_rows = list({key: text for key, text in rows}.items())
    source = bytes(data)
    patched = bytearray(data)
    changed = 0
    missing = 0
    space_padded = 0
    for key, text in patch_rows:
        start = find_lang0_value_start(source, key)
        if start < 0:
            missing += 1
            continue
        end = find_lang0_value_end(source, start, key)
        old_value = decode_lang0_value(unescape_lang0_value(source[start:end]))
        old_specs = printf_specs(old_value)
        new_specs = printf_specs(text)
        if old_specs != new_specs and not printf_mismatch_allowed(key, old_specs, new_specs):
            raise PatchError(f"Printf placeholder mismatch for {key}: {old_specs} -> {new_specs}")
        new_value = encode_lang0_value(text, encoding)
        old_len = end - start
        if len(new_value) > old_len:
            raise PatchError(
                f"Translation is too long for fixed lang0 field: {key} "
                f"({len(new_value)} bytes > {old_len} bytes): {old_value!r} -> {text!r}"
            )
        pad_len = old_len - len(new_value)
        patched[start : end + 1] = new_value + b'"' + (b" " * pad_len)
        if pad_len:
            space_padded += 1
        changed += 1
    return bytes(patched), {"rows": len(patch_rows), "changed": changed, "missing": missing, "space_padded": space_padded}


def backup_lang0(game_dir: Path) -> Path:
    source = lang0_path(game_dir)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = dbo_root(game_dir) / "hanhua_backup" / f"{stamp}_lang0_gbk"
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source, backup_dir / "lang0.pak")
    return backup_dir


def install(game_dir: Path, overrides_path: Path | None) -> Path:
    if not is_game_dir(game_dir):
        raise PatchError(f"Invalid game folder, DBOZero\\pack\\lang0.pak not found: {game_dir}")
    running = running_game_processes()
    if running:
        raise PatchError("Game/launcher processes are still running: " + ", ".join(running))

    rows = read_overrides(overrides_path)
    path = lang0_path(game_dir)
    original = path.read_bytes()
    patched, stats = patch_lang0_bytes(original, rows)
    if stats["changed"] <= 0:
        raise PatchError("No lang0.pak rows were changed. Check lang0_overrides.tsv keys.")
    backup_dir = backup_lang0(game_dir)
    path.write_bytes(patched)
    report = [
        "DBO Zero lang0.pak GBK patch installed.",
        f"Rows: {stats['rows']}",
        f"Changed: {stats['changed']}",
        f"Missing: {stats['missing']}",
        f"Space padded: {stats['space_padded']}",
    ]
    (backup_dir / "install_report.txt").write_text("\n".join(report), encoding="utf-8")
    return backup_dir


def restore(game_dir: Path, backup_dir: Path) -> None:
    source = backup_dir / "lang0.pak"
    if not source.is_file():
        raise PatchError(f"Backup lang0.pak not found: {source}")
    target = lang0_path(game_dir)
    if not target.parent.is_dir():
        raise PatchError(f"Invalid game folder, pack folder not found: {target.parent}")
    shutil.copy2(source, target)


def command_plan(args: argparse.Namespace) -> int:
    game_dir = args.game_dir.resolve()
    rows = read_overrides(args.overrides)
    source = lang0_path(game_dir)
    if not source.is_file():
        raise PatchError(f"Missing lang0.pak: {source}")
    _patched, stats = patch_lang0_bytes(source.read_bytes(), rows)
    print(f"Game dir: {game_dir}")
    print("No files were changed by plan mode.")
    print(f"Rows: {stats['rows']}")
    print(f"Would change: {stats['changed']}")
    print(f"Missing keys: {stats['missing']}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    backup = install(args.game_dir.resolve(), args.overrides)
    print("Installed lang0.pak GBK patch.")
    print(f"Backup: {backup}")
    return 0


def command_restore(args: argparse.Namespace) -> int:
    restore(args.game_dir.resolve(), args.backup.resolve())
    print(f"Restored lang0.pak from backup: {args.backup.resolve()}")
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
    try:
        game_dir: Path | None = None
        explicit = args.game_dir.resolve()
        if is_game_dir(explicit):
            game_dir = explicit
        else:
            detected = auto_detect_game_dir()
            if detected and messagebox.askyesno(
                "DBOZ lang0 开发版",
                f"检测到游戏目录：\n\n{detected}\n\n是否安装到这个目录？",
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
            messagebox.showerror("选择错误", "请选择 DBO Zero 2.0 游戏根目录。", parent=root)

        if not messagebox.askyesno(
            "确认安装",
            "安装前请关闭游戏和启动器。\n\n"
            f"游戏目录：\n{game_dir}\n\n"
            "本工具只修改 DBOZero\\pack\\lang0.pak，并会先备份原文件。\n\n"
            "现在开始安装？",
            parent=root,
        ):
            return 1

        root.config(cursor="watch")
        root.update()
        backup = install(game_dir, args.overrides)
        root.config(cursor="")
        messagebox.showinfo("安装完成", f"lang0.pak 补丁安装完成。\n\n备份位置：\n{backup}", parent=root)
        return 0
    except PatchError as exc:
        root.config(cursor="")
        messagebox.showerror("安装失败", str(exc), parent=root)
        return 2
    finally:
        root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DBO Zero lang0.pak GBK patch installer")
    parser.add_argument("--game-dir", type=Path, default=default_game_dir())
    parser.add_argument("--overrides", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("install")
    sub.add_parser("wizard")
    restore_cmd = sub.add_parser("restore")
    restore_cmd.add_argument("--backup", type=Path, required=True)
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
