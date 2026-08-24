# -*- coding: utf-8 -*-
"""Terminal progress helpers for dboc (build / scan / translate / update)."""

from __future__ import annotations


class Progress:
    """Simple terminal progress bar (no external deps)."""

    def __init__(self, total: int, label: str = "") -> None:
        self.total = max(int(total), 1)
        self.current = 0
        self.label = label
        self._width = 22

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
        print(f"         {prefix}{message}", flush=True)

    def done(self, message: str = "完成") -> None:
        self.current = self.total
        self._render(message)

    def _render(self, message: str) -> None:
        filled = int(self._width * self.current / self.total)
        bar = "#" * filled + "-" * (self._width - filled)
        pct = int(100 * self.current / self.total)
        prefix = f"{self.label}: " if self.label else ""
        msg = f" {message}" if message else ""
        print(
            f"[{bar}] {pct:3d}% ({self.current}/{self.total}) {prefix}{msg}".rstrip(),
            flush=True,
        )


# Backward-compatible alias used by build_output patches
BuildProgress = Progress
