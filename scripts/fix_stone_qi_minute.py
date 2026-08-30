#!/usr/bin/env python3
"""Fix: 升級石→強化石, Energy/氣力/氣功藥水→氣合藥水, DST_TIME_MINUTE 最小→分鐘."""
from __future__ import annotations

from pathlib import Path
import csv
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

BY_ID = {
    "DST_TIME_MINUTE": " 分鐘",
    "DST_TABITEMUPGRADENORMALSTONE_ERR": "請放入普通強化石。",
    "DST_TABITEMUPGRADEUPPERSTONE_ERR": "請放入高級強化石。",
}

# English original → preferred Chinese (Energy Potion family)
BY_EN = {
    "Energy Potion": "氣合藥水",
    "Energy Potion (Small)": "氣合藥水（小）",
    "Energy Potion (Medium)": "氣合藥水（中）",
    "Energy Potion (Large)": "氣合藥水（大）",
    "Energy Potion (X)": "氣合藥水（X）",
    "Energy Potion [20x]": "氣合藥水［20×］",
    "Energy Potion [10x]": "氣合藥水［10×］",
    "Energy Potion [5x]": "氣合藥水［5×］",
    "EV Energy Potion": "活動氣合藥水",
}

# Order: longer first
TEXT_REPL = [
    ("氣力藥水", "氣合藥水"),
    ("氣功藥水", "氣合藥水"),
    ("升級石", "強化石"),
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
    print(f"OK: fixed {n} rows in {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
