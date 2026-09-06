from pathlib import Path

from hanhua_v3.runtime.resource_writer import write_queue


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    lines = ["surface\tfile\tid\tsource_text\tsource_hash\tzh_cn\tstatus\tlegacy_source\tlegacy_row\tnote"]
    for row in rows:
        lines.append(
            "\t".join(
                [row.get("surface", ""), row["file"], row["id"], row["source_text"], "", row["zh_cn"], "confirmed", "", "", ""]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_xml_writer_uses_descending_offsets(tmp_path: Path) -> None:
    source = tmp_path / "resources"
    out = tmp_path / "out"
    source.mkdir()
    resource = source / "table.xml"
    resource.write_text("<root><a>Negative</a><b>Greetings</b></root>", encoding="utf-8")
    data = resource.read_bytes()
    first = data.find(b"Negative")
    second = data.find(b"Greetings")
    queue = tmp_path / "queue.tsv"
    write_tsv(
        queue,
        [
            {"file": "table.xml", "id": f"offset:{first}", "source_text": "Negative", "zh_cn": "負面"},
            {"file": "table.xml", "id": f"offset:{second}", "source_text": "Greetings", "zh_cn": "問候"},
        ],
    )
    write_queue(queue, source, out)
    assert (out / "table.xml").read_text(encoding="utf-8") == "<root><a>負面</a><b>問候</b></root>"


def test_dat_writer_preserves_quotes(tmp_path: Path) -> None:
    source = tmp_path / "resources"
    out = tmp_path / "out"
    source.mkdir()
    resource = source / "local.dat"
    resource.write_text('GREETING = "Hello"\n', encoding="utf-8")
    offset = resource.read_bytes().find(b'"Hello"')
    queue = tmp_path / "queue.tsv"
    write_tsv(queue, [{"file": "local.dat", "id": f"offset:{offset}", "source_text": "Hello", "zh_cn": "你好"}])
    write_queue(queue, source, out)
    assert resource.read_text(encoding="utf-8") == 'GREETING = "Hello"\n'
    assert (out / "local.dat").read_text(encoding="utf-8") == 'GREETING = "你好"\n'


def test_tbl2_writer_rejects_invalid_offset(tmp_path: Path) -> None:
    source = tmp_path / "resources"
    out = tmp_path / "out"
    source.mkdir()
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
