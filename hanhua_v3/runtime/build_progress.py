# -*- coding: utf-8 -*-
"""Terminal progress helpers for dboc — driven by real work units, not fake timers."""

from __future__ import annotations

import sys
import time


class Progress:
    """Same-line terminal progress bar based on actual completed units.

    - total / current are real counts (rows, files, steps you advance)
    - updates overwrite the same line via \\r (no spam)
    - note() / done() break to a new line
    """

    def __init__(self, total: int = 0, label: str = "") -> None:
        self.total = max(int(total), 0)
        self.current = 0
        self.label = label
        self._width = 28
        self._last_render = 0.0
        self._min_interval = 0.05  # throttle redraws during tight loops
        self._finished = False
        self._live = False  # True while a \\r line is active

    def set_total(self, total: int) -> None:
        self.total = max(int(total), 0)
        if self.current > self.total:
            self.current = self.total

    def step(self, message: str = "", n: int = 1) -> None:
        """Advance by n real units (default 1)."""
        self.current = min(self.current + max(int(n), 0), max(self.total, 1))
        self._render(message, force=False)

    def advance(self, n: int, message: str = "") -> None:
        self.step(message, n=n)

    def set(self, current: int, message: str = "") -> None:
        self.current = max(0, min(int(current), max(self.total, 1)))
        self._render(message, force=True)

    def ratio(self, current: int, total: int, message: str = "") -> None:
        total = max(int(total), 1)
        self.total = total
        self.current = max(0, min(int(current), total))
        self._render(message, force=True)

    def note(self, message: str) -> None:
        self._end_live_line()
        prefix = f"{self.label}: " if self.label else ""
        print(f"  · {prefix}{message}", flush=True)

    def done(self, message: str = "完成") -> None:
        if self.total > 0:
            self.current = self.total
        self._render(message, force=True)
        self._end_live_line()
        self._finished = True

    def _end_live_line(self) -> None:
        if self._live:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._live = False

    def _render(self, message: str, *, force: bool) -> None:
        now = time.monotonic()
        if not force and self._live and (now - self._last_render) < self._min_interval:
            if self.current < self.total:
                return
        self._last_render = now

        total = max(self.total, 1)
        cur = min(self.current, total)
        filled = int(self._width * cur / total) if self.total else 0
        bar = "█" * filled + "░" * (self._width - filled)
        pct = int(100 * cur / total) if self.total else 0
        prefix = f"{self.label} " if self.label else ""
        msg = f" {message}" if message else ""
        line = f"\r{prefix}[{bar}] {pct:3d}% ({cur}/{total}){msg}"
        # pad to clear previous longer message
        line = line.ljust(max(len(line), 90))
        sys.stdout.write(line)
        sys.stdout.flush()
        self._live = True


# Backward-compatible alias used by build_output patches
BuildProgress = Progress
