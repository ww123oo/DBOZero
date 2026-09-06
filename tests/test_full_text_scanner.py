from pathlib import Path

from hanhua_v3.runtime.full_text_scanner import scan_file


def test_lang0_scan_exposes_key_as_id(tmp_path: Path) -> None:
    path = tmp_path / "lang0.pak"
    path.write_bytes(b'DST_HELLO = "Hello"\nDST_GOODBYE = "Bye"\n')
    hits = scan_file(path)
    lang_hits = [hit for hit in hits if hit.kind == "lang0_entry"]
    assert [(hit.id, hit.text) for hit in lang_hits] == [("DST_HELLO", "Hello"), ("DST_GOODBYE", "Bye")]


def test_bin_is_not_a_scan_target(tmp_path: Path) -> None:
    (tmp_path / "ignored.bin").write_bytes(b"Hello")
    assert list(__import__("hanhua_v3.runtime.full_text_scanner", fromlist=["files_to_scan"]).files_to_scan(tmp_path)) == []
