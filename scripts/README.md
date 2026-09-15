# scripts/

維護與一次性修復腳本。日常漢化流程以 **`dboc`** / **`build_output.py`** 為主，不必執行本目錄全部檔案。

## 建議保留／常用

| 腳本 | 用途 |
|------|------|
| `apply_tw_main_table.py` | 主表台灣用字修正（OpenCC／詞彙） |
| `merge_translations.py` | 合併翻譯片段 |
| `consolidate_deltas.py` | 整理 delta 到 `data/deltas/` |
| `fix_sc_residues.py` | 簡體殘留批次修正 |
| `fix_lang0_length_ids.py` | 列出／處理 lang0 超長 ID |

## 建置進度條（可選）

| 腳本 | 用途 |
|------|------|
| `apply_build_progress.py` | 將進度列接進本機 build |
| `install_real_progress.py` | 安裝進度相關檔 |

進度顯示實作於 `hanhua_v3/runtime/build_progress.py`（使用 `chr(13)` 歸位，避免字面 `\r`）。

## 歷史／一次性

`fix_*.py`、`bo_pay_*.txt`、`build_output_p*.b64`、`assemble_*.py` 等為過去批次修復或 bootstrap 產物。**新環境請優先使用倉庫內完整的 `build_output.py`**，無需再組裝 b64 碎片。

若需清理本機，可只保留上表「常用」與文件，其餘移入私有備份即可；刪除前請確認沒有未合併的譯文依賴。

## 原則

1. 改翻譯資料 → 優先改 `data/new_translations.tsv`，再 `dboc build --force`。  
2. 不要把遊戲 `.pak` / 完整 `src_file` 經 scripts 提交進庫。  
3. 新增腳本請寫簡短模組說明與範例命令。
