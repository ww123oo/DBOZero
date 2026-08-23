#!/usr/bin/env python3
import zlib, base64
from pathlib import Path
root = Path(__file__).resolve().parents[1]
b64 = (root / "data" / "merge_parts" / "parts.b64").read_text().strip()
raw = zlib.decompress(base64.b64decode(b64)).decode("utf-8")
chunks = raw.split("\n---PART---\n")
outdir = root / "data" / "merge_parts"
outdir.mkdir(parents=True, exist_ok=True)
for i, chunk in enumerate(chunks, 1):
    (outdir / f"part{i}.tsv").write_text(chunk, encoding="utf-8")
    print("wrote part", i, len(chunk))
print("done")
