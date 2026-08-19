# legacy/：歷史歸檔（非正式流程）

此目錄保留 **v3 之前** 的工具殘件與歷史譯文，供掃描時當「建議來源」或遷移參考。

> **重要**  
> - 這裡的歷史大檔**可能不完整**，也可能有**錯別字、過期譯法**。  
> - **不要**把本目錄當日常翻譯入口。  
> - 正式、可維護的譯文只在倉庫根目錄的 `data/*.tsv`。

## 目錄說明

| 路徑 | 用途 | 備註 |
|------|------|------|
| `tools/` | 舊腳本相容墊片 | 真正邏輯在 `hanhua_v3/runtime/` |
| `translations/` | 舊手工 override TSV | 掃描可能讀取 |
| `candidates/` | 舊候選／匯出 TSV | 掃描可能當建議；體積較大 |
| `reports/` | 舊稽核／備份 TSV | **刻意完整保留當考古資料**；可能有錯字或過期內容 |
| `docs/` | 舊筆記 | 僅供考古 |
| `assets/testpng/` | 舊測試截圖 | 不參與構建；可忽略 |

## 和 v3 的關係

- `hanhua_v3/scan.py` 可能讀取 `legacy/translations/*`、`legacy/candidates/*`，用來產生「建議譯文」。  
- 建議**不會**自動覆蓋你在 `data/new_translations.tsv` 已填的內容。  
- 若某條 legacy 建議明顯錯誤，請在 `data/` 手填正確譯文並 `dboc build`，不必改 legacy 大檔。

日常請使用根目錄 [README.md](../README.md) 與 [docs/faq.md](../docs/faq.md)。
