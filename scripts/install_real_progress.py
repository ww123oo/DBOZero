#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安裝真實進度條 build_output.py（從 scripts/build_output.py.gz.b64 展開）。"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assemble = Path(__file__).resolve().parent / "assemble_build_output.py"
    if not assemble.is_file():
        print("ERROR: missing scripts/assemble_build_output.py", file=sys.stderr)
        return 1
    print("Assembling full build_output.py ...")
    rc = subprocess.call([sys.executable, str(assemble)], cwd=str(root))
    if rc == 0:
        print()
        print("完成。請執行： dboc build --variant taiwan")
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
