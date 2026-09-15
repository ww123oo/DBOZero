# -*- coding: utf-8 -*-
"""Placeholder until the full StageProgress build_output is pushed.

The full file (~52KB, with begin_stage progress bars + id:N tbl locator) is too large
for some automated uploads. Restore it from your artifacts sync folder, then push:

  Copy-Item "<artifacts>\\build_output_PROGRESS_52k.py" .\\build_output.py -Force
  # or build_output.py from the same folder if size ~52000

  (Get-Item .\\build_output.py).Length   # must be ~52000
  Select-String -Path .\\build_output.py -Pattern "begin_stage"

  git add build_output.py
  git commit -m "feat: StageProgress build_output"
  git push origin main

After that, dboc build shows:
  [████] 100% (1/1) 讀取翻譯表 完成 (...)
"""
raise SystemExit(
    "build_output.py is a placeholder.\n"
    "Copy artifacts/build_output_PROGRESS_52k.py over this file (~52KB), then:\n"
    "  git add build_output.py && git commit -m \"feat: StageProgress build_output\" && git push\n"
)
