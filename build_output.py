# -*- coding: utf-8 -*-
"""Bootstrap: expands StageProgress build_output from scripts/build_output_s0..s17.txt"""
from __future__ import annotations
import base64, gzip, runpy, sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent
_SELF = Path(__file__).resolve()
_N = 18

def _ensure_full() -> Path:
    data = _SELF.read_bytes()
    if b"begin_stage" in data and len(data) > 20000:
        return _SELF
    scripts = _ROOT / "scripts"
    parts = []
    for i in range(_N):
        p = scripts / f"build_output_s{i}.txt"
        if not p.is_file():
            raise SystemExit(f"Missing {p}; git pull and retry")
        parts.append(p.read_text(encoding="ascii").strip())
    full = gzip.decompress(base64.b64decode("".join(parts)))
    if b"begin_stage" not in full or b"parse_locator" not in full:
        raise SystemExit("invalid build_output payload")
    _SELF.write_bytes(full)
    print(f"[build_output] expanded StageProgress build_output.py ({len(full)} bytes)", flush=True)
    return _SELF

_path = _ensure_full()
if __name__ == "__main__":
    sys.argv[0] = str(_path)
    raise SystemExit(runpy.run_path(str(_path), run_name="__main__") and 0)
else:
    exec(compile(_path.read_text(encoding="utf-8"), str(_path), "exec"), globals())
