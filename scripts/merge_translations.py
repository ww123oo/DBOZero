#!/usr/bin/env python3
"""Merge delta TSVs into data/new_translations.tsv 填写中文."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"
merge_files = [
    root / "data" / "translations_to_merge.tsv",
    root / "data" / "ui_equip_delta.tsv",
    root / "data" / "ui_long_delta.tsv",
    root / "data" / "length_fix_delta.tsv",
    root / "data" / "ui_length_fix2_delta.tsv",
    root / "data" / "ui_batch_delta.tsv",
    root / "data" / "ui_batch2_delta.tsv",
    root / "data" / "ui_batch3_delta.tsv",
    root / "data" / "ui_batch4_delta.tsv",
    root / "data" / "ui_itemascend_delta.tsv",
    root / "data" / "ui_element_labels_delta.tsv",
    root / "data" / "ui_lang0_labels_delta.tsv",
    root / "data" / "ui_scs_fix_delta.tsv",
    root / "data" / "lang0_s2t_delta.tsv",
    root / "data" / "place_name_fix_delta.tsv",
    root / "data" / "term_advanced_fix_delta.tsv",
    root / "data" / "term_wagu_fix_delta.tsv",
    root / "data" / "term_armor_fangju_delta.tsv",
    root / "data" / "term_kaili_fix_delta.tsv",
] + [
    root / "data" / name
    for name in [
        "tbl_batch_delta.tsv",
        *[f"tbl_batch{i}_delta.tsv" for i in range(2, 60)],
    ]
]

M = {}
for mp in merge_files:
    if not mp.exists():
        continue
    with mp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            en = (r.get("原文") or "").strip().replace("\\n", "\n")
            zh = (r.get("填写中文") or "").strip().replace("\\n", "\n")
            if en and zh:
                M[en] = zh
    print(f"loaded {mp.name}: keys {len(M)}")

if not M:
    print("no merge data")
    sys.exit(1)
if not target.exists():
    print("missing", target)
    sys.exit(1)

rows = []
filled = 0
with target.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        en = (r.get("原文") or "").strip()
        cur = (r.get("填写中文") or "").strip()
        pos = (r.get("位置") or "").strip()
        if pos in ("DST_SCS_GUI_BUTTON_SEND", "DST_SCS_BEGIN_BTN"):
            if cur != "驗證":
                r["填写中文"] = "驗證"
                filled += 1
        elif en in M:
            if cur != M[en]:
                r["填写中文"] = M[en]
                filled += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: data/new_translations.tsv updated {filled} from {len(M)} keys")
