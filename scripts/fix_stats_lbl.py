#!/usr/bin/env python3
"""Fix DST_STATS_LBL_* style labels in translations.tsv and new_translations.tsv.

Wrong: 诚攻/怪攻/野攻/雅攻/搞攻
Right: 真攻/奇攻/猛攻/麗攻/樂攻 (+ 防)
Also repair WLD rows broken by tab inside 猛攻.
"""
from __future__ import annotations

from pathlib import Path
import csv
import re
import sys

root = Path(__file__).resolve().parents[1]

# id -> (style label for 真系, elemental label 冰/雷/風/水/火)
STYLE = {
    "DST_STATS_LBL_HON_OFF": ("真攻:", "冰攻:"),
    "DST_STATS_LBL_HON_DEF": ("真防:", "冰防:"),
    "DST_STATS_LBL_STR_OFF": ("奇攻:", "雷攻:"),
    "DST_STATS_LBL_STR_DEF": ("奇防:", "雷防:"),
    "DST_STATS_LBL_WLD_OFF": ("猛攻:", "風攻:"),
    "DST_STATS_LBL_WLD_DEF": ("猛防:", "風防:"),
    "DST_STATS_LBL_ELG_OFF": ("麗攻:", "水攻:"),
    "DST_STATS_LBL_ELG_DEF": ("麗防:", "水防:"),
    "DST_STATS_LBL_FNY_OFF": ("樂攻:", "火攻:"),
    "DST_STATS_LBL_FNY_DEF": ("樂防:", "火防:"),
}

REPL = [
    ("诚攻", "真攻"), ("诚防", "真防"),
    ("怪攻", "奇攻"), ("怪防", "奇防"),
    ("野攻", "猛攻"), ("野防", "猛防"),
    ("雅攻", "麗攻"), ("雅防", "麗防"),
    ("搞攻", "樂攻"), ("搞防", "樂防"),
    ("丽攻", "麗攻"), ("丽防", "麗防"),
    ("乐攻", "樂攻"), ("乐防", "樂防"),
    ("风攻", "風攻"), ("风防", "風防"),
]


def fix_text(s: str) -> str:
    if not s:
        return s
    for a, b in REPL:
        s = s.replace(a, b)
    return s


def fix_translations_tsv(path: Path) -> int:
    if not path.exists():
        return 0
    rows = []
    changed = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            rid = (r.get("id") or "").strip()
            if rid in STYLE:
                style, elem = STYLE[rid]
                # local_data mirror: keep style in source_text, elemental in zh_cn
                # (matches existing accepted rows; repairs broken WLD tabs)
                before = (r.get("source_text"), r.get("source_hash"), r.get("zh_cn"), r.get("status"))
                r["source_text"] = style
                r["source_hash"] = ""
                r["zh_cn"] = elem
                r["status"] = "accepted"
                if not (r.get("note") or "").strip():
                    r["note"] = "stats_lbl_style_fix"
                after = (r.get("source_text"), r.get("source_hash"), r.get("zh_cn"), r.get("status"))
                if before != after:
                    changed += 1
            else:
                for col in ("source_text", "zh_cn"):
                    old = r.get(col) or ""
                    new = fix_text(old)
                    if new != old:
                        r[col] = new
                        changed += 1
            rows.append(r)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return changed


def fix_new_translations(path: Path) -> int:
    if not path.exists():
        return 0
    rows = []
    changed = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            pos = (r.get("位置") or "").strip()
            zh = r.get("填写中文") or ""
            ref = r.get("参考译文") or ""
            if pos in STYLE:
                # lang0 English is Ice/Lit/Wind… — keep elemental 冰雷風水火
                _, elem = STYLE[pos]
                if (zh or "").strip() != elem:
                    # only replace wrong style words if present; else set elemental
                    new_zh = fix_text(zh) if zh else elem
                    # if still style-wrong names, force elemental for lang0 row
                    if any(x in new_zh for x in ("真", "奇", "猛", "麗", "樂", "诚", "怪", "野", "雅", "搞")):
                        new_zh = elem
                    if new_zh != zh:
                        r["填写中文"] = new_zh
                        changed += 1
            else:
                new = fix_text(zh)
                if new != zh:
                    r["填写中文"] = new
                    changed += 1
                new2 = fix_text(ref)
                if new2 != ref:
                    r["参考译文"] = new2
                    changed += 1
            rows.append(r)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return changed


def main() -> int:
    n1 = fix_translations_tsv(root / "data" / "translations.tsv")
    n2 = fix_new_translations(root / "data" / "new_translations.tsv")
    print(f"OK: translations.tsv touched~{n1}, new_translations.tsv touched~{n2}")
    print("  Style: 真/奇/猛/麗/樂 攻|防")
    print("  Element: 冰/雷/風/水/火 攻|防")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
