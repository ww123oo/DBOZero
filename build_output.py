# -*- coding: utf-8 -*-
"""Expand full build_output from scripts/build_output_p0..p8.b64"""
from __future__ import annotations
import base64, gzip, importlib.util, runpy, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
N = 9

def expand() -> bytes:
    parts = []
    for i in range(N):
        p = HERE / "scripts" / f"build_output_p{i}.b64"
        if not p.is_file():
            raise SystemExit(f"Missing {p}\ngit pull, then retry.")
        parts.append(p.read_text(encoding="ascii").strip())
    data = gzip.decompress(base64.b64decode("".join(parts)))
    if b"set_total" not in data or b"begin_stage" not in data:
        raise SystemExit("invalid payload")
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
