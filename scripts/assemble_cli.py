#!/usr/bin/env python3
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parts_dir = root / "data" / "cli_text_parts"
text = "".join(p.read_text(encoding="utf-8") for p in sorted(parts_dir.glob("*.txt")))
out = root / "hanhua_v3" / "cli.py"
out.write_text(text, encoding="utf-8")
print("restored", out, out.stat().st_size)
