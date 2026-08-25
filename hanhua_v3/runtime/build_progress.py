# -*- coding: utf-8 -*-
"""Terminal progress helpers for dboc (build / scan / translate / update)."""

from __future__ import annotations

import sys


class Progress:
    """Compact terminal progress bar (no external deps)."""

    # Prefer block glyphs; fall back to ASCII if the console can't encode them.
    _FILL = "█"
    _EMPTY = "░"
    _WIDTH = 16

    def __init__(self, total: int, label: str = "") -> None:
        self.total = max(int(total), 1)
        self.current = 0
        self.label = label
        self._use_blocks = self._console_supports_blocks()

    @staticmethod
    def _console_supports_blocks() -> bool:
        enc = getattr(sys.stdout, "encoding", None) or ""
        try:
            "█░".encode(enc or "utf-8")
            return True
        except Exception:
            return False

    def step(self, message: str = "") -> None:
        self.current = min(self.current + 1, self.total)
        self._render(message)

    def set(self, current: int, message: str = "") -> None:
        self.current = max(0, min(int(current), self.total))
        self._render(message)

    def ratio(self, current: int, total: int, message: str = "") -> None:
        total = max(int(total), 1)
        self.total = total
        self.current = max(0, min(int(current), total))
        self._render(message)

    def note(self, message: str) -> None:
        prefix = f"{self.label}: " if self.label else ""
        print(f"  · {prefix}{message}", flush=True)

    def done(self, message: str = "完成") -> None:
        self.current = self.total
        self._render(message)

    def _render(self, message: str) -> None:
        filled = int(self._WIDTH * self.current / self.total)
        if self._use_blocks:
            bar = self._FILL * filled + self._EMPTY * (self._WIDTH - filled)
        else:
            bar = "=" * filled + "-" * (self._WIDTH - filled)
        pct = int(100 * self.current / self.total)
        # Keep one short line:  44% ████░░░░  4/9  tbl1.pak
        parts = [f"{pct:3d}%", bar, f"{self.current}/{self.total}"]
        if self.label:
            parts.append(self.label)
        if message:
            parts.append(message)
        print("  " + "  ".join(parts), flush=True)


# Backward-compatible alias used by build_output patches
BuildProgress = Progress
