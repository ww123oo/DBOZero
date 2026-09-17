# DBOZero

Dragon Ball Online（DBO Zero）**繁體中文（台灣）／簡體中文**漢化工具鏈。

以實際遊戲資源為 source of truth：掃描 → 翻譯佇列 → 安全寫入 → 雙語建置與格式驗證。  
不修改遊戲程式、不寫入系統登錄檔；**本倉庫不提供遊戲本體或可散布的遊戲資源**。

![CI](https://github.com/ww123oo/DBOZero/actions/workflows/ci.yml/badge.svg)

| 項目 | 說明 |
|------|------|
| 版本 | **v3.0.0**（工具鏈基準，非「全文已翻完」宣告） |
| 授權 | 見 [LICENSE](LICENSE) |
| 需求 | Windows、Python 3.9+、Git、自備合法原版遊戲資源 |

---

## 快速開始

```powershell
git clone https://github.com/ww123oo/DBOZero.git
cd DBOZero
pip install -e .

dboc config --game-dir "G:\DBO Zero 2.0\DBOZero"
dboc config --show

dboc refresh
dboc scan
dboc translate --fill-all
dboc build --variant taiwan --force
```

產物目錄：`output_taiwan/DBOZero/`。覆蓋遊戲前請自行備份原版 `pack` 與 `localize/Taiwan`。

雙語建置：

```powershell
dboc build --variant all --force
```

正式 Release Gate：

```powershell
dboc release --force
```

---

## 架構（一句話）

```text
原版資源 (src_file)
        ↓
全面掃描器
        ↓
translation queue / data/new_translations.tsv
        ↓
翻譯與術語正規化
        ↓
dboc build / build_output.py
        ↓
resource_writer
        ↓
resource_validator
        ↓
output / output_taiwan（勿提交）
```

| 資料 | 角色 |
|------|------|
| `data/new_translations.tsv` | **日常工作表**：新增與維護譯文 |
| `data/translations.tsv` | **歷史參考**：原作者舊譯，不作完整清單 |
| `src_file/DBOZero/` | 本機遊戲快照（`.gitignore`，勿進 main） |
| `output*` / `release/` | 建置產物（勿提交） |

詳見 [data/README.md](data/README.md) 與 [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)。

---

## 掃描與寫入範圍

| 類型 | 目前處理方式 |
|------|------|
| `lang0.pak` | key 導向掃描、依原檔 UTF-8/GBK 判定、固定欄位寫入 |
| `tbl0.pak` / `tbl1.pak` | UTF-16LE 固定欄位、offset 導向寫入 |
| `tbl2.pak` | 結構化記錄掃描、穩定 ID 導向、UTF-16LE 固定欄位 |
| 其他 `.pak` | 泛用固定寬度文字欄位；UTF-16 可自動 NUL 補齊，其他編碼要求 byte 數相同 |
| `*.rdf` / `*.xml` | 文字屬性／元素內容掃描、offset 導向寫入 |
| `*.dat` | 結構化 key/value 掃描與字串寫入 |
| 排除 | `.bin` 等非翻譯二進位 |

`lang0` 譯文編碼後不可超過原欄位。`tbl0/tbl1/tbl2` 與泛用 PAK 固定欄位不得擴張檔案大小；`tbl2` 必須使用穩定 ID／邊界驗證，禁止盲目全檔字串取代。

---

## 常用指令

| 指令 | 用途 |
|------|------|
| `dboc config --game-dir …` | 儲存遊戲目錄（寫入本機 `dboc.toml`） |
| `dboc refresh` | 從遊戲同步原版資源到 `src_file` |
| `dboc scan` | 掃描並更新翻譯佇列 |
| `dboc translate --fill-all` | 填入可從既有譯表複用的譯文 |
| `dboc build --variant taiwan --force` | 建置台灣繁中 |
| `dboc build --variant simplified --force` | 建置簡體中文 |
| `dboc build --variant all --force` | 依序建置雙語產品 |
| `dboc release --force` | 雙語建置與格式驗證閘門 |
| `dboc status` | 佇列與源檔差異概況 |

---

## 倉庫結構

```text
DBOZero/
├── .github/          # GitHub Actions / CI
├── data/              # 翻譯資料、delta 與歷史參考
├── docs/              # 設計、流程、格式與專案結構文件
├── hanhua_v3/         # 核心 Python 套件與 runtime
├── legacy/            # 舊版實作與相容資料
├── reports/           # 掃描、翻譯與格式驗證報告
├── scripts/           # 維護、合併與一次性工具
├── tests/             # 自動化測試與測試資料
├── build_output.py    # canonical builder / 驗證入口
├── scan_all_text.py   # 完整文字掃描入口
├── pyproject.toml     # Python 專案與 CLI 設定
├── README.md          # 專案首頁
├── CONTRIBUTING.md    # 貢獻指南
├── CHANGELOG.md       # 變更紀錄
└── LICENSE            # 授權
```

完整結構與資料流請見 [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)。

分支：

| 分支 | 用途 |
|------|------|
| `main` | 程式、翻譯資料、測試、文件 |
| `reference-resources` | 大型參考資源（不塞進 main） |

---

## 台灣用字（摘要）

| 避免 | 採用 |
|------|------|
| 升級石 | 強化石 |
| 能量／氣功／氣力藥水 | 氣合藥水 |
| 稀有度 | 稀少度 |
| 升階（道具進階語境） | 進階 |
| 賬號 | 帳號 |

完整規則見 [docs/translation-rules.md](docs/translation-rules.md)。

---

## 開發

```powershell
pip install -e ".[dev]"
pytest -q
```

CI 會在 Windows / Linux × Python 3.9 / 3.12 執行 compile、unit tests 與 CLI smoke test。CI 綠燈代表程式與測試通過，**不代表** CI 持有完整遊戲資源或產出正式遊戲資源包。

---

## 注意事項

1. 僅使用你有權使用的原版遊戲檔；打過補丁的 `pack` 勿當 refresh 來源。  
2. 勿將 `src_file/`、`output*`、遊戲本體 commit 到 `main`。  
3. 固定欄位資源不允許任意擴張；超長譯文會 fail-closed。  
4. `tbl2.pak` 現在走結構化 stable-ID 寫入與 deterministic validation；若你的實際客戶端仍出現與 tbl2 相關的問題，請保留原版 `tbl2.pak` 作為獨立回復材料。  
5. 本專案與遊戲官方無關，為玩家社群維護之工具鏈。

---

## 相關文件

- [建置流程](docs/BUILD_PIPELINE.md)
- [TBL2 格式／排錯備註](docs/TBL2_SKIP.md)
- [專案結構](docs/PROJECT_STRUCTURE.md)
- [翻譯規則](docs/translation-rules.md)

---

## 相關連結

- Releases：https://github.com/ww123oo/DBOZero/releases  
- Issues：https://github.com/ww123oo/DBOZero/issues