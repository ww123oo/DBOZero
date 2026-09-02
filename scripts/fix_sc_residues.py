#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix Simplified-Chinese residues in data/new_translations.tsv for Taiwan wording.

Run from repo root:
  python scripts/fix_sc_residues.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "data" / "new_translations.tsv"

# Longest-first phrase replacements (SC -> TW). Never single-char 制->製.
REPLACEMENTS: list[tuple[str, str]] = [
    ("能量药水", "氣合藥水"),
    ("气功药水", "氣合藥水"),
    ("气力药水", "氣合藥水"),
    ("升级石", "強化石"),
    ("稀有度", "稀少度"),
    ("服务器", "伺服器"),
    ("竞技场", "競技場"),
    ("账号", "帳號"),
    ("帐户", "帳戶"),
    ("登录", "登錄"),
    ("升阶", "進階"),
    ("制作", "製作"),
    ("制造", "製造"),
    ("确认", "確認"),
    ("权限", "權限"),
    ("失败", "失敗"),
    ("获得", "獲得"),
    ("无法", "無法"),
    ("仅可", "僅可"),
    ("染剂", "染劑"),
    ("学习", "學習"),
    ("放弃", "放棄"),
    ("继续", "繼續"),
    ("相关", "相關"),
    ("极品", "極品"),
    ("正确", "正確"),
    ("默认", "預設"),
    ("设置", "設定"),
    ("信息", "訊息"),
    ("窗口", "視窗"),
    ("网络", "網路"),
    ("用户", "使用者"),
    ("连接", "連線"),
    ("社区", "社群"),
    ("龙珠", "龍珠"),
    ("请先", "請先"),
    ("请稍", "請稍"),
    ("请选", "請選"),
    ("请按", "請按"),
    ("请输", "請輸"),
    ("请再", "請再"),
    ("请等", "請等"),
    ("请确", "請確"),
    ("请使", "請使"),
    ("请在", "請在"),
    ("请点", "請點"),
    ("请勿", "請勿"),
    ("请注", "請注"),
    ("游戏", "遊戲"),
    ("状态", "狀態"),
    ("团队", "團隊"),
    ("报名", "報名"),
    ("奖励", "獎勵"),
    ("准备", "準備"),
    ("属性", "屬性"),
    ("应用", "套用"),
    ("已经", "已經"),
    ("选中", "選中"),
    ("选择", "選擇"),
    ("频道", "頻道"),
    ("离线", "離線"),
    ("当前", "目前"),
    ("检查", "檢查"),
    ("技术", "技術"),
    ("习得", "習得"),
    ("浓度", "濃度"),
    ("装备", "裝備"),
    ("气功", "氣功"),
    ("气力", "氣力"),
    ("防御", "防禦"),
    ("等级", "等級"),
    ("任务", "任務"),
    ("攻击", "攻擊"),
    ("时间", "時間"),
    ("进入", "進入"),
    ("开始", "開始"),
    ("确定", "確定"),
    ("进行", "進行"),
    ("关闭", "關閉"),
    ("结束", "結束"),
    ("数量", "數量"),
    ("开启", "開啟"),
    ("经验", "經驗"),
    ("之后", "之後"),
    ("之前", "之前"),
]
REPLACEMENTS = [(a, b) for a, b in REPLACEMENTS if a != b]
REPLACEMENTS.sort(key=lambda x: -len(x[0]))


def main() -> int:
    if not TSV.is_file():
        print(f"ERROR: missing {TSV}")
        return 1

    with TSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        if not fieldnames or "填写中文" not in fieldnames:
            print("ERROR: TSV must have column 填写中文")
            return 1
        rows = list(reader)

    changed = 0
    for row in rows:
        zh = row.get("填写中文") or ""
        new = zh
        for a, b in REPLACEMENTS:
            if a in new:
                new = new.replace(a, b)
        if new != zh:
            row["填写中文"] = new
            changed += 1

    bak = TSV.with_suffix(".tsv.bak_before_sc_fix")
    if not bak.exists():
        bak.write_bytes(TSV.read_bytes())
        print(f"backup: {bak.name}")

    with TSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"OK: updated {changed} rows in {TSV.relative_to(ROOT)}")
    print("Next: dboc build --variant taiwan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
