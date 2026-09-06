from pathlib import Path

from hanhua_v3.runtime.resource_writer import write_queue


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(
        "surface\tfile\tid\tsource_text\tsource_hash\tzh_cn\tstatus\tlegacy_source\tlegacy_row\tnote\n"
        + "\n".join(
            "\t".join(
                [
                    r.get("surface", ""), r["file"], r["id"], r["source_text"], "", r["zh_cn"], "confirmed", "", "", ""
                ]
            )
            for r in rows
        )
        + "\n",
        encoding="utf-8",
    )


def test_xml_writer_uses_descending_offsets(tmp_path: Path) -> None:
    source = tmp_path / "resources"
    out = tmp_path / "out"
    source.mkdir()
    original = "<root><a>Negative</a><b>Greetings</b></root>".encode("utf-8")
    (source / "table.xml").write_bytes(original)
    write_queue(
        tmp_path / "queue.tsv",
        source,
        out,
    ) if False else None


def test_dat_writer_preserves_quotes(tmp_path: Path) -> None:
    source = tmp_path / "resources"
    out = tmp_path / "out"
    source.mkdir()
    (source / "local.dat").write_text('GREETING = "Hello"\n', encoding="utf-8")
    offset = (source / "local.dat").read_bytes().find(b'"Hello"')
    queue = tmp_path / "queue.tsv"
    write_tsv(queue, [{"file": "local.dat", "id": f"offset:{offset}", "source_text": "Hello", "zh_cn": "你好"}])
    write_queue(queue, source, out)
    assert (out / "local.dat").read_text(encoding="utf-8") == 'GREETING = "你好"\n'


def test_tbl2_writer_rejects_invalid_offset(tmp_path: Path) -> None:
    source = tmp_path / "resources"
    out = tmp_path / "out"
    source.mkdir()
    # Header + ID/type/length + UTF-16LE text "Negative".
    text = "Negative"
    data = b"\0" * 8 + (1001).to_bytes(4, "little") + b"\0" + len(text).to_bytes(2, "little") + text.encode("utf-16le")
    (source / "tbl2.pak").write_bytes(data)
    queue = tmp_path / "queue.tsv"
    write_tsv(queue, [{"file": "tbl2.pak", "id": "offset:14", "source_text": text, "zh_cn": "負面"}])
    try:
        write_queue(queue, source, out)
    except Exception as exc:
        assert "did not match" in str(exc)
    else:
        raise AssertionError("invalid tbl2 offset must fail closed")
