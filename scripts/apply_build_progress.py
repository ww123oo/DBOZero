#!/usr/bin/env python3
"""Patch build_output.py so dboc build shows a terminal progress bar."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
target = root / "build_output.py"
if not target.exists():
    print("missing", target)
    sys.exit(1)

t = target.read_text(encoding="utf-8")
if "_BuildProgress" in t and '_p("pack/lang0.pak")' in t:
    print("already patched")
    sys.exit(0)

if "from pathlib import Path" not in t:
    print("unexpected build_output.py layout")
    sys.exit(1)

if "_BuildProgress" not in t:
    t = t.replace(
        "from pathlib import Path\n",
        "from pathlib import Path\n\n"
        "try:\n"
        "    from hanhua_v3.runtime.build_progress import Progress as _BuildProgress\n"
        "except Exception:  # pragma: no cover\n"
        "    try:\n"
        "        from build_progress import Progress as _BuildProgress\n"
        "    except Exception:\n"
        "        _BuildProgress = None\n",
        1,
    )

old = '''    manifest = load_build_manifest(out_dir)\n    code_sig = build_code_hash()\n    stats: dict[str, dict[str, int]] = {}\n'''
new = '''    manifest = load_build_manifest(out_dir)\n    code_sig = build_code_hash()\n    stats: dict[str, dict[str, int]] = {}\n    progress = _BuildProgress(9, label=ansi_encoding) if _BuildProgress else None\n\n    def _p(msg: str) -> None:\n        if progress is not None:\n            progress.step(msg)\n        else:\n            print(f"  · {msg}", flush=True)\n'''
if old not in t:
    print("anchor1 not found")
    sys.exit(1)
t = t.replace(old, new, 1)

old = '''        stats.update(taiwan_stats)\n\n    lang0_rows = transform_lang0(translations.lang0, text_transform)\n'''
new = '''        stats.update(taiwan_stats)\n    _p("localize/Taiwan/language")\n\n    lang0_rows = transform_lang0(translations.lang0, text_transform)\n'''
if old in t:
    t = t.replace(old, new, 1)

old = '''        builder=build_lang0,\n    )\n\n    tbl_rows = transform_tbl(translations.tbl, text_transform)\n'''
new = '''        builder=build_lang0,\n    )\n    _p("pack/lang0.pak")\n\n    tbl_rows = transform_tbl(translations.tbl, text_transform)\n'''
if old in t:
    t = t.replace(old, new, 1)

old = '''                ansi_encoding,\n            ),\n        )\n\n    gui0_stats = {}\n'''
new = '''                ansi_encoding,\n            ),\n        )\n        _p(f"pack/{file_name}")\n\n    gui0_stats = {}\n'''
if old in t:
    t = t.replace(old, new, 1)

old = '''    copy_missing_pack_files(source_dir, pack_dir)\n\n    readme_writer(out_dir)\n    if gui0_stats:\n        stats["pack/gui0.pak"] = gui0_stats\n    write_build_manifest(out_dir, manifest)\n    return stats\n'''
new = '''    if gui0_stats or source_gui0.is_file():\n        _p("pack/gui0.pak")\n    copy_missing_pack_files(source_dir, pack_dir)\n    _p("copy pack files")\n\n    readme_writer(out_dir)\n    _p("write README")\n    if gui0_stats:\n        stats["pack/gui0.pak"] = gui0_stats\n    write_build_manifest(out_dir, manifest)\n    _p("write manifest")\n    if progress is not None:\n        progress.done("完成")\n    return stats\n'''
if old in t:
    t = t.replace(old, new, 1)

old = '''    built = run_build_jobs(\n        jobs,\n        source_dir,\n        translations,\n        clean=args.force and not args.no_clean,\n        force=args.force,\n        gui_font=gui_font,\n        parallel=args.variant == "all" and not args.no_parallel,\n    )\n'''
new = '''    for job in jobs:\n        print(f"=== 開始構建 {job.label} ({job.ansi_encoding}) → {job.out_dir} ===", flush=True)\n    built = run_build_jobs(\n        jobs,\n        source_dir,\n        translations,\n        clean=args.force and not args.no_clean,\n        force=args.force,\n        gui_font=gui_font,\n        parallel=args.variant == "all" and not args.no_parallel,\n    )\n'''
if old in t:
    t = t.replace(old, new, 1)

compile(t, "build_output.py", "exec")
target.write_text(t, encoding="utf-8", newline="\n")
print("OK: patched", target)
