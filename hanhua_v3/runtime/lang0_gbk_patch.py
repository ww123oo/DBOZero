# -*- coding: utf-8 -*-
"""
DBO Zero lang0.pak fixed-size single-value patcher.

This dev tool intentionally keeps the original file size and only replaces the
quoted value for keys that already exist in lang0.pak.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

__all__ = [
    "ALLOWED_PRINTF_MISMATCHES",
    "PatchError",
    "PRINTF_SPEC_RE",
    "auto_detect_game_dir",
    "backup_lang0",
    "build_parser",
    "decode_lang0_value",
    "encode_lang0_value",
    "encoded_text_bytes",
    "find_lang0_value_end",
    "find_lang0_value_start",
    "install",
    "is_game_dir",
    "lang0_path",
    "main",
    "tool_dir",
]


class PatchError(RuntimeError):
    pass


PRINTF_SPEC_RE = re.compile(r"%(?:\d+\$)?[+#0\- ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?[diuoxXfFeEgGaAcspn%]")
ALLOWED_PRINTF_MISMATCHES = {
    "DST_INVENTORY_SORT_SUCCESS": (("%s",), ()),
    "DST_ITEM_REMOTE_SELL": (("% o", "%s", "%s"), ("%s", "%s")),
    # "100% success" false-positive "% s"; allow pure TW "已是100% 成功。"
    "GAME_ITEM_UPGRADE_CANT_USE_STONE_CORE_WITH_SAFE": (("% s",), ()),
}
