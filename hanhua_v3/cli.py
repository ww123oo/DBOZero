from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import __version__, batch_translate_queue, config, scan
from .config import ConfigError
from .recover import RecoveryError, recover_from_git
from .resource_writer import WriteError, write_queue
from .source import (
    DEFAULT_SOURCE_DIR,
    SourceRefreshError,
    compare_source,
    detect_patched_source,
    refresh_source,
    resolve_game_dir,
    resolve_source_dir,
)


__all__ = [
    "CliError", "DEFAULT_QUEUE", "ROOT", "add_build_args", "add_source_args", "add_translate_args",
    "build_parser", "create_checkpoint", "git_command", "main", "print_refresh_results", "queue_keys_from_rows",
    "read_git_queue_rows", "read_queue_rows", "run_build", "run_config", "run_recover", "run_refresh", "run_scan",
    "run_status", "run_translate", "run_update", "run_write",
]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "new_translations.tsv"


class CliError(RuntimeError):
    pass


def git_command(*args: str, capture: bool = False) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-c", "user.name=dboc", "-c", "user.email=dboc-local@localhost", *args]
    return subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)


def create_checkpoint() -> str:
    try:
        status = git_command("status", "--porcelain", "--untracked-files=no", capture=True).stdout.decode("utf-8", errors="replace")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CliError("無法檢查 Git 狀態，已停止源檔案刷新") from exc
    message = f"Checkpoint before source refresh {datetime.now():%Y-%m-%d %H:%M:%S}"
    try:
        if status.strip():
            git_command("add", "-u")
            git_command("commit", "-m", message)
        else:
            git_command("commit", "--allow-empty", "-m", message)
        return git_command("rev-parse", "--short", "HEAD", capture=True).stdout.decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CliError("無法建立刷新前 Git 恢復點，未讀取實際遊戲目錄") from exc


