#!/usr/bin/env python3
"""Add GAME_ITEM_UPGRADE printf allowlist entry; set translation to 已是100% 成功。"""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
patch = root / "hanhua_v3" / "runtime" / "lang0_gbk_patch.py"
tsv = root / "data" / "new_translations.tsv"

OLD = (
    "ALLOWED_PRINTF_MISMATCHES = {\n"
    '    "DST_INVENTORY_SORT_SUCCESS": (("%s",), ()),\n'
    '    "DST_ITEM_REMOTE_SELL": (("% o", "%s", "%s"), ("%s", "%s")),\n'
    "}\n"
)
NEW = (
    "ALLOWED_PRINTF_MISMATCHES = {\n"
    '    "DST_INVENTORY_SORT_SUCCESS": (("%s",), ()),\n'
    '    "DST_ITEM_REMOTE_SELL": (("% o", "%s", "%s"), ("%s", "%s")),\n'
    '    # "100% success" false-positive "% s"; allow TW "已是100% 成功。"\n'
    '    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": (("% s",), ()),\n'
    "}\n"
)

if not patch.exists():
    print("missing", patch)
    sys.exit(1)

text = patch.read_text(encoding="utf-8")
if 'GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": (("% s",), ())' in text:
    print("allowlist already present")
elif OLD not in text:
    print("unexpected lang0_gbk_patch.py layout; cannot patch")
    sys.exit(1)
else:
    patch.write_text(text.replace(OLD, NEW, 1), encoding="utf-8", newline="\n")
    print("OK: patched", patch)

if tsv.exists():
    rows = []
    changed = 0
    with tsv.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            pos = (r.get("位置") or "").strip()
            en = (r.get("原文") or "").strip()
            if pos == "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE" or en == "Already 100% success rate.":
                if (r.get("填写中文") or "") != "已是100% 成功。":
                    r["填写中文"] = "已是100% 成功。"
                    changed += 1
            rows.append(r)
    with tsv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK: tsv rows changed {changed}")
