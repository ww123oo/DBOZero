#!/usr/bin/env python3
"""Assemble build_output.py from scripts/build_output.py.gz.b64 (preferred)
or scripts/build_output_chunks/*.b64 (legacy).
"""
from __future__ import annotations
import base64
import gzip
from pathlib import Path

root = Path(__file__).resolve().parents[1]
scripts = Path(__file__).resolve().parent
out = root / "build_output.py"
bak = out.with_suffix(".py.bak_before_real_progress")

gz_b64 = scripts / "build_output.py.gz.b64"
parts_dir = scripts / "build_output_chunks"

if gz_b64.is_file():
    data = gzip.decompress(base64.b64decode(gz_b64.read_text(encoding="ascii").strip()))
    print("source: scripts/build_output.py.gz.b64")
else:
    parts = sorted(parts_dir.glob("chunk_*.b64"))
    if not parts:
        raise SystemExit(f"missing {gz_b64} and no chunks in {parts_dir}")
    data = b"".join(base64.b64decode(p.read_text(encoding="ascii").strip()) for p in parts)
    print(f"source: {len(parts)} chunks in build_output_chunks/")

if out.is_file() and out.read_bytes()[:40] != data[:40]:
    if not bak.exists():
        bak.write_bytes(out.read_bytes())

out.write_bytes(data)
print("wrote", out, len(data), "bytes")
text = data.decode("utf-8")
assert "set_total" in text, "missing set_total"
assert "_BuildProgress(9" not in text, "still has fake 9 steps"
assert "begin_stage" in text, "missing begin_stage"
print("OK: real progress build_output.py")
