# -*- coding: utf-8 -*-
"""Terminal progress for dboc — sequential stages, one permanent line each.

Desired look:

    [████████████████████████████] 100% (1/1) 讀取翻譯表
    [████████████████████████████] 100% (53773/53773) localize/Taiwan/language
    [████████████████████████████] 100% (3240/3240) pack/lang0.pak
    [████████░░░░░░░░░░░░░░░░░░░░]  30% (230/769) pack/tbl0.pak   ← live \\r
    …
    [████████████████████████████] 100% 總進度 (53773/53773) 完成
"""

from __future__ import annotations

import sys
import time


class Progress:
    """One stage at a time; finished stages stay on screen as permanent lines."""

    def __init__(self, total: int = 0, label: str = "") -> None:
        self.overall_total = max(int(total), 0)
        self.overall_current = 0
        self.label = label
        self._width = 28
        self._last_render = 0.0
        self._min_interval = 0.08
        self._finished = False
        self._live = False  # current stage line is open (no newline yet)

        self.stage_name = ""
        self.stage_total = 0
        self.stage_current = 0
        self._stage_open = False

        # compatibility aliases used by older call sites
        self.total = self.overall_total
        self.current = self.overall_current

    def set_total(self, total: int) -> None:
        self.overall_total = max(int(total), 0)
        self.total = self.overall_total
        if self.overall_current > self.overall_total:
            self.overall_current = self.overall_total
            self.current = self.overall_current

    def begin_stage(self, name: str, total: int = 1) -> None:
        if self._stage_open:
            self.end_stage()
        self.stage_name = name
        self.stage_total = max(int(total), 1)
        self.stage_current = 0
        self._stage_open = True
        self._render_live(force=True)

    def end_stage(self, message: str = "") -> None:
        if not self._stage_open:
            return
        self.stage_current = self.stage_total
        label = message or self.stage_name
        self._finish_line(label)
        self._stage_open = False

    def step(self, message: str = "", n: int = 1) -> None:
        n = max(int(n), 0)
        if self._stage_open:
            self.stage_current = min(self.stage_current + n, self.stage_total)
        self.overall_current = min(self.overall_current + n, max(self.overall_total, 1))
        self.current = self.overall_current
        self.total = self.overall_total
        if message:
            self.stage_name = message if not self.stage_name else self.stage_name
        self._render_live(force=False, label=message or self.stage_name)

    def advance(self, n: int, message: str = "") -> None:
        self.step(message, n=n)

    def set(self, current: int, message: str = "") -> None:
        self.overall_current = max(0, min(int(current), max(self.overall_total, 1)))
        self.current = self.overall_current
        self._render_live(force=True, label=message or self.stage_name)

    def ratio(self, current: int, total: int, message: str = "") -> None:
        total = max(int(total), 1)
        self.overall_total = total
        self.total = total
        self.overall_current = max(0, min(int(current), total))
        self.current = self.overall_current
        self._render_live(force=True, label=message or self.stage_name)

    def note(self, message: str) -> None:
        if self._live:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._live = False
        prefix = f"{self.label}: " if self.label else ""
        print(f"  · {prefix}{message}", flush=True)
        if self._stage_open:
            self._render_live(force=True)

    def done(self, message: str = "完成") -> None:
        if self._stage_open:
            self.end_stage()
        if self.overall_total > 0:
            self.overall_current = self.overall_total
            self.current = self.overall_current
        bar, pct = self._bar(self.overall_current, self.overall_total)
        ot = max(self.overall_total, 1)
        oc = min(self.overall_current, ot)
        line = f"[{bar}] {pct:3d}% 總進度 ({oc}/{ot}) {message}"
        print(line, flush=True)
        self._finished = True

    def _bar(self, cur: int, total: int) -> tuple[str, int]:
        total = max(total, 1)
        cur = min(max(cur, 0), total)
        filled = int(self._width * cur / total)
        bar = "█" * filled + "░" * (self._width - filled)
        pct = int(100 * cur / total)
        return bar, pct

    def _render_live(self, *, force: bool, label: str | None = None) -> None:
        """Update the current stage on one \\r line (no ANSI cursor-up)."""
        if not self._stage_open:
            return
        now = time.monotonic()
        if (
            not force
            and self._live
            and (now - self._last_render) < self._min_interval
            and self.stage_current < self.stage_total
        ):
            return
        self._last_render = now

        st = max(self.stage_total, 1)
        sc = min(self.stage_current, st)
        bar, pct = self._bar(sc, st)
        name = label or self.stage_name or ""
        line = f"[{bar}] {pct:3d}% ({sc}/{st}) {name}"
        line = line.ljust(88)
        sys.stdout.write("\r" + line)
        sys.stdout.flush()
        self._live = True

    def _finish_line(self, label: str) -> None:
        """Write permanent 100% line for the finished stage."""
        st = max(self.stage_total, 1)
        bar, pct = self._bar(st, st)
        line = f"[{bar}] {pct:3d}% ({st}/{st}) {label}".ljust(88)
        if self._live:
            sys.stdout.write("\r" + line + "\n")
        else:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        self._live = False


BuildProgress = Progress
