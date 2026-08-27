#!/usr/bin/env python3
"""Restore hanhua_v3/runtime/lang0_gbk_patch.py (embedded known-good + allowlist)."""
from pathlib import Path
import base64
import sys

root = Path(__file__).resolve().parents[1]
out = root / "hanhua_v3" / "runtime" / "lang0_gbk_patch.py"

# Full known-good source (f52a037 + GAME_ITEM allowlist), base64 to avoid truncate on push.
_B64 = open(Path(__file__).with_name("_lang0_gbk_patch.b64"), encoding="utf-8").read() if False else None
