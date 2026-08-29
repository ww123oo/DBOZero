# data/archive/ — 歷史增量歸檔

此目錄用來放**已合併進 `new_translations.tsv` 的 delta**，避免 `data/` 根目錄上百個 `tbl_batch*_delta.tsv`。

建議結構（由 `scripts/organize_data.ps1` 建立）：

```text
archive/
├── batches/      tbl_batch*_delta.tsv
├── term_fixes/   term_* / place_* / lang0_s2t* / length_*
├── ui_deltas/    ui_*_delta.tsv
└── misc/         translations_to_merge、merge_parts 等
```

`merge_translations.py` 仍會讀取 `archive/**/*_delta.tsv`（若存在），因此歸檔後不必刪檔也可再合併一次。
