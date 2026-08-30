#!/usr/bin/env python3
"""Merge data/*_delta.tsv into data/new_translations.tsv.

Order: later files overwrite same 原文. For tbl0/1/2 rows, skip 填写中文
that are longer (GBK/CP950 bytes) than 原文 — avoids fixed-field crash.
"""
from __future__ import annotations

from pathlib import Path
import csv
import re
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


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def bytelen(s: str, enc: str) -> int:
    return len(s.encode(enc, "replace"))


def fits_tbl(en: str, zh: str) -> bool:
    if not zh or not en:
        return False
    limit = max(bytelen(en, "cp950"), len(en.encode("ascii", "replace")))
    return max(bytelen(zh, "cp950"), bytelen(zh, "gbk")) <= limit


def collect_delta_files() -> list[Path]:
    files: list[Path] = []
    for name in (
        "translations_to_merge.tsv",
        "tbl0_full_delta.tsv",
        "tbl_length_fix_delta.tsv",
        "tbl_batch_delta.tsv",
        "ui_lang0_empty_fill_delta.tsv",
    ):
        p = data / name
        if p.exists():
            files.append(p)
    for p in sorted(data.glob("*_delta.tsv")):
        if p not in files:
            files.append(p)
    batches = sorted(
        data.glob("tbl_batch*_delta.tsv"),
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
        if re.search(r"(\d+)", p.stem)
        else 0,
    )
    for p in batches:
        if p not in files:
            files.append(p)
    arch = data / "archive"
    if arch.is_dir():
        for p in sorted(arch.rglob("*_delta.tsv")):
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
        print("no delta files under data/")
        return 1
    M = load_map(paths)
    if not M:
        print("empty map")
        return 1

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
    print(f"OK: updated {filled}, skipped overlong tbl {skipped}, keys {len(M)}, files {len(paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
