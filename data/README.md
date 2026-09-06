# data/

## 日常翻譯請記住一件事

**日常新增翻譯，以及遊戲更新後掃出的新文字，主要都進 `new_translations.tsv`。**

你不需要先搞懂整個舊翻譯系統。對一般日常維護來說，可以把它理解成：

```text
遊戲更新 / 掃描
      ↓
發現新文字
      ↓
new_translations.tsv
      ↓
填寫中文翻譯
      ↓
建置
      ↓
遊戲測試
```

### `new_translations.tsv`

這是目前日常新增翻譯的主要工作表。

- 新掃到、以前沒有處理過的文字 → 放這裡
- AI 協助整理的新翻譯 → 放這裡
- 人工確認後的繁中翻譯 → 在這裡維護
- 遊戲更新後再次掃描 → 仍然以這裡作為日常翻譯入口

### `translations.tsv`

這是原作者留下的重要舊翻譯資料。

它仍然有價值，但**不要把它當成目前遊戲的完整翻譯清單，也不要把日常新增內容只塞回這裡**。

主要用途：

- 查找原作者以前翻好的內容
- 繼承歷史譯名
- 避免重複翻譯
- 作為新翻譯的參考
- 與掃描結果比對

### 掃描結果

完整掃描器會從實際遊戲資源建立最新文字索引。掃描範圍包括：

```text
lang0.pak
tbl0.pak
tbl1.pak
tbl2.pak
*.rdf
*.xml
*.dat
```

**不掃描 `.bin`。**

掃描後建議使用：

```powershell
python scan_all_text.py "src_file\DBOZero" -o translation_scan.tsv
python -m hanhua_v3.runtime.translation_queue translation_scan.tsv
```

如果確認要把新發現直接加入日常工作表：

```powershell
python -m hanhua_v3.runtime.translation_queue translation_scan.tsv --sync-daily
```

這個同步只會新增目前不存在的候選，不會用掃描結果覆蓋已經有中文翻譯或已確認狀態的人工資料。

掃描候選報告預設產生：

```text
reports/internal/untranslated_candidates.tsv
```

這個檔案是「待處理候選清單」，**不是遊戲資源，也不會直接修改遊戲檔案**。

## 其他資料

| 路徑 | 用途 |
|------|------|
| `gui_font.ini` | GUI 字型設定 |
| `deltas/` | 少量現行增量（可選） |
| `舊譯表/` | 歷史合併 delta、台服原版對照（不參與日常 build） |
| `archive/` | 已歸檔的舊 `*_delta.tsv`（勿當日常來源） |
| `client_local/` | client 本機相關說明／佔位 |

**根目錄不要再堆 `tbl_batch*_delta.tsv` / `ui_*_delta.tsv`。**

歷史內容已合併到 `舊譯表/deltas_merged/`，需要時再採用。

## 建置

台灣繁中：

```powershell
dboc build --variant taiwan
```

全部版本：

```powershell
dboc build
```
