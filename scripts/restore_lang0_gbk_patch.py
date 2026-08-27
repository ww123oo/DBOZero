#!/usr/bin/env python3
"""Restore hanhua_v3/runtime/lang0_gbk_patch.py from scripts/_lang0_gbk_patch.b64"""
from pathlib import Path
import base64
import sys

root = Path(__file__).resolve().parents[1]
b64_path = Path(__file__).resolve().parent / "_lang0_gbk_patch.b64"
out = root / "hanhua_v3" / "runtime" / "lang0_gbk_patch.py"

if not b64_path.exists():
    # fallback: download known-good revision
    import urllib.request
    URL = "https://raw.githubusercontent.com/ww123oo/DBOZero/f52a0378150b81a86bc5d4e5d57e113b1a1a50a1/hanhua_v3/runtime/lang0_gbk_patch.py"
    print("b64 missing; downloading", URL)
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
else:
    text = base64.b64decode("".join(b64_path.read_text(encoding="utf-8").split())).decode("utf-8")

if "printf_specs" not in text:
    print("ERROR: payload missing printf_specs")
    sys.exit(1)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding="utf-8", newline="\n")
compile(text, str(out), "exec")
print("OK: restored", out, "bytes", out.stat().st_size)
print("has printf_specs:", "printf_specs" in text)
