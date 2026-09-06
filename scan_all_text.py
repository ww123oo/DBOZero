# -*- coding: utf-8 -*-
"""Convenience entry point for the DBO full text scanner."""
from __future__ import annotations

import sys
from pathlib import Path

from hanhua_v3.runtime.full_text_scanner import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        root = Path("src_file") / "DBOZero"
        sys.argv.extend([str(root), "-o", "translation_scan.tsv"])
    raise SystemExit(main())
