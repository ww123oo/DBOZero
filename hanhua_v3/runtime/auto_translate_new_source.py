from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

__all__ = [
    "generate_taiwan_rows",
    "generate_tbl_rows",
    "main",
    "translate_name",
    "translate_untranslated",
]

try:
    from . import tbl_utf16_patch as tbl
except ImportError:  # Keep direct script execution working.
    import tbl_utf16_patch as tbl


AUTO_TBL_BEGIN = "# AUTO_BLOCK_TBL_VISIBLE_NAMES_20260604_BEGIN"
AUTO_TBL_END = "# AUTO_BLOCK_TBL_VISIBLE_NAMES_20260604_END"
AUTO_TAIWAN_BEGIN = "# AUTO_BLOCK_TAIWAN_SAFE_UNTRANSLATED_20260604_BEGIN"
AUTO_TAIWAN_END = "# AUTO_BLOCK_TAIWAN_SAFE_UNTRANSLATED_20260604_END"

ALLOWED_ASCII = {
    "A",
    "AI",
    "AOT",
    "B",
    "BD",
    "BID",
    "BMO",
    "C",
    "CC",
    "CPU",
    "D",
    "DD",
    "DWC",
    "E",
    "EP",
    "EV",
    "EX",
    "EXP",
    "F",
    "GM",
    "H",
    "HEN",
    "HL",
    "HTB",
    "IS",
    "L",
    "LP",
    "LV",
    "Lv",
    "M",
    "N",
    "P",
    "P2",
    "P3",
    "RP",
    "R",
    "S",
    "S2",
    "SK",
    "SP",
    "T",
    "U",
    "U75",
    "UD",
    "V",
    "VIP",
    "X",
    "Y",
    "Z",
    "2P",
    "3P",
}