def queue_keys_from_rows(rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {((row.get("文件") or row.get("file") or "").strip(), (row.get("原文") or row.get("source_text") or "").strip()) for row in rows if (row.get("文件") or row.get("file") or "").strip() and (row.get("原文") or row.get("source_text") or "").strip()}


def read_queue_rows(path: Path = DEFAULT_QUEUE) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_git_queue_rows(ref: str) -> list[dict[str, str]]:
    try:
        payload = git_command("show", f"{ref}:data/new_translations.tsv", capture=True).stdout.decode("utf-8-sig")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        raise CliError(f"無法從 Git 引用讀取翻譯佇列：{ref}") from exc
    return list(csv.DictReader(io.StringIO(payload), delimiter="\t"))


def print_refresh_results(results) -> None:
    changed = sum(result.changed for result in results)
    print(f"源檔案同步完成：changed={changed}, unchanged={len(results) - changed}")
    for result in results:
        print(f"  [{'更新' if result.changed else '一致'}] {result.relative_path.as_posix()} ({result.size} bytes)")


def run_refresh(args: argparse.Namespace, *, checkpoint: bool = True) -> int:
    if checkpoint:
        print(f"刷新前 Git 恢復點：{create_checkpoint()}")
    print_refresh_results(refresh_source(args.game_dir, args.source_dir))
    return 0


def run_scan(args: argparse.Namespace) -> int:
    return scan.main(["--source-dir", str(args.source_dir), "--data-dir", str(ROOT / "data"), "--report-dir", str(ROOT / "reports")])


def run_translate(args: argparse.Namespace, only_keys: set[tuple[str, str]] | None = None) -> int:
    if args.new_since:
        only_keys = queue_keys_from_rows(read_queue_rows(args.queue)) - queue_keys_from_rows(read_git_queue_rows(args.new_since))
        print(f"相對 {args.new_since} 的新增原文：{len(only_keys)}")
    stats = batch_translate_queue.translate_queue(queue_path=args.queue, out_path=args.queue, translations_path=ROOT / "data" / "translations.tsv", fill_all=args.fill_all, replace_existing=args.replace_existing, ignore_existing_map=args.ignore_existing_map, only_keys=only_keys)
    print(f"翻譯完成：selected={stats.selected}, filled={stats.filled}, empty_after={stats.empty_after}")
    print(f"複用現有譯文：{stats.reused_existing}")
    print(f"翻譯佇列：{args.queue}")
    return 0


def run_write(args: argparse.Namespace) -> int:
    try:
        stats = write_queue(args.queue, args.source_dir, args.output_dir)
    except WriteError as exc:
        raise CliError(f"資源寫入停止（fail-closed）：{exc}") from exc
    total = sum(stats.values())
    print(f"資源寫入完成：files={len(stats)}, changed={total}")
    for name, changed in stats.items():
        print(f"  {name}: changed={changed}")
    return 0


def run_recover(args: argparse.Namespace) -> int:
    stats = recover_from_git(args.refs, dry_run=args.dry_run)
    print(f"Git 參考：{', '.join(stats.references)}")
    print(f"恢復佇列譯文：{stats.queue_filled}")
    print(f"恢復主表譯文：{stats.master_added}")
    print(f"當前源中不存在：{stats.missing_current_source}")
    print(f"歷史譯法衝突：{stats.conflicts}（按參數順序保留第一個）")
    if args.dry_run:
        print("dry-run：未寫入檔案")
    return 0


def run_build(args: argparse.Namespace) -> int:
    import build_output
    build_args = ["--source-dir", str(args.source_dir), "--variant", args.variant]
    if args.force:
        build_args.append("--force")
    if args.no_parallel:
        build_args.append("--no-parallel")
    return build_output.main(build_args)


def run_update(args: argparse.Namespace) -> int:
    previous_keys = queue_keys_from_rows(read_queue_rows(args.queue))
    print(f"刷新前 Git 恢復點：{create_checkpoint()}")
    print("\n[1/5] 同步實際遊戲源檔案")
    print_refresh_results(refresh_source(args.game_dir, args.source_dir))
    print("\n[2/5] 掃描新版詞條")
    run_scan(args)
    current_keys = queue_keys_from_rows(read_queue_rows(args.queue))
    new_keys = current_keys - previous_keys
    print(f"本次新增原文：{len(new_keys)}")
    if args.recover_refs:
        print("\n[歷史恢復] 回填 Git 中仍匹配當前源的譯文")
        recovery = recover_from_git(args.recover_refs)
        print(f"恢復佇列譯文：{recovery.queue_filled}，恢復主表譯文：{recovery.master_added}")
    print("\n[3/5] 翻譯新增詞條")
    translate_args = argparse.Namespace(queue=args.queue, fill_all=args.fill_all, replace_existing=False, ignore_existing_map=False, new_since=None)
    run_translate(translate_args, only_keys=None if args.translate_all else new_keys)
    print("\n[4/5] 寫入翻譯資源")
    run_write(args)
    print("\n[5/5] 構建並驗證補丁")
    return run_build(args)


def run_status(args: argparse.Namespace) -> int:
    rows = read_queue_rows(args.queue)
    filled = sum(bool((row.get("填写中文") or row.get("zh_cn") or "").strip()) for row in rows)
    print(f"翻譯佇列：total={len(rows)}, filled={filled}, empty={len(rows) - filled}")
    try:
        comparison = compare_source(args.game_dir, args.source_dir)
    except SourceRefreshError as exc:
        print(f"實際遊戲源檢查失敗：{exc}")
        return 2
    different = [result for result in comparison if result.changed]
    print(f"源快照：different={len(different)}, matched={len(comparison) - len(different)}")
    for result in different:
        print(f"  [不同] {result.relative_path.as_posix()}")
    patched_warnings = detect_patched_source(resolve_game_dir(args.game_dir))
    for warning in patched_warnings:
        print(f"  [疑似補丁] {warning}")
    if patched_warnings:
        print("遊戲目錄疑似已打補丁，請先恢復官方原版檔案再執行 dboc refresh/update")
        return 2
    return 1 if different else 0


def run_config(args: argparse.Namespace) -> int:
    if args.game_dir is not None:
        game_root = resolve_game_dir(args.game_dir)
        config.save_game_dir(game_root)
        print(f"已儲存遊戲目錄：{game_root}")
        return 0
    print(config.load())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dboc")
    sub = parser.add_subparsers(dest="command", required=True)
    for command, func in (("refresh", run_refresh), ("scan", run_scan), ("translate", run_translate), ("write", run_write), ("build", run_build), ("update", run_update), ("recover", run_recover), ("status", run_status), ("config", run_config)):
        p = sub.add_parser(command)
        p.set_defaults(func=func)
        add_source_args(p)
        if command in {"scan", "translate", "write", "build", "update", "recover", "status"}:
            add_queue_args(p)
        if command in {"write", "build", "update"}:
            p.add_argument("--output-dir", type=Path, default=ROOT / "output_taiwan")
        if command in {"build", "update"}:
            add_build_args(p)
        if command == "translate":
            add_translate_args(p)
        if command == "update":
            add_translate_args(p)
            p.add_argument("--translate-all", action="store_true")
            p.add_argument("--recover-refs", nargs="*", default=[])
        if command == "recover":
            p.add_argument("refs", nargs="+", help="Git refs to recover from")
            p.add_argument("--dry-run", action="store_true")
        if command == "config":
            p.add_argument("--game-dir", type=Path)
    return parser


def add_queue_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)


def add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--game-dir", type=Path, default=None)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "src_file" / "DBOZero")


def add_translate_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fill-all", action="store_true")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--ignore-existing-map", action="store_true")
    parser.add_argument("--new-since")


def add_build_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--variant", default="taiwan")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-parallel", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (CliError, ConfigError, RecoveryError, SourceRefreshError, WriteError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
