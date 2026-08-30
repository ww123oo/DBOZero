#!/usr/bin/env python3
"""Force locked short lang0 translations by 位置 ID.

Must: (1) fit source field byte length  (2) keep same printf placeholders.
"""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# ID -> 填写中文 (byte-safe + placeholders match 原文)
LOCKED = {
    # no placeholders
    "DST_SKILL_FILTER_ETC": "Etc",
    "DST_PETITION_CATEGORY2_BUG_ETC": "Etc",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS": "Cls",
    "DST_CHAT_MODE_FIND_PARTY": "LFP",
    "DST_TAB_RAID": "副本",
    "DST_MOVIE_AGE1000": "Age1000",
    "DST_CITYMAP_DEADMINE": "DeadMine",
    "DST_SCS_GUI_BUTTON_SEND": "驗證",
    "DST_SCS_BEGIN_BTN": "驗證",
    # keep %d/%u/%s
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA": "%dW %dL %dD",  # source %dW %dL %dD
    "DST_OBSERVER_RECORD": "%dW %dL %dD",
    "DST_CHAT_MODE_FIND_PARTY_EXTEND": "LFG: %s",
    "DST_GUILD_PASSIVE_COST": "費:%u聲望+%uZ",  # was Cost: %u rep + %u zeni
    "DST_NOTIFY_GAIN_EXP_AND_BONUS": "+%u(+%u)EXP",
    "DST_NOTIFY_GAIN_MIX_EXP": "+%u EXP",
    "DST_QUESTREWARD_INFO_REPUTATION": "%d聲望",
    "DST_RANKBATTLE_MEMBER_GIVEUP": "%s逃走",
    "DST_SYSTEMMSG_CASTING_DEFENDER": "%s蓄力%s。",
    "DST_SYSTEMMSG_SKILL_EP": "%s: %s +%d EP.",
    "DST_SYSTEMMSG_SKILL_LP": "%s: %s +%d LP.",
    "DST_YARDRAT_BTN_CLAIM_WAIT": "等%d秒",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "No reply",
    # ASCII only (fullwidth dash/tilde overflow)
    "DST_ITEM_USE_ITEM_MIN_MAX_LEVEL_TEXT": "Lv.%d - %d",
    "DST_WORLDMAP_RECOMMENDED_LEVEL": "Lv. %d ~ %d",
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
                    if not (r.get("长度状态") or "").strip():
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
