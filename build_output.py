# -*- coding: utf-8 -*-
"""Expands full build_output.py from scripts/build_output.py.gz.b64 then re-runs."""
from __future__ import annotations
import base64
import gzip
import importlib.util
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GZ = HERE / "scripts" / "build_output.py.gz.b64"
SELF = Path(__file__).resolve()

def expand() -> bytes:
    if not GZ.is_file():
        raise SystemExit(
            "Missing scripts/build_output.py.gz.b64\n"
            "git pull, then retry."
        )
    raw = GZ.read_text(encoding="ascii").strip()
    data = gzip.decompress(base64.b64decode(raw))
    if b"set_total" not in data or b"begin_stage" not in data:
        raise SystemExit("invalid build_output.py.gz.b64 payload")
    return data

def main() -> None:
    data = expand()
    bak = SELF.with_suffix(".py.bak_stub")
    if not bak.exists():
        bak.write_bytes(SELF.read_bytes())
    SELF.write_bytes(data)
    sys.argv[0] = str(SELF)
    runpy.run_path(str(SELF), run_name="__main__")

if __name__ == "__main__":
    main()
else:
    data = expand()
    SELF.write_bytes(data)
    spec = importlib.util.spec_from_file_location("build_output", SELF)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_output"] = mod
    spec.loader.exec_module(mod)
