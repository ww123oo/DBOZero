#!/usr/bin/env python3
"""Force locked short lang0 translations by 位置 ID (never overwrite later)."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# ID -> exact 填写中文 (must fit source field bytes)
LOCKED = {
    "DST_SKILL_FILTER_ETC": "Etc",
    "DST_PETITION_CATEGORY2_BUG_ETC": "Etc",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS": "Cls",
    "DST_CHAT_MODE_FIND_PARTY": "LFP",
    "DST_CHAT_MODE_FIND_PARTY_EXTEND": "LFG",
    "DST_TAB_RAID": "Raid",
    "DST_MOVIE_AGE1000": "Age1000",
    "DST_CITYMAP_DEADMINE": "DeadMine",
    "DST_YARDRAT_BTN_CLAIM_WAIT": "Wait",
    "DST_QUESTREWARD_INFO_REPUTATION": "Rep",
    "DST_RANKBATTLE_MEMBER_GIVEUP": "GiveUp",
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA": "Record",
    "DST_OBSERVER_RECORD": "Record",
    "DST_NOTIFY_GAIN_EXP_AND_BONUS": "+%u EXP",
    "DST_NOTIFY_GAIN_MIX_EXP": "+%u EXP",
    "DST_SYSTEMMSG_SKILL_EP": "EP %s",
    "DST_SYSTEMMSG_SKILL_LP": "LP %s",
    "DST_SYSTEMMSG_CASTING_DEFENDER": "%s cast",
    "DST_GUILD_PASSIVE_COST": "Cost %u",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "No reply",
    # fullwidth dash/tilde exceed source by 1 byte — keep ASCII
    "DST_ITEM_USE_ITEM_MIN_MAX_LEVEL_TEXT": "Lv.%d - %d",  # source=10
    "DST_WORLDMAP_RECOMMENDED_LEVEL": "Lv. %d ~ %d",  # source=11, ASCII ~
    # short rank battle record (source=23)
    "DST_RB_RESULT_RECORD_INFO_1": "總%u 勝%u 負%u",
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
    print(f"OK: locked {changed} lang0 length IDs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
