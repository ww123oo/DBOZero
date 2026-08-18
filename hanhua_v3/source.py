from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "src_file" / "DBOZero"

# Only copy original assets consumed by scan.py and build_output.py. Runtime
# logs, account data, executables, caches, and updater files never belong here.
SOURCE_FILES = (
    Path("localize/Taiwan/language/local_data.dat"),
    Path("localize/Taiwan/language/local_sync_data.dat"),
    Path("localize/Taiwan/language/table_quest_text_data.rdf"),
    Path("localize/Taiwan/language/table_text_all_data.rdf"),
    Path("pack/gui0.pak"),
    Path("pack/lang0.pak"),
    Path("pack/tbl0.pak"),
    Path("pack/tbl1.pak"),
    Path("pack/tbl2.pak"),
)


class SourceRefreshError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceFileResult:
    relative_path: Path
    changed: bool
    size: int
    sha256: str


def resolve_game_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    if (path / "pack" / "lang0.pak").is_file():
        return path
    nested = path / "DBOZero"
    if (nested / "pack" / "lang0.pak").is_file():
        return nested
    raise SourceRefreshError(f"找不到遊戲資源目錄：{path}")


def resolve_source_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.name.casefold() == "dbozero":
        return path
    return path / "DBOZero"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_layout(root: Path) -> None:
    missing = [str(relative) for relative in SOURCE_FILES if not (root / relative).is_file()]
    if missing:
        raise SourceRefreshError("缺少必要源檔案：" + ", ".join(missing))


OUTPUT_VARIANT_DIRS = (
    ROOT / "output" / "DBOZero",
    ROOT / "output_taiwan" / "DBOZero",
)

# gui0.pak is copied verbatim into outputs when no font alias changes, so an
# original gui0 always matches the build output and must be excluded from
# patched-content detection.
PASSTHROUGH_FILES = frozenset({Path("pack/gui0.pak")})

# Originals of these files are always valid UTF-8 (English/UTF-8 text), while
# the built patch rewrites them as GBK/CP950. A decode failure flags a patched
# file even when no build outputs are available to compare against.
UTF8_ORIGINAL_FILES = frozenset(
    {
        Path("pack/lang0.pak"),
        Path("localize/Taiwan/language/local_sync_data.dat"),
    }
)


def detect_patched_source(
    game_root: Path, *, variant_dirs: tuple[Path, ...] = OUTPUT_VARIANT_DIRS
) -> list[str]:
    """Return warning lines for live files that look like built patch output.

    The snapshot must always hold original game files. Pulling an already
    patched file would overwrite the clean snapshot and corrupt every
    downstream scan/translation, so refresh refuses to proceed when any file
    is byte-identical to a build output or fails the UTF-8 originality check.
    """
    warnings: list[str] = []
    for relative in SOURCE_FILES:
        live_file = game_root / relative
        if not live_file.is_file() or relative in PASSTHROUGH_FILES:
            continue
        live_hash = sha256_file(live_file)
        matched_variant = next(
            (
                variant.parent.name
                for variant in variant_dirs
                if (variant / relative).is_file() and sha256_file(variant / relative) == live_hash
            ),
            None,
        )
        if matched_variant is not None:
            warnings.append(f"{relative.as_posix()} 與構建輸出 {matched_variant} 逐位元組一致")
        elif relative in UTF8_ORIGINAL_FILES:
            try:
                live_file.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                warnings.append(f"{relative.as_posix()} 不是有效 UTF-8，疑似 GBK/CP950 補丁輸出")
    return warnings


def assert_source_not_patched(game_root: Path, *, variant_dirs: tuple[Path, ...] = OUTPUT_VARIANT_DIRS) -> None:
    warnings = detect_patched_source(game_root, variant_dirs=variant_dirs)
    if warnings:
        details = "\n".join(f"  - {line}" for line in warnings)
        raise SourceRefreshError(
            "遊戲目錄裡的檔案看起來是已打補丁的版本，已停止同步以避免覆蓋原版快照：\n"
            f"{details}\n"
            "請先用遊戲啟動器的檔案校驗／修復功能恢復官方原版檔案，再重新執行。"
        )


def refresh_source(
    game_dir: Path,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    *,
    variant_dirs: tuple[Path, ...] = OUTPUT_VARIANT_DIRS,
) -> list[SourceFileResult]:
    game_root = resolve_game_dir(game_dir)
    source_root = resolve_source_dir(source_dir)
    validate_layout(game_root)
    assert_source_not_patched(game_root, variant_dirs=variant_dirs)

    results: list[SourceFileResult] = []
    for relative in SOURCE_FILES:
        source = game_root / relative
        target = source_root / relative
        source_hash = sha256_file(source)
        changed = not target.is_file() or sha256_file(target) != source_hash
        if changed:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.refresh.tmp")
            try:
                shutil.copy2(source, temporary)
                if sha256_file(temporary) != source_hash:
                    raise SourceRefreshError(f"複製校驗失敗：{relative}")
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        results.append(SourceFileResult(relative, changed, source.stat().st_size, source_hash))

    validate_layout(source_root)
    return results


def compare_source(game_dir: Path, source_dir: Path = DEFAULT_SOURCE_DIR) -> list[SourceFileResult]:
    game_root = resolve_game_dir(game_dir)
    source_root = resolve_source_dir(source_dir)
    validate_layout(game_root)

    results: list[SourceFileResult] = []
    for relative in SOURCE_FILES:
        live_file = game_root / relative
        live_hash = sha256_file(live_file)
        snapshot_file = source_root / relative
        changed = not snapshot_file.is_file() or sha256_file(snapshot_file) != live_hash
        results.append(SourceFileResult(relative, changed, live_file.stat().st_size, live_hash))
    return results
