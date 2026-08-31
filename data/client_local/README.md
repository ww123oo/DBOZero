# client_local

客戶端本機字串檔（台灣繁體已處理）。

## 目前取得方式

**請從 Grok 專案 artifacts 下載：**

- `client_local_tw.zip`（內含兩個 dat + 4 筆 UI delta）
- 或直接下載 `local_data.dat`、`local_sync_data.dat`

覆蓋到遊戲客戶端對應路徑後測試。

與 `dboc build --variant taiwan` 的 lang0/tbl 流程分開。

## 4 筆 UI 簡體修正 delta

見 repo：
- `data/ui_fix_4simp_delta.tsv`
- `data/ui_fix_4simp_by_id.tsv`

可 merge 進 `data/new_translations.tsv` 後 rebuild。
