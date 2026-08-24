#!/usr/bin/env python3
"""Restore hanhua_v3/cli.py from data/cli_restore/chunk*.txt"""
import base64, gzip
from pathlib import Path

root = Path(__file__).resolve().parents[1]
chunk_dir = root / "data" / "cli_restore"
parts = []
for path in sorted(chunk_dir.glob("chunk*.txt")):
    parts.append(path.read_text(encoding="ascii").strip())
b64 = "".join(parts)
out = root / "hanhua_v3" / "cli.py"
out.write_bytes(gzip.decompress(base64.b64decode(b64)))
print("restored", out, out.stat().st_size)
