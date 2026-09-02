# -*- coding: utf-8 -*-
"""
Build copy-only DBO Zero localization outputs from the v3 translation tables.

This reads:
- data/translations.tsv
- data/new_translations.tsv
- src_file/DBOZero

It writes:
- output/DBOZero
- output_taiwan/DBOZero

It never reads or writes the live game directory.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import re
import shutil
import struct
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

try:
    from hanhua_v3.runtime.build_progress import Progress as _BuildProgress
except Exception:  # pragma: no cover
    try:
        from build_progress import Progress as _BuildProgress
    except Exception:
        _BuildProgress = None
from typing import Callable

from hanhua_v3.policy import TBL_INTERNAL_TOKEN_DENYLIST, is_tbl_internal_token
from hanhua_v3.runtime import console_color, install_hanhua, lang0_gbk_patch, tbl_utf16_patch


ROOT = Path(__file__).resolve().parent


ACTIVE_STATUSES = {"", "accepted", "active", "ok", "keep"}
TAIWAN_FILES = set(install_hanhua.LOCALIZATION_FILES)
CORE_PACK_FILES = ("lang0.pak", "tbl0.pak", "tbl1.pak", "tbl2.pak")
OPTIONAL_PACK_FILES = ("gui0.pak",)
BUILD_CACHE_VERSION = 1
BUILD_MANIFEST_NAME = ".build_manifest.json"
BUILD_CODE_FILES = (
    Path("build_output.py"),
    Path("hanhua_v3/runtime/install_hanhua.py"),
    Path("hanhua_v3/runtime/lang0_gbk_patch.py"),
    Path("hanhua_v3/runtime/tbl_utf16_patch.py"),
)
GUI0_FONT_ALIASES = ("Default", "detail", "Lolita", "SimHei")
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc"}
UNQUOTED_LANG0_KEYS = {
    "DST_MAILSYSTEM_MAIL_MARKET",
    "DST_MARKET_ALLCATEGORY",
    "DST_MARKET_BUYTEXT",
    "DST_MARKET_CONSOLE_MACHINE",
    "DST_MARKET_EXP_BUFF",
    "DST_MARKET_NORMALTYPE",
    "DST_MARKET_REFRESH",
    "DST_MARKET_SELL_NOT",
    "DST_MARKET_TITLE",
    "DST_STATUS_STAT_CON",
    "DST_STATUS_STAT_DEX",
    "DST_STATUS_STAT_ENG",
    "DST_STATUS_STAT_FOC",
    "DST_STATUS_STAT_SOL",
    "DST_STATUS_STAT_STR",
}