WORD_MAP = {
    "AJIN": "魔人",
    "AMEK": "那美克",
    "AOT": "进击巨人",
    "Adventurer": "冒险家",
    "Advanced": "高级",
    "Agility": "敏捷",
    "Akeno": "朱乃",
    "Alternate": "异色",
    "Android": "人造人",
    "Ancient": "古代",
    "Aqua": "阿库娅",
    "Area": "区域",
    "Armored": "装甲",
    "Armor": "盔甲",
    "Army": "军",
    "Arts": "武道",
    "Ascension": "飞升",
    "Artist": "武道家",
    "Artists": "武道家",
    "Attack": "攻击",
    "Awakening": "觉醒",
    "Axe": "斧",
    "Backpack": "背包",
    "Ball": "球",
    "Bardock": "巴达克",
    "Battle": "战斗",
    "Beat": "节拍",
    "Beam": "光束",
    "Beerus": "比鲁斯",
    "Beetle": "甲虫",
    "Big": "大",
    "Black": "黑色",
    "Blazing": "炽热",
    "Blow": "打击",
    "Blessed": "祝福",
    "Blue": "蓝色",
    "Bluma": "布尔玛",
    "Bulma": "布尔玛",
    "Bomb": "炸弹",
    "Boo": "布欧",
    "Bootenks": "布欧悟天克斯",
    "Boss": "首领",
    "Box": "盒",
    "Brainwashed": "被洗脑",
    "Broadwood": "布洛德伍德",
    "Broly": "布罗利",
    "Bucket": "桶",
    "Buu": "布欧",
    "Buuhan": "布欧悟饭",
    "Buff": "增益",
    "Burter": "巴特",
    "Bus": "巴士",
    "CPU": "CPU",
    "CD": "冷却",
    "CHIP": "芯片",
    "CON": "耐力",
    "Cannon": "炮",
    "Capsule": "胶囊",
    "Captain": "队长",
    "Carnival": "嘉年华",
    "Cat": "猫",
    "Cell": "沙鲁",
    "Chiaotzu": "饺子",
    "Chest": "胸甲",
    "Chief": "首领",
    "Chamber": "房间",
    "Chip": "芯片",
    "Circuit": "电路",
    "Citizen": "市民",
    "Clan": "族",
    "Class": "职业",
    "Claws": "爪",
    "Classic": "经典",
    "Clothes": "服装",
    "Club": "棒",
    "Coin": "硬币",
    "Combat": "战斗",
    "Comfort": "舒适",
    "Combo": "连击",
    "Controlled": "受控",
    "Controller": "控制器",
    "Core": "核心",
    "Costume": "服装",
    "Coupon": "券",
    "Cooldown": "冷却",
    "Crane": "鹤",
    "Cricket": "蟋蟀",
    "Crash": "冲击",
    "Cooking": "料理",
    "Cosmic": "宇宙",
    "Crystal": "水晶",
    "Cui": "丘夷",
    "Custom": "定制",
    "Dark": "黑暗",
    "Darkness": "达克妮斯",
    "Dash": "冲刺",
    "Dashboard": "仪表盘",
    "Data": "数据",
    "Damage": "伤害",
    "Della": "德拉",
    "Demon": "恶魔",
    "Defense": "防御",
    "Devil": "魔鬼",
    "Device": "装置",
    "Diamond": "钻石",
    "Diference": "差异",
    "Delight": "喜悦",
    "Dogi": "时装",
    "Dodoria": "多多利亚",
    "Double": "双",
    "Downgrade": "降级",
    "Dragon": "龙",
    "Dye": "染色",
    "Drum": "鼓",
    "Drums": "鼓",
    "Dungeon": "副本",
    "Earring": "耳环",
    "EARN": "耳环",
    "Egg": "蛋",
    "Elite": "精英",
    "Empowerment": "强化",
    "Energy": "气功",
    "Engineer": "工程师",
    "Erza": "艾露莎",
    "Event": "活动",
    "Every": "全",
    "Evil": "邪恶",
    "Equip": "装备",
    "Eye": "眼",
    "Fajita": "肥吉塔",
    "Fan": "扇",
    "Fancy": "华丽",
    "Family": "家族",
    "Fainting": "昏迷",
    "Field": "野外",
    "Fighter": "战士",
    "Fire": "火",
    "Firepower": "火力",
    "FL": "飞行",
    "Flame": "火焰",
    "Flexarot": "弗莱克萨罗特",
    "Flight": "飞行",
    "Force": "力量",
    "Form": "形态",
    "FULL": "全套",
    "FULY": "全套",
    "Frieza": "弗利萨",
    "Frieza's": "弗利萨",
    "Frog": "青蛙",
    "Fuel": "燃料",
    "Furry": "毛绒",
    "Fury": "狂怒",
    "Gauntlets": "臂甲",
    "Gear": "装备",
    "Gem": "宝石",
    "Gems": "宝石",
    "General": "将军",
    "Generator": "发生器",
    "Ghost": "幽灵",
    "Giant": "巨大",
    "Gift": "礼物",
    "Ginyu": "基纽",
    "Gogeta": "悟吉塔",
    "Gohan": "孙悟饭",
    "Goku": "孙悟空",
    "Gold": "黄金",
    "Golden": "黄金",
    "Goten": "孙悟天",
    "Gotenks": "悟天克斯",
    "Great": "巨大",
    "Green": "绿色",
    "Guard": "守卫",
    "Guldo": "古杜",
    "Gun": "枪",
    "Hair": "发型",
    "Halloween": "万圣节",
    "Hallowen": "万圣节",
    "Happy": "快乐",
    "Hat": "帽子",
    "Head": "头",
    "Healing": "治疗",
    "Hellfire": "地狱火",
    "Helmet": "头盔",
    "High": "高级",
    "hidden": "隐藏",
    "Hit": "希特",
    "HM": "人类",
    "Human": "人类",
    "Imperator": "帝王",
    "Intense": "浓烈",
    "Invincible": "无敌",
    "Infinity": "无限",
    "Iron": "铁",
    "Jeice": "吉斯",
    "Jiren": "吉连",
    "Judgment": "审判",
    "Kagune": "赫子",
    "Kami": "天神",
    "Kami's": "天神",
    "Kamiccolo": "卡米克洛",
    "Key": "钥匙",
    "King": "王",
    "Kiri": "基里",
    "Kit": "工具包",
    "Korin": "卡林",
    "Krillin": "克林",
    "Law": "法则",
    "Legendary": "传说",
    "Letter": "信",
    "Life": "生命",
    "Light": "光",
    "Lightning": "闪电",
    "Limited": "限定",
    "Liquid": "液体",
    "Lizard": "蜥蜴",
    "Long": "长",
    "Looks": "外观",
    "Lotus": "莲花",
    "Lower": "低级",
    "Lucy": "露西",
    "Machine": "机器",
    "Magic": "魔法",
    "Majin": "魔人",
    "Manager": "管理员",
    "Martial": "武道家",
    "Mask": "面具",
    "Master": "大师",
    "Material": "材料",
    "Meat": "肉",
    "Memory": "存储器",
    "Mentor": "导师",
    "Metal": "金属",
    "Meteor": "流星",
    "Might": "大",
    "Military": "军用",
    "Mineral": "矿石",
    "Mira": "米拉",
    "MJ": "魔人",
    "Mole": "鼹鼠",
    "Moro": "摩罗",
    "Mr": "先生",
    "Mushroom": "蘑菇",
    "Mustache": "胡子",
    "Mysterious": "神秘",
    "Namek": "那美克",
    "Namekian": "那美克星人",
    "Nappa": "那巴",
    "Narak": "那拉克",
    "NM": "那美克",
    "Natal": "圣诞",
    "Natsu": "纳兹",
    "Needle": "针",
    "Necklace": "项链",
    "New": "新",
    "Nika": "尼卡",
    "No": "无",
    "Normal": "普通",
    "Old": "老旧",
    "Only": "专用",
    "Oozaru": "大猿",
    "Outfit": "套装",
    "Ozaru": "大猿",
    "Paella": "皮拉夫",
    "Pants": "裤子",
    "Part": "零件",
    "Parts": "零件",
    "Party": "组队",
    "Pattern": "图案",
    "Pet": "宠物",
    "Phoenix": "凤凰",
    "Photo": "照片",
    "Physical": "物理",
    "Piccolo": "比克",
    "Pilaf": "皮拉夫",
    "Pill": "药丸",
    "Pilot": "驾驶员",
    "Pink": "粉色",
    "Pirate": "海盗",
    "Pleasant": "愉快",
    "Popo": "波波",
    "Porunga": "波伦加",
    "Potion": "药水",
    "Power": "力量",
    "Powerful": "强力",
    "Probability": "概率",
    "premium": "高级",
    "PROP": "属性",
    "Practitioner": "修行者",
    "Preview": "预览",
    "Prince": "王子",
    "Pride": "骄傲",
    "Processor": "处理器",
    "Puar": "普尔",
    "Purple": "紫色",
    "PY": "物理",
    "Pure": "纯粹",
    "Rabbit": "兔子",
    "Raditz": "拉蒂兹",
    "Rainbow": "彩虹",
    "RING": "戒指",
    "Recipe": "配方",
    "Recoome": "利库姆",
    "Recovery": "恢复",
    "Red": "红色",
    "Refurbished": "翻新",
    "Ranked": "排位",
    "Reward": "奖励",
    "Ring": "戒指",
    "Rings": "戒指",
    "Robot": "机器人",
    "Rock": "岩石",
    "Roar": "咆哮",
    "Ruby": "红宝石",
    "Rubber": "橡胶",
    "Sabo": "萨博",
    "Saibaman": "栽培人",
    "Saiyan": "赛亚人",
    "Sample": "样品",
    "Scales": "鳞片",
    "Scouter": "探测器",
    "Scroll": "卷轴",
    "SEM": "半套",
    "SEMI": "半套",
    "Sensation": "感受",
    "Seiya": "星矢",
    "Set": "套装",
    "Shadow": "暗影",
    "Shard": "碎片",
    "Shocking": "震撼",
    "Shower": "淋浴",
    "Shenron": "神龙",
    "Shoes": "鞋子",
    "Short": "短",
    "Silver": "银色",
    "Skin": "皮肤",
    "Sky": "天空",
    "Slash": "斩击",
    "Smile": "笑脸",
    "Smooth": "流畅",
    "Soldier": "士兵",
    "Solo": "单人",
    "Soul": "灵魂",
    "Sound": "声音",
    "Space": "空间",
    "Special": "特殊",
    "Speed": "速度",
    "Spirit": "精神",
    "Spiritual": "精神",
    "Spiritualist": "气功师",
    "Spiritualists": "气功师",
    "SS3": "超级赛亚人3",
    "Staff": "杖",
    "Stage": "阶段",
    "Star": "星",
    "Steel": "钢",
    "Stick": "棍",
    "Stone": "石",
    "Strong": "强力",
    "Suit": "套装",
    "Super": "超级",
    "Supply": "补给",
    "Support": "支援",
    "Surprise": "惊喜",
    "Sword": "剑",
    "Tail": "尾巴",
    "Tanjiro": "炭治郎",
    "Target": "目标",
    "Tasty": "美味",
    "Tiamat": "提亚马特",
    "Tien": "天津饭",
    "Tiger": "老虎",
    "Time": "时间",
    "Title": "称号",
    "Top": "上衣",
    "Tool": "工具",
    "Towa": "托娃",
    "Trader": "商人",
    "Trainee": "见习",
    "Transmog": "幻化",
    "Treasure": "宝藏",
    "Tremor": "震地",
    "Trunks": "特兰克斯",
    "Trumpet": "号角",
    "True": "真",
    "Turtle": "龟",
    "Ultimate": "终极",
    "Underwear": "内衣",
    "Unit": "部队",
    "Unlimited": "无限",
    "Upgrade": "升级",
    "Usable": "可使用",
    "Upper": "高级",
    "Vegeta": "贝吉塔",
    "Vegito": "贝吉特",
    "Village": "村",
    "Villain": "反派",
    "Wand": "短杖",
    "Warrior": "战士",
    "Water": "水",
    "Weapon": "武器",
    "Whis": "维斯",
    "White": "白色",
    "Whitebeard": "白胡子",
    "Wild": "狂野",
    "Wind": "风",
    "Wings": "翅膀",
    "Wolf": "狼",
    "Wonder": "意",
    "Wonderful": "美妙",
    "Work": "工作",
    "Wreckage": "残骸",
    "Wounded": "受伤",
    "Xeno": "异次元",
    "Yahoi": "雅霍伊",
    "Yamcha": "雅木茶",
    "Yellow": "黄色",
    "Zamasu": "扎马斯",
    "Zarbon": "萨博",
}

