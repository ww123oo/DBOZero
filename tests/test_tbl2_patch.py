from hanhua_v3.runtime.tbl_utf16_patch import tbl2_record_at


def test_tbl2_observed_record_layout():
    # Header + id + type + little-endian UTF-16 code-unit length + UTF-16LE text.
    data = b"\x00" * 8 + (1001).to_bytes(4, "little") + b"\x00" + (8).to_bytes(2, "little") + "Negative".encode("utf-16le")
    assert tbl2_record_at(data, 15, "Negative")


def test_tbl2_rejects_wrong_offset():
    data = b"\x00" * 8 + (1001).to_bytes(4, "little") + b"\x00" + (8).to_bytes(2, "little") + "Negative".encode("utf-16le")
    assert not tbl2_record_at(data, 14, "Negative")
