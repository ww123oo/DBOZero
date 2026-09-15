# DBOZero

Dragon Ball Online（DBO Zero）**繁體中文（台灣）／簡體中文**漢化工具鏈。

以實際遊戲資源為 source of truth：掃描 → 翻譯佇列 → 安全寫入 → 雙語建置與驗證。  
不修改遊戲程式、不寫入系統登錄檔；**本倉庫不提供遊戲本體或可散布的遊戲資源**。

![CI](https://github.com/ww123oo/DBOZero/actions/workflows/ci.yml/badge.svg)

| 項目 | 說明 |
|------|------|
| 版本 | **v0.1.x**（工具鏈基準，非「全文已翻完」宣告） |
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
dboc build --variant taiwan --force
```

產物目錄：`output_taiwan/DBOZero/`。覆蓋遊戲前請自行備份原版 `pack` 與 `localize/Taiwan`。

```powershell
dboc release --force
```

---

## 架構（一句話）

```text
原版資源 (src_file) → scan / queue → data/new_translations.tsv
                                        ↓
                              build_output / dboc build
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

| 類型 | 檔案 |
|------|------|
| PAK | `lang0.pak`, `tbl0.pak`, `tbl1.pak`, `tbl2.pak` |
| 其他 | `*.rdf`, `*.xml`, `*.dat`（翻譯相關） |
| 排除 | `.bin` 等非翻譯二進位 |

`lang0` 為**固定欄位長度**：譯文編碼後不可超過原文 byte 數。  
`tbl2` 需穩定 ID／邊界驗證，禁止盲目全檔字串取代。

---

## 常用指令

| 指令 | 用途 |
|------|------|
| `dboc config --game-dir …` | 儲存遊戲目錄（寫入本機 `dboc.toml`） |
| `dboc refresh` | 從遊戲同步原版資源到 `src_file` |
| `dboc scan` | 掃描並更新翻譯佇列 |
| `dboc build --variant taiwan --force` | 強制建置繁中 |
| `dboc build --variant simplified --force` | 強制建置簡中 |
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
├── build_output.py    # 建置入口／相容入口
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

- 貢獻：[CONTRIBUTING.md](CONTRIBUTING.md)
- 變更紀錄：[CHANGELOG.md](CHANGELOG.md)
- 代理／維護備註：[AGENTS.md](AGENTS.md)
- 專案結構：[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

CI：Windows / Linux × Python 3.9 / 3.12。全綠表示程式與 smoke test 通過，**不代表** CI 持有完整遊戲資源。

---

## 注意事項

1. 僅使用你有權使用的原版遊戲檔；打過補丁的 `pack` 勿當 refresh 來源。  
2. 勿將 `src_file/`、`output*`、遊戲本體 commit 到 `main`。  
3. `lang0` 超長譯文會導致建置失敗或略過該 key——需縮短譯文，無法「無限加長欄位」。  
4. 本專案與遊戲官方無關，為玩家社群維護之工具鏈。

---

## 相關連結

- Releases：https://github.com/ww123oo/DBOZero/releases  
- Issues：https://github.com/ww123oo/DBOZero/issues