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
from .source import (
    DEFAULT_SOURCE_DIR,
    SourceRefreshError,
    compare_source,
    detect_patched_source,
    refresh_source,
    resolve_game_dir,
    resolve_source_dir,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "new_translations.tsv"


class CliError(RuntimeError):
    pass


def git_command(*args: str, capture: bool = False) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args]
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def create_checkpoint() -> str:
    try:
        status = git_command("status", "--porcelain", "--untracked-files=no", capture=True).stdout.decode(
            "utf-8", errors="replace"
        )
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
    return {
        ((row.get("文件") or "").strip(), (row.get("原文") or "").strip())
        for row in rows
        if (row.get("文件") or "").strip() and (row.get("原文") or "").strip()
    }


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
        state = "更新" if result.changed else "一致"
        print(f"  [{state}] {result.relative_path.as_posix()} ({result.size} bytes)")


def run_refresh(args: argparse.Namespace, *, checkpoint: bool = True) -> int:
    if checkpoint:
        commit = create_checkpoint()
        print(f"刷新前 Git 恢復點：{commit}")
    results = refresh_source(args.game_dir, args.source_dir)
    print_refresh_results(results)
    return 0


def run_scan(args: argparse.Namespace) -> int:
    return scan.main(
        [
            "--source-dir",
            str(args.source_dir),
            "--data-dir",
            str(ROOT / "data"),
            "--report-dir",
            str(ROOT / "reports"),
        ]
    )


def run_translate(args: argparse.Namespace, only_keys: set[tuple[str, str]] | None = None) -> int:
    if args.new_since:
        old_keys = queue_keys_from_rows(read_git_queue_rows(args.new_since))
        current_keys = queue_keys_from_rows(read_queue_rows(args.queue))
        only_keys = current_keys - old_keys
        print(f"相對 {args.new_since} 的新增原文：{len(only_keys)}")

    stats = batch_translate_queue.translate_queue(
        queue_path=args.queue,
        out_path=args.queue,
        translations_path=ROOT / "data" / "translations.tsv",
        fill_all=args.fill_all,
        replace_existing=args.replace_existing,
        ignore_existing_map=args.ignore_existing_map,
        only_keys=only_keys,
    )
    print(f"翻譯完成：selected={stats.selected}, filled={stats.filled}, empty_after={stats.empty_after}")
    print(f"複用現有譯文：{stats.reused_existing}")
    print(f"翻譯佇列：{args.queue}")
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

    build_args = [
        "--source-dir",
        str(args.source_dir),
        "--variant",
        args.variant,
    ]
    if args.force:
        build_args.append("--force")
    if args.no_parallel:
        build_args.append("--no-parallel")
    return build_output.main(build_args)


def run_update(args: argparse.Namespace) -> int:
    previous_keys = queue_keys_from_rows(read_queue_rows(args.queue))
    commit = create_checkpoint()
    print(f"刷新前 Git 恢復點：{commit}")

    print("\n[1/4] 同步實際遊戲源檔案")
    print_refresh_results(refresh_source(args.game_dir, args.source_dir))

    print("\n[2/4] 掃描新版詞條")
    run_scan(args)
    current_keys = queue_keys_from_rows(read_queue_rows(args.queue))
    new_keys = current_keys - previous_keys
    print(f"本次新增原文：{len(new_keys)}")

    if args.recover_refs:
        print("\n[歷史恢復] 回填 Git 中仍匹配當前源的譯文")
        recovery = recover_from_git(args.recover_refs)
        print(f"恢復佇列譯文：{recovery.queue_filled}，恢復主表譯文：{recovery.master_added}")

    print("\n[3/4] 翻譯本次新增詞條")
    translate_args = argparse.Namespace(
        queue=args.queue,
        fill_all=args.fill_all,
        replace_existing=False,
        ignore_existing_map=False,
        new_since=None,
    )
    run_translate(translate_args, only_keys=None if args.translate_all else new_keys)

    print("\n[4/4] 構建並驗證補丁")
    return run_build(args)


