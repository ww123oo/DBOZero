# data/

## 乾淨結構（整理後）

```text
data/
├── new_translations.tsv   ★ 主表
├── translations.tsv       ★ 舊譯
├── gui_font.ini
├── README.md
├── deltas/                ★ 增量（只有下面 3 個）
│   ├── term.tsv
│   ├── ui.tsv
│   └── tbl.tsv
└── archive/
    └── legacy_deltas/     舊的上百個 tbl_batch*_delta.tsv（可查、可刪）
```

## 一鍵整理（把散落的 delta 合成 3 個檔）

```powershell
python scripts\consolidate_deltas.py
git add -A data scripts
git commit -m "chore: consolidate deltas into data/deltas/"
git push
```

## 合併進主表

```powershell
python scripts\merge_translations.py
python scripts\fix_tbl_overlong.py
python scripts\fix_lang0_length_ids.py
dboc build --variant taiwan
```
