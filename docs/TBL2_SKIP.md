# tbl2.pak 結構化寫入／排錯備註

這份文件原本是 `tbl2.pak` 暫停漢化期間的緊急備註。現在 canonical build pipeline 已提供 `tbl2.pak` 的結構化 stable-ID 寫入與 deterministic resource validation，因此「預設永久跳過 tbl2」不再是目前建置流程的規則。

## 目前規則

`tbl2.pak` 翻譯項目必須具備穩定 ID（例如 `id:123456`），並通過結構與固定欄位驗證。

禁止使用全域 UTF-16 字串取代，也禁止在定位失敗時猜 offset。翻譯超過原固定欄位時直接 fail-closed，不繼續輸出該修改。

建置流程會檢查：

- 資源檔案樹是否與原始 source 一致
- PAK 檔案大小是否維持不變
- `tbl2` record 的 ID、type、長度與 UTF-16LE 欄位是否一致
- 寫入後的固定欄位內容是否與翻譯佇列一致

這些都是工具／資源格式檢查，不包含遊戲內測試要求。

## 遇到 tbl2 問題時

請保留官方原版 `pack/tbl2.pak`，不要拿已產生的補丁檔反過來當 `dboc refresh` 的 source。

可以先單獨比較：

```powershell
fc /b "（原版）\DBOZero\pack\tbl2.pak" "（遊戲）\DBOZero\pack\tbl2.pak"
```

再檢查建置輸出的檔案大小與 validator 結果。若問題集中在特定詞條，優先移除該詞條、縮短譯文或重新掃描取得新的 stable ID，不要手動修改二進位 offset。

## 歷史急救方式

若你需要先恢復原版 `tbl2.pak`，可直接用官方原檔覆蓋：

```powershell
Copy-Item "（原版）\DBOZero\pack\tbl2.pak" "（遊戲）\DBOZero\pack\tbl2.pak" -Force
```

恢復原版後，再從乾淨 source 重新執行 `dboc scan` → `dboc translate` → `dboc build`。