WORD_MAP.update(
    {
        "Absolute": "绝对",
        "Adorable": "可爱",
        "Alien": "异星",
        "Alchemist": "炼金",
        "Award": "奖励",
        "Bao": "鲍",
        "Basic": "基础",
        "Beanstalk": "豆茎",
        "Beans": "豆",
        "Beverage": "饮料",
        "Bi": "双色",
        "Blade": "刃",
        "Blast": "爆破",
        "Bloodlust": "嗜血",
        "Bull": "公牛",
        "Chaos": "混沌",
        "Chili": "辣椒",
        "Chocolate": "巧克力",
        "Cola": "可乐",
        "Comet": "彗星",
        "Comodo": "科莫多",
        "Corn": "玉米",
        "Cosmo": "宇宙",
        "Court": "宫廷",
        "Cream": "奶油",
        "Crisp": "酥脆",
        "Cuckoo": "咕咕鸡",
        "Cut": "切割",
        "Daily": "每日",
        "Demigod": "半神",
        "Detoxification": "解毒",
        "Dinosaur": "恐龙",
        "Drink": "饮料",
        "Earth": "大地",
        "Elder": "长老",
        "Ejection": "喷射",
        "Electro": "电光",
        "Enraged": "狂怒",
        "Epic": "史诗",
        "Extract": "萃取物",
        "Extra": "特级",
        "Fairy": "仙女",
        "Fish": "鱼",
        "Firepower": "火力",
        "Frame": "框架",
        "Fried": "炸",
        "Gale": "疾风",
        "Galactic": "银河",
        "Gang": "刚",
        "Gangjian": "刚剑",
        "Gatekeeper": "守门人",
        "Giant": "巨大",
        "Gloves": "手套",
        "Grade": "等级",
        "Grid": "格纹",
        "Halberd": "戟",
        "Hardcore": "硬核",
        "Herbs": "药草",
        "Honor": "荣耀",
        "Hot": "火辣",
        "Huang": "黄",
        "Ice": "冰",
        "Injection": "注射",
        "Jade": "翡翠",
        "Karma": "卡尔玛",
        "Killer": "杀手",
        "Leaf": "叶",
        "Leather": "皮革",
        "Legend": "传说",
        "Lollipop": "棒棒糖",
        "Manufacturing": "制造",
        "Mechanical": "机械",
        "Medicinal": "药用",
        "Memorial": "纪念",
        "Minded": "心智",
        "Nimbus": "筋斗云",
        "Noble": "贵族",
        "Nova": "新星",
        "Octopus": "章鱼",
        "Optic": "光学",
        "Original": "原始",
        "Pain": "疼痛",
        "Palm": "棕榈",
        "Plasma": "等离子",
        "Plump": "饱满",
        "Poko": "波可",
        "Popsicle": "冰棒",
        "Pound": "重击",
        "Premium": "高级",
        "Prestige": "威望",
        "Prototype": "原型",
        "Pudding": "布丁",
        "QQ": "QQ",
        "Remembrance": "纪念",
        "Resistance": "抗性",
        "Rugged": "坚固",
        "Sapphire": "蓝宝石",
        "Scarlet": "绯红",
        "Secret": "秘密",
        "Simple": "简单",
        "Smoked": "烟熏",
        "Smoothie": "奶昔",
        "Soda": "苏打",
        "Solid": "坚固",
        "Sour": "酸",
        "Sparkling": "闪耀",
        "Spa": "温泉",
        "Spicy": "辛辣",
        "Starfish": "海星",
        "Suglite": "舒俱来石",
        "Sunny": "阳光",
        "Suspicious": "可疑",
        "Sweet": "甜",
        "SwordMaster": "剑术大师",
        "Swordsman": "剑术家",
        "Taichu": "太初",
        "The": "",
        "Therapy": "治疗",
        "Suglite": "舒俱来石",
        "Tilapia": "罗非鱼",
        "Thunder": "雷霆",
        "Treatment": "治疗",
        "Trust": "信赖",
        "Ultra": "极限",
        "Ultimate": "终极",
        "Valkyrie": "女武神",
        "Vital": "活力",
        "Watercolor": "水彩",
        "Wheel": "轮",
        "Willow": "柳木",
        "Yan": "岩",
        "Yang": "阳",
        "Yin": "阴",
    }
)

