from __future__ import annotations

from hanhua_v3.runtime.resource_writer import QueueRow, _detect_lang0_encoding
from hanhua_v3.runtime import lang0_gbk_patch


def test_detect_lang0_utf8() -> None:
    data = 'ACCOUNT="Account"\n'.encode("utf-8")
    assert _detect_lang0_encoding(data) == "utf-8"


def test_lang0_utf8_fixed_field_preserves_size() -> None:
    original = 'ACCOUNT="Account"\nOTHER="Keep"\n'.encode("utf-8")
    patched, stats = lang0_gbk_patch.patch_lang0_bytes(
        original,
        [("ACCOUNT", "帳號")],
        encoding="utf-8",
    )

    assert stats["changed"] == 1
    assert len(patched) == len(original)
    assert b'ACCOUNT="帳號"' in patched
    assert b'OTHER="Keep"' in patched


def test_queue_row_shape_is_writer_compatible() -> None:
    row = QueueRow("pack/lang0.pak", "ACCOUNT", "Account", "帳號", "utf-8", "lang0_entry")
    assert row.file.endswith("lang0.pak")
    assert row.locator == "ACCOUNT"
