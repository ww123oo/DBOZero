from __future__ import annotations

"""DBO automatic translation engine v2.

Goals:
- exact curated translations first;
- Taiwan Traditional Chinese normalization;
- protect printf placeholders and DBO markup;
- translate proper names and domain phrases before generic words;
- refuse to invent a translation when confidence is too low;
- expose a small API so CLI/batch translation can adopt it incrementally.

This is intentionally a deterministic *translation candidate* engine. It does
not pretend that word-by-word substitution is a high-quality human translation.
Unknown long sentences are returned unchanged with a low-confidence result.
"""

import re
from dataclasses import dataclass
from functools import lru_cache

try:
    from ..glossary import CURATED_TRANSLATIONS
    from .auto_translate_new_source import WORD_MAP, PHRASE_MAP
except ImportError:  # direct script execution
    from glossary import CURATED_TRANSLATIONS
    from auto_translate_new_source import WORD_MAP, PHRASE_MAP

__all__ = ["TranslationResult", "translate", "translate_name", "normalize_taiwan"]

# Taiwan terminology should be applied after the base translation so old
# simplified glossary entries can still be reused safely.
TAIWAN_PHRASES = {
    "服务器": "伺服器",
    "服务器列表": "伺服器列表",
    "账号": "帳號",
    "帐号": "帳號",
    "帐户": "帳戶",
    "账户": "帳戶",
    "登录": "登入",
    "登陆": "登入",
    "注册": "註冊",
    "网络": "網路",
    "程序": "程式",
    "信息": "資訊",
    "消息": "訊息",
    "设置": "設定",
    "默认": "預設",
    "自动": "自動",
    "删除": "刪除",
    "复活": "復活",
    "伤害": "傷害",
    "攻击": "攻擊",
    "防御": "防禦",
    "经验": "經驗",
    "经验值": "經驗值",
    "等级": "等級",
    "技能": "技能",
    "装备": "裝備",
    "强化": "強化",
    "属性": "屬性",
    "物理": "物理",
    "能量": "能量",
    "气功": "氣功",
    "队伍": "隊伍",
    "组队": "組隊",
    "玩家": "玩家",
    "频道": "頻道",
    "区域": "區域",
    "地图": "地圖",
    "任务": "任務",
    "奖励": "獎勵",
    "道具": "道具",
    "药水": "藥水",
    "药品": "藥品",
    "背包": "背包",
    "仓库": "倉庫",
    "邮件": "郵件",
    "拍卖行": "拍賣行",
    "冷却": "冷卻",
    "恢复": "恢復",
    "飞行": "飛行",
    "战斗": "戰鬥",
    "首领": "首領",
    "副本": "副本",
    "活动": "活動",
    "购买": "購買",
    "出售": "出售",
    "取消": "取消",
    "确认": "確認",
    "关闭": "關閉",
    "开启": "開啟",
    "选择": "選擇",
    "开始": "開始",
    "结束": "結束",
    "继续": "繼續",
    "请输入": "請輸入",
    "无法": "無法",
    "不能": "不能",
    "已经": "已經",
    "正在": "正在",
    "剩余": "剩餘",
    "时间": "時間",
    "分钟": "分鐘",
    "小时": "小時",
    "天": "天",
    "金币": "金幣",
    "硬币": "硬幣",
    "幸运": "幸運",
    "暴击": "暴擊",
    "击倒": "擊倒",
    "麻痹": "麻痺",
    "恐惧": "恐懼",
    "混乱": "混亂",
    "防具": "防具",
    "武器": "武器",
    "裤子": "褲子",
    "头盔": "頭盔",
    "项链": "項鍊",
    "戒指": "戒指",
    "耳环": "耳環",
    "翅膀": "翅膀",
    "胶囊": "膠囊",
    "卷轴": "卷軸",
    "森林": "森林",
    "东": "東",
    "西": "西",
    "北": "北",
    "南": "南",
    "龙珠": "龍珠",
    "神龙": "神龍",
    "神龙祭坛": "神龍祭壇",
    "索尼": "索尼",
}

# Proper-name corrections commonly encountered in DBO resources. These are
# deliberately explicit rather than inferred from arbitrary English words.
NAME_MAP = {
    "Goku": "悟空",
    "Son Goku": "孫悟空",
    "Gohan": "悟飯",
    "Son Gohan": "孫悟飯",
    "Goten": "悟天",
    "Vegeta": "達爾",
    "Trunks": "特南克斯",
    "Piccolo": "比克",
    "Krillin": "克林",
    "Bulma": "布瑪",
    "Frieza": "弗力札",
    "Cell": "賽魯",
    "Buu": "普烏",
    "Majin": "魔人",
    "Namek": "那美克",
    "Namekian": "那美克星人",
    "Korin": "卡林",
    "Porunga": "波倫加",
    "Shenron": "神龍",
    "Ginyu": "基紐",
    "Bardock": "巴達克",
    "Broly": "布羅利",
    "Gogeta": "悟吉塔",
    "Gotenks": "悟天克斯",
    "Beerus": "比魯斯",
    "Whis": "維斯",
    "Jiren": "吉連",
    "Hit": "希特",
}

