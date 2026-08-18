# src_file：源快照目錄

本目錄存放從本機遊戲**只讀同步**過來的原始資源，作為掃描與構建的輸入。  
遊戲資源受版權保護，**不得提交到 Git**（已由 `.gitignore` 排除）。

## 需要的檔案

相對路徑 `src_file/DBOZero/`：

```text
localize/Taiwan/language/local_data.dat
localize/Taiwan/language/local_sync_data.dat
localize/Taiwan/language/table_quest_text_data.rdf
localize/Taiwan/language/table_text_all_data.rdf
pack/gui0.pak
pack/lang0.pak
pack/tbl0.pak
pack/tbl1.pak
pack/tbl2.pak
```

## 如何取得

設定好遊戲目錄後執行：

```powershell
dboc refresh
# 或
dboc update
```

CLI 只會讀取上述檔案並複製到此處，不會寫入遊戲目錄，也不會複製帳號、日誌、執行檔或更新快取。

也可手動依上述相對路徑複製進來，再執行 `dboc scan` / `dboc build`。

## 注意

- 遊戲目錄必須是**官方原版**。若已套用漢化補丁，請先用啟動器修復後再 refresh。
- 建議順序：遊戲更新 → `dboc update` → 再把新補丁覆蓋回遊戲。
