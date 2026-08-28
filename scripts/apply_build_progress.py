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
if "_BuildProgress" in t and '_p("pack/lang0.pak")' in t and "progress.done" in t:
    print("already patched")
    sys.exit(0)

if "from pathlib import Path\n" not in t:
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

def must_replace(old: str, new: str, name: str) -> None:
    global t
    if old not in t:
        print(f"ERROR: anchor not found: {name}")
        sys.exit(1)
    t = t.replace(old, new, 1)
    print(f"ok {name}")

must_replace(
    "    manifest = load_build_manifest(out_dir)\n"
    "    code_sig = build_code_hash()\n"
    "    stats: dict[str, dict[str, int]] = {}\n",
    "    manifest = load_build_manifest(out_dir)\n"
    "    code_sig = build_code_hash()\n"
    "    stats: dict[str, dict[str, int]] = {}\n"
    "    progress = _BuildProgress(9, label=ansi_encoding) if _BuildProgress else None\n"
    "\n"
    "    def _p(msg: str) -> None:\n"
    "        if progress is not None:\n"
    "            progress.step(msg)\n"
    "        else:\n"
    '            print(f"  · {msg}", flush=True)\n',
    "init",
)

must_replace(
    "        stats.update(taiwan_stats)\n"
    "\n"
    "    lang0_rows = transform_lang0(translations.lang0, text_transform)\n",
    "        stats.update(taiwan_stats)\n"
    '    _p("localize/Taiwan/language")\n'
    "\n"
    "    lang0_rows = transform_lang0(translations.lang0, text_transform)\n",
    "taiwan",
)

must_replace(
    "        builder=build_lang0,\n"
    "    )\n"
    "\n"
    "    tbl_rows = transform_tbl(translations.tbl, text_transform)\n",
    "        builder=build_lang0,\n"
    "    )\n"
    '    _p("pack/lang0.pak")\n'
    "\n"
    "    tbl_rows = transform_tbl(translations.tbl, text_transform)\n",
    "lang0",
)

must_replace(
    "            builder=lambda file_name=file_name, file_rows=file_rows: patch_tbl_file(\n"
    "                source_dir,\n"
    "                pack_dir,\n"
    "                file_name,\n"
    "                file_rows,\n"
    "                ansi_encoding,\n"
    "            ),\n"
    "        )\n"
    "\n"
    "    gui0_stats = {}\n",
    "            builder=lambda file_name=file_name, file_rows=file_rows: patch_tbl_file(\n"
    "                source_dir,\n"
    "                pack_dir,\n"
    "                file_name,\n"
    "                file_rows,\n"
    "                ansi_encoding,\n"
    "            ),\n"
    "        )\n"
    '        _p(f"pack/{file_name}")\n'
    "\n"
    "    gui0_stats = {}\n",
    "tbl",
)

must_replace(
    "            builder=lambda: write_gui0_pack(source_dir, pack_dir, gui_font),\n"
    "        )\n"
    "    copy_missing_pack_files(source_dir, pack_dir)\n"
    "\n"
    "    readme_writer(out_dir)\n"
    "    if gui0_stats:\n"
    '        stats["pack/gui0.pak"] = gui0_stats\n'
    "    write_build_manifest(out_dir, manifest)\n"
    "    return stats\n",
    "            builder=lambda: write_gui0_pack(source_dir, pack_dir, gui_font),\n"
    "        )\n"
    "    if source_gui0.is_file() or gui0_stats:\n"
    '        _p("pack/gui0.pak")\n'
    "    copy_missing_pack_files(source_dir, pack_dir)\n"
    '    _p("copy pack files")\n'
    "\n"
    "    readme_writer(out_dir)\n"
    '    _p("write README")\n'
    "    if gui0_stats:\n"
    '        stats["pack/gui0.pak"] = gui0_stats\n'
    "    write_build_manifest(out_dir, manifest)\n"
    '    _p("write manifest")\n'
    "    if progress is not None:\n"
    '        progress.done("完成")\n'
    "    return stats\n",
    "tail",
)

must_replace(
    "    stats = build_one(\n"
    "        source_dir,\n"
    "        job.out_dir,\n"
    "        translations,\n"
    "        clean=clean,\n"
    "        force=force,\n"
    "        text_transform=text_transform,\n"
    "        transform_sig=job.transform_sig,\n"
    "        ansi_encoding=job.ansi_encoding,\n"
    "        readme_writer=readme_writer,\n"
    "        gui_font=gui_font,\n"
    "    )\n"
    "    return job.label, job.out_dir, job.ansi_encoding, stats\n",
    '    print(f"=== 開始構建 {job.label} ({job.ansi_encoding}) → {job.out_dir}", flush=True)\n'
    "    stats = build_one(\n"
    "        source_dir,\n"
    "        job.out_dir,\n"
    "        translations,\n"
    "        clean=clean,\n"
    "        force=force,\n"
    "        text_transform=text_transform,\n"
    "        transform_sig=job.transform_sig,\n"
    "        ansi_encoding=job.ansi_encoding,\n"
    "        readme_writer=readme_writer,\n"
    "        gui_font=gui_font,\n"
    "    )\n"
    '    print(f"=== 完成 {job.label} ===", flush=True)\n'
    "    return job.label, job.out_dir, job.ansi_encoding, stats\n",
    "banner",
)

target.write_text(t, encoding="utf-8", newline="\n")
compile(t, str(target), "exec")
print("OK: patched", target)
print("Verify with: dboc build --variant taiwan")
