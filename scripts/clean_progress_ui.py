# -*- coding: utf-8 -*-
"""One-shot: clean progress UI in build_output.py (remove 實際工作量 / · notes)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "build_output.py"
if not path.is_file():
    raise SystemExit(f"missing {path}")
text = path.read_text(encoding="utf-8")
orig = text

# drop work-unit note
text = text.replace(
    '        progress.note(f"實際工作量：lang0 {_lang0_n} 列 + tbl {_tbl_n} 單位 + 其他 {_fixed_n} 步")\n',
    "",
)
# drop per-pack notes
text = text.replace(
    '        progress.note(f"pack/lang0.pak：{_lang0_n} 列")\n',
    "",
)
text = text.replace(
    '        progress.note(f"pack/{file_name}: {len(rows)} 列")\n',
    "",
)
# no cp950 label prefix on every bar line
text = text.replace(
    "progress = _BuildProgress(0, label=ansi_encoding)",
    'progress = _BuildProgress(0, label="")',
)
# quieter step labels (keep stage name from begin_stage)
text = text.replace(
    'progress.step(f"lang0 {idx}/{n_rows}", n=1)',
    "progress.step(n=1)",
)
text = text.replace(
    'progress.step(f"pack/{file_name} (copy)", n=unit)',
    "progress.step(n=unit)",
)
text = text.replace(
    'progress.step(f"pack/{file_name} 完成", n=unit)',
    "progress.step(n=unit)",
)
text = text.replace(
    'progress.step(f"pack/{file_name} (略過)", n=unit)',
    "progress.step(n=unit)",
)
text = text.replace(
    'progress.step("pack/lang0.pak (略過)", n=max(_lang0_n, 1))',
    "progress.step(n=max(_lang0_n, 1))",
)

# insert 讀取翻譯表 once after set_total if missing
needle = "        progress.set_total(_fixed_n + _lang0_n + _tbl_n)\n"
insert = (
    needle
    + '        progress.begin_stage("讀取翻譯表", total=1)\n'
    + '        progress.step("讀取翻譯表", n=1)\n'
    + '        progress.end_stage("讀取翻譯表")\n'
)
if "讀取翻譯表" not in text and needle in text:
    text = text.replace(needle, insert, 1)

if text == orig:
    print("already clean or patterns not found")
else:
    path.write_text(text, encoding="utf-8")
    print(f"updated {path} ({len(orig)} -> {len(text)} bytes)")
print("done")
