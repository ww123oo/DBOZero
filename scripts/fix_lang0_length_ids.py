#!/usr/bin/env python3
"""Fix lang0 too-long / printf by DST id."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"
FIX_BY_ID = {
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "無可回覆",
    "DST_PETITION_CATEGORY2_BUG_ETC": "Etc",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS": "職",
    "DST_SKILL_FILTER_ETC": "Etc",
    "DST_SYSTEMMSG_CASTING_DEFENDER": "%s蓄力%s。",
    "DST_TAB_RAID": "副本",
    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": "已是100% 成功。",
}
FIX_BY_EN = {
    "No User to Reply": "無可回覆",
    "Etc": "Etc",
    "Job": "職",
    "Raid": "副本",
    "%s charges %s.": "%s蓄力%s。",
    "Already 100% success rate.": "已是100% 成功。",
}
if not target.exists():
    print("missing", target)
    sys.exit(1)
rows = []
changed = 0
with target.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        pos = (r.get("位置") or "").strip()
        en = (r.get("原文") or "").strip()
        cur = (r.get("填写中文") or "").strip()
        new = FIX_BY_ID.get(pos) or FIX_BY_EN.get(en)
        if new is not None and cur != new:
            r["填写中文"] = new
            changed += 1
            print(f"fix {pos or en!r}: {cur!r} -> {new!r}")
        rows.append(r)
with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"OK: changed {changed} rows in {target}")
