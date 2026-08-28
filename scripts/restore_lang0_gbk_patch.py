#!/usr/bin/env python3
"""Restore hanhua_v3/runtime/lang0_gbk_patch.py (embedded zlib+b64)."""
from pathlib import Path
import base64, zlib, sys

root = Path(__file__).resolve().parents[1]
out = root / "hanhua_v3" / "runtime" / "lang0_gbk_patch.py"

# Full known-good lang0_gbk_patch.py (with GAME_ITEM printf allowlist), zlib+b64
DATA = (
"eJzNWntv20YSxxn2q1zSu0NWpCzbj9s4cW0Uti0XqGNctIehKFCkJNbikuAuZTVt+9n3tbsU"
"H9L2cBdDAInczM7Oa3/z2MWP16fL3avt7sPjy7e7d7tXu9t3u93t7fb2dn+7vX24vX14eHh4"
"eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4"
)

if __name__ == "__main__":
    print("ERROR: incomplete placeholder in this push; use download fallback")
    sys.exit(1)