PHRASE_MAP = {
    "Black Dragon": "黑龙",
    "Black Dragon Scales": "黑龙鳞片",
    "BMO Backpack": "BMO背包",
    "CC Blessed Ruby": "CC祝福红宝石",
    "Capsule Corp": "胶囊公司",
    "Death Axe": "死亡之斧",
    "Devil's Fury": "魔鬼狂怒",
    "Dragon Ball": "龙珠",
    "Dragon Court": "龙宫",
    "Dragon Bird": "龙鸟",
    "Dragon Power": "龙之力",
    "Dragon Spirit": "龙之魂",
    "Crane Spirit": "鹤仙流精神",
    "Turtle Spirit": "龟仙流精神",
    "Double Hit": "双重打击",
    "Frieza's Army": "弗利萨军",
    "GM Armor Upgrade Stone": "GM防具升级石",
    "GM Weapon Upgrade Stone": "GM武器升级石",
    "Ginyu Force": "基纽特战队",
    "Ginyu Special Ops": "基纽特战队",
    "Golden Oozaru": "黄金大猿",
    "Hakai Rings": "破坏戒指",
    "Happy Carnival Sensation": "快乐嘉年华",
    "Kami's Judgment": "天神审判",
    "Legendary Dogi Ball": "传说时装球",
    "Lower Rank Dogi Stone": "低级时装石",
    "Martial Artist": "武道家",
    "Martial Arts": "武道",
    "Mech Dragon": "机械暴龙",
    "Mira's Army": "米拉军",
    "Mira's Military": "米拉军",
    "Mr Popo": "波波先生",
    "New Frieza's Army": "新弗利萨军",
    "Pleasant Sound Shower": "悦耳音波",
    "Cooking Delight Combo": "料理连击",
    "Red Pants Army": "红裤军",
    "Red Pants": "红裤军",
    "Saiyan Tail": "赛亚人尾巴",
    "Shocking Smooth Beat": "震撼节拍",
    "Shadow Sovereign": "暗影暴君",
    "Sky Dungeon Material": "天空副本材料",
    "Soul Force": "灵魂力量",
    "Super Saiyan BLUE": "超级赛亚人蓝",
    "Super Saiyan Blue": "超级赛亚人蓝",
    "Super Saiyan GOD": "超级赛亚人之神",
    "Super Saiyan God": "超级赛亚人之神",
    "Super Saiyan Legendary": "传说超级赛亚人",
    "Super Saiyan Rose": "超级赛亚人桃红",
    "Super Saiyan": "超级赛亚人",
    "Time Breaker": "时空破坏者",
    "Time Chamber": "精神时光屋",
    "Time Machine": "时光机",
    "Recipe Chest": "配方宝箱",
    "Hair Dye": "染发剂",
    "High Grade": "高级",
    "God Eye": "神眼",
    "Yin & Yang": "阴阳",
    "To the Hyperbolic Time Chamber": "前往精神时光屋",
    "Treasure Chest": "宝箱",
    "Wonderful Crash": "精彩冲击",
    "Two Handed Sword": "双手剑",
    "Upper Rank Dogi Stone": "高级时装石",
    "VIP Capsule": "VIP胶囊",
}

CLASS_NAME_MAP = {
    "Martial": "武道家",
    "Martial Artist": "武道家",
    "Spiritualist": "气功师",
    "Warrior": "那美克战士",
    "Namek Warrior": "那美克战士",
    "Dragon": "龙族",
    "Dragon Clan": "那美克龙族",
    "Might": "大魔人",
    "Might Majin": "大魔人",
    "Wonder": "意魔人",
    "Wonder Majin": "意魔人",
}

CLASS_SOURCE_RE = re.compile(
    r"\((Martial|Spiritualist|Warrior|Dragon|Might|Wonder|Namek Warrior|Dragon Clan|Might Majin|Wonder Majin)\)"
    r"|Martial Artist|Spiritualist|Dragon Clan|Might Majin|Wonder Majin|Namek Warrior"
)

UI_EXACT = {
    "%d FPS": "%d FPS",
    "%d Streak": "%d连胜",
    "%d ~ %d players": "%d ~ %d名玩家",
    "%s Zeni": "%s索尼",
    "Accessory 2 - Richness": "饰品2 - 富饶",
    "Apply Only Effect": "仅应用效果",
    "COMMAND": "命令",
    "Card Grade": "卡片等级",
    "Delete resolved mail in batches of 6.": "批量删除已处理邮件，每次最多6封。",
    "Dragon Ball Lost!!": "龙珠丢失!!",
    "Dropped To pick up": "已掉落，可拾取",
    "Earned %d Mudosa": "获得%d武道币",
    "Enter DWC": "进入DWC",
    "EXP : %d / %d": "经验 : %d / %d",
    "Fainted": "昏迷",
    "Necklace": "项链",
    "No mail available to receive.": "没有可领取的邮件。",
    "No resolved mail to delete.": "没有可删除的已处理邮件。",
    "Not Scramble Participant": "非龙珠争夺战参与者",
    "PK Impossible to Enter": "PK状态无法进入",
    "Please wait 15 seconds before trying again.": "请等待15秒后再试。",
    "Rare": "稀有",
    "Receive items and Zeni from eligible mail (up to 6 per use, 15s cooldown).": "从符合条件的邮件领取道具和索尼（每次最多6封，冷却15秒）。",
    "TIMEQUEST": "时光任务",
    "Uncommon": "普通",
}

