# data/archive/

已歸檔的歷史增量（`tbl_batch*_delta.tsv` 等）。

**日常翻譯只改：**

- `data/new_translations.tsv`
- `data/translations.tsv`

歷史合併結果在 `data/舊譯表/deltas_merged/`，需要時再採用。
勿把本目錄當現行來源重套。

一鍵整理（本機）：

```powershell
python scripts\consolidate_deltas.py
git add -A data
git commit -m "chore: archive legacy deltas, clean data/ root"
git push
```
