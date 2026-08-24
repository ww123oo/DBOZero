#!/usr/bin/env python3
import base64, gzip
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parts = [p.read_text().strip() for p in sorted((root/"data"/"tbl_batch3_chunks").glob("chunk*.txt"))]
out = root / "data" / "tbl_batch3_delta.tsv"
out.write_bytes(gzip.decompress(base64.b64decode("".join(parts))))
print("wrote", out, out.stat().st_size)
