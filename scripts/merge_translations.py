#!/usr/bin/env python3
"""Merge data/deltas/*.tsv into data/new_translations.tsv only."""
from __future__ import annotations

from pathlib import Path
import csv
import re
import sys

root = Path(__file__).resolve().parents[1]
data = root / "data"
target = data / "new_translations.tsv"
deltas = data / "deltas"

LOCKED_IDS = {
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA", "DST_OBSERVER_RECORD",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY", "DST_CHAT_MODE_FIND_PARTY",
    "DST_CHAT_MODE_FIND_PARTY_EXTEND", "DST_CITYMAP_DEADMINE",
    "DST_GUILD_PASSIVE_COST", "DST_MOVIE_AGE1000",
    "DST_NOTIFY_GAIN_EXP_AND_BONUS", "DST_NOTIFY_GAIN_MIX_EXP",
    "DST_PETITION_CATEGORY2_BUG_ETC", "DST_SKILL_FILTER_ETC",
    "DST_QUESTREWARD_INFO_REPUTATION", "DST_RANKBATTLE_MEMBER_GIVEUP",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS", "DST_SYSTEMMSG_CASTING_DEFENDER",
    "DST_SYSTEMMSG_SKILL_EP", "DST_SYSTEMMSG_SKILL_LP",
    "DST_TAB_RAID", "DST_YARDRAT_BTN_CLAIM_WAIT",
    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE",
    "DST_SCS_GUI_BUTTON_SEND", "DST_SCS_BEGIN_BTN",
}


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def bytelen(s: str, enc: str) -> int:
    return len(s.encode(enc, "replace"))


def fits_tbl(en: str, zh: str) -> bool:
    if not zh or not en:
        return False
    limit = max(bytelen(en, "cp950"), len(en.encode("ascii", "replace")))
    return max(bytelen(zh, "cp950"), bytelen(zh, "gbk")) <= limit


def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1
    if not deltas.is_dir():
        print("missing data/deltas/ — run: python scripts/consolidate_deltas.py")
        return 1

    paths: list[Path] = []
    for name in ("term.tsv", "ui.tsv", "tbl.tsv"):
        p = deltas / name
        if p.exists():
            paths.append(p)
    for p in sorted(deltas.glob("*.tsv")):
        if p not in paths:
            paths.append(p)
    if not paths:
        print("no tsv in data/deltas/")
        return 1

    M: dict[str, str] = {}
    for mp in paths:
        with mp.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                en = (r.get("原文") or "").strip().replace("\\n", "\n")
                zh = (r.get("填写中文") or "").strip().replace("\\n", "\n")
                if en and zh:
                    M[en] = zh
        print(f"loaded {mp.name}: keys {len(M)}")

    rows, filled, skipped = [], 0, 0
    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            en = (r.get("原文") or "").strip()
            cur = (r.get("填写中文") or "").strip()
            pos = (r.get("位置") or "").strip()
            file_ = (r.get("文件") or "").lower()
            if pos in LOCKED_IDS or en not in M:
                rows.append(r)
                continue
            zh = M[en]
            is_tbl = any(x in file_ for x in ("tbl0", "tbl1", "tbl2"))
            if is_tbl and has_cjk(zh) and not fits_tbl(en, zh):
                skipped += 1
                rows.append(r)
                continue
            if cur != zh:
                r["填写中文"] = zh
                filled += 1
            rows.append(r)

    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK: updated {filled}, skipped overlong tbl {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