def run_status(args: argparse.Namespace) -> int:
    rows = read_queue_rows(args.queue)
    filled = sum(bool((row.get("填写中文") or "").strip()) for row in rows)
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
        print(f"已寫入 {config.CONFIG_PATH}：game_dir = {game_root}")
    if args.show or args.game_dir is None:
        try:
            resolved = config.resolve_game_dir(None)
        except ConfigError as exc:
            print(exc)
            return 2
        print(f"當前生效的遊戲目錄：{resolve_game_dir(resolved)}")
        if config.CONFIG_PATH.is_file():
            print(f"設定檔：{config.CONFIG_PATH}")
        else:
            print("設定檔：未建立（當前值來自環境變數或自動探測）")
    return 0


def add_source_args(parser: argparse.ArgumentParser, *, include_game: bool) -> None:
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="src_file 或 src_file/DBOZero 路徑",
    )
    if include_game:
        parser.add_argument(
            "--game-dir",
            type=Path,
            default=None,
            help="實際遊戲 DBOZero 目錄，僅作為只讀同步源；缺省時依次讀取 DBOC_GAME_DIR 環境變數、dboc.toml 和自動探測",
        )


def add_build_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--variant", choices=("all", "mainland", "taiwan"), default="all")
    parser.add_argument("--force", action="store_true", help="強制清理並重建輸出")
    parser.add_argument("--no-parallel", action="store_true", help="順序構建大陸與台灣版本")


def add_translate_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--fill-all", action="store_true", help="對選中列啟用兜底詞組翻譯")
    parser.add_argument("--replace-existing", action="store_true", help="重新產生已填寫列")
    parser.add_argument("--ignore-existing-map", action="store_true", help="不複用 translations.tsv 同原文譯法")
    parser.add_argument("--new-since", help="只翻譯相對指定 Git 引用新增的原文，例如 HEAD")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dboc", description="DBO Zero 漢化 v3 統一命令列工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update = subparsers.add_parser("update", help="一鍵完成恢復點、源刷新、掃描、翻譯和構建")
    add_source_args(update, include_game=True)
    add_build_args(update)
    update.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    update.add_argument("--fill-all", action="store_true", help="為本次新增詞條啟用兜底詞組翻譯")
    update.add_argument("--translate-all", action="store_true", help="處理全部空白佇列，而非僅本次新增")
    update.add_argument("--recover-ref", action="append", dest="recover_refs", default=[], help="掃描後從指定 Git 引用恢復譯文，可重複")
    update.set_defaults(handler=run_update)

    refresh = subparsers.add_parser("refresh", help="建立恢復點並從實際遊戲目錄刷新必要源檔案")
    add_source_args(refresh, include_game=True)
    refresh.set_defaults(handler=run_refresh)

    scan_parser = subparsers.add_parser("scan", help="掃描 src_file 並刷新翻譯佇列")
    add_source_args(scan_parser, include_game=False)
    scan_parser.set_defaults(handler=run_scan)

    translate = subparsers.add_parser("translate", help="批量填寫可確定的佇列譯文")
    add_translate_args(translate)
    translate.set_defaults(handler=run_translate)

    recover = subparsers.add_parser("recover", help="從 Git 歷史狀態結構化恢復遺失譯文")
    recover.add_argument("--ref", action="append", dest="refs", required=True, help="Git 引用，可重複並按優先順序排列")
    recover.add_argument("--dry-run", action="store_true", help="只統計，不寫入 TSV")
    recover.set_defaults(handler=run_recover)

    build = subparsers.add_parser("build", help="構建大陸簡中和台灣繁中補丁")
    add_source_args(build, include_game=False)
    add_build_args(build)
    build.set_defaults(handler=run_build)

    status = subparsers.add_parser("status", help="檢查翻譯佇列和實際遊戲源快照差異")
    add_source_args(status, include_game=True)
    status.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    status.set_defaults(handler=run_status)

    config_parser = subparsers.add_parser("config", help="查看或寫入本機遊戲目錄設定（dboc.toml）")
    config_parser.add_argument("--game-dir", type=Path, default=None, help="校驗並寫入遊戲目錄到 dboc.toml")
    config_parser.add_argument("--show", action="store_true", help="顯示當前生效的遊戲目錄")
    config_parser.set_defaults(handler=run_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    if hasattr(args, "source_dir"):
        args.source_dir = resolve_source_dir(args.source_dir)
    if getattr(args, "game_dir", None) is None and hasattr(args, "game_dir") and args.command != "config":
        args.game_dir = config.resolve_game_dir(None)
    try:
        return args.handler(args)
    except (CliError, ConfigError, RecoveryError, SourceRefreshError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
