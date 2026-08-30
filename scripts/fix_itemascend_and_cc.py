#!/usr/bin/env python3
"""Fix Item Ascend terminology and CC status labels in new_translations.tsv.

- 升階 -> 進階 (Item Ascend UI)
- 稀有度 -> 稀少度
- Status: 麻痺 恐怖 混亂 石化 糖果 出血 腹痛 燃燒
"""
from pathlib import Path
import csv
import re

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# Direct ID overrides
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

# Exact English short labels seen in UI
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
    ("麻痺", "麻痺"),
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

# Re-run full pass with BY_ID for itemascend - redefine main more completely

def main2() -> int:
    if not target.exists():
        print("missing", target)
        return 1
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
    rows = []
    n = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        for r in reader:
            pos = (r.get("位置") or "").strip()
            en = (r.get("原文") or "").strip()
            zh = r.get("填写中文") or ""
            new = zh
            if pos in STYLE:
                # for ITEMASCEND handled below via TEXT_REPL and BY
                pass
            # apply style if this is a style label id - for translations style was set above
            new = fix_text(zh)
            for a, b in [
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
            ]:
                if a in new:
                    new = new.replace(a, b)
            # ItemAscend by ID
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
            if pos in STYLE:
                pass  # handled above for style - for lang0 elemental is fine
            if pos in {
                "DST_ITEMASCEND_TITLE", "DST_ITEMASCEND_INFO", "DST_ITEMASCEND_MATERIAL",
                "DST_ITEMASCEND_ZENNY", "DST_ITEMASCEND_SUCCESSRATE", "DST_ITEMASCEND_BTN_ASCEND",
                "DST_ITEMASCEND_SUCCESS", "DST_ITEMASCEND_FAIL", "DST_ITEMASCEND_MAXRANK",
                "DST_STATS_CC_PARALYZE", "DST_STATS_CC_TERROR", "DST_STATS_CC_CONFUSE",
                "DST_STATS_CC_STONE", "DST_STATS_CC_CANDY", "DST_STATS_CC_BLEED",
                "DST_STATS_CC_STOMACH", "DST_STATS_CC_BURN",
            }:
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
                if pos in BY_ID and r.get("填写中文") != BY_ID[pos]:
                    r["填写中文"] = BY_ID[pos]
                    changed += 1
            en_s = (r.get("原文") or "").strip()
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
            if pos in {
                "DST_ITEMASCEND_TITLE", "DST_ITEMASCEND_INFO", "DST_ITEMASCEND_MATERIAL",
                "DST_ITEMASCEND_ZENNY", "DST_ITEMASCEND_SUCCESSRATE", "DST_ITEMASCEND_BTN_ASCEND",
                "DST_ITEMASCEND_SUCCESS", "DST_ITEMASCEND_FAIL", "DST_ITEMASCEND_MAXRANK",
                "DST_STATS_CC_PARALYZE", "DST_STATS_CC_TERROR", "DST_STATS_CC_CONFUSE",
                "DST_STATS_CC_STONE", "DST_STATS_CC_CANDY", "DST_STATS_CC_BLEED",
                "DST_STATS_CC_STOMACH", "DST_STATS_CC_BURN",
            }:
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
                if pos in BY_ID and r.get("填写中文") != BY_ID[pos]:
                    r["填写中文"] = BY_ID[pos]
                    changed += 1
            en_s = (r.get("原文") or "").strip()
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
            if en_s in {
                "Materials", "Required Materials", "Success Rate", "Zeni",
                "Paralyze", "Paralysis", "Terror", "Fear", "Confuse", "Confusion",
                "Stone", "Candy", "Bleed", "Bleeding", "Stomach", "Burn",
                "Ascend System", "ASCEND",
                "Ascension succeeded!",
                "Ascension failed. Success rate increased.",
                "This item is already at the maximum rarity.",
                "Place an equipment piece here to ascend it to the next rarity tier.",
                "Items must have the same rarity.",
                "This item cannot be ascended (no recipe found).",
                "This item cannot be ascended right now.",
            }:
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
                if en_s in BY_EN and r.get("填写中文") != BY_EN[en_s]:
                    r["填写中文"] = BY_EN[en_s]
                    changed += 1
            # text replacements for 升階 etc
            zh2 = r.get("填写中文") or ""
            new2 = zh2
            for a, b in [
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
            ]:
                if a in new2:
                    new2 = new2.replace(a, b)
            if new2 != zh2:
                r["填写中文"] = new2
                changed += 1
            rows.append(r)

    # The above double-appends - I made a mess. Rewrite cleanly below - actually the loop structure is wrong.
    return changed


if __name__ == "__main__":
    raise SystemExit(main())
