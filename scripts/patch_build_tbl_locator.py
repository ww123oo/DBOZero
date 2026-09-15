# -*- coding: utf-8 -*-
"""Patch local build_output.py to parse id:N and pass TblOverride.item_id."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "build_output.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if "parse_locator" in text and "row.item_id" in text:
        print("already patched")
        return 0
    bak = TARGET.with_suffix(".py.bak_before_tbl_locator")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print("backup", bak)

    old_m = (
        "            offset = tbl_utf16_patch.parse_offset(item_id, row_no)\n"
        "            tbl[(file_name, item_id, source_text)] = tbl_utf16_patch.TblOverride(file_name, offset, source_text, translation)\n"
    )
    new_m = (
        "            offset, stable_id = tbl_utf16_patch.parse_locator(item_id, row_no)\n"
        "            tbl[(file_name, item_id, source_text)] = tbl_utf16_patch.TblOverride(\n"
        "                file_name, offset, source_text, translation, stable_id\n"
        "            )\n"
    )
    old_q = (
        "            offset = None if item_id in tbl_utf16_patch.ALL_OFFSETS else tbl_utf16_patch.parse_offset(item_id, row_no)\n"
        "            for existing_key in list(tbl):\n"
        "                if existing_key[0] == file_name and existing_key[2] == source_text:\n"
        "                    del tbl[existing_key]\n"
        "            tbl[(file_name, item_id, source_text)] = tbl_utf16_patch.TblOverride(file_name, offset, source_text, translation)\n"
    )
    new_q = (
        "            offset, stable_id = tbl_utf16_patch.parse_locator(item_id, row_no)\n"
        "            for existing_key in list(tbl):\n"
        "                if existing_key[0] == file_name and existing_key[2] == source_text:\n"
        "                    del tbl[existing_key]\n"
        "            tbl[(file_name, item_id, source_text)] = tbl_utf16_patch.TblOverride(\n"
        "                file_name, offset, source_text, translation, stable_id\n"
        "            )\n"
    )
    old_tr = (
        "        tbl_utf16_patch.TblOverride(row.file_name, row.offset, row.source_text, transform(row.translation))\n"
    )
    new_tr = (
        "        tbl_utf16_patch.TblOverride(\n"
        "            row.file_name, row.offset, row.source_text, transform(row.translation), row.item_id\n"
        "        )\n"
    )
    n = 0
    for old, new in ((old_m, new_m), (old_q, new_q), (old_tr, new_tr)):
        if old not in text:
            print("block not found:", repr(old[:60]))
            return 2
        text = text.replace(old, new, 1)
        n += 1
    TARGET.write_text(text, encoding="utf-8")
    print(f"patched {n} blocks in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
