# scripts/

開發／一次性修補腳本。**一般使用者不必執行這裡的任何檔案。**

## 日常請用

```text
dboc build --variant taiwan
dboc update
```

## 目錄說明

| 路徑 | 用途 |
|------|------|
| `merge_translations.py` | 合併翻譯片段 |
| `organize_data.ps1` | 本機整理 data 目錄 |
| `assemble_build_output.py` | 從 chunks 組回完整 `build_output.py`（開發用） |
| 其餘 `fix_*.py` / `apply_*.py` | 歷史一次性修補（已合併進主表者勿重跑） |

歷史腳本若需保留，可移到 `scripts/archive/`，不要當成現行流程。
