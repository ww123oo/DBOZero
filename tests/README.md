# tests

DBOZero 的自動化測試目錄。

## 測試範圍

測試只驗證工具鏈本身與資源格式處理，不要求啟動遊戲或進行遊戲內驗證。

預計依資源類型分組：

```text
tests/
├── fixtures/
│   ├── lang0/
│   ├── tbl0/
│   ├── tbl1/
│   └── tbl2/
├── test_scanner.py
├── test_translation.py
├── test_lang0.py
├── test_tbl0.py
├── test_tbl1.py
├── test_tbl2.py
└── test_validator.py
```

## 測試原則

- 使用最小化、可重現的測試資料。
- 不依賴使用者本機遊戲目錄。
- 不把遊戲原始資源提交到 Git。
- 對固定長度欄位、編碼、ID、offset、邊界等結構進行驗證。
- 驗證失敗時應明確失敗，不產生看似成功的資源檔。

## 執行

```powershell
pytest -q
```
