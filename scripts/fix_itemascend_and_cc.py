#!/usr/bin/env python3
"""Fix Item Ascend UI, rarity wording, Materials/Success Rate/Zeni, CC labels."""
from __future__ import annotations

from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

BY_ID = {
    "DST_ITEMASCEND_TITLE": "裝備進階",
    "DST_ITEMASCEND_INFO": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "DST_ITEMASCEND_MATERIAL": "所需材料",
    "DST_ITEMASCEND_ZENNY": "索尼",
    "DST_ITEMASCEND_SUCCESSRATE": "成功率",
    "DST_ITEMASCEND_BTN_ASCEND": "進階",
    "DST_ITEMASCEND_SUCCESS": "進階成功！",
    "DST_ITEMASCEND_FAIL": "進階失敗，成功率已提升。",
    "DST_ITEMASCEND_MAXRANK": "該裝備已達最高稀少度。",
    "DST_STATS_CC_PARALYZE": "麻痺",
    "DST_STATS_CC_TERROR": "恐怖",
    "DST_STATS_CC_CONFUSE": "混亂",
    "DST_STATS_CC_STONE": "石化",
    "DST_STATS_CC_CANDY": "糖果",
    "DST_STATS_CC_BLEED": "出血",
    "DST_STATS_CC_STOMACH": "腹痛",
    "DST_STATS_CC_BURN": "燃燒",
}

BY_EN = {
    "Materials": "材料",
    "Required Materials": "所需材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
    "Paralyze": "麻痺",
    "Paralysis": "麻痺",
    "Terror": "恐怖",
    "Fear": "恐怖",
    "Confuse": "混亂",
    "Confusion": "混亂",
    "Stone": "石化",
    "Candy": "糖果",
    "Bleed": "出血",
    "Bleeding": "出血",
    "Stomach": "腹痛",
    "Burn": "燃燒",
    "Ascend System": "裝備進階",
    "ASCEND": "進階",
    "Ascension succeeded!": "進階成功！",
    "Ascension failed. Success rate increased.": "進階失敗，成功率已提升。",
    "This item is already at the maximum rarity.": "該裝備已達最高稀少度。",
    "Place an equipment piece here to ascend it to the next rarity tier.": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "Items must have the same rarity.": "道具稀少度必須相同。",
    "This item cannot be ascended (no recipe found).": "該裝備無法進階（未找到配方）。",
    "This item cannot be ascended right now.": "該裝備目前無法進階。",
}

TEXT_REPL = [
    ("裝備升階", "裝備進階"),
    ("升階成功", "進階成功"),
    ("升階失敗", "進階失敗"),
    ("無法升階", "無法進階"),
    ("使其升階", "使其進階"),
    ("升階至", "進階至"),
    ("升階", "進階"),
    ("稀有度", "稀少度"),
    ("麻痹", "麻痺"),
    ("恐懼", "恐怖"),
    ("胃部", "腹痛"),
]


def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1

    rows = []
    n = 0
    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            pos = (r.get("位置") or "").strip()
            en = (r.get("原文") or "").strip()
            zh = r.get("填写中文") or ""
            new = zh

            if pos in BY_ID:
                new = BY_ID[pos]
            elif en in BY_EN:
                new = BY_EN[en]
            else:
                for a, b in TEXT_REPL:
                    if a in new:
                        new = new.replace(a, b)

            if new != zh:
                r["填写中文"] = new
                n += 1
            rows.append(r)

    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK: fixed {n} rows")
    return 0


BY_ID = {
    "DST_ITEMASCEND_TITLE": "裝備進階",
    "DST_ITEMASCEND_INFO": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "DST_ITEMASCEND_MATERIAL": "所需材料",
    "DST_ITEMASCEND_ZENNY": "索尼",
    "DST_ITEMASCEND_SUCCESSRATE": "成功率",
    "DST_ITEMASCEND_BTN_ASCEND": "進階",
    "DST_ITEMASCEND_SUCCESS": "進階成功！",
    "DST_ITEMASCEND_FAIL": "進階失敗，成功率已提升。",
    "DST_ITEMASCEND_MAXRANK": "該裝備已達最高稀少度。",
    "DST_STATS_CC_PARALYZE": "麻痺",
    "DST_STATS_CC_TERROR": "恐怖",
    "DST_STATS_CC_CONFUSE": "混亂",
    "DST_STATS_CC_STONE": "石化",
    "DST_STATS_CC_CANDY": "糖果",
    "DST_STATS_CC_BLEED": "出血",
    "DST_STATS_CC_STOMACH": "腹痛",
    "DST_STATS_CC_BURN": "燃燒",
}

