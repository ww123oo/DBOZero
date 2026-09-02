#!/usr/bin/env python3
"""Expand data/舊譯表/deltas_merged/*.tsv.gz.b64 (+ optional tbl_p*.b64) to .tsv"""
from __future__ import annotations
import base64, gzip
from pathlib import Path

HERE = Path(__file__).resolve().parent

def expand_one(name: str) -> None:
    p = HERE / f"{name}.tsv.gz.b64"
    if not p.is_file():
        return
    out = HERE / f"{name}.tsv"
    out.write_bytes(gzip.decompress(base64.b64decode(p.read_text(encoding="ascii").strip())))
    print(f"wrote {out.name} ({out.stat().st_size} bytes)")

def expand_parts(prefix: str, out_name: str) -> None:
    parts = sorted(HERE.glob(f"{prefix}*.b64"))
    if not parts:
        return
    b64 = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    out = HERE / out_name
    out.write_bytes(gzip.decompress(base64.b64decode(b64)))
    print(f"wrote {out.name} from {len(parts)} parts ({out.stat().st_size} bytes)")

def main() -> None:
    expand_one("term")
    expand_one("ui")
    expand_one("tbl")
    expand_one("all_deltas")
    expand_parts("tbl_p", "tbl.tsv")
    expand_parts("tbl8_", "tbl.tsv")
    expand_parts("all_p", "all_deltas.tsv")
    print("done")

if __name__ == "__main__":
    main()
