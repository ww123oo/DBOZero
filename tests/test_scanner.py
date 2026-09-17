from __future__ import annotations

from pathlib import Path

from hanhua_v3.runtime.full_text_scanner import scan_tbl2_structured


def make_tbl2(item_id: int, text: str) -> bytes:
    encoded = text.encode("utf-16le")
    return item_id.to_bytes(4, "little") + b"\x00" + len(text).to_bytes(2, "little") + encoded


def test_tbl2_scanner_keeps_stable_id(tmp_path: Path) -> None:
    path = tmp_path / "tbl2.pak"
    path.write_bytes(make_tbl2(987654, "Hello"))

    hits = scan_tbl2_structured(path)
    assert len(hits) == 1
    assert hits[0].id == "987654"
    assert hits[0].text == "Hello"
    assert hits[0].encoding == "utf-16le"
    assert hits[0].kind == "tbl2_record"