BY_EN = {
    "Materials": "材料",
    "Required Materials": "所需材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
    "Paralyze": "麻痺",
    "Paralysis": "麻痺",
    "Terror": "恐怖",
    "Fear": "恐怖",
    "Confuse": "混亂",
    "Confusion": "混亂",
    "Stone": "石化",
    "Candy": "糖果",
    "Bleed": "出血",
    "Bleeding": "出血",
    "Stomach": "腹痛",
    "Burn": "燃燒",
    "Ascend System": "裝備進階",
    "ASCEND": "進階",
    "Ascension succeeded!": "進階成功！",
    "Ascension failed. Success rate increased.": "進階失敗，成功率已提升。",
    "This item is already at the maximum rarity.": "該裝備已達最高稀少度。",
    "Place an equipment piece here to ascend it to the next rarity tier.": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "Items must have the same rarity.": "道具稀少度必須相同。",
    "This item cannot be ascended (no recipe found).": "該裝備無法進階（未找到配方）。",
    "This item cannot be ascended right now.": "該裝備目前無法進階。",
    "Materials": "材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
}

TEXT_REPL = [
    ("裝備升階", "裝備進階"),
    ("升階成功", "進階成功"),
    ("升階失敗", "進階失敗"),
    ("無法升階", "無法進階"),
    ("使其升階", "使其進階"),
    ("升階至", "進階至"),
    ("升階", "進階"),
    ("稀有度", "稀少度"),
    ("麻痹", "麻痺"),
    ("恐懼", "恐怖"),
    ("胃部", "腹痛"),
]

BY_ID = {
    "DST_ITEMASCEND_TITLE": "裝備進階",
    "DST_ITEMASCEND_INFO": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "DST_ITEMASCEND_MATERIAL": "所需材料",
    "DST_ITEMASCEND_ZENNY": "索尼",
    "DST_ITEMASCEND_SUCCESSRATE": "成功率",
    "DST_ITEMASCEND_BTN_ASCEND": "進階",
    "DST_ITEMASCEND_SUCCESS": "進階成功！",
    "DST_ITEMASCEND_FAIL": "進階失敗，成功率已提升。",
    "DST_ITEMASCEND_MAXRANK": "該裝備已達最高稀少度。",
    "DST_STATS_CC_PARALYZE": "麻痺",
    "DST_STATS_CC_TERROR": "恐怖",
    "DST_STATS_CC_CONFUSE": "混亂",
    "DST_STATS_CC_STONE": "石化",
    "DST_STATS_CC_CANDY": "糖果",
    "DST_STATS_CC_BLEED": "出血",
    "DST_STATS_CC_STOMACH": "腹痛",
    "DST_STATS_CC_BURN": "燃燒",
}

BY_EN = {
    "Materials": "材料",
    "Required Materials": "所需材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
    "Paralyze": "麻痺",
    "Paralysis": "麻痺",
    "Terror": "恐怖",
    "Fear": "恐怖",
    "Confuse": "混亂",
    "Confusion": "混亂",
    "Stone": "石化",
    "Candy": "糖果",
    "Bleed": "出血",
    "Bleeding": "出血",
    "Stomach": "腹痛",
    "Burn": "燃燒",
    "Ascend System": "裝備進階",
    "ASCEND": "進階",
    "Ascension succeeded!": "進階成功！",
    "Ascension failed. Success rate increased.": "進階失敗，成功率已提升。",
    "This item is already at the maximum rarity.": "該裝備已達最高稀少度。",
    "Place an equipment piece here to ascend it to the next rarity tier.": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "Items must have the same rarity.": "道具稀少度必須相同。",
    "This item cannot be ascended (no recipe found).": "該裝備無法進階（未找到配方）。",
    "This item cannot be ascended right now.": "該裝備目前無法進階。",
    "Materials": "材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
}