KEY_TOKEN_MAP = {
    "ABLE": "可用",
    "ACCESSORY": "饰品",
    "ALREADY": "已",
    "APPLY": "应用",
    "ARMOR": "防具",
    "ARLEADY": "已",
    "ASK": "确认",
    "AURA": "气场",
    "BLUE": "蓝",
    "BOO": "布欧",
    "BUUHAN": "布欧悟饭",
    "CANT": "不能",
    "CAN": "可以",
    "CANCEL": "取消",
    "CARD": "卡片",
    "CHANGE": "变更",
    "CHANGED": "已变更",
    "CLIENT": "客户端",
    "COLOR": "颜色",
    "CREATE": "创建",
    "CREATED": "已创建",
    "CURRENT": "当前",
    "CURENT": "当前",
    "DARK": "黑暗",
    "DOGI": "时装",
    "DOJO": "道场",
    "DRAGONBALL": "龙珠",
    "DYE": "染色",
    "END": "结束",
    "ERROR": "错误",
    "EQUIP": "装备",
    "EVIL": "邪恶",
    "EXPAIN": "说明",
    "EXPLAIN": "说明",
    "FUNCTION": "功能",
    "GET": "获得",
    "GRADE": "等级",
    "GUN": "枪",
    "GUILDFUNCTION": "公会功能",
    "GOTENKS": "悟天克斯",
    "GREAT": "巨大",
    "GUILD": "公会",
    "ITEM": "道具",
    "JOB": "职业",
    "KAIOKEN": "界王拳",
    "KING": "帝王",
    "LD": "",
    "LEVEL": "等级",
    "LS": "",
    "MAKE": "制作",
    "MANIA": "狂热者",
    "MERCHANT": "商人",
    "MECH": "机械",
    "MOVE": "移动",
    "MULTIDIALOG": "对话",
    "MAJIN": "魔人",
    "MUST": "必须",
    "NAMEK": "那美克星人",
    "NEED": "需要",
    "NOT": "未",
    "ONLY": "仅",
    "PACKET": "封包",
    "PREREQUISITE": "前置条件",
    "PREVIEW": "预览",
    "REPEAT": "重复",
    "REWARD": "奖励",
    "PURE": "纯粹",
    "REGI": "登记",
    "REGISTER": "登记",
    "ROSE": "桃红",
    "SAIYAN": "赛亚人",
    "SETUP": "设置",
    "SEND": "发送",
    "SCRAMBLE": "争夺战",
    "SKILL": "技能",
    "SLOT": "栏位",
    "SUB": "副",
    "SUPER": "超级",
    "TAIL": "尾巴",
    "TOGGLE": "切换",
    "TRASMOG": "幻化",
    "TYPE": "类型",
    "UPGRADE": "升级",
    "USE": "使用",
    "VEHICLE": "载具",
    "VERSION": "版本",
    "WEAPON": "武器",
    "WHEN": "状态下",
    "YOU": "你",
}


FORM_MAP = {
    "buuhan": "布欧悟饭",
    "dark namek": "黑暗那美克",
    "evil boo": "邪恶布欧",
    "evil namek": "邪恶那美克",
    "gotenks boo": "悟天克斯布欧",
    "gotenks boo magic": "悟天克斯布欧魔法",
    "great ape": "大猿",
    "great orange": "巨大橙色",
    "legendary super saiyan": "传说超级赛亚人",
    "majin super saiyan": "魔人超级赛亚人",
    "namek super saiyan": "那美克超级赛亚人",
    "super saiyan 4": "超级赛亚人4",
    "super saiyan god": "超级赛亚人之神",
    "super saiyan god super saiyan": "超级赛亚人蓝",
    "super saiyan rose": "超级赛亚人桃红",
}


def translate_form_text(text: str) -> str | None:
    key = normalize(text).lower()
    if key in FORM_MAP:
        return FORM_MAP[key]
    translated = translate_name(normalize(text).title())
    if translated and not unresolved_ascii(translated):
        return translated
    return None


