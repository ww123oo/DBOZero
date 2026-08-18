# 日常翻譯小清單（給已會構建的人）

第一次使用請先看根目錄 [README.md](../README.md) 的「新手快速開始」。

## 1. 補新內容

開啟：`data/new_translations.tsv`

**只填這一欄（表頭原文如此，請勿改名）：**

- `填写中文`

其他欄只供參考。  
`ok` = 長度大致可用；`untranslated` = 尚未填；`too_long` = 可能放不進固定長度欄位。

TBL 列很多，建議用試算表依「来源」「文件」或關鍵字篩選後再填。

## 2. 改舊翻譯

開啟：`data/translations.tsv`

**只改：** `zh_cn`

## 3. 產生補丁

```powershell
dboc build
```

- 簡中 → `output/DBOZero`
- 繁中 → `output_taiwan/DBOZero`

**不要**把 `src_file`、`data`、`legacy`、`reports` 整包發給玩家。

## 4. 套用到遊戲

覆蓋前先備份，再把對應 `DBOZero` 內容複製到遊戲的 `DBOZero`。

## 5. 檢查產物是否存在

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

## 6. 其他

- `reports/internal/`：工具內部產物，平時不用看。
- 繁中用字：`hanhua_v3/runtime/install_hanhua.py` 的 `TAIWAN_SIMPLIFY_FIXUPS`。
- 詳細規則：`docs/translation-rules.md`。
