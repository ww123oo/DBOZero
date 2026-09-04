# -*- coding: utf-8 -*-
"""Restore Taiwan wording on data/new_translations.tsv (s2tw + game terms).

Run from repo root:
  pip install opencc-python-reimplemented
  python scripts/apply_tw_main_table.py
Then:
  git add data/new_translations.tsv
  git commit -m "i18n: TW main table (強化石/伺服器/登錄/驗證)"
  git push
"""
from __future__ import annotations
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError:
    raise SystemExit("pip install opencc-python-reimplemented")

cc = OpenCC("s2tw")
FIXUPS = [
    ("升級石", "強化石"),
    ("能量藥水", "氣合藥水"),
    ("氣功藥水", "氣合藥水"),
    ("氣力藥水", "氣合藥水"),
    ("稀有度", "稀少度"),
    ("賬號", "帳號"),
    ("賬戶", "帳戶"),
]

def fix_cell(pos: str, text: str) -> str:
    if not text:
        return text
    if pos == "DST_SCS_GUI_BUTTON_SEND":
        return "驗證"
    s = cc.convert(text)
    for a, b in FIXUPS:
        s = s.replace(a, b)
    return s

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "data" / "new_translations.tsv"
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    bak = path.with_suffix(".tsv.bak_before_tw")
    raw = path.read_bytes()
    bak.write_bytes(raw)
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    if not lines:
        raise SystemExit("empty tsv")
    header = lines[0]
    out_lines = [header]
    changed = 0
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= 6:
            nf = fix_cell(parts[2], parts[5])
            if nf != parts[5]:
                changed += 1
                parts[5] = nf
            out_lines.append("\t".join(parts))
        else:
            out_lines.append(line)
    path.write_text("\n".join(out_lines) + "\n", encoding="utf-8-sig")
    print(f"backup: {bak}")
    print(f"updated: {path}")
    print(f"changed rows: {changed}")
    sample = path.read_text(encoding="utf-8")
    print("升级石 count:", sample.count("升级石"))
    print("強化石 count:", sample.count("強化石"))
    for line in sample.splitlines():
        if "\tDST_SCS_GUI_BUTTON_SEND\t" in line:
            print("SEND:", line.split("\t")[5])
            break

if __name__ == "__main__":
    main()
