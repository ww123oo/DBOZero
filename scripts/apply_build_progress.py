#!/usr/bin/env python3
"""Patch build_output.py to show progress during dboc build. Idempotent."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
path = root / "build_output.py"
text = path.read_text(encoding="utf-8")
if "BuildProgress" in text and "tick(" in text:
    print("already patched")
    sys.exit(0)

imp = "from hanhua_v3.runtime import console_color, install_hanhua, lang0_gbk_patch, tbl_utf16_patch"
new_imp = imp + "\nfrom hanhua_v3.runtime.build_progress import BuildProgress"
if imp not in text:
    print("import line not found", file=sys.stderr)
    sys.exit(1)
text = text.replace(imp, new_imp, 1)

old = """    readme_writer: Callable[[Path], None],
    gui_font: GuiFontPatch | None,
) -> dict[str, dict[str, int]]:"""
new = """    readme_writer: Callable[[Path], None],
    gui_font: GuiFontPatch | None,
    progress: BuildProgress | None = None,
) -> dict[str, dict[str, int]]:"""
if old not in text:
    print("build_one signature not found", file=sys.stderr)
    sys.exit(1)
text = text.replace(old, new, 1)

old = """    stats: dict[str, dict[str, int]] = {}

    taiwan_sources = {"""
new = """    stats: dict[str, dict[str, int]] = {}

    def tick(message: str) -> None:
        if progress is not None:
            progress.step(message)

    taiwan_sources = {"""
text = text.replace(old, new, 1)

pairs = [
(
"""    taiwan_stats = maybe_build_target(
        manifest=manifest,
        target_id=\"DBOZero/localize/Taiwan/language\",""",
"""    tick(\"localize/Taiwan/language\")
    taiwan_stats = maybe_build_target(
        manifest=manifest,
        target_id=\"DBOZero/localize/Taiwan/language\",""",
),
(
"""    stats[\"pack/lang0.pak\"] = maybe_build_target(
        manifest=manifest,
        target_id=\"DBOZero/pack/lang0.pak\",""",
"""    tick(\"pack/lang0.pak\")
    stats[\"pack/lang0.pak\"] = maybe_build_target(
        manifest=manifest,
        target_id=\"DBOZero/pack/lang0.pak\",""",
),
(
"""    for file_name in tbl_utf16_patch.TBL_FILES:
        source_tbl = tbl_utf16_patch.tbl_path(source_dir, file_name)""",
"""    for file_name in tbl_utf16_patch.TBL_FILES:
        tick(f\"pack/{file_name}\")
        source_tbl = tbl_utf16_patch.tbl_path(source_dir, file_name)""",
),
(
"""        gui0_stats = maybe_build_target(
            manifest=manifest,
            target_id=\"DBOZero/pack/gui0.pak\",""",
"""        tick(\"pack/gui0.pak\")
        gui0_stats = maybe_build_target(
            manifest=manifest,
            target_id=\"DBOZero/pack/gui0.pak\",""",
),
(
"""    copy_missing_pack_files(source_dir, pack_dir)

    readme_writer(out_dir)
    if gui0_stats:
        stats[\"pack/gui0.pak\"] = gui0_stats
    write_build_manifest(out_dir, manifest)
    return stats
""",
"""    else:
        tick(\"pack/gui0.pak (略過)\")
    tick(\"copy pack files\")
    copy_missing_pack_files(source_dir, pack_dir)

    tick(\"write README\")
    readme_writer(out_dir)
    if gui0_stats:
        stats[\"pack/gui0.pak\"] = gui0_stats
    tick(\"write manifest\")
    write_build_manifest(out_dir, manifest)
    return stats
""",
),
(
"""    stats = build_one(
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
    return job.label, job.out_dir, job.ansi_encoding, stats
""",
"""    progress = BuildProgress(9, label=job.label)
    print(f\"=== 開始構建 {job.label} ({job.ansi_encoding}) → {job.out_dir} ===\", flush=True)
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
        progress=progress,
    )
    print(f\"=== 完成 {job.label} ===\", flush=True)
    return job.label, job.out_dir, job.ansi_encoding, stats
""",
),
(
"""    require_source_layout(source_dir)
    translations = load_translation_sets(args.data_dir)
""",
"""    require_source_layout(source_dir)
    print(\"[準備] 載入翻譯表…\", flush=True)
    translations = load_translation_sets(args.data_dir)
    print(f\"[準備] 主表 {translations.master_rows} 列，佇列已填 {translations.queue_rows} 列\", flush=True)
""",
),
(
"""    if not args.no_validate:
        for label, out_dir, ansi_encoding, _stats in built:
            validate_basic(source_dir, out_dir, label, ansi_encoding)
""",
"""    if not args.no_validate:
        print(\"[驗證] 檢查輸出檔案…\", flush=True)
        for i, (label, out_dir, ansi_encoding, _stats) in enumerate(built, 1):
            print(f\"[驗證] ({i}/{len(built)}) {label}\", flush=True)
            validate_basic(source_dir, out_dir, label, ansi_encoding)
""",
),
]

for a, b in pairs:
    if a not in text:
        print("pattern not found:", repr(a[:60]), file=sys.stderr)
        sys.exit(1)
    text = text.replace(a, b, 1)

path.write_text(text, encoding="utf-8")
print(f"patched {path}")
