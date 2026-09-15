# -*- coding: utf-8 -*-
"""Bootstrap: expands full StageProgress build_output.py from scripts/bo_pay_0..3.txt."""
from __future__ import annotations

import base64
import gzip
import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SELF = Path(__file__).resolve()


def _ensure_full() -> Path:
    data = _SELF.read_bytes()
    if b"begin_stage" in data and len(data) > 20000:
        return _SELF
    scripts = _ROOT / "scripts"
    parts = []
    for i in range(4):
        p = scripts / f"bo_pay_{i}.txt"
        if not p.is_file():
            raise SystemExit(f"Missing {p}; run git pull")
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
    _src = _path.read_text(encoding="utf-8")
    exec(compile(_src, str(_path), "exec"), globals())
