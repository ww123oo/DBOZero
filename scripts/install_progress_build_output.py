# -*- coding: utf-8 -*-
"""Expand StageProgress build_output.py from scripts/bo_pay_0..3.txt"""
from __future__ import annotations
import base64, gzip
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent

def main() -> int:
    parts = []
    for i in range(4):
        p = SCRIPTS / f"bo_pay_{i}.txt"
        if not p.is_file():
            raise SystemExit(f"Missing {p}")
        parts.append(p.read_text(encoding="ascii").strip())
    data = gzip.decompress(base64.b64decode("".join(parts)))
    if b"begin_stage" not in data or b"parse_locator" not in data:
        raise SystemExit("invalid payload")
    target = ROOT / "build_output.py"
    target.write_bytes(data)
    print(f"wrote {target} size={len(data)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
