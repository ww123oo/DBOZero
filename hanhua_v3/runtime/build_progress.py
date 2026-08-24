# -*- coding: utf-8 -*-
"""Terminal progress helpers for dboc build."""

from __future__ import annotations


class BuildProgress:
    """Simple terminal progress bar (no external deps)."""

    def __init__(self, total: int, label: str = "") -> None:
        self.total = max(total, 1)
        self.current = 0
        self.label = label
        self._width = 22

    def step(self, message: str) -> None:
        self.current += 1
        filled = int(self._width * self.current / self.total)
        bar = "#" * filled + "-" * (self._width - filled)
        pct = int(100 * self.current / self.total)
        prefix = f"{self.label}: " if self.label else ""
        print(
            f"[{bar}] {pct:3d}% ({self.current}/{self.total}) {prefix}{message}",
            flush=True,
        )

    def note(self, message: str) -> None:
        prefix = f"{self.label}: " if self.label else ""
        print(f"         {prefix}{message}", flush=True)
