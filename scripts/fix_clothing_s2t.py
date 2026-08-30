#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix clothing half-translations (EN names left) + simplified Chinese residuals."""
from __future__ import annotations

from pathlib import Path
import csv
import re
import sys

root = Path(__file__).resolve().parents[1]
target = root / "data" / "new_translations.tsv"

CLOTHING_NAMES = {
    "Gordon Energy Clothes": "戈登氣合服裝",
    "Enhanced Battle Equip": "強化戰鬥裝備",
    "Archer Armor": "射手鎧甲",
    "Juggernaut Suit": "主宰套裝",
    "Salted Suit": "鹽之套裝",
    "Nebula Combat Gear": "星雲戰鬥裝備",
    "Sun Battle Suit": "太陽戰鬥套裝",
    "Jet Combat Gear": "噴射戰鬥裝備",
    "Spray Coat": "噴塗外套",
    "King of Fighting Gear": "格鬥之王裝備",
    "Armor of God": "神之鎧甲",
    "Rune Clothes": "符文服裝",
    "Bibo's Clothes": "比博的服裝",
    "Combat Equipment No.7": "戰鬥裝備7號",
    "Star Hermit Equip": "星隱士裝備",
    "Hermit Equip": "隱士裝備",
    "Sin Crane Clothes": "罪鶴服裝",
    "Galaxy Turtle Suit": "銀河龜套裝",
    "Raptor Turtle Clothes": "猛禽龜服裝",
    "Raptor Crane Clothes": "猛禽鶴服裝",
    "Phantom Spirit Suit": "幻影之魂套裝",
    "Dream Spirit Suit": "夢境之魂套裝",
    "Geothermal Gear": "地熱裝備",
    "Heavenly Turtle Suit": "天龜套裝",
    "Novitiate Engineer Kit": "見習工程師套件",
    "Gunslinger Clothes": "槍手服裝",
    "Dragonhide Engineer Kit": "龍皮工程師套件",
    "Meteor Gunmen Clothes": "流星槍手服裝",
    "Grimace Work Clothes": "鬼臉工作服",
    "Oracle Gear": "神諭裝備",
    "God Pilot Clothes": "神之駕駛員服裝",
    "Magic Bullet Suit": "魔法子彈套裝",
    "Practice Magic Equip": "練習魔法裝備",
    "Guardian Magic Equip": "守護魔法裝備",
    "Blast Suit": "爆破套裝",
    "Mystic Light Equip": "神秘之光裝備",
    "Demonic Combat Equip": "惡魔戰鬥裝備",
    "Mystic Dragon Equip": "神秘龍裝備",
    "Sacred Magic Equip": "神聖魔法裝備",
    "Linked Combat Equip": "連攜戰鬥裝備",
    "Magic Breaker Battle Suit": "破魔戰鬥套裝",
    "Invisible Magic Clothes": "隱形魔法服裝",
    "Magic Festival Suit": "魔法祭典套裝",
    "God Battle Dragon Gear": "神戰龍裝備",
    "Implied Magic Suit": "隱喻魔法套裝",
    "Guardian Suit": "守護套裝",
    "Lantana Battle Suit": "馬纓丹戰鬥套裝",
    "Practice Dragon Equip": "練習龍裝備",
    "Grace Dragon Battle": "優雅龍戰鬥裝",
    "Mountain Magic Equip": "山岳魔法裝備",
    "Exotic Dragon Equip": "異國龍裝備",
    "Wave Suit": "波動套裝",
    "Every Day Clothes": "日常服裝",
    "Day by Day Clothes": "日日服裝",
    "Every Day Space Suit": "日常太空衣",
    "Magic Ritual Suit": "魔法儀式套裝",
    "Tiamat Wave Suit": "提亞馬特波動套裝",
    "Enhanced Combat Gear": "強化戰鬥裝備",
    "Beginner Fun Clothes": "新手趣味服裝",
    "Scaled Dragon Suit": "鱗龍套裝",
    "Various Artist Suit": "百藝套裝",
    "Famous Spirit Suit": "名魂套裝",
    "Wind of War Armor": "戰爭之風鎧甲",
    "Nature Dragon Suit": "自然龍套裝",
    "Exotic Dragon Suit": "異國龍套裝",
    "Magic Puff Clothes": "魔法膨膨服裝",
    "Soft Magic Clothes": "柔軟魔法服裝",
    "Bloody Mary Suit": "血腥瑪麗套裝",
    "Galaxy Star Armor": "銀河星鎧",
    "Soul Enhanced Clothes": "魂強化服裝",
    "Parunga Wave Suit": "帕蘭加波動套裝",
    "God Dragon Wave Suit": "神龍波動套裝",
    "Novice Enhanced Equip": "新手強化裝備",
    "Magic Coat": "魔法外套",
    "Bliss Magic Suit": "極樂魔法套裝",
    "Loaded Chief Suit": "滿載首領套裝",
    "Very Happy Clothes": "超開心服裝",
    "Warm Suit": "保暖套裝",
    "Magic Volcano Suit": "魔法火山套裝",
    "Diamon Combat Suit": "鑽石戰鬥套裝",
    "Scaled Battle Armor": "鱗甲戰鬥鎧",
    "Hard Magic Clothes": "堅硬魔法服裝",
    "Mirror Clothes": "鏡之服裝",
    "Northern Battle Suit": "北方戰鬥套裝",
    "Angry and Fun Clothes": "怒與樂服裝",
    "Luxury Flame Clothes": "豪華火焰服裝",
    "Final Battle Suit": "最終戰鬥套裝",
    "Shadow Knight Armor": "魔導戰士鎧甲",
    "East Battle Armor": "東方戰鬥鎧甲",
    "West Battle Armor": "西方戰鬥鎧甲",
    "Soft Clothes": "柔軟服裝",
    "Hot Clothes": "炎熱服裝",
    "Planet Dragon God": "行星龍神裝",
    "Celebration Clothes": "慶祝服裝",
    "Celebration Martial Arts Clothes": "慶祝武道服",
    "Noisy Magic Clothes": "吵鬧魔法服裝",
    "Arrival Wave Clothes": "降臨波動服裝",
    "Dragon Law Wave Suit": "龍律波動套裝",
    "Awakening Wave Suit": "覺醒波動套裝",
    "Super Fun Suit": "超趣味套裝",
    "Parunga Dragon Armor": "帕蘭加龍鎧",
    "God Turtle Clothes": "神龜服裝",
    "God Crane Clothes": "神鶴服裝",
    "Combat Intructor Gear": "戰鬥教官裝備",
    "Combat Instructor Gear": "戰鬥教官裝備",
    "New Type Combat Gear": "新型戰鬥裝備",
    "Futuristic Combat Gear": "未來戰鬥裝備",
    "T Type Battle Armor": "T型戰鬥鎧甲",
    "Battle Suit of Gachra": "加克拉戰鬥套裝",
    "Magic Bloody Eye Battle Suit": "魔法血眼戰鬥套裝",
    "Super Shy Magic Clothes": "超害羞魔法服裝",
    "Super Soft Magic Clothes": "超柔軟魔法服裝",
    "Omega Combat Gear": "歐米茄戰鬥裝備",
    "Gale Magic Armor": "疾風魔法鎧甲",
    "Dark Battle Armor": "黑暗戰鬥鎧甲",
    "Super Tiger Martial Arts Clothes": "超虎武道服",
    "Ultra Martial Arts Clothes": "究極武道服",
    "Super Dragon Martial Arts Clothes": "超龍武道服",
    "Classic Martial Arts Clothes": "經典武道服",
    "Prototype CC Martial Arts Clothes": "原型CC武道服",
    "Korin Martial Arts Clothes": "克林武道服",
    "Korin Chief Martial Arts Clothes": "克林長武道服",
    "CC Spirit Clothes": "CC之魂服裝",
    "Super hidden Martial Arts Clothes": "超隱藏武道服",
    "Super Creation Battle Suit": "超創造戰鬥套裝",
}

