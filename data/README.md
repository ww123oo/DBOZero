# data/ — 翻譯資料

日常**只需要關心這兩個主表**：

| 檔案 | 用途 |
|------|------|
| **`new_translations.tsv`** | 新詞／佇列主表（填 `填写中文`） |
| **`translations.tsv`** | 舊譯主表（改 `zh_cn`） |

其餘多半是歷史 delta 或一次修正用，**合併進主表後不必再手動編輯**。

---

## 建議目錄概念

```text
data/
├── new_translations.tsv      ★ 主表（必改）
├── translations.tsv          ★ 舊譯（必改）
├── gui_font.ini              字型相關設定
├── README.md                 本說明
│
├── *_delta.tsv               歷史增量（已併入主表後可歸檔）
├── tbl_batch*_delta.tsv      批次翻譯增量（同上）
├── merge_parts/              大檔分段輔助（考古）
└── tbl_batch3_chunks/        舊分段（考古）
```

歸檔建議（本機執行，見 `scripts/organize_data.ps1`）：

```text
data/archive/
├── batches/     ← tbl_batch*_delta.tsv
├── term_fixes/  ← term_* / place_* / length_* / lang0_s2t*
└── ui_deltas/   ← ui_*_delta.tsv
```

`scripts/merge_translations.py` 會用 glob 讀取仍留在 `data/` 下的 `*_delta.tsv`（含子目錄時請改腳本路徑）。

---

## 合併流程

```powershell
python scripts\merge_translations.py   # 把 delta 寫進 new_translations.tsv
python scripts\apply_s2t_quick.py      # 簡→繁殘留
python scripts\fix_kaili.py           # 凱裡→凱里
python scripts\fix_lang0_length_ids.py # lang0 長度鎖定
dboc build --variant taiwan
```

---

## 完成度（約）

| 來源 | 狀態 |
|------|------|
| UI lang0 | ≈98%（剩格式字串可維持英文） |
| tbl0 | ≈98%（剩內部代號） |
| tbl1 | MOB 內部名已補 |
| tbl2 | ≈100% 可讀內容 |
