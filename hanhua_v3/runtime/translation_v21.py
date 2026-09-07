from __future__ import annotations

"""Translation v2.1 helpers: classification, memory lookup and validation.

This module deliberately does not write game resources.  It turns scanned text
into safer translation candidates and leaves uncertain text for review.
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from .auto_translate_v2 import translate

__all__ = [
    "TranslationMemory",
    "TranslationCandidate",
    "classify_text",
    "make_candidate",
    "validate_translation",
]


@dataclass(frozen=True)
class TranslationCandidate:
    source: str
    translation: str
    category: str
    method: str
    confidence: float
    valid: bool
    reason: str = ""


class TranslationMemory:
    """Read legacy/daily TSV files without making them the source of truth."""

    def __init__(self) -> None:
        self.by_exact: dict[tuple[str, str, str], str] = {}
        self.by_file_hash: dict[tuple[str, str], str] = {}
        self.by_source: dict[str, set[str]] = {}

    @staticmethod
    def _norm_file(value: str) -> str:
        return value.replace("\\", "/").strip().lower()

    def load(self, path: str | Path) -> int:
        loaded = 0
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                source = (row.get("source_text") or row.get("source") or "").strip()
                zh = (row.get("zh_cn") or row.get("translation") or "").strip()
                if not source or not zh or source == zh:
                    continue
                file_name = self._norm_file(row.get("file") or row.get("File") or "")
                source_hash = (row.get("source_hash") or "").strip()
                key = (file_name, (row.get("id") or "").strip(), source)
                self.by_exact[key] = zh
                self.by_source.setdefault(source, set()).add(zh)
                if file_name and source_hash:
                    self.by_file_hash[(file_name, source_hash)] = zh
                loaded += 1
        return loaded

    def lookup(self, file_name: str, item_id: str, source: str, source_hash: str = "") -> str | None:
        file_name = self._norm_file(file_name)
        exact = self.by_exact.get((file_name, item_id.strip(), source.strip()))
        if exact:
            return exact
        if source_hash:
            value = self.by_file_hash.get((file_name, source_hash.strip()))
            if value:
                return value
        values = self.by_source.get(source.strip(), set())
        return next(iter(values)) if len(values) == 1 else None


# These patterns are intentionally conservative.  Unknown data is classified
# rather than translated aggressively.
NAME_HINT = re.compile(r"(?:npc|monster|mob|boss|character|name|title)", re.I)
ITEM_HINT = re.compile(r"(?:item|equip|weapon|armor|costume|capsule|recipe|potion|scroll)", re.I)
SKILL_HINT = re.compile(r"(?:skill|technique|attack|buff|debuff)", re.I)
MAP_HINT = re.compile(r"(?:map|zone|field|dungeon|area|world)", re.I)
UI_HINT = re.compile(r"(?:menu|button|dialog|window|confirm|cancel|setting|option|queue)", re.I)


def classify_text(source: str, file_name: str = "", item_id: str = "") -> str:
    """Return a translation class used for confidence/routing decisions."""
    text = source.strip()
    lower = f"{file_name} {item_id}".lower()
    if not text:
        return "empty"
    if re.fullmatch(r"[A-Z][A-Z0-9_.-]{1,}", text):
        return "identifier"
    if NAME_HINT.search(lower):
        return "name"
    if ITEM_HINT.search(lower):
        return "item"
    if SKILL_HINT.search(lower):
        return "skill"
    if MAP_HINT.search(lower):
        return "map"
    if UI_HINT.search(lower):
        return "ui"
    if len(text) <= 28 and not re.search(r"[.!?。！？]", text):
        return "label"
    return "sentence"


# Placeholders/tags that must survive unchanged.  We compare multisets rather
# than positions so a translator may legitimately reorder placeholders.
TOKEN_RE = re.compile(
    r"%\d*\$?[+-]?(?:\d+)?(?:\.\d+)?[diouxXeEfFgGscu]|"
    r"\\[nrt]|\[[^\]]+\]|<[^>]+>"
)


def _tokens(value: str) -> list[str]:
    return sorted(TOKEN_RE.findall(value))


def validate_translation(source: str, translation: str) -> tuple[bool, str]:
    if not translation.strip():
        return False, "empty translation"
    if _tokens(source) != _tokens(translation):
        return False, "placeholder/tag mismatch"
    # Never accept a candidate that silently deletes ordinary source content
    # when no translation mechanism actually changed it.
    if source.strip() == translation.strip():
        return False, "unchanged"
    return True, "ok"


def make_candidate(
    source: str,
    *,
    file_name: str = "",
    item_id: str = "",
    source_hash: str = "",
    memory: TranslationMemory | None = None,
) -> TranslationCandidate:
    category = classify_text(source, file_name, item_id)
    if category in {"empty", "identifier"}:
        return TranslationCandidate(source, source, category, "skip", 0.0, False, category)

    if memory is not None:
        remembered = memory.lookup(file_name, item_id, source, source_hash)
        if remembered:
            valid, reason = validate_translation(source, remembered)
            if valid:
                return TranslationCandidate(source, remembered, category, "memory", 0.97, True)

    result = translate(source)
    valid, reason = validate_translation(source, result.translation) if result.changed else (False, "no candidate")
    if not valid:
        return TranslationCandidate(source, source, category, result.method, 0.0, False, reason)

    # Names/labels can safely use curated short candidates more readily than
    # long prose.  Sentences remain reviewable unless confidence is high.
    confidence = result.confidence
    if category == "sentence":
        confidence = min(confidence, 0.82)
    elif category in {"name", "item", "skill", "map", "label"}:
        confidence = min(0.96, confidence + 0.03)
    return TranslationCandidate(source, result.translation, category, result.method, confidence, True)
