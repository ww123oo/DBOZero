# -*- coding: utf-8 -*-
"""Expand full build_output.py from scripts/bo_pay_0..3.txt — run once after git pull."""
from __future__ import annotations
import base64, gzip
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent

def main() -> None:
    parts = []
    for i in range(4):
        p = SCRIPTS / f"bo_pay_{i}.txt"
        if not p.is_file():
            raise SystemExit(f"Missing {p} — git pull 後再試")
        parts.append(p.read_text(encoding="ascii").strip())
    data = gzip.decompress(base64.b64decode("".join(parts)))
    if b"def build_one" not in data or b"ThreadPoolExecutor" not in data:
        raise SystemExit("invalid build_output payload")
    target = ROOT / "build_output.py"
    bak = target.with_suffix(".py.bak_before_expand")
    if target.exists() and target.stat().st_size < 10000 and not bak.exists():
        bak.write_bytes(target.read_bytes())
    target.write_bytes(data)
    print("wrote", target, len(data), "bytes")
    print("OK — dboc build --variant taiwan")

if __name__ == "__main__":
    main()
