#!/usr/bin/env python3
"""Force short lang0 填写中文 by 位置 — do not lengthen these later."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# Locked short fills (must fit source byte length). Do not change without re-checking lengths.
FIX_BY_ID = {
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA": "%dW %dL %dD",
    "DST_OBSERVER_RECORD": "%dW %dL %dD",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "無可回覆",
    "DST_CHAT_MODE_FIND_PARTY": "LFP",
    "DST_CHAT_MODE_FIND_PARTY_EXTEND": "LFG: %s",
    "DST_CITYMAP_DEADMINE": "膠囊廢礦",
    "DST_GUILD_PASSIVE_COST": "費:%u聲望+%uZ",
    "DST_MOVIE_AGE1000": "Age 1000",
    "DST_NOTIFY_GAIN_EXP_AND_BONUS": "+%u(+%u)EXP",
    "DST_NOTIFY_GAIN_MIX_EXP": "獲EXP(%u)",
    "DST_PETITION_CATEGORY2_BUG_ETC": "Etc",
    "DST_SKILL_FILTER_ETC": "Etc",
    "DST_QUESTREWARD_INFO_REPUTATION": "%d聲望",
    "DST_RANKBATTLE_MEMBER_GIVEUP": "%s逃走",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS": "職",
    "DST_SYSTEMMSG_CASTING_DEFENDER": "%s蓄力%s。",
    "DST_SYSTEMMSG_SKILL_EP": "%s: %s +%d EP.",
    "DST_SYSTEMMSG_SKILL_LP": "%s: %s +%d LP.",
    "DST_TAB_RAID": "副本",
    "DST_YARDRAT_BTN_CLAIM_WAIT": "等%d秒",
    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": "已是100% s。",
    "DST_SCS_GUI_BUTTON_SEND": "驗證",
    "DST_SCS_BEGIN_BTN": "驗證",
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
        cur = (r.get("填写中文") or "").strip()
        if pos in FIX_BY_ID and cur != FIX_BY_ID[pos]:
            r["填写中文"] = FIX_BY_ID[pos]
            changed += 1
            print(f"fix {pos}: {cur!r} -> {FIX_BY_ID[pos]!r}")
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: locked {changed} lang0 length rows (total locked ids {len(FIX_BY_ID)})")