WORD_MAP = [
    ("Martial Arts Clothes", "武道服"),
    ("Battle Armor", "戰鬥鎧甲"),
    ("Battle Suit", "戰鬥套裝"),
    ("Combat Gear", "戰鬥裝備"),
    ("Combat Equip", "戰鬥裝備"),
    ("Magic Armor", "魔法鎧甲"),
    ("Magic Clothes", "魔法服裝"),
    ("Magic Suit", "魔法套裝"),
    ("Magic Equip", "魔法裝備"),
    ("Dragon Suit", "龍套裝"),
    ("Dragon Armor", "龍鎧"),
    ("Dragon Equip", "龍裝備"),
    ("Wave Suit", "波動套裝"),
    ("Wave Clothes", "波動服裝"),
    ("Spirit Suit", "之魂套裝"),
    ("Space Suit", "太空衣"),
    ("Work Clothes", "工作服"),
    ("Engineer Kit", "工程師套件"),
    ("Battle Equip", "戰鬥裝備"),
    ("Enhanced Equip", "強化裝備"),
    ("Every Day", "日常"),
    ("Day by Day", "日日"),
    ("Armor of God", "神之鎧甲"),
    ("Shadow Knight", "魔導戰士"),
    ("Gunslinger", "槍手"),
    ("Juggernaut", "主宰"),
    ("Galaxy Star", "銀河星"),
    ("Galaxy Turtle", "銀河龜"),
    ("Heavenly Turtle", "天龜"),
    ("Wind of War", "戰爭之風"),
    ("Soul Enhanced", "魂強化"),
    ("Magic Breaker", "破魔"),
    ("Bloody Eye", "血眼"),
    ("Bloody Mary", "血腥瑪麗"),
    ("New Type", "新型"),
    ("Futuristic", "未來型"),
    ("Probability Recipe", "機率配方"),
    ("Limited Edition", "限定版"),
    ("Synthesis", "合成"),
    ("Recipe", "配方"),
    ("Beginner", "新手"),
    ("Novice", "新手"),
    ("Practice", "練習"),
    ("Guardian", "守護"),
    ("Invisible", "隱形"),
    ("Implied", "隱喻"),
    ("Sacred", "神聖"),
    ("Mystic", "神秘"),
    ("Demonic", "惡魔"),
    ("Exotic", "異國"),
    ("Scaled", "鱗甲"),
    ("Nature", "自然"),
    ("Phantom", "幻影"),
    ("Dream", "夢境"),
    ("Famous", "著名"),
    ("Luxury", "豪華"),
    ("Final", "最終"),
    ("Northern", "北方"),
    ("Celebration", "慶祝"),
    ("Awakening", "覺醒"),
    ("Arrival", "降臨"),
    ("Oracle", "神諭"),
    ("Blast", "爆破"),
    ("Armor", "鎧甲"),
    ("Clothes", "服裝"),
    ("Outfit", "服裝"),
    ("Costume", "服裝"),
    ("Suit", "套裝"),
    ("Gear", "裝備"),
    ("Equip", "裝備"),
    ("Coat", "外套"),
    ("Gloves", "手套"),
    ("Helmet", "頭盔"),
    ("Boots", "靴子"),
    ("Magic", "魔法"),
    ("Battle", "戰鬥"),
    ("Combat", "戰鬥"),
    ("Dragon", "龍"),
    ("Turtle", "龜"),
    ("Crane", "鶴"),
    ("Wave", "波動"),
    ("God", "神"),
    ("Super", "超"),
    ("Ultra", "究極"),
    ("Classic", "經典"),
    ("Prototype", "原型"),
    ("Enhanced", "強化"),
    ("Dark", "黑暗"),
    ("Gale", "疾風"),
    ("Soft", "柔軟"),
    ("Hard", "堅硬"),
    ("Hot", "炎熱"),
    ("Warm", "保暖"),
    ("Fun", "趣味"),
    ("Noisy", "吵鬧"),
    ("Mirror", "鏡"),
    ("Flame", "火焰"),
    ("Volcano", "火山"),
    ("Festival", "祭典"),
    ("Ritual", "儀式"),
    ("Bullet", "子彈"),
    ("Pilot", "駕駛員"),
    ("Engineer", "工程師"),
    ("Hermit", "隱士"),
    ("Spirit", "之魂"),
    ("Soul", "魂"),
    ("Star", "星"),
    ("Sun", "太陽"),
    ("Galaxy", "銀河"),
    ("Nebula", "星雲"),
    ("Meteor", "流星"),
    ("Mountain", "山岳"),
    ("Linked", "連攜"),
    ("Loaded", "滿載"),
    ("Chief", "長"),
    ("Hidden", "隱藏"),
    ("Creation", "創造"),
    ("Tiger", "虎"),
    ("Omega", "歐米茄"),
    ("East", "東"),
    ("West", "西"),
]

