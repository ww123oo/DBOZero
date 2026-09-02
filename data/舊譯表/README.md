# 舊譯表（參考用，可再採用）

此目錄**不參與日常 build**。需要時可手動把用詞併回 `data/new_translations.tsv`。

## 台服原版/

台服官方 `local_data` / `local_sync_data` 備份，**僅供對照用詞**。

- 檔案為 UTF-16（與 client 一致）
- **不可**整份覆蓋私服 dat（私服 KEY 會不同）
- 校對時：共有 KEY 可對照此處改用詞

來源：使用者提供的台服原版 [2026-09-02]

## deltas_merged/

把歷史散落的 `data/*_delta.tsv`、`tbl_batch*_delta.tsv` 等**合併去重**後的結果，之後可採用。

| 檔案 | 說明 | 約略筆數 |
|------|------|----------|
| `term.tsv` | 術語／道具名等 | ~190 |
| `ui.tsv` | UI／lang0 相關 | ~385 |
| `tbl.tsv` | tbl 表內文 | ~8670 |
| `all_deltas.tsv` | 上述三者合併（同 key 後寫覆蓋） | ~9110 |

欄位：`原文`（TAB）`填写中文`

### 如何採用（範例）

```powershell
# 只採用 term
python scripts\merge_translations.py   # 若腳本支援指定 delta 路徑，改指到此目錄
# 或手動把需要的列貼進 data/new_translations.tsv 後再 build
```

**注意：** 這些是歷史增量紀錄，多數已併入主表 `new_translations.tsv`。重新採用前請先 diff，避免覆蓋已校對過的繁中。
