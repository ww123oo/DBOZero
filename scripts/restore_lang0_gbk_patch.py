#!/usr/bin/env python3
"""Restore hanhua_v3/runtime/lang0_gbk_patch.py from known-good commit + GAME_ITEM allowlist."""
from pathlib import Path
import urllib.request
import sys

root = Path(__file__).resolve().parents[1]
out = root / "hanhua_v3" / "runtime" / "lang0_gbk_patch.py"

# Known-good revision (before accidental truncate)
URL = (
    "https://raw.githubusercontent.com/ww123oo/DBOZero/"
    "f52a0378150b81a86bc5d4e5d57e113b1a1a50a1/hanhua_v3/runtime/lang0_gbk_patch.py"
)

print("downloading good lang0_gbk_patch.py ...")
text = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")
if "printf_specs" not in text:
    print("ERROR: downloaded file missing printf_specs")
    sys.exit(1)

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

if "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE" not in text:
    if OLD not in text:
        print("ERROR: allowlist block not found in downloaded file")
        sys.exit(1)
    text = text.replace(OLD, NEW, 1)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding="utf-8", newline="\n")
compile(text, str(out), "exec")
print("OK: restored", out, "bytes", out.stat().st_size)
print("has printf_specs:", "printf_specs" in text)
print("has GAME_ITEM allowlist:", "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE" in text)
