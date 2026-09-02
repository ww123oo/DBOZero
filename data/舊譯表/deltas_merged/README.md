# deltas_merged

歷史 `*_delta.tsv` 合併去重後的參考表，**不參與 build**。

| 檔案 | 說明 | 約略筆數 |
|------|------|----------|
| `term.tsv` / `term.tsv.gz.b64` | 術語／道具 | ~190 |
| `ui.tsv` / `ui.tsv.gz.b64` | UI／lang0 | ~385 |
| `tbl.tsv` | tbl 內文 | ~8670 |
| `all_deltas.tsv` | 三者合併 | ~9110 |

## 解壓

```powershell
cd data\舊譯表\deltas_merged
python expand.py
```

會從 `*.tsv.gz.b64`（及分片）寫出明文 `.tsv`。

欄位：`原文` TAB `填写中文`

要採用時再併入 `data/new_translations.tsv`（先 diff，避免覆蓋已校對繁中）。
