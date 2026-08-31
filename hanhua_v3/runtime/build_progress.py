# -*- coding: utf-8 -*-
"""Terminal progress helpers for dboc — stage-by-stage + overall total (option B)."""

from __future__ import annotations

import sys
import time


class Progress:
    """Sequential stages (each 0→100% on real units) + overall total bar.

    Display (two live lines when supported):
        [████████░░░░░░░░░░░░░░░░░░░░]  67% (2170/3240) pack/lang0.pak
        總進度 [████░░░░░░░░░░░░░░░░░░░░░░░░]  18% (3920/21745)
    """

    def __init__(self, total: int = 0, label: str = "") -> None:
        self.overall_total = max(int(total), 0)
        self.overall_current = 0
        self.label = label
        self._width = 28
        self._last_render = 0.0
        self._min_interval = 0.05
        self._finished = False
        self._live_lines = 0

        self.stage_name = ""
        self.stage_total = 0
        self.stage_current = 0
        self._stage_open = False

        # compatibility
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
        self._render(force=True)

    def end_stage(self, message: str = "") -> None:
        if not self._stage_open:
            return
        self.stage_current = self.stage_total
        self._render(force=True, message=message or self.stage_name)
        self._end_live_lines()
        self._stage_open = False

    def step(self, message: str = "", n: int = 1) -> None:
        n = max(int(n), 0)
        if self._stage_open:
            self.stage_current = min(self.stage_current + n, self.stage_total)
        self.overall_current = min(self.overall_current + n, max(self.overall_total, 1))
        self.current = self.overall_current
        self.total = self.overall_total
        self._render(message=message, force=False)

    def advance(self, n: int, message: str = "") -> None:
        self.step(message, n=n)

    def set(self, current: int, message: str = "") -> None:
        self.overall_current = max(0, min(int(current), max(self.overall_total, 1)))
        self.current = self.overall_current
        self._render(message=message, force=True)

    def ratio(self, current: int, total: int, message: str = "") -> None:
        total = max(int(total), 1)
        self.overall_total = total
        self.total = total
        self.overall_current = max(0, min(int(current), total))
        self.current = self.overall_current
        self._render(message=message, force=True)

    def note(self, message: str) -> None:
        self._end_live_lines()
        prefix = f"{self.label}: " if self.label else ""
        print(f"  · {prefix}{message}", flush=True)

    def done(self, message: str = "完成") -> None:
        if self._stage_open:
            self.end_stage()
        if self.overall_total > 0:
            self.overall_current = self.overall_total
            self.current = self.overall_current
        self.stage_name = message
        self.stage_total = 1
        self.stage_current = 1
        self._stage_open = True
        self._render(force=True, message=message)
        self._end_live_lines()
        self._stage_open = False
        self._finished = True

    def _end_live_lines(self) -> None:
        if self._live_lines > 0:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._live_lines = 0

    def _bar(self, cur: int, total: int) -> tuple[str, int]:
        total = max(total, 1)
        cur = min(max(cur, 0), total)
        filled = int(self._width * cur / total) if total else 0
        bar = "█" * filled + "░" * (self._width - filled)
        pct = int(100 * cur / total) if total else 0
        return bar, pct

    def _render(self, message: str = "", *, force: bool = False) -> None:
        now = time.monotonic()
        if (
            not force
            and self._live_lines > 0
            and (now - self._last_render) < self._min_interval
            and self.stage_current < self.stage_total
        ):
            return
        self._last_render = now

        stage_bar, stage_pct = self._bar(self.stage_current, self.stage_total)
        overall_bar, overall_pct = self._bar(self.overall_current, self.overall_total)

        stage_label = message or self.stage_name or ""
        st = max(self.stage_total, 1)
        sc = min(self.stage_current, st)
        ot = max(self.overall_total, 1)
        oc = min(self.overall_current, ot)

        line1 = f"[{stage_bar}] {stage_pct:3d}% ({sc}/{st}) {stage_label}".ljust(78)
        line2 = f"總進度 [{overall_bar}] {overall_pct:3d}% ({oc}/{ot})".ljust(78)

        if self._live_lines == 2:
            sys.stdout.write("\033[A\r" + line1 + "\n" + line2)
        elif self._live_lines == 1:
            sys.stdout.write("\r" + line1 + "\n" + line2)
        else:
            sys.stdout.write(line1 + "\n" + line2)
        sys.stdout.flush()
        self._live_lines = 2


BuildProgress = Progress
