#!/usr/bin/env python3
"""Advanced items: 進階→高級 (not Item Ascend 進階). Class name fills."""
from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

# Phrase replacements (longer first)
REPL = [
    ("進階經驗卷軸", "高級經驗卷軸"),
    ("进阶经验卷轴", "高級經驗卷軸"),
    ("進階防具強化石", "高級防具強化石"),
    ("进阶防具强化石", "高級防具強化石"),
    ("進階武器強化石", "高級武器強化石"),
    ("进阶武器强化石", "高級武器強化石"),
    ("進階舞空術卷軸", "高級舞空術卷軸"),
    ("进阶舞空术卷轴", "高級舞空術卷軸"),
    ("進階藥水膠囊", "高級藥水膠囊"),
    ("进阶药水胶囊", "高級藥水膠囊"),
    ("進階強化石膠囊", "高級強化石膠囊"),
    ("进阶强化石胶囊", "高級強化石膠囊"),
    ("進階飾品配方箱", "高級飾品配方箱"),
    ("进阶饰品配方箱", "高級飾品配方箱"),
    # Only when clearly "Advanced X" product names, not 裝備進階
    ("進階經驗", "高級經驗"),
    ("進階防具", "高級防具"),
    ("進階武器", "高級武器"),
]

# Exact 原文 overrides for classes
BY_EN = {
    "Mighty Majin": "大魔人",
    "Wonder Majin": "意魔人",
    "Martial Artist": "武道家",
    "Fighter": "格鬥家",
    "Spiritualist": "氣功師",
    "Crane Hermit": "鶴仙流",
    "Swordsman": "劍術家",
    "Turtle Hermit": "龜仙流",
    "Warrior": "戰士",
    "Dragon Clan": "龍族",
    "Dark Warrior": "魔界戰士",
    "Shadow Knight": "魔導戰士",
    "Dende Priest": "天天導師",
    "Poko Priest": "波可導師",
    "Grand Chef Majin": "葛蘭魔",
    "Ultimate Majin": "奧迪魔",
    "Karma Majin": "卡爾魔",
    "Plasma Majin": "普利茲魔",
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
        en = (r.get("原文") or "").strip()
        zh = r.get("填写中文") or ""
        new = zh
        if en in BY_EN:
            if new != BY_EN[en]:
                new = BY_EN[en]
        else:
            for a, b in REPL:
                if a in new:
                    # skip pure 裝備進階 UI strings
                    if "裝備進階" in new and a.startswith("進階") and "卷軸" not in new and "強化石" not in new and "膠囊" not in new and "配方" not in new and "經驗" not in new and "防具" not in new and "武器" not in new:
                        continue
                    new = new.replace(a, b)
        if new != zh:
            r["填写中文"] = new
            changed += 1
        rows.append(r)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"OK: advanced/class fixes on {changed} rows")
