from __future__ import annotations

import importlib
from pathlib import Path


def make_tbl2(item_id: int, text: str) -> bytes:
    encoded = text.encode("utf-16le")
    return item_id.to_bytes(4, "little") + b"\x00" + len(text).to_bytes(2, "little") + encoded


def write_queue(path: Path) -> None:
    path.write_text(
        "surface\tfile\tid\tsource_hash\tsource_text\tzh_cn\tstatus\tkind\tencoding\tlegacy_source\tlegacy_row\tnote\n"
        "pak\tpack/lang0.pak\tACCOUNT\t\tAccount\t账号\ttranslated\tlang0_entry\tutf-8\t\t\t\n",
        encoding="utf-8-sig",
    )


def test_build_one_creates_valid_taiwan_product(tmp_path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    source_root = tmp_path / "src_file" / "DBOZero"
    queue = tmp_path / "queue.tsv"
    source_root.joinpath("pack").mkdir(parents=True)
    project_root.mkdir()

    source_root.joinpath("pack/lang0.pak").write_bytes(
        'ACCOUNT="Account"\n'.encode("utf-8")
    )
    source_root.joinpath("pack/tbl0.pak").write_bytes(b"tbl0")
    source_root.joinpath("pack/tbl1.pak").write_bytes(b"tbl1")
    source_root.joinpath("pack/tbl2.pak").write_bytes(make_tbl2(1234, "Hello"))
    source_root.joinpath("readme.txt").write_text("untouched", encoding="utf-8")
    write_queue(queue)

    build_output = importlib.import_module("build_output")
    monkeypatch.setattr(build_output, "ROOT", project_root)

    output = project_root / "output_taiwan" / "DBOZero"
    assert build_output.build_one(
        source_dir=source_root,
        variant="taiwan",
        queue_path=queue,
        output_dir=output,
        force=True,
    ) == 0

    result = output.joinpath("pack/lang0.pak").read_bytes()
    assert b'ACCOUNT="帳號"' in result
    assert output.joinpath("pack/tbl2.pak").read_bytes() == source_root.joinpath("pack/tbl2.pak").read_bytes()
    assert output.joinpath("readme.txt").read_text(encoding="utf-8") == "untouched"