# Protect tokens that must survive byte-for-byte in resource files.
PROTECTED_RE = re.compile(
    r"(?:%\d*\$?[+-]?(?:\d+)?(?:\.\d+)?[diouxXeEfFgGsc])|"
    r"(?:%[uUxXdi fsg])|"
    r"(?:\\n|\\r|\\t)|"
    r"(?:\[[^\]]+\])|"
    r"(?:<[^>]+>)"
)

# Basic ASCII identifier detection: internal keys should not be translated.
INTERNAL_RE = re.compile(r"^(?:[A-Z]{2,}_[A-Z0-9_.-]+|[A-Z0-9_.-]{2,})$")


def _protect(text: str) -> tuple[str, dict[str, str]]:
    saved: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        token = f"\ue000{len(saved)}\ue001"
        saved[token] = match.group(0)
        return token

    return PROTECTED_RE.sub(repl, text), saved


def _restore(text: str, saved: dict[str, str]) -> str:
    for token, value in saved.items():
        text = text.replace(token, value)
    return text


def normalize_taiwan(text: str) -> str:
    """Normalize known Simplified-Chinese output to Taiwan Traditional usage."""
    # Longest-first prevents partial replacements such as 服务器 -> 伺服器
    # from interfering with longer domain phrases.
    for src in sorted(TAIWAN_PHRASES, key=len, reverse=True):
        text = text.replace(src, TAIWAN_PHRASES[src])
    # Optional high-quality converter when the user's environment provides it.
    # The explicit map above remains the deterministic baseline.
    try:
        from opencc import OpenCC  # type: ignore
        text = OpenCC("s2twp").convert(text)
    except Exception:
        pass
    return text


def _curated(text: str) -> str | None:
    if text in CURATED_TRANSLATIONS:
        return CURATED_TRANSLATIONS[text]
    if text in PHRASE_MAP:
        return PHRASE_MAP[text]
    if text in NAME_MAP:
        return NAME_MAP[text]
    return None


@lru_cache(maxsize=8192)
def translate(text: str) -> "TranslationResult":
    source = text.strip()
    if not source:
        return TranslationResult(text, text, "empty", 0.0, False)

    exact = _curated(source)
    if exact is not None:
        return TranslationResult(text, normalize_taiwan(exact), "exact", 1.0, True)

    if INTERNAL_RE.fullmatch(source) and not any(c.islower() for c in source):
        return TranslationResult(text, text, "identifier", 1.0, False)

    protected, saved = _protect(source)
    translated = protected
    score = 0.0
    changed = False

    # Long phrases first. Phrase maps are trusted more than individual words.
    phrase_items = sorted(PHRASE_MAP.items(), key=lambda item: len(item[0]), reverse=True)
    for src, dst in phrase_items:
        if src and src in translated:
            translated = translated.replace(src, dst)
            score += min(0.45, 0.08 + len(src) / 200)
            changed = True

    # Explicit proper names before generic WORD_MAP.
    for src, dst in sorted(NAME_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(r"(?<![A-Za-z])" + re.escape(src) + r"(?![A-Za-z])", translated):
            translated = re.sub(r"(?<![A-Za-z])" + re.escape(src) + r"(?![A-Za-z])", dst, translated)
            score += 0.25
            changed = True

    # Word-level replacement only on word boundaries; this avoids mangling
    # identifiers such as DragonBallOnline or numeric IDs.
    for src, dst in sorted(WORD_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if len(src) < 2 or not re.search(r"[A-Za-z]", src):
            continue
        pattern = r"(?<![A-Za-z])" + re.escape(src) + r"(?![A-Za-z])"
        new_value, count = re.subn(pattern, dst, translated, flags=re.IGNORECASE if src.isalpha() else 0)
        if count:
            translated = new_value
            score += min(0.2, 0.02 * count)
            changed = True

    translated = normalize_taiwan(_restore(translated, saved))

    # If we changed at least one trusted token, return a candidate. Otherwise
    # leave the source untouched: guessing is worse than queueing for review.
    if changed:
        confidence = min(0.94, 0.45 + score)
        return TranslationResult(text, translated, "composed", confidence, True)
    return TranslationResult(text, text, "unknown", 0.0, False)


@dataclass(frozen=True)
class TranslationResult:
    source: str
    translation: str
    method: str
    confidence: float
    changed: bool


def translate_name(text: str) -> str:
    result = translate(text)
    return result.translation if result.changed else text
