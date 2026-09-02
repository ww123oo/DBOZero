# -*- coding: utf-8 -*-
"""Expands full build_output.py from scripts/build_output*.b64 then re-runs."""
from __future__ import annotations
import base64
import gzip
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GZ = HERE / "scripts" / "build_output.py.gz.b64"
P1 = HERE / "scripts" / "build_output_p1.b64"
P2 = HERE / "scripts" / "build_output_p2.b64"
SELF = Path(__file__).resolve()

# Known transcription errors in the published p2 half (3 chars); fix on load.
_P2_FIXES = (
    ("f977579v43", "f977179v43"),
    ("uXqiHcfk65", "uXqiHffk65"),
    ("jNFm29U5du", "jNFm39U5du"),
)

def _load_gz_text() -> str:
    if GZ.is_file():
        return GZ.read_text(encoding="ascii").strip()
    if P1.is_file() and P2.is_file():
        p1 = P1.read_text(encoding="ascii").strip()
        p2 = P2.read_text(encoding="ascii").strip()
        for bad, good in _P2_FIXES:
            p2 = p2.replace(bad, good, 1)
        return p1 + p2
    raise SystemExit(
        "build_output.py not installed yet.\n"
        "Missing scripts/build_output.py.gz.b64 (or p1+p2).\n"
        "git pull, then: python scripts/install_real_progress.py"
    )

def expand() -> bytes:
    data = gzip.decompress(base64.b64decode(_load_gz_text()))
    if b"set_total" not in data or b"begin_stage" not in data:
        raise SystemExit("invalid build_output b64 payload")
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
