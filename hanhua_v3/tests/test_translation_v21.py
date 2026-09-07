from __future__ import annotations

from hanhua_v3.runtime.translation_v21 import TranslationMemory, classify_text, make_candidate, validate_translation


def test_classify_common_resource_text():
    assert classify_text("Goku", "tbl2.pak", "character_name") == "name"
    assert classify_text("Confirm", "ui_menu.xml", "button_confirm") == "ui"
    assert classify_text("Potion", "item.dat", "item_100") == "item"


def test_placeholder_validation():
    assert validate_translation("Queue: %u / %u players", "隊列：%u / %u 名玩家")[0]
    assert not validate_translation("Queue: %u / %u players", "隊列：%u 名玩家")[0]


def test_memory_exact_lookup():
    memory = TranslationMemory()
    memory.by_exact[("tbl2.pak", "256001", "Consent")] = "同意"
    candidate = make_candidate("Consent", file_name="tbl2.pak", item_id="256001", memory=memory)
    assert candidate.translation == "同意"
    assert candidate.method == "memory"
    assert candidate.valid
