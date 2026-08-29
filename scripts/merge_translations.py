#!/usr/bin/env python3
"""Merge all data/*_delta.tsv (and a few known files) into data/new_translations.tsv."""
from __future__ import annotations

from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
data = root / "data"
target = data / "new_translations.tsv"

LOCKED_IDS = {
    "DST_BUDOKAI_INDI_REQ_RECORD_DATA",
    "DST_OBSERVER_RECORD",
    "DST_CHAT_HAVE_NO_USER_TO_REPLY",
    "DST_CHAT_MODE_FIND_PARTY",
    "DST_CHAT_MODE_FIND_PARTY_EXTEND",
    "DST_CITYMAP_DEADMINE",
    "DST_GUILD_PASSIVE_COST",
    "DST_MOVIE_AGE1000",
    "DST_NOTIFY_GAIN_EXP_AND_BONUS",
    "DST_NOTIFY_GAIN_MIX_EXP",
    "DST_PETITION_CATEGORY2_BUG_ETC",
    "DST_SKILL_FILTER_ETC",
    "DST_QUESTREWARD_INFO_REPUTATION",
    "DST_RANKBATTLE_MEMBER_GIVEUP",
    "DST_RANKBOARD_TMQ_SUBJECT_CLASS",
    "DST_SYSTEMMSG_CASTING_DEFENDER",
    "DST_SYSTEMMSG_SKILL_EP",
    "DST_SYSTEMMSG_SKILL_LP",
    "DST_TAB_RAID",
    "DST_YARDRAT_BTN_CLAIM_WAIT",
    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE",
    "DST_SCS_GUI_BUTTON_SEND",
    "DST_SCS_BEGIN_BTN",
}


def collect_delta_files() -> list[Path]:
    """Prefer flat data/*.tsv deltas; also archive subfolders if still present."""
    files: list[Path] = []
    # explicit small helpers first (order: later wins on same EN key)
    for name in (
        "translations_to_merge.tsv",
        "tbl0_full_delta.tsv",
        "tbl_length_fix_delta.tsv",
        "tbl_batch_delta.tsv",
    ):
        p = data / name
        if p.exists():
            files.append(p)
    # all *_delta.tsv under data/ (not recursive into archive by default)
    for p in sorted(data.glob("*_delta.tsv")):
        if p not in files:
            files.append(p)
    # optional: still load archive if user has not deleted it yet
    arch = data / "archive"
    if arch.is_dir():
        for p in sorted(arch.rglob("*_delta.tsv")):
            files.append(p)
        for p in sorted(arch.rglob("translations_to_merge.tsv")):
            files.append(p)
    return files


def load_map(paths: list[Path]) -> dict[str, str]:
    M: dict[str, str] = {}
    for mp in paths:
        try:
            with mp.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f, delimiter="\t"):
                    en = (r.get("原文") or "").strip().replace("\\n", "\n")
                    zh = (r.get("填写中文") or "").strip().replace("\\n", "\n")
                    if en and zh:
                        M[en] = zh
            print(f"loaded {mp.relative_to(root)}: keys {len(M)}")
        except Exception as e:
            print(f"skip {mp}: {e}")
    return M


def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1
    paths = collect_delta_files()
    if not paths:
        print("no delta files found under data/")
        return 1
    M = load_map(paths)
    if not M:
        print("empty merge map")
        return 1

    rows, filled = [], 0
    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            en = (r.get("原文") or "").strip()
            cur = (r.get("填写中文") or "").strip()
            pos = (r.get("位置") or "").strip()
            if pos not in LOCKED_IDS and en in M and cur != M[en]:
                r["填写中文"] = M[en]
                filled += 1
            rows.append(r)

    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK: updated {filled} rows from {len(paths)} files / {len(M)} keys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
