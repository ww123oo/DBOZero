# -*- coding: utf-8 -*-
"""Expand build_output.py from scripts/bo_payload_a.txt + bo_payload_b.txt"""
from __future__ import annotations
import base64, gzip
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent

def main() -> None:
    a = (SCRIPTS / "bo_payload_a.txt").read_text(encoding="ascii").strip()
    b = (SCRIPTS / "bo_payload_b.txt").read_text(encoding="ascii").strip()
    data = gzip.decompress(base64.b64decode(a + b))
    if b"set_total" not in data or b"begin_stage" not in data:
        raise SystemExit("invalid payload")
    target = ROOT / "build_output.py"
    target.write_bytes(data)
    # also write p0-p2 for stub compatibility
    s = a + b
    n, chunk = 3, (len(s) + 2) // 3
    for i in range(3):
        (SCRIPTS / f"build_output_p{i}.b64").write_text(s[i*chunk:(i+1)*chunk], encoding="ascii")
    print("wrote", target, len(data))
    print("wrote p0-p2")

if __name__ == "__main__":
    main()
