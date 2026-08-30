# data/ — 翻譯資料

## 主表（必保留）

| 檔案 | 用途 |
|------|------|
| **`new_translations.tsv`** | 主表（填 `填写中文`） |
| **`translations.tsv`** | 舊譯 |

穩定可玩基準：**merge 前** `ee96361` 的主表。  
`fa7d471` 整批 merge 曾導致 tbl2 超長閃退。

## delta 要不要寫進主表？

**要，但不要一次無檢查硬併。**

所有 `tbl_batch*_delta.tsv` **翻譯內容可留著**，它們是增量稿：

```text
tbl_batch_delta.tsv
tbl_batch2_delta.tsv … tbl_batch106_delta.tsv
```

### 合併順序（腳本已處理）

1. 一般 `*_delta.tsv`（term／ui／place…）
2. `tbl_batch_delta.tsv`
3. `tbl_batch2` → `tbl_batch106`（**數字由小到大**；同英文後面覆蓋前面）
4. 若有 `data/archive/**` 也會讀

### 安全合併（推薦）

主表先用能玩的 `ee96361`，再：

```powershell
python scripts\merge_translations.py
# 只寫入「中文字節 ≤ 英文原文」的 tbl 譯文；超長自動跳過
python scripts\fix_tbl_overlong.py   # 雙保險
dboc build --variant taiwan
```

這樣 **delta 不用刪**，能進主表的會進去，超長的留在 delta 裡以後再縮短。
