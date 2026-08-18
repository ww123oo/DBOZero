# 日常翻譯工作說明

平時只需要關心下面兩個檔案與一次構建命令。

## 1. 補新內容

開啟：`data/new_translations.tsv`

**只填這一欄：**

- `填寫中文`

其他欄僅供參考（來源、檔案、位置、原文、參考譯文、長度狀態）。  
`ok` = 長度可用；`untranslated` = 尚未填；`too_long` = 可能放不進固定長度欄位。

TBL 列很多，建議依「來源」「檔案」或關鍵字篩選後再填。

## 2. 改舊翻譯

開啟：`data/translations.tsv`

**只改這一欄：**

- `zh_cn`

## 3. 產生補丁

```powershell
dboc build
```

- 簡中：打包 `output/`
- 繁中：打包 `output_taiwan/`

**不要**把 `src_file`、`data`、`legacy`、`reports` 一起發出。

## 4. 檢查產物

至少確認這些檔案存在：

```text
output/DBOZero/localize/Taiwan/language/local_data.dat
output/DBOZero/pack/lang0.pak
output/DBOZero/pack/tbl0.pak
output/DBOZero/pack/tbl1.pak
output_taiwan/DBOZero/localize/Taiwan/language/local_data.dat
output_taiwan/DBOZero/pack/lang0.pak
output_taiwan/DBOZero/pack/tbl0.pak
output_taiwan/DBOZero/pack/tbl1.pak
```

`dboc build` 只讀 `src_file/DBOZero`，不會動真實遊戲目錄。

## 5. 其他

`reports/internal/` 是工具內部產物，平時不用看。  
繁中用字修正見 `hanhua_v3/runtime/install_hanhua.py` 的 `TAIWAN_SIMPLIFY_FIXUPS`。
