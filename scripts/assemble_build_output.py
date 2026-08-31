#!/usr/bin/env python3
"""Assemble build_output.py from base64 chunks (real progress version)."""
import base64
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parts_dir = Path(__file__).resolve().parent / "build_output_chunks"
parts = sorted(parts_dir.glob("chunk_*.b64"))
if not parts:
    raise SystemExit(f"no chunks in {parts_dir}")
data = b"".join(base64.b64decode(p.read_text(encoding="ascii").strip()) for p in parts)
out = root / "build_output.py"
bak = out.with_suffix(".py.bak_before_real_progress")
if out.is_file() and not bak.exists():
    bak.write_bytes(out.read_bytes())
out.write_bytes(data)
print("wrote", out, len(data), "bytes")