SLOT_MAP = [
    ("(Top)", "（上）"),
    ("(Pants)", "（褲）"),
    ("(Shoes)", "（鞋）"),
    ("(Gloves)", "（手套）"),
    ("(Helmet)", "（頭盔）"),
    ("(Boots)", "（靴）"),
]

S2T = [
    ("贝吉特", "貝吉特"), ("贝吉塔", "貝吉塔"), ("扎马斯", "扎馬斯"), ("假发", "假髮"),
    ("合体", "合體"), ("定制版", "訂製版"), ("定制", "訂製"), ("最强", "最強"),
    ("为代表", "為代表"), ("龙魂", "龍魂"), ("第三阶段", "第三階段"), ("阶段", "階段"),
    ("的进化", "的進化"), ("进化。", "進化。"), ("闪耀", "閃耀"), ("绿松石", "綠松石"),
    ("萤石", "螢石"), ("红裤军总部", "紅褲軍總部"), ("怪物出现", "怪物出現"),
    ("出现", "出現"), (" %d 点", " %d 點"), ("%d 点", "%d 點"),
    ("进入戰鬥时", "進入戰鬥時"), ("戰鬥时", "戰鬥時"), ("邮件", "郵件"),
    ("拍卖行会", "拍賣行會"), ("自动关闭", "自動關閉"), ("会自動", "會自動"),
    ("隐藏所有目标", "隱藏所有目標"), ("目标", "目標"), ("受擊画面", "受擊畫面"),
    ("受擊贴图", "受擊貼圖"), ("贴图特效", "貼圖特效"), ("贴图", "貼圖"),
    ("冲击闪光", "衝擊閃光"), ("冲击", "衝擊"), ("未击中", "未擊中"),
    ("击倒·麻痹抵抗", "擊倒·麻痺抵抗"), ("击倒·恐惧抵抗", "擊倒·恐怖抵抗"),
    ("击倒·混乱抵抗", "擊倒·混亂抵抗"), ("击倒", "擊倒"), ("麻痹", "麻痺"),
    ("恐惧", "恐怖"), ("混乱", "混亂"), ("格挡", "格擋"),
    ("伤害数字与", "傷害數字與"), ("数字与", "數字與"), ("与受擊", "與受擊"),
    ("点击后套用", "點擊後套用"), ("点击后", "點擊後"), ("总计", "總計"),
    (" %u 胜", " %u 勝"), (" %u 负", " %u 負"), ("%u 胜", "%u 勝"), ("%u 负", "%u 負"),
    ("请登录之后", "請登錄之後"), ("之后角色", "之後角色"), ("龙鼾岩", "龍鼾岩"),
    ("神龙峡谷", "神龍峽谷"), ("峡谷北部", "峽谷北部"), ("峡谷南部", "峽谷南部"),
    ("气合", "氣合"), ("气攻", "氣攻"), ("异常抗性", "異常抗性"),
    ("受损的未来特兰克斯服装", "受損的未來特蘭克斯服裝"),
    ("特兰克斯背心服装", "特蘭克斯背心服裝"),
    ("時間巡逻队特兰克斯服装", "時間巡邏隊特蘭克斯服裝"),
    ("巡逻队", "巡邏隊"), ("特兰克斯", "特蘭克斯"),
    ("SAB 悟空服装", "SAB 悟空服裝"), ("SAB 貝吉塔服装", "SAB 貝吉塔服裝"),
    ("布尔琪服装", "布爾琪服裝"), ("布尔琪", "布爾琪"),
    ("合體扎馬斯服装", "合體扎馬斯服裝"),
    ("西装蓝领带", "西裝藍領帶"), ("西装红领带", "西裝紅領帶"), ("西装黄领带", "西裝黃領帶"),
    ("凱里服装", "凱里服裝"), ("超级布罗利电影服装", "超級布羅利電影服裝"),
    ("布罗利", "布羅利"), ("悟饭超级英雄服装", "悟飯超級英雄服裝"), ("悟饭", "悟飯"),
    ("受损的死神服装", "受損的死神服裝"), ("受损", "受損"),
    ("红领巾军总部废墟", "紅領巾軍總部廢墟"),
    ("舞空术移动", "舞空術移動"), ("舞空术快速", "舞空術快速"),
    ("舞空术加速", "舞空術加速"), ("舞空术训练", "舞空術訓練"),
    ("学习舞空术任務", "學習舞空術任務"), ("舞空术", "舞空術"),
    ("学习", "學習"), ("训练", "訓練"), ("移动", "移動"),
    ("服装", "服裝"), ("超级", "超級"), ("电影", "電影"),
    ("损失", "損失"), ("维斯特兰", "維斯特蘭"), ("奥所罗岛", "奧所羅島"),
    ("时，", "時，"),
]


def translate_clothing(zh: str) -> str:
    new = zh
    for en_name in sorted(CLOTHING_NAMES.keys(), key=len, reverse=True):
        if en_name in new:
            new = new.replace(en_name, CLOTHING_NAMES[en_name])
    for a, b in WORD_MAP:
        if a and a in new:
            new = new.replace(a, b)
    for a, b in SLOT_MAP:
        if a in new:
            new = new.replace(a, b)
    new = re.sub(r"  +", " ", new)
    return new.strip()


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
            zh = r.get("填写中文") or ""
            new = zh
            for a, b in S2T:
                if a in new:
                    new = new.replace(a, b)
            if re.search(r"[A-Za-z]{3,}", new):
                new = translate_clothing(new)
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
