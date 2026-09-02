# -*- coding: utf-8 -*-
"""Expands full build_output.py from scripts/build_output.py.gz.b64 then re-runs."""
from __future__ import annotations
import base64
import gzip
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GZ = HERE / "scripts" / "build_output.py.gz.b64"
SELF = Path(__file__).resolve()

def expand() -> bytes:
    if not GZ.is_file():
        raise SystemExit(
            "build_output.py not installed yet.\n"
            "Run:  python scripts/install_real_progress.py\n"
            "Then: dboc build --variant taiwan"
        )
    data = gzip.decompress(base64.b64decode(GZ.read_text(encoding="ascii").strip()))
    if b"set_total" not in data or b"begin_stage" not in data:
        raise SystemExit("invalid scripts/build_output.py.gz.b64")
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
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_output", SELF)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_output"] = mod
    spec.loader.exec_module(mod)
