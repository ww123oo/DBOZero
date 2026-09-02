# data/

日常翻譯**只改**這兩個檔：

| 檔案 | 用途 |
|------|------|
| `new_translations.tsv` | 主表：填 `填写中文` |
| `translations.tsv` | 舊譯：改 `zh_cn` |

其他：

| 路徑 | 說明 |
|------|------|
| `gui_font.ini` | GUI 字型設定 |
| `deltas/` | 少量現行增量（可選） |
| `舊譯表/` | 歷史合併 delta、台服原版對照（**不參與 build**） |
| `archive/` | 已歸檔的舊 `*_delta.tsv`（勿當日常來源） |
| `client_local/` | client 本機相關說明／佔位 |

**根目錄不要再堆 `tbl_batch*_delta.tsv` / `ui_*_delta.tsv`。**  
歷史內容已合併到 `舊譯表/deltas_merged/`，需要時再採用。

```powershell
dboc build --variant taiwan
```
