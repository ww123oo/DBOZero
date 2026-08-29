#!/usr/bin/env python3
"""Quick replace common Simplified→Traditional in 填写中文."""
from pathlib import Path
import csv

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

REPL = [
    ("战斗", "戰鬥"), ("无法", "無法"), ("竞技场", "競技場"), ("经验", "經驗"),
    ("连胜", "連勝"), ("升级", "升級"), ("公会", "公會"), ("被动", "被動"),
    ("已达", "已達"), ("等级", "等級"), ("点数", "點數"), ("时间", "時間"),
    ("返还", "返還"), ("目录", "目錄"), ("记录", "記錄"), ("邮件", "郵件"),
    ("拍卖", "拍賣"), ("进入", "進入"), ("该宠", "該寵"), ("自动", "自動"),
    ("捡起", "撿起"), ("会长", "會長"), ("隐藏", "隱藏"), ("受击", "受擊"),
    ("任务", "任務"), ("资讯", "資訊"), ("解锁", "解鎖"), ("网页", "網頁"),
    ("无效", "無效"), ("声望", "聲望"), ("冷却", "冷卻"), ("进行", "進行"),
    ("失败", "失敗"), ("设置", "設置"), ("确认", "確認"), ("开始", "開始"),
    ("结束", "結束"), ("完成", "完成"), ("挑战", "挑戰"), ("奖励", "獎勵"),
    ("礼包", "禮包"), ("账号", "帳號"), ("登录", "登入"), ("服务器", "伺服器"),
    ("强化", "強化"), ("药水", "藥水"), ("技能", "技能"), ("角色", "角色"),
    ("背包", "背包"), ("物品", "物品"), ("伤害", "傷害"), ("暴击", "暴擊"),
    ("闪避", "閃避"), ("格斗", "格鬥"), ("气功", "氣功"), ("剑术", "劍術"),
    ("战士", "戰士"), ("龙族", "龍族"), ("装备", "裝備"), ("防御", "防禦"),
    ("攻击", "攻擊"), ("打开", "打開"), ("关闭", "關閉"), ("开启", "開啟"),
    ("关闭", "關閉"), ("选择", "選擇"), ("确认", "確認"), ("取消", "取消"),
]

rows, n = [], 0
with target.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fields = reader.fieldnames
    for r in reader:
        zh = r.get("填写中文") or ""
        new = zh
        for a, b in REPL:
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
print(f"OK: s2t touched {n} rows")