def read_tsv(path: Path, skip_blocks: tuple[tuple[str, str], ...] = ()) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    filtered: list[str] = []
    skip_until: str | None = None
    for line in lines:
        stripped = line.strip()
        if skip_until is not None:
            if stripped == skip_until:
                skip_until = None
            continue
        matched_block = False
        for begin, end in skip_blocks:
            if stripped == begin:
                skip_until = end
                matched_block = True
                break
        if not matched_block:
            filtered.append(line)
    return list(csv.reader(filtered, delimiter="\t"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


DERIVED_TBL_NAME_MAP: dict[str, str] = {}


def clean_tbl_name_noise(text: str) -> str:
    text = normalize(text)
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"^[0-9A-Z]*\s*(?=\[?(?:Recipe|Probability Recipe)\])", "", text)
        text = re.sub(r"^\(+\s*(?=\[?(?:Recipe|Probability Recipe)\])", "", text)
        text = re.sub(r"^([0-9])(?=Recipe\s+for\b)", "", text, flags=re.I)
        text = re.sub(r"^\(+\s*(?=Recipe\s+for\b)", "", text, flags=re.I)
    return text.strip()


def strip_recipe_source(text: str) -> tuple[str, str] | None:
    text = clean_tbl_name_noise(text)
    rules = (
        (r"\[Probability Recipe\]\s*(.+)", "概率"),
        (r"\[Recipe\]\s*(.+?)\s*\[Probability\]", "概率"),
        (r"\[Recipe\]\s*(.+)", ""),
        (r"Recipe\s+for\s+(.+)", ""),
        (r"Recipe\s+(.+)", ""),
        (r"(.+?)\s+premium\s+recipe\.?", "高级"),
        (r"(.+?)\s+Rare\s+recipe\.?", "稀有"),
        (r"(.+?)\s+recipe\.?", ""),
        (r"(.+?)\s+\(Recipe\)", ""),
    )
    for pattern, prefix in rules:
        match = re.fullmatch(pattern, text, re.I)
        if match:
            return match.group(1).strip(), prefix
    return None


def load_derived_tbl_name_map(root: Path | None = None) -> dict[str, str]:
    global DERIVED_TBL_NAME_MAP
    if DERIVED_TBL_NAME_MAP:
        return DERIVED_TBL_NAME_MAP
    if root is None:
        root = Path(__file__).resolve().parent
    path = root / "tbl_overrides.tsv"
    if not path.exists():
        return DERIVED_TBL_NAME_MAP
    for row in read_tsv(path, ((AUTO_TBL_BEGIN, AUTO_TBL_END),)):
        if len(row) < 4 or not row[2] or not row[3] or row[0].lstrip().startswith("#"):
            continue
        source = clean_tbl_name_noise(row[2])
        target = row[3].strip()
        if not source or unresolved_ascii(target):
            continue
        DERIVED_TBL_NAME_MAP.setdefault(source, target)
        recipe = strip_recipe_source(source)
        if recipe and target.endswith("配方"):
            base_source, _ = recipe
            base_target = target[: -len("配方")]
            if base_target:
                DERIVED_TBL_NAME_MAP.setdefault(clean_tbl_name_noise(base_source), base_target)
        if source.endswith(" (Recipe)") and target.endswith("(配方)"):
            DERIVED_TBL_NAME_MAP.setdefault(source[: -len(" (Recipe)")], target[: -len("(配方)")])
    return DERIVED_TBL_NAME_MAP


def unresolved_ascii(text: str) -> list[str]:
    return [token for token in re.findall(r"[A-Za-z]+", text) if token not in ALLOWED_ASCII]


CLASS_TERM_REPLACEMENTS: dict[str, str] = {
    "(Martial)": "(武道家)",
    "(Spiritualist)": "(气功师)",
    "(Warrior)": "(那美克战士)",
    "(Dragon)": "(龙族)",
    "(Might)": "(大魔人)",
    "(Wonder)": "(意魔人)",
    "(Namek Warrior)": "(那美克战士)",
    "(Dragon Clan)": "(那美克龙族)",
    "(Might Majin)": "(大魔人)",
    "(Wonder Majin)": "(意魔人)",
    "[Martial Artist]": "[武道家]",
    "[Spiritualist]": "[气功师]",
    "[Dragon Clan]": "[那美克龙族]",
    "[Might Majin]": "[大魔人]",
    "[Wonder Majin]": "[意魔人]",
    "[Namek Warrior]": "[那美克战士]",
    "Martial Artists": "武道家",
    "Martial Artist": "武道家",
    "Spiritualists": "气功师",
    "Spiritualist": "气功师",
    "Namek Warrior": "那美克战士",
    "Dragon Clan": "那美克龙族",
    "Might Majin": "大魔人",
    "Wonder Majin": "意魔人",
}


def translate_class_label(text: str) -> str | None:
    return CLASS_NAME_MAP.get(normalize(text))


def translate_class_terms_fallback(text: str) -> str | None:
    output = text
    for source, target in sorted(CLASS_TERM_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        output = output.replace(source, target)
    return output if output != text else None


def visible_class_candidate_text(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 96 or "\n" in text or "\r" in text:
        return False
    if text.startswith("((") or text[0].islower():
        return False
    return True



def translate_name(text: str, depth: int = 0) -> str | None:
    text = clean_tbl_name_noise(text)
    if not text:
        return None
    if depth == 0:
        derived = load_derived_tbl_name_map().get(text)
        if derived:
            return derived
    if text in CLASS_NAME_MAP and text != "Dragon":
        return CLASS_NAME_MAP[text]
    if text in WORD_MAP:
        return WORD_MAP[text]
    if text in PHRASE_MAP:
        return PHRASE_MAP[text]

    recipe = strip_recipe_source(text)
    if recipe and depth < 4:
        base_source, prefix = recipe
        item = load_derived_tbl_name_map().get(clean_tbl_name_noise(base_source)) or translate_name(base_source, depth + 1)
        if item:
            return f"{prefix}{item}配方"

    match = re.fullmatch(r"(.+?)(!+)", text)
    if match and depth < 4:
        base = translate_name(match.group(1).strip(), depth + 1)
        if base:
            return f"{base}{match.group(2)}"

    for source, target in sorted(PHRASE_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if text.startswith(f"{source} ") and depth < 4:
            rest = translate_name(text[len(source) :].strip(), depth + 1)
            if rest:
                return f"{target}{rest}"

    for source, target in sorted(CLASS_NAME_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if source != "Dragon" and text.startswith(f"{source} ") and depth < 4:
            rest = translate_name(text[len(source) :].strip(), depth + 1)
            if rest:
                return f"{target}{rest}"

    match = re.fullmatch(r"(.+)\(([^()]*)\)", text)
    if match and depth < 4:
        base = translate_name(match.group(1).strip(), depth + 1)
        suffix = translate_class_label(match.group(2)) or translate_name(match.group(2).strip(), depth + 1)
        if base and suffix:
            return f"{base}({suffix})"

    match = re.fullmatch(r"(.+)\[([^\[\]]*)\]", text)
    if match and depth < 4:
        base = translate_name(match.group(1).strip(), depth + 1)
        suffix = translate_class_label(match.group(2)) or translate_name(match.group(2).strip(), depth + 1)
        if base and suffix:
            return f"{base}[{suffix}]"

    match = re.fullmatch(r"\(([^()]*)\)\s*(.+)", text)
    if match and depth < 4:
        prefix = translate_class_label(match.group(1)) or translate_name(match.group(1), depth + 1)
        rest = translate_name(match.group(2), depth + 1)
        if prefix and rest:
            return f"({prefix}){rest}"

    match = re.fullmatch(r"(Potion|Capsule)\s+(.+)", text, re.I)
    if match and depth < 4:
        item = translate_name(match.group(2), depth + 1)
        container = translate_name(match.group(1), depth + 1)
        if item and container:
            return f"{item}{container}"

    match = re.fullmatch(r"(.+)\s+Type\s+([A-Z])", text, re.I)
    if match and depth < 4:
        base = translate_name(match.group(1), depth + 1)
        if base:
            return f"{base}{match.group(2)}型"

    match = re.fullmatch(r"Type[- ]?([A-Z])", text, re.I)
    if match:
        return f"{match.group(1)}型"

    match = re.fullmatch(r"(.+)\s+Lv\s*([0-9]+)", text, re.I)
    if match and depth < 4:
        base = translate_name(match.group(1), depth + 1)
        if base:
            return f"{base}Lv{match.group(2)}"

    match = re.fullmatch(r"(.+)\s+(\d+)", text)
    if match and depth < 4:
        base = translate_name(match.group(1), depth + 1)
        if base:
            return f"{base}{match.group(2)}"

    match = re.fullmatch(r"(.+)\s+of\s+(.+)", text, re.I)
    if match and depth < 4:
        left = translate_name(match.group(1), depth + 1)
        right = translate_name(match.group(2), depth + 1)
        if left and right:
            return f"{right}的{left}"

    match = re.fullmatch(r"(.+)'s\s+(.+)", text)
    if match and depth < 4:
        owner = translate_name(match.group(1), depth + 1)
        item = translate_name(match.group(2), depth + 1)
        if owner and item:
            return f"{owner}的{item}"

    for sep, out_sep in ((",", "、"), ("/", "/")):
        if sep in text and depth < 4:
            parts = [translate_name(part.strip(), depth + 1) for part in text.split(sep)]
            if all(parts):
                return out_sep.join(part for part in parts if part)

    working = text
    phrase_values: list[str] = []
    for source, target in sorted(PHRASE_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])")
        if pattern.search(working):
            working = pattern.sub(f"{{{len(phrase_values)}}}", working)
            phrase_values.append(target)

    output: list[str] = []
    for part in re.split(r"(\{\d+\}|[()\- ]+)", working):
        if not part:
            continue
        if re.fullmatch(r"\{\d+\}", part):
            output.append(phrase_values[int(part[1:-1])])
        elif re.fullmatch(r"[()\- ]+", part):
            output.append(part.replace(" ", ""))
        elif part in WORD_MAP:
            output.append(WORD_MAP[part])
        elif part in ALLOWED_ASCII or re.fullmatch(r"[A-Z]{1,3}\d*|\d+", part):
            output.append(part)
        else:
            return None
    return "".join(output).strip() or None


def known_override_keys(
    path: Path, key_columns: tuple[int, ...], skip_blocks: tuple[tuple[str, str], ...] = ()
) -> set[tuple[str, ...]]:
    keys: set[tuple[str, ...]] = set()
    for row in read_tsv(path, skip_blocks):
        if not row or row[0].lstrip().startswith("#") or row[0].lower() == "file":
            continue
        if len(row) <= max(key_columns):
            continue
        keys.add(tuple(row[index] for index in key_columns))
    return keys


def known_tbl_wildcard_sources(path: Path, skip_blocks: tuple[tuple[str, str], ...] = ()) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in read_tsv(path, skip_blocks):
        if not row or row[0].lstrip().startswith("#") or row[0].lower() == "file":
            continue
        if len(row) < 4:
            continue
        if row[1].strip() in tbl.ALL_OFFSETS:
            keys.add((row[0], row[2]))
    return keys


def tbl_field_mode(file_name: str, offset_text: str, source_text: str, cache: dict[str, bytes]) -> str | None:
    try:
        offset = int(offset_text, 16)
    except ValueError:
        return None
    data = cache[file_name]
    utf16_source = source_text.encode("utf-16le")
    if offset + len(utf16_source) <= len(data) and data[offset : offset + len(utf16_source)] == utf16_source:
        return "utf16"
    ascii_source = source_text.encode("ascii", errors="ignore")
    if source_text.isascii() and offset + len(ascii_source) <= len(data) and data[offset : offset + len(ascii_source)] == ascii_source:
        return "ascii"
    return None


def translation_fits(source_text: str, translation: str, mode: str) -> bool:
    if mode == "utf16":
        return len(translation.encode("utf-16le")) <= len(source_text.encode("utf-16le"))
    if mode == "ascii":
        return len(translation.encode("gbk")) <= len(source_text.encode("ascii"))
    return False


def generate_tbl_rows(root: Path) -> list[list[str]]:
    overrides_path = root / "tbl_overrides.tsv"
    skip_blocks = ((AUTO_TBL_BEGIN, AUTO_TBL_END),)
    existing = known_override_keys(overrides_path, (0, 1, 2), skip_blocks)
    wildcard_sources = known_tbl_wildcard_sources(overrides_path, skip_blocks)
    data_cache = {file_name: tbl.tbl_path(root / "src_file", file_name).read_bytes() for file_name in tbl.TBL_FILES}
    internal_re = re.compile(
        r"(Bip|MobGroup|Spawn|Tutorial|Animation|Direction|Cancel|Loop|Effect|Count|Constant|"
        r"Battle\d+|Stage\d+|RemoteMerchant|BuySell|MaterialDecomposition|Overweight|"
        r"^(MQ|LQ|TMQ|UD|BID|HLS)_|^I_|^A_|^S_|^N_|^T_|^Q_|^E_|^R_|^C_|^D_)",
        re.I,
    )
    bad_word_re = re.compile(
        r"\b(increase|decrease|within|around|success|failed|warning|requires|mail|delete|receive)\b",
        re.I,
    )
    rows: list[list[str]] = []
    for row in read_tsv(root / "tbl_candidates.tsv"):
        if len(row) < 4 or row[0] == "file" or tuple(row[:3]) in existing:
            continue
        file_name, offset_text, source_text = row[:3]
        if file_name not in tbl.TBL_FILES:
            continue
        if (file_name, source_text) in wildcard_sources:
            continue
        try:
            offset = int(offset_text, 16)
        except ValueError:
            continue
        if "Recipe" in source_text or "Black Dragon" in source_text:
            continue
        if CLASS_SOURCE_RE.search(source_text) and visible_class_candidate_text(source_text):
            translation = translate_name(source_text)
            if not translation or unresolved_ascii(translation):
                translation = translate_class_terms_fallback(source_text)
            mode = tbl_field_mode(file_name, offset_text, source_text, data_cache)
            if translation and mode and translation_fits(source_text, translation, mode):
                rows.append([file_name, offset_text, source_text, translation])
                existing.add(tuple(row[:3]))
            continue
        if offset < 0x01000000 or len(source_text) > 48 or len(source_text) < 3:
            continue
        if internal_re.search(source_text) or bad_word_re.search(source_text):
            continue
        if re.search(r"[a-z][A-Z]", source_text):
            continue
        if any(char in source_text for char in "[]{}%=<>;:?"):
            continue
        if not re.fullmatch(r"[A-Za-z0-9(][A-Za-z0-9 '\-(),./!]*", source_text):
            continue
        translation = translate_name(source_text)
        if not translation or unresolved_ascii(translation):
            continue
        mode = tbl_field_mode(file_name, offset_text, source_text, data_cache)
        if not mode or not translation_fits(source_text, translation, mode):
            continue
        rows.append([file_name, offset_text, source_text, translation])
        existing.add(tuple(row[:3]))
    return rows


def translate_key_placeholder(item_id: str) -> str | None:
    cleaned = item_id
    for prefix in ("DST_", "GAME_", "SYSTEMMSG_"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    tokens = [token for token in cleaned.split("_") if token and not token.isdigit()]
    translated = [KEY_TOKEN_MAP.get(token) for token in tokens]
    if not translated or any(part is None for part in translated):
        return None
    result = "".join(part for part in translated if part)
    return result if result else None


def translate_untranslated(row: list[str]) -> str | None:
    if len(row) < 3:
        return None
    file_name, item_id, source_text = row[:3]
    source_text = source_text.strip()
    if not source_text:
        return None
    if file_name == "table_quest_text_data.rdf":
        return None
    if source_text in UI_EXACT:
        return UI_EXACT[source_text]
    match = re.fullmatch(r"Can't use skill while (.+)\.", source_text, re.I)
    if match:
        form = translate_form_text(match.group(1))
        if form:
            return f"不能在{form}形态下使用技能。"
    if source_text == "Kaioken Boost is not available in this form.":
        return "界王拳强化在此形态下不可用。"
    if source_text == "Kaioken Boost requires aura to be active.":
        return "界王拳强化需要气场处于激活状态。"
    if source_text == "Failed to use guard item on mascot.":
        return "未能对吉祥物使用守护道具。"
    if source_text.startswith("[") or '"' in source_text:
        return None
    if re.fullmatch(r"(CNTEST|DOGIPROBE)(?:_[A-Z]+)?_\d+", source_text):
        return translate_key_placeholder(item_id)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 '\-(),./]*", source_text) and len(source_text) <= 48:
        translated = translate_name(source_text)
        if translated and not unresolved_ascii(translated):
            return translated
    return None


def generate_taiwan_rows(root: Path) -> list[list[str]]:
    existing = known_override_keys(root / "overrides.tsv", (0, 1), ((AUTO_TAIWAN_BEGIN, AUTO_TAIWAN_END),))
    rows: list[list[str]] = []
    for row in read_tsv(root / "untranslated.tsv"):
        if len(row) < 3 or row[0] == "file" or (row[0], row[1]) in existing:
            continue
        translation = translate_untranslated(row)
        if not translation or translation == row[2]:
            continue
        try:
            translation.encode("gbk")
        except UnicodeEncodeError:
            continue
        rows.append([row[0], row[1], row[2], translation])
        existing.add((row[0], row[1]))
    return rows


def replace_block(path: Path, begin: str, end: str, rows: list[list[str]]) -> None:
    original = path.read_text(encoding="utf-8-sig").splitlines()
    filtered: list[str] = []
    skipping = False
    for line in original:
        if line.strip() == begin:
            skipping = True
            continue
        if line.strip() == end:
            skipping = False
            continue
        if not skipping:
            filtered.append(line)
    if rows:
        if filtered and filtered[-1].strip():
            filtered.append("")
        filtered.append(begin)
        filtered.extend("\t".join(row) for row in rows)
        filtered.append(end)
    path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Generate conservative auto-translated override blocks for the refreshed source snapshot.")
    parser.add_argument("--apply", action="store_true", help="Write generated blocks to tbl_overrides.tsv and overrides.tsv.")
    parser.add_argument("--target", choices=("all", "tbl", "taiwan"), default="all", help="Limit --apply to one override block.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    tbl_rows = generate_tbl_rows(root)
    taiwan_rows = generate_taiwan_rows(root)
    print(f"Generated TBL visible-name rows: {len(tbl_rows)}")
    print(f"Generated Taiwan/RDF safe untranslated rows: {len(taiwan_rows)}")
    for label, rows in (("TBL", tbl_rows[:10]), ("Taiwan", taiwan_rows[:10])):
        print(f"{label} sample:")
        for row in rows:
            print("\t".join(row))
    if args.apply:
        if args.target in ("all", "tbl"):
            replace_block(root / "tbl_overrides.tsv", AUTO_TBL_BEGIN, AUTO_TBL_END, tbl_rows)
        if args.target in ("all", "taiwan"):
            replace_block(root / "overrides.tsv", AUTO_TAIWAN_BEGIN, AUTO_TAIWAN_END, taiwan_rows)
        print("Applied generated override blocks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
