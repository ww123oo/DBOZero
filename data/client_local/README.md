# client_local

客戶端本機字串檔（台灣繁體已處理）。

- `local_data.dat` — UI / 系統字串（DST_*）
- `local_sync_data.dat` — 同步／錯誤訊息（GAME_* / AUTH_* 等）

請依你的客戶端路徑覆蓋對應檔案後測試。
與 `dboc build --variant taiwan` 的 lang0/tbl 流程分開，這兩份是獨立的 local 檔。
