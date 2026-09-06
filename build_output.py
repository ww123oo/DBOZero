# -*- coding: utf-8 -*-
"""Stable launcher for the bundled DBOZero build implementation.

The bundled builder is stored in scripts/build_output_p*.b64. This launcher
executes it without overwriting build_output.py itself.
"""
from __future__ import annotations

import base64
import gzip
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD_PARTS = 3


def expand() -> bytes:
    parts: list[str] = []
    for i in range(PAYLOAD_PARTS):
        path = HERE / "scripts" / f"build_output_p{i}.b64"
        if not path.is_file():
            raise SystemExit(f"Missing {path}\ngit pull, then retry.")
        parts.append(path.read_text(encoding="ascii").strip())
    try:
        data = gzip.decompress(base64.b64decode("".join(parts), validate=True))
    except Exception as exc:
        raise SystemExit(f"invalid build_output payload: {exc}") from exc
    if b"set_total" not in data or b"begin_stage" not in data:
        raise SystemExit("invalid build_output payload")
    return data


def execute(data: bytes) -> None:
    module = types.ModuleType("__main__")
    module.__file__ = str(HERE / "build_output.py")
    module.__package__ = ""
    module.__cached__ = None
    module.__dict__["__name__"] = "__main__"
    sys.modules["__main__"] = module
    code = compile(data, str(HERE / "build_output.py"), "exec")
    exec(code, module.__dict__)


def main() -> None:
    execute(expand())


if __name__ == "__main__":
    main()
