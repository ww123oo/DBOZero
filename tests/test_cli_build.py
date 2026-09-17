from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

from hanhua_v3 import cli


def test_run_build_all_invokes_both_products(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    class FakeBuilder:
        @staticmethod
        def main(args: list[str]) -> int:
            calls.append(args)
            return 0

    monkeypatch.setitem(sys.modules, "build_output", FakeBuilder)

    queue = tmp_path / "queue.tsv"
    source = tmp_path / "source"
    args = argparse.Namespace(
        source_dir=source,
        variant="all",
        queue=queue,
        force=True,
        no_parallel=True,
    )

    assert cli.run_build(args) == 0
    assert len(calls) == 2
    assert calls[0] == [
        "--source-dir", str(source),
        "--variant", "mainland",
        "--queue", str(queue),
        "--force",
        "--no-parallel",
    ]
    assert calls[1] == [
        "--source-dir", str(source),
        "--variant", "taiwan",
        "--queue", str(queue),
        "--force",
        "--no-parallel",
    ]


def test_build_parser_exposes_all_variant() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["build", "--variant", "all"])
    assert args.variant == "all"
    assert args.queue == cli.DEFAULT_QUEUE
