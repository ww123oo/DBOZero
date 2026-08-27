#!/usr/bin/env python3
"""Restore hanhua_v3/runtime/lang0_gbk_patch.py from b64 parts or known-good URL."""
from pathlib import Path
import base64
import sys
import urllib.request

root = Path(__file__).resolve().parents[1]
scripts = Path(__file__).resolve().parent
out = root / "hanhua_v3" / "runtime" / "lang0_gbk_patch.py"

parts = sorted(scripts.glob("_lang0_gbk_patch.b64.part*"))
single = scripts / "_lang0_gbk_patch.b64"
text = None

if parts:
    raw = "".join(p.read_text(encoding="utf-8") for p in parts)
    text = base64.b64decode("".join(raw.split())).decode("utf-8")
elif single.exists():
    text = base64.b64decode("".join(single.read_text(encoding="utf-8").split())).decode("utf-8")
else:
    URL = (
        "https://raw.githubusercontent.com/ww123oo/DBOZero/"
        "f52a0378150b81a86bc5d4e5d57e113b1a1a50a1/hanhua_v3/runtime/lang0_gbk_patch.py"
    )
    print("no local b64; downloading", URL)
    text = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")
    OLD = (
        "ALLOWED_PRINTF_MISMATCHES = {\n"
        '    "DST_INVENTORY_SORT_SUCCESS": (("%s",), ()),\n'
        '    "DST_ITEM_REMOTE_SELL": (("% o", "%s", "%s"), ("%s", "%s")),\n'
        "}\n"
    )
    NEW = (
        "ALLOWED_PRINTF_MISMATCHES = {\n"
        '    "DST_INVENTORY_SORT_SUCCESS": (("%s",), ()),\n'
        '    "DST_ITEM_REMOTE_SELL": (("% o", "%s", "%s"), ("%s", "%s")),\n'
        '    # "100% success" false-positive "% s"; allow TW "已是100% 成功。"\n'
        '    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": (("% s",), ()),\n'
        "}\n"
    )
    if "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE" not in text and OLD in text:
        text = text.replace(OLD, NEW, 1)

if not text or "printf_specs" not in text:
    print("ERROR: restored content missing printf_specs")
    sys.exit(1)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding="utf-8", newline="\n")
compile(text, str(out), "exec")
print("OK: restored", out, "bytes", out.stat().st_size)
print("has printf_specs:", True)
print("has GAME_ITEM allowlist:", "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE" in text)
