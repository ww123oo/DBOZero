#!/usr/bin/env python3
"""Force locked short lang0 translations by position ID.

Must fit original field length AND keep placeholders (%s/%d/%u).
"""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# ID -> exact translation (Traditional where needed; placeholders required)
LOCKED = {
    "DST_SKILL_FILTER_ETC": "Etc",
    "DST_PETITION_CATEGORY2_BUG_ETC": "Etc",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS": "Cls",
    "DST_CHAT_MODE_FIND_PARTY": "LFP",
    "DST_TAB_RAID": "Raid",
    "DST_MOVIE_AGE1000": "Age1000",
    "DST_CITYMAP_DEADMINE": "DeadMine",
    "DST_SCS_GUI_BUTTON_SEND": "\u9a57\u8b49",
    "DST_SCS_BEGIN_BTN": "\u9a57\u8b49",
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA": "%dW %dL %dD",
    "DST_OBSERVER_RECORD": "%dW %dL %dD",
    "DST_CHAT_MODE_FIND_PARTY_EXTEND": "LFG: %s",
    "DST_GUILD_PASSIVE_COST": "Cost: %u rep + %uZ",
    "DST_NOTIFY_GAIN_EXP_AND_BONUS": "+%u(+%u)EXP",
    "DST_NOTIFY_GAIN_MIX_EXP": "+%u EXP",
    "DST_QUESTREWARD_INFO_REPUTATION": "%d Rep",
    "DST_RANKBATTLE_MEMBER_GIVEUP": "%s Fled",
    "DST_SYSTEMMSG_CASTING_DEFENDER": "%s charges %s!",
    "DST_SYSTEMMSG_SKILL_EP": "%s: %s +%d EP",
    "DST_SYSTEMMSG_SKILL_LP": "%s: %s +%d LP",
    "DST_YARDRAT_BTN_CLAIM_WAIT": "WAIT %ds",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "No reply",
    "DST_ITEM_USE_ITEM_MIN_MAX_LEVEL_TEXT": "Lv.%d - %d",
    "DST_WORLDMAP_RECOMMENDED_LEVEL": "Lv. %d ~ %d",
    "DST_RB_RESULT_RECORD_INFO_1": "Total: %u I, %u W, %u L",
}


def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1
    rows = []
    changed = 0
    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            pos = (r.get("位置") or "").strip()
            if pos in LOCKED:
                want = LOCKED[pos]
                cur = (r.get("填写中文") or "").strip()
                if cur != want:
                    r["填写中文"] = want
                    changed += 1
                if fields and "长度状态" in fields:
                    st = (r.get("长度状态") or "").strip()
                    if not st:
                        r["长度状态"] = "ok"
            rows.append(r)
    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK: locked {changed} lang0 IDs (placeholders preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
