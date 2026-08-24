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

text = text.replace(
    """    taiwan_stats = maybe_build_target(
        manifest=manifest,
        target_id=\"DBOZero/localize/Taiwan/language\",""",
    """    tick(\"localize/Taiwan/language\")\n    taiwan_stats = maybe_build_target(\n        manifest=manifest,\n        target_id=\"DBOZero/localize/Taiwan/language\",""",
    1,
)
text = text.replace(
    """    stats[\"pack/lang0.pak\"] = maybe_build_target(\n        manifest=manifest,\n        target_id=\"DBOZero/pack/lang0.pak\",""",
    """    tick(\"pack/lang0.pak\")\n    stats[\"pack/lang0.pak\"] = maybe_build_target(\n        manifest=manifest,\n        target_id=\"DBOZero/pack/lang0.pak\",""",
    1,
)
text = text.replace(
    """    for file_name in tbl_utf16_patch.TBL_FILES:\n        source_tbl = tbl_utf16_patch.tbl_path(source_dir, file_name)""",
    """    for file_name in tbl_utf16_patch.TBL_FILES:\n        tick(f\"pack/{file_name}\")\n        source_tbl = tbl_utf16_patch.tbl_path(source_dir, file_name)""",
    1,
)
text = text.replace(
    """        gui0_stats = maybe_build_target(\n            manifest=manifest,\n            target_id=\"DBOZero/pack/gui0.pak\",""",
    """        tick(\"pack/gui0.pak\")\n        gui0_stats = maybe_build_target(\n            manifest=manifest,\n            target_id=\"DBOZero/pack/gui0.pak\",""",
    1,
)
text = text.replace(
    """    copy_missing_pack_files(source_dir, pack_dir)\n\n    readme_writer(out_dir)\n    if gui0_stats:\n        stats[\"pack/gui0.pak\"] = gui0_stats\n    write_build_manifest(out_dir, manifest)\n    return stats\n""",
    """    else:\n        tick(\"pack/gui0.pak (略過)\")\n    tick(\"copy pack files\")\n    copy_missing_pack_files(source_dir, pack_dir)\n\n    tick(\"write README\")\n    readme_writer(out_dir)\n    if gui0_stats:\n        stats[\"pack/gui0.pak\"] = gui0_stats\n    tick(\"write manifest\")\n    write_build_manifest(out_dir, manifest)\n    return stats\n""",
    1,
)

old_v = """    stats = build_one(\n        source_dir,\n        job.out_dir,\n        translations,\n        clean=clean,\n        force=force,\n        text_transform=text_transform,\n        transform_sig=job.transform_sig,\n        ansi_encoding=job.ansi_encoding,\n        readme_writer=readme_writer,\n        gui_font=gui_font,\n    )\n    return job.label, job.out_dir, job.ansi_encoding, stats\n"""
new_v = """    progress = BuildProgress(9, label=job.label)\n    print(f\"=== 開始構建 {job.label} ({job.ansi_encoding}) → {job.out_dir} ===\", flush=True)\n    stats = build_one(\n        source_dir,\n        job.out_dir,\n        translations,\n        clean=clean,\n        force=force,\n        text_transform=text_transform,\n        transform_sig=job.transform_sig,\n        ansi_encoding=job.ansi_encoding,\n        readme_writer=readme_writer,\n        gui_font=gui_font,\n        progress=progress,\n    )\n    print(f\"=== 完成 {job.label} ===\", flush=True)\n    return job.label, job.out_dir, job.ansi_encoding, stats\n"""
if old_v not in text:
    print("run_build_variant body not found", file=sys.stderr)
    sys.exit(1)
text = text.replace(old_v, new_v, 1)

text = text.replace(
    """    require_source_layout(source_dir)\n    translations = load_translation_sets(args.data_dir)\n""",
    """    require_source_layout(source_dir)\n    print(\"[準備] 載入翻譯表…\", flush=True)\n    translations = load_translation_sets(args.data_dir)\n    print(f\"[準備] 主表 {translations.master_rows} 列，佇列已填 {translations.queue_rows} 列\", flush=True)\n""",
    1,
)
text = text.replace(
    """    if not args.no_validate:\n        for label, out_dir, ansi_encoding, _stats in built:\n            validate_basic(source_dir, out_dir, label, ansi_encoding)\n""",
    """    if not args.no_validate:\n        print(\"[驗證] 檢查輸出檔案…\", flush=True)\n        for i, (label, out_dir, ansi_encoding, _stats) in enumerate(built, 1):\n            print(f\"[驗證] ({i}/{len(built)}) {label}\", flush=True)\n            validate_basic(source_dir, out_dir, label, ansi_encoding)\n""",
    1,
)

path.write_text(text, encoding="utf-8")
print(f"patched {path}")
