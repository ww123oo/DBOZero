# -*- coding: utf-8 -*-
"""DBO Zero Simplified Chinese patch builder/installer."""
from pathlib import Path as _Path
_dir = _Path(__file__).resolve().parent
exec(compile(
    (_dir / "_install_hanhua_part_a.py").read_text(encoding="utf-8")
    + (_dir / "_install_hanhua_part_b.py").read_text(encoding="utf-8"),
    str(_Path(__file__).resolve()),
    "exec",
), globals())
