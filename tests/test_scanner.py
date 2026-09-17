from __future__ import annotations

from pathlib import Path

from hanhua_v3.runtime.full_text_scanner import scan_file, scan_tbl2_structured


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


def test_tbl2_generic_utf16_scan_does_not_duplicate_structured_record(tmp_path: Path) -> None:
    path = tmp_path / "tbl2.pak"
    path.write_bytes(make_tbl2(1234, "Hello") + b"\x00" * 8)

    hits = scan_file(path)
    structured = [hit for hit in hits if hit.kind == "tbl2_record"]
    duplicate_generic = [hit for hit in hits if hit.kind == "utf16" and hit.text == "Hello"]
    assert len(structured) == 1
    assert duplicate_generic == []


def test_xml_and_rdf_text_and_attribute_values_are_discoverable(tmp_path: Path) -> None:
    path = tmp_path / "table_text.rdf"
    path.write_text(
        '<root title="Dragon Radar"><entry>Hello World</entry></root>',
        encoding="utf-8",
    )

    hits = scan_file(path)
    texts = {hit.text for hit in hits}
    assert "Dragon Radar" in texts
    assert "Hello World" in texts
    assert any(hit.kind == "xml_attribute" for hit in hits)
    assert any(hit.kind == "xml_text" for hit in hits)
