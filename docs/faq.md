# 常見問題（FAQ）

第一次使用請先看根目錄 [README.md](../README.md) 的「新手快速開始」。

---

## 安裝與環境

### `pip` 或 `dboc` 不是內部或外部命令

- 重裝 [Python 3.9+](https://www.python.org/downloads/)，安裝時勾選 **Add Python to PATH**。
- 或改用：

```powershell
python -m pip install -e .
python -m hanhua_v3 --help
```

### 一定要用 `pip install -e .` 嗎？

**是。** 工具以「倉庫根目錄」當工作區（`data/`、`src_file/`、`output/` 都相對根目錄）。  
不要只用 `pip install .`（沒有 `-e`），否則路徑會找錯。

### 支援哪些系統？

- **建議 Windows**：遊戲是 Windows 版，繁中轉碼也依賴 Windows 環境較完整。
- macOS／Linux 可跑多數 Python 流程，但實際進遊戲驗證仍需 Windows。

### Python 版本？

需要 **3.9 或更高**。用 `python --version` 確認。

---

## 遊戲目錄與源檔

### `找不到遊戲目錄` / `缺少必要源檔案`

- `--game-dir` 可指到：
  - 遊戲根目錄（內含 `DBOZero` 資料夾），或
  - 直接指到 `...\DBOZero`
- 路徑有空格請加引號，例如：

```powershell
dboc config --game-dir "E:\DBO Zero 2.0"
```

- 確認目錄內有 `pack\lang0.pak`。

### `疑似已打補丁` / 拒絕同步

工具發現遊戲檔已和漢化產出一樣，為避免把「已漢化檔」當原版同步進來而拒絕。

**作法：** 用遊戲啟動器做**檔案校驗／修復**，還原官方原版後再：

```powershell
dboc update
```

### 正確的更新順序是什麼？

1. 遊戲更新／修復成**官方原版**  
2. `dboc update`  
3. 再把 `output_taiwan`（或 `output`）覆蓋回遊戲  

**不要**帶著舊漢化去 `refresh`／`update`。

---

## 構建與套用補丁

### 構建成功後補丁在哪？

| 版本 | 目錄 |
|------|------|
| 台灣繁中 | `output_taiwan\DBOZero` |
| 大陸簡中 | `output\DBOZero` |

把對應目錄內容覆蓋到遊戲的 `DBOZero`（先備份）。

### 工具會不會自動改我的遊戲檔？

**不會。** CLI 只讀遊戲目錄；寫入的是倉庫內的 `src_file/`、`output/`、`output_taiwan/`。  
套用補丁要你自己複製覆蓋。

### 為什麼沒有 Release？

遊戲常更新，補丁需反覆實測。穩定前請自行 `dboc build`／`dboc update` 產生。有正式包時會放在 [Releases](https://github.com/ww123oo/DBOZero/releases)。

### 構建很慢或失敗？

- 確認已 `pip install -e .` 且在倉庫根目錄執行。
- 先 `dboc status` 看源是否齊。
- 可試：`dboc build --force`（強制重建）。
- 開發檢查：

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
```

---

## 翻譯與用字

### 我要改哪個檔、哪一欄？

| 目的 | 檔案 | 只改這一欄 |
|------|------|------------|
| 新詞 | `data/new_translations.tsv` | `填写中文`（表頭原文如此） |
| 改舊譯 | `data/translations.tsv` | `zh_cn` |

改完執行 `dboc build`。詳見 [translation-rules.md](translation-rules.md)。

### 遊戲裡還是簡體、或用字不對（例如「賬號」）？

1. 確認覆蓋的是 **`output_taiwan`**（繁中），不是 `output`（簡中）。  
2. 繁中會再套用台灣用字表；可在  
   `hanhua_v3/runtime/taiwan_fixups.py` 的 `TAIWAN_SIMPLIFY_FIXUPS` 追加：

```python
("帳號", "账号"),
```

長詞放前面，改完再 `dboc build`。

### `legacy/` 裡的舊翻譯可以當準嗎？

**僅供參考。** 歷史匯出可能不完整、有錯別字或過期譯法。  
正式以 `data/*.tsv` 為準；掃描時 legacy 只當「建議來源」，不會自動覆寫你手填的內容。

---

## 其他

### clone 很大？

主要來自 `data/` 與 `legacy/candidates/` 歷史表。  
`legacy/reports/` 刻意完整保留當考古資料；`legacy/assets/testpng/` 為舊測試圖、不參與構建。  
`legacy/candidates` 仍可能被掃描當建議，故保留。

### 想貢獻翻譯或修工具？

見 [CONTRIBUTING.md](../CONTRIBUTING.md)。
