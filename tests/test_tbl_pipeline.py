from __future__ import annotations

import pytest

from hanhua_v3.runtime.resource_validator import ValidationError, validate_build
from hanhua_v3.runtime.resource_writer import QueueRow, _fixed_generic_pak_replacement
from hanhua_v3.runtime.tbl_utf16_patch import PatchError, TblOverride, patch_tbl_bytes


def make_tbl2(item_id: int, text: str) -> bytes:
    encoded = text.encode("utf-16le")
    return item_id.to_bytes(4, "little") + b"\x00" + len(text).to_bytes(2, "little") + encoded


def test_tbl2_stable_id_patches_without_changing_field_width() -> None:
    original = make_tbl2(256001, "Hello")
    patched, stats = patch_tbl_bytes(
        original,
        [TblOverride("tbl2.pak", None, "Hello", "嗨", 256001)],
    )

    assert stats["changed"] == 1
    assert len(patched) == len(original)
    assert patched[0:4] == (256001).to_bytes(4, "little")
    assert patched[7:17] == "嗨".encode("utf-16le") + b"\x00" * 8


def test_tbl2_translation_that_grows_the_fixed_field_is_rejected() -> None:
    with pytest.raises(PatchError, match="too long"):
        patch_tbl_bytes(
            make_tbl2(256001, "Hi"),
            [TblOverride("tbl2.pak", None, "Hi", "這個翻譯太長", 256001)],
        )


def test_tbl2_validator_detects_corrupted_output(tmp_path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    source_tbl2 = source / "tbl2.pak"
    output_tbl2 = output / "tbl2.pak"
    source_tbl2.write_bytes(make_tbl2(1234, "Hello"))
    output_tbl2.write_bytes(make_tbl2(1234, "Oops!"))

    row = QueueRow("tbl2.pak", "id:1234", "Hello", "嗨", "utf-16le", "tbl2_record")
    with pytest.raises(ValidationError, match="tbl2 output record"):
        validate_build(source, output, [row])


def test_generic_utf16_pak_replacement_preserves_width() -> None:
    old, new = _fixed_generic_pak_replacement("Hello", "嗨", "utf-16le")
    assert len(old) == len(new)
    assert new == "嗨".encode("utf-16le") + b"\x00" * 8
