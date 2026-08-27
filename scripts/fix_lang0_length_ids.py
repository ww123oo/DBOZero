#!/usr/bin/env python3
"""Force short lang0 填写中文 by 位置 id so dboc build passes length/printf checks."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# Must be <= source byte length under gbk/cp950. Keep printf tokens when required.
FIX_BY_ID = {
    # source "%dW %dL %dD" (11) — keep English short form
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA": "%dW %dL %dD",
    "DST_OBSERVER_RECORD": "%dW %dL %dD",
    # source "No User to Reply" (16)
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "無可回覆",
    # source "HoiPoi Mine" (11)
    "DST_CITYMAP_DEADMINE": "膠囊廢礦",
    # source "Cost: %u rep + %u zeni" (22)
    "DST_GUILD_PASSIVE_COST": "費:%u聲望+%uZ",
    # source "Age 1000" (8) — keep English
    "DST_MOVIE_AGE1000": "Age 1000",
    # source "+%u(+%u)EXP" (11)
    "DST_NOTIFY_GAIN_EXP_AND_BONUS": "+%u(+%u)EXP",
    # source "Gain (%u) EXP." (14)
    "DST_NOTIFY_GAIN_MIX_EXP": "獲EXP(%u)",
    # source "Etc" (3)
    "DST_PETITION_CATEGORY2_BUG_ETC": "Etc",
    "DST_SKILL_FILTER_ETC": "Etc",
    # source "%d Rep" (6)
    "DST_QUESTREWARD_INFO_REPUTATION": "%d聲望",
    # source "%s Fled" (7)
    "DST_RANKBATTLE_MEMBER_GIVEUP": "%s逃走",
    # source "Job" (3)
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS": "職",
    # source "%s charges %s." (14)
    "DST_SYSTEMMSG_CASTING_DEFENDER": "%s蓄力%s。",
    # source "%s: %s +%d EP." (14) — keep English tokens
    "DST_SYSTEMMSG_SKILL_EP": "%s: %s +%d EP.",
    "DST_SYSTEMMSG_SKILL_LP": "%s: %s +%d LP.",
    # source "Raid" (4)
    "DST_TAB_RAID": "副本",
    # source "WAIT %ds" (8)
    "DST_YARDRAT_BTN_CLAIM_WAIT": "等%d秒",
    # source has false-positive "% s" from "100% success"
    # Prefer pure TW if allowlist exists; else keep "% s" shape.
    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": "已是100% s。",
}

FIX_BY_EN = {
    "No User to Reply": "無可回覆",
    "HoiPoi Mine": "膠囊廢礦",
    "Cost: %u rep + %u zeni": "費:%u聲望+%uZ",
    "Age 1000": "Age 1000",
    "+%u(+%u)EXP": "+%u(+%u)EXP",
    "Gain (%u) EXP.": "獲EXP(%u)",
    "Etc": "Etc",
    "%d Rep": "%d聲望",
    "%s Fled": "%s逃走",
    "Job": "職",
    "%s charges %s.": "%s蓄力%s。",
    "%s: %s +%d EP.": "%s: %s +%d EP.",
    "%s: %s +%d LP.": "%s: %s +%d LP.",
    "Raid": "副本",
    "WAIT %ds": "等%d秒",
    "Already 100% success rate.": "已是100% s。",
    "%dW %dL %dD": "%dW %dL %dD",
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
            print(f"fix {pos or en}: {cur!r} -> {new!r}")
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: changed {changed} rows")
print("Note: if GAME_ITEM still fails printf, run scripts/patch_stone_core_allowlist.py")
