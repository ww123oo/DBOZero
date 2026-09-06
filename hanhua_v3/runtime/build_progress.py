# -*- coding: utf-8 -*-
"""Terminal progress for dboc — sequential stages, one permanent line each.

    [████████████████████████████] 100% (1/1) 讀取翻譯表 完成 (0.1s)
    [████████████████████████████] 100% (5368/5368) pack/lang0.pak 完成 (2.3s)
    [████████████████████████████] 100% 總進度 (53773/53773) 完成 (45.2s)
"""

from __future__ import annotations

import sys
import time


class Progress:
    def __init__(self, total: int = 0, label: str = "") -> None:
        self.overall_total = max(int(total), 0)
        self.overall_current = 0
        self.label = label
        self._width = 28
        self._last_render = 0.0
        self._min_interval = 0.08
        self._finished = False
        self._live = False
        self.stage_name = ""
        self.stage_total = 0
        self.stage_current = 0
        self._stage_open = False
        self._stage_t0 = 0.0
        self._run_t0 = time.monotonic()
        self.total = self.overall_total
        self.current = self.overall_current

    def set_total(self, total: int) -> None:
        self.overall_total = max(int(total), 0)
        self.total = self.overall_total
        if self.overall_current > self.overall_total:
            self.overall_current = self.overall_total
            self.current = self.overall_current

    @staticmethod
    def _fmt_sec(seconds: float) -> str:
        if seconds < 10:
            return f"{seconds:.1f}s"
        return f"{int(round(seconds))}s"

    def begin_stage(self, name: str, total: int = 1) -> None:
        if self._stage_open:
            self.end_stage()
        self.stage_name = name
        self.stage_total = max(int(total), 1)
        self.stage_current = 0
        self._stage_open = True
        self._stage_t0 = time.monotonic()
        self._render_live(force=True)

    def end_stage(self, message: str = "") -> None:
        if not self._stage_open:
            return
        self.stage_current = self.stage_total
        label = message or self.stage_name
        elapsed = time.monotonic() - self._stage_t0 if self._stage_t0 else 0.0
        self._finish_line(label, elapsed)
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
        print(f"  · {message}", flush=True)

    def wait_futures(self, futs_map, label: str = "平行構建中") -> list:
        from concurrent.futures import as_completed
        return [(fut, futs_map[fut]) for fut in as_completed(futs_map)]

    def done(self, message: str = "完成") -> None:
        if self._stage_open:
            self.end_stage()
        if self.overall_total > 0:
            self.overall_current = self.overall_total
            self.current = self.overall_current
        bar, pct = self._bar(self.overall_current, self.overall_total)
        ot = max(self.overall_total, 1)
        oc = min(self.overall_current, ot)
        total_elapsed = self._fmt_sec(time.monotonic() - self._run_t0)
        text = (message or "完成").rstrip()
        if not text.endswith("完成"):
            text = f"{text} 完成"
        print(f"[{bar}] {pct:3d}% 總進度 ({oc}/{ot}) {text} ({total_elapsed})", flush=True)
        self._finished = True

    def _bar(self, cur: int, total: int) -> tuple[str, int]:
        total = max(total, 1)
        cur = min(max(cur, 0), total)
        filled = int(self._width * cur / total)
        bar = "█" * filled + "░" * (self._width - filled)
        return bar, int(100 * cur / total)

    def _render_live(self, *, force: bool, label: str | None = None) -> None:
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
        sys.stdout.write("\r" + f"[{bar}] {pct:3d}% ({sc}/{st}) {name}".ljust(96))
        sys.stdout.flush()
        self._live = True

    def _finish_line(self, label: str, elapsed: float = 0.0) -> None:
        st = max(self.stage_total, 1)
        bar, pct = self._bar(st, st)
        text = (label or "").rstrip()
        if not text.endswith("完成"):
            text = f"{text} 完成".strip()
        line = f"[{bar}] {pct:3d}% ({st}/{st}) {text} ({self._fmt_sec(elapsed)})"
        if self._live:
            sys.stdout.write("\r" + line + "\n")
        else:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        self._live = False


BuildProgress = Progress
