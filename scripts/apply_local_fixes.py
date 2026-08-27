#!/usr/bin/env python3
"""One-shot: write length/term/UI fixes into data/new_translations.tsv (local only)."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

FIX_BY_ID = {
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA": "%dW %dL %dD",
    "DST_OBSERVER_RECORD": "%dW %dL %dD",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY": "無可回覆",
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
    "DST_ITEMASCEND_TITLE": "裝備升階",
    "DST_ITEMASCEND_MATERIAL": "所需材料",
    "DST_ITEMASCEND_ZENNY": "索尼",
    "DST_ITEMASCEND_SUCCESSRATE": "成功率",
    "DST_ITEMASCEND_BTN_ASCEND": "升階",
}

FIX_BY_EN = {
    "No User to Reply": "無可回覆",
    "HoiPoi Mine": "膠囊廢礦",
    "Cost: %u rep + %u zeni": "費:%u聲望+%uZ",
    "Age 1000": "Age 1000",
    "Etc": "Etc",
    "Job": "職",
    "Raid": "副本",
    "WAIT %ds": "等%d秒",
    "Already 100% success rate.": "已是100% s。",
    "Required Materials": "所需材料",
    "Materials": "材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
    "ASCEND": "升階",
    "Ascend System": "裝備升階",
    "Armor": "防具",
}

ARMOR_REPL = [
    ("高级盔甲升级石", "高級防具強化石"),
    ("史诗盔甲升级石", "史詩防具強化石"),
    ("盔甲升级石", "防具強化石"),
    ("盔甲降级石", "防具降級石"),
    ("盔甲券", "防具券"),
    ("盔甲石", "防具石"),
    ("盔甲商人", "防具商人"),
    ("盔甲制作", "防具製作"),
    ("盔甲升级", "防具強化"),
    ("盔甲", "防具"),
]

# Load optional delta TSVs (原文 → 填写中文)
M = dict(FIX_BY_EN)
for name in [
    "ui_itemascend_delta.tsv",
    "length_fix_delta.tsv",
    "ui_length_fix2_delta.tsv",
    "term_armor_fangju_delta.tsv",
]:
    p = root / "data" / name
    if not p.exists():
        continue
    with p.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            en = (r.get("原文") or "").strip().replace("\\n", "\n")
            zh = (r.get("填写中文") or "").strip().replace("\\n", "\n")
            if en and zh:
                M[en] = zh

if not target.exists():
    print("ERROR: missing", target)
    sys.exit(1)

rows = []
n_id = n_en = n_armor = 0
with target.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        pos = (r.get("位置") or "").strip()
        en = (r.get("原文") or "").strip()
        cur = (r.get("填写中文") or "").strip()
        new = cur
        if pos in FIX_BY_ID:
            new = FIX_BY_ID[pos]
            if new != cur:
                n_id += 1
        elif en in M:
            new = M[en]
            if new != cur:
                n_en += 1
        if "盔甲" in new:
            before = new
            for a, b in ARMOR_REPL:
                new = new.replace(a, b)
            if new != before:
                n_armor += 1
        if new != cur:
            r["填写中文"] = new
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print(f"OK: wrote {target}")
print(f"  by-id fixes: {n_id}")
print(f"  by-原文 fixes: {n_en}")
print(f"  盔甲→防具 rows: {n_armor}")
print(f"  total rows: {len(rows)}")
# spot-check a few
for want_id, want_zh in [
    ("DST_TAB_RAID", "副本"),
    ("DST_ITEMASCEND_SUCCESSRATE", "成功率"),
    ("DST_SKILL_FILTER_ETC", "Etc"),
]:
    for r in rows:
        if (r.get("位置") or "").strip() == want_id:
            got = (r.get("填写中文") or "").strip()
            ok = "OK" if got == want_zh else f"BAD got={got!r}"
            print(f"  check {want_id}: {ok}")
            break
