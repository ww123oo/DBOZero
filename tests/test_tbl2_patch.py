from hanhua_v3.runtime.tbl_utf16_patch import TblOverride, patch_tbl_bytes, tbl2_record_at


def test_tbl2_observed_record_layout():
    # Header + id + type + little-endian UTF-16 code-unit length + UTF-16LE text.
    data = b"\x00" * 8 + (1001).to_bytes(4, "little") + b"\x00" + (8).to_bytes(2, "little") + "Negative".encode("utf-16le")
    assert tbl2_record_at(data, 15, "Negative")


def test_tbl2_rejects_wrong_offset():
    data = b"\x00" * 8 + (1001).to_bytes(4, "little") + b"\x00" + (8).to_bytes(2, "little") + "Negative".encode("utf-16le")
    assert not tbl2_record_at(data, 14, "Negative")


def test_tbl2_can_patch_by_stable_id_without_using_offset():
    prefix = b"\x00" * 8
    record = (1001).to_bytes(4, "little") + b"\x00" + (8).to_bytes(2, "little") + "Negative".encode("utf-16le")
    data = prefix + record + b"\x7f" * 16
    patched, stats = patch_tbl_bytes(
        data,
        [TblOverride("tbl2.pak", None, "Negative", "否定", 1001)],
    )
    assert stats["changed"] == 1
    assert stats["missing"] == 0
    assert len(patched) == len(data)
    assert patched[8:12] == (1001).to_bytes(4, "little")
    assert patched[15:31] == "否定".encode("utf-16le") + b"\x00" * 12