TEXT_REPL = [
    ("裝備升階", "裝備進階"),
    ("升階成功", "進階成功"),
    ("升階失敗", "進階失敗"),
    ("無法升階", "無法進階"),
    ("使其升階", "使其進階"),
    ("升階至", "進階至"),
    ("升階", "進階"),
    ("稀有度", "稀少度"),
    ("麻痹", "麻痺"),
    ("恐懼", "恐怖"),
    ("胃部", "腹痛"),
]

# Fix main to properly use BY_ID, BY_EN, TEXT_REPL

def main() -> int:
    if not target.exists():
        print("missing", target)
        return 1

    rows = []
    n = 0
    with target.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            pos = (r.get("位置") or "").strip()
            en = (r.get("原文") or "").strip()
            zh = r.get("填写中文") or ""
            new = zh
            if pos in BY_ID:
                new = BY_ID[pos]
            elif en in BY_EN:
                new = BY_EN[en]
            else:
                for a, b in TEXT_REPL:
                    if a in new:
                        new = new.replace(a, b)
            if new != zh:
                r["填写中文"] = new
                n += 1
            rows.append(r)

    with target.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK: fixed {n} rows")
    return 0


BY_ID = {
    "DST_ITEMASCEND_TITLE": "裝備進階",
    "DST_ITEMASCEND_INFO": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "DST_ITEMASCEND_MATERIAL": "所需材料",
    "DST_ITEMASCEND_ZENNY": "索尼",
    "DST_ITEMASCEND_SUCCESSRATE": "成功率",
    "DST_ITEMASCEND_BTN_ASCEND": "進階",
    "DST_ITEMASCEND_SUCCESS": "進階成功！",
    "DST_ITEMASCEND_FAIL": "進階失敗，成功率已提升。",
    "DST_ITEMASCEND_MAXRANK": "該裝備已達最高稀少度。",
    "DST_STATS_CC_PARALYZE": "麻痺",
    "DST_STATS_CC_TERROR": "恐怖",
    "DST_STATS_CC_CONFUSE": "混亂",
    "DST_STATS_CC_STONE": "石化",
    "DST_STATS_CC_CANDY": "糖果",
    "DST_STATS_CC_BLEED": "出血",
    "DST_STATS_CC_STOMACH": "腹痛",
    "DST_STATS_CC_BURN": "燃燒",
}

BY_EN = {
    "Materials": "材料",
    "Required Materials": "所需材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
    "Paralyze": "麻痺",
    "Paralysis": "麻痺",
    "Terror": "恐怖",
    "Fear": "恐怖",
    "Confuse": "混亂",
    "Confusion": "混亂",
    "Stone": "石化",
    "Candy": "糖果",
    "Bleed": "出血",
    "Bleeding": "出血",
    "Stomach": "腹痛",
    "Burn": "燃燒",
    "Ascend System": "裝備進階",
    "ASCEND": "進階",
    "Ascension succeeded!": "進階成功！",
    "Ascension failed. Success rate increased.": "進階失敗，成功率已提升。",
    "This item is already at the maximum rarity.": "該裝備已達最高稀少度。",
    "Place an equipment piece here to ascend it to the next rarity tier.": "將一件裝備放在這裡，使其進階至下一稀少度。",
    "Items must have the same rarity.": "道具稀少度必須相同。",
    "This item cannot be ascended (no recipe found).": "該裝備無法進階（未找到配方）。",
    "This item cannot be ascended right now.": "該裝備目前無法進階。",
    "Materials": "材料",
    "Success Rate": "成功率",
    "Zeni": "索尼",
}

TEXT_REPL = [
    ("裝備升階", "裝備進階"),
    ("升階成功", "進階成功"),
    ("升階失敗", "進階失敗"),
    ("無法升階", "無法進階"),
    ("使其升階", "使其進階"),
    ("升階至", "進階至"),
    ("升階", "進階"),
    ("稀有度", "稀少度"),
    ("麻痹", "麻痺"),
    ("恐懼", "恐怖"),
    ("胃部", "腹痛"),
] + REPL
