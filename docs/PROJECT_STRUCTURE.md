# Project Structure

DBOZero 採用「核心程式、翻譯資料、文件、測試、維護腳本」分層，避免日常漢化資料與程式實作互相混雜。

## 目錄

```text
DBOZero/
├── .github/                  # GitHub Actions / CI
├── data/                     # 翻譯主表、佇列、delta 與本機資料說明
│   ├── archive/              # 歷史資料
│   ├── client_local/         # 本機 client-local 工作區說明
│   ├── deltas/               # 增量翻譯資料
│   └── 舊譯表/                # 舊版翻譯參考資料
├── docs/                     # 專案設計、流程與格式文件
├── hanhua_v3/                # 核心 Python 套件
│   └── runtime/              # 執行期元件
├── legacy/                   # 舊版實作與相容資料
├── reports/                  # 掃描、翻譯與驗證報告
├── scripts/                  # 維護、合併與一次性工具
├── tests/                    # 自動化測試與測試資料
├── build_output.py           # 建置入口／相容入口
├── scan_all_text.py          # 完整文字掃描入口
├── pyproject.toml            # Python 專案與 CLI 設定
├── README.md                 # 專案首頁
├── CONTRIBUTING.md           # 貢獻指南
├── CHANGELOG.md              # 版本變更紀錄
└── LICENSE                   # 授權
```

## 資料流

```text
原版遊戲資源
      │
      ▼
   src_file/
      │
      ▼
 scanner / dboc scan
      │
      ▼
 data/new_translations.tsv
      │
      ▼
 translation data
      │
      ▼
 dboc build / build_output
      │
      ├── output_taiwan/
      └── output_simplified/
```

`src_file/`、`output*` 與完整遊戲資源屬於本機工作資料，不應提交至 `main`。

## 分層原則

### `hanhua_v3/`

只放可重複使用的核心程式碼。資源掃描、翻譯處理、建置、驗證與 runtime 元件應優先在此實作。

### `data/`

放翻譯資料與資料處理所需的參考檔。大型歷史資料或舊譯表應與日常主表分開，避免誤修改。

### `scripts/`

放維護與一次性工具。若功能已成為正式 CLI 流程，應逐步移入 `hanhua_v3/`。

### `tests/`

只驗證工具鏈、編碼、資源結構、翻譯寫入與建置邏輯；不以遊戲內啟動或遊戲內結果作為必要測試條件。

### `docs/`

記錄格式、流程、翻譯規則與開發決策，讓程式碼與資料的用途可以被獨立理解。
