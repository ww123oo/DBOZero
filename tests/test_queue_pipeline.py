from __future__ import annotations

import csv
from pathlib import Path

from hanhua_v3.runtime.translation_queue import build_queue, source_hash, write_tsv


SCHEMA = (
    "surface",
    "file",
    "id",
    "source_hash",
    "source_text",
    "zh_cn",
    "status",
    "kind",
    "encoding",
    "legacy_source",
    "legacy_row",
    "note",
)


def row(file_name: str, locator: str, source: str, translation: str = "") -> dict[str, str]:
    return {
        "surface": "pak",
        "file": file_name,
        "id": locator,
        "source_hash": source_hash(source),
        "source_text": source,
        "zh_cn": translation,
        "status": "translated" if translation else "new",
        "kind": "utf16",
        "encoding": "utf-16le",
        "legacy_source": "",
        "legacy_row": "",
        "note": "",
    }


def write_scan(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["file", "offset", "encoding", "byte_length", "confidence", "kind", "id", "source_text", "translation"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for item in rows:
            writer.writerow(item)


def test_queue_migrates_unique_basename_match(tmp_path: Path) -> None:
    scan = tmp_path / "scan.tsv"
    legacy = tmp_path / "legacy.tsv"
    daily = tmp_path / "daily.tsv"
    output = tmp_path / "out.tsv"

    write_scan(
        scan,
        [
            {
                "file": "pack/new/gui0.pak",
                "offset": "0x10",
                "encoding": "utf-16le",
                "byte_length": "10",
                "confidence": "high",
                "kind": "utf16",
                "id": "",
                "source_text": "Hello",
                "translation": "",
            }
        ],
    )
    write_tsv(legacy, [row("old/gui0.pak", "offset:0x10", "Hello", "嗨")])
    write_tsv(daily, [])

    candidates, _merged = build_queue(scan, legacy, daily)
    assert len(candidates) == 1
    assert candidates[0]["zh_cn"] == "嗨"
    assert candidates[0]["status"] == "translated"


def test_queue_rejects_ambiguous_basename_translation(tmp_path: Path) -> None:
    scan = tmp_path / "scan.tsv"
    legacy = tmp_path / "legacy.tsv"
    daily = tmp_path / "daily.tsv"
    write_scan(
        scan,
        [
            {
                "file": "pack/new/gui0.pak",
                "offset": "0x10",
                "encoding": "utf-16le",
                "byte_length": "10",
                "confidence": "high",
                "kind": "utf16",
                "id": "",
                "source_text": "Hello",
                "translation": "",
            }
        ],
    )
    write_tsv(
        legacy,
        [
            row("old/a/gui0.pak", "offset:0x10", "Hello", "嗨"),
            row("old/b/gui0.pak", "offset:0x10", "Hello", "您好"),
        ],
    )
    write_tsv(daily, [])

    candidates, _merged = build_queue(scan, legacy, daily)
    assert len(candidates) == 1
    assert candidates[0]["zh_cn"] == ""
    assert candidates[0]["status"] == "new"
