# DBOZero — Dragon Ball Online 繁體中文漢化工具鏈

> **目前版本定位：** `v0.1.0` Release Candidate／首個公開工具鏈版本。
>
> 以實際 DBO Zero 遊戲資源為 source of truth，建立可持續更新、可驗證、可回溯的繁體中文漢化工具鏈。

![CI](https://github.com/ww123oo/DBOZero/actions/workflows/ci.yml/badge.svg)

本專案是玩家自製的 Dragon Ball Online（DBO Zero）繁體中文翻譯工具鏈，不修改遊戲程式、不寫入系統登錄檔。

> **重要：** 本倉庫不提供遊戲本體或可直接散布的遊戲資源。請只使用你自己取得、並有權使用的 DBO Zero 資源進行掃描與建置。

## 專案狀態

| 項目 | 狀態 |
|---|---|
| 完整文字掃描框架 | ✅ |
| `lang0.pak` / `tbl0.pak` / `tbl1.pak` 掃描 | ✅ |
| `tbl2.pak` 掃描與結構化定位 | ✅ |
| `*.rdf` / `*.xml` / `*.dat` 掃描 | ✅ |
| 舊翻譯繼承與新翻譯佇列 | ✅ |
| 簡中獨立建置 | ✅ |
| 台灣繁中獨立建置 | ✅ |
| 雙語 Release Gate | ✅ |
| CI：Windows/Linux × Python 3.9/3.12 | ✅ 4/4 PASS |
| 最新遊戲資源完整實機測試 | ⏳ |

**CI 全綠代表程式碼、單元測試與 CLI smoke test 通過；不代表 GitHub CI 已經持有你的完整 DBO 遊戲資源。** 正式交付前仍須在有實際遊戲資源的環境執行雙語 Release Gate 並進行遊戲內測試。

## 目錄

- [專案狀態](#專案狀態)
- [Release](#release)
- [核心設計](#核心設計)
- [翻譯資料的正確觀念](#翻譯資料的正確觀念)
- [目前掃描範圍](#目前掃描範圍)
- [資源檔案與 Git 分支規則](#資源檔案與-git-分支規則)
- [第一次使用](#第一次使用)
- [完整掃描](#完整掃描)
- [遊戲更新後](#遊戲更新後)
- [日常翻譯流程](#日常翻譯流程)
- [雙語建置與發布](#雙語建置與發布)
- [台灣繁中用字](#台灣繁中用字)
- [開發與測試](#開發與測試)
- [專案結構](#專案結構)
- [注意事項](#注意事項)

## Release

目前 Release 系列以 **`v0.1.x`** 為第一階段公開版本。

`v0.1.0` 的目標不是宣稱「所有遊戲文字都已完成翻譯」，而是建立第一個可持續更新的工具鏈基準：

- 完整掃描遊戲實際存在的文字資源
- 使用舊翻譯作為歷史資產，而不是掃描範圍限制
- 將新文字導入 `data/new_translations.tsv`
- 對 `tbl2.pak` 使用結構化、穩定 ID 的安全寫入策略
- 簡中與台灣繁中分開建置、分開驗證
- 兩個產品都 PASS 後才允許通過 Release Gate

GitHub Releases 頁面：

https://github.com/ww123oo/DBOZero/releases

## 核心設計

整體流程：

```text
官方原版遊戲資源
        ↓
完整掃描
        ↓
建立最新文字索引
        ↓
舊翻譯繼承 + 新文字進入佇列
        ↓
翻譯
        ↓
依資源格式安全寫入
        ↓
簡中 build + validation
        ↓
台灣繁中 build + validation
        ↓
RELEASE GATE PASS
        ↓
才可交付
```

**遊戲目前實際存在的文字，才是完整度的依據。**

## 翻譯資料的正確觀念

### `translations.tsv` 不是最新完整表

原作者停止維護後，遊戲仍可能更新並出現新的文字與資源，例如 `tbl2.pak`。因此不能把舊的 `translations.tsv` 當成完整遊戲文字清單。

舊翻譯主要用來：

- 繼承已確認翻譯
- 查找歷史譯名
- 避免重複翻譯
- 比對不同版本資源
- 作為新翻譯的詞彙參考

### `new_translations.tsv` 是日常新翻譯佇列

新的遊戲文字經完整掃描後，應進入：

```text
data/new_translations.tsv
```

完成確認的歷史／既有翻譯則保留於：

```text
data/translations.tsv
```

兩者都不是遊戲資源本身的完整清單。

## 目前掃描範圍

### PAK

```text
lang0.pak
tbl0.pak
tbl1.pak
tbl2.pak
```

### 其他文字資源

```text
*.rdf
*.xml
*.dat
```

專案不把其他非翻譯資源自動加入掃描範圍。

### `tbl2.pak` 為什麼要特別處理？

`tbl2.pak` 包含結構化記錄，例如 ID、旗標、長度與 UTF-16LE 文字。不能用全檔盲目字串取代。

寫入時應：

1. 優先使用穩定 ID 定位。
2. 驗證記錄邊界與原始文字。
3. 驗證固定長度與 UTF-16LE 資料。
4. 定位失敗時 fail-closed，不猜 offset。
5. 寫入後再做格式驗證。

## 資源檔案與 Git 分支規則

### `main`

`main` 是程式碼、翻譯資料、測試與文件的主要分支。

大型遊戲原始資源、台服原版參考檔與研究用資源不應放進 `main`。

### `reference-resources`

大型參考資料放在：

```text
reference-resources
```

目前規劃的參考檔包括：

```text
table_quest_text_data.xml
table_quest_text_data(台服原版).xml
table_text_all_data.xml
table_text_all_data(台服原版).xml
table_quest_text_data.rdf
table_text_all_data.rdf
local_data.dat
local_sync_data.dat
```

本機遊戲來源快照：

```text
src_file/DBOZero/
```

不應直接提交到 `main`。

## 第一次使用

### 需要

- Windows
- Python 3.9+
- Git
- 一份你自己取得並有權使用的 DBO Zero 原版遊戲資源

安裝：

```powershell
pip install -e .
```

設定遊戲目錄：

```powershell
dboc config --game-dir "E:\DBO Zero 2.0"
```

確認：

```powershell
dboc config --show
```

## 完整掃描

新版完整掃描入口：

```powershell
python scan_all_text.py "src_file\DBOZero" -o translation_scan.tsv
```

不指定參數時預設掃描：

```text
src_file/DBOZero
```

主要輸出欄位：

```text
file
offset
encoding
byte_length
confidence
kind
id
source_text
translation
```

`kind` 會保留資源格式資訊，供後續翻譯佇列與寫入器使用。

## 遊戲更新後

每次遊戲更新都建議重新掃描，而不是只依賴舊翻譯表：

```text
1. 更新／修復成官方原版
2. 更新本機 src_file/DBOZero
3. 執行完整掃描
4. 與舊翻譯資料比對
5. 新文字進入 new_translations.tsv
6. 翻譯與術語確認
7. 格式驗證
8. 雙語建置
9. 實際進遊戲測試
```

特別確認：

```text
lang0.pak
tbl0.pak
tbl1.pak
tbl2.pak
*.rdf
*.xml
*.dat
```

## 日常翻譯流程

主要翻譯資料：

```text
data/new_translations.tsv
data/translations.tsv
data/舊譯表/
```

推薦順序：

```text
掃描 → 建立 inventory → 繼承舊譯 → 新增翻譯 → 寫入 → 驗證
```

未知文字不要為了填滿表格而猜測翻譯；應保留待人工確認。

## 雙語建置與發布

### 單獨建置台灣繁中

```powershell
dboc build --variant taiwan
```

輸出：

```text
output_taiwan/
```

### 單獨建置簡中

```powershell
dboc build --variant simplified
```

輸出：

```text
output/
```

### 正式 Release Gate

```powershell
dboc release
```

Release Gate 會依序：

1. 建置簡體中文。
2. 驗證簡體中文。
3. PASS 後才建置台灣繁體中文。
4. 驗證台灣繁體中文。
5. 兩者都 PASS 才回報 `RELEASE GATE PASS`。

任何一個版本失敗都停止，不會因另一個版本成功而宣稱 Release 完成。

詳細規則：

```text
docs/BUILD_PIPELINE.md
docs/REALTIME_UPDATE_FLOW.md
```

## 命令快速對照

| 命令 | 用途 |
|---|---|
| `dboc config` | 設定遊戲目錄 |
| `dboc config --show` | 查看遊戲目錄設定 |
| `dboc status` | 檢查來源狀態 |
| `dboc scan` | 舊流程掃描入口 |
| `dboc translate` | 處理可自動確定的翻譯 |
| `dboc build --variant simplified` | 單獨建置簡中 |
| `dboc build --variant taiwan` | 單獨建置台灣繁中 |
| `dboc build` | 建置兩個語言產品 |
| `dboc release` | 雙語獨立建置 + Release Gate |
| `dboc update` | 更新來源、掃描、翻譯與建置流程 |
| `python scan_all_text.py` | 完整文字掃描 |

## 台灣繁中用字

本專案以台灣玩家習慣與台灣遊戲用語為優先。

| 原文／簡中 | 台灣繁中 |
|---|---|
| 登录 | **登錄** |
| 账号 | **帳號** |
| 账户 | **帳戶** |
| 服务器 | **伺服器** |
| 升级石 | **強化石** |
| 气力／气功／能量药水 | **氣合藥水** |
| 升阶（裝備） | **進階** |
| 稀有度 | **稀少度** |
| 连接（伺服器） | **連線** |

固定譯名與詳細規則：

```text
docs/translation-rules.md
```

## 開發與測試

本地至少執行：

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
```

CLI smoke test：

```powershell
dboc --help
dboc build --help
dboc release --help
```

CI 目前驗證：

- Windows / Python 3.9
- Windows / Python 3.12
- Ubuntu / Python 3.9
- Ubuntu / Python 3.12
- compile check
- unit tests
- CLI smoke test

目前最新一輪 CI：**4/4 PASS**。

## 專案結構

```text
DBOZero/
├── README.md
├── AGENTS.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── build_output.py
├── scan_all_text.py
│
├── data/
│   ├── new_translations.tsv
│   ├── translations.tsv
│   ├── gui_font.ini
│   ├── deltas/
│   ├── 舊譯表/
│   └── archive/
│
├── hanhua_v3/
│   └── runtime/
│       ├── full_text_scanner.py
│       ├── translation_inventory.py
│       ├── translation_queue.py
│       ├── auto_translate_v2.py
│       ├── tbl_utf16_patch.py
│       ├── lang0_gbk_patch.py
│       ├── resource_writer.py
│       └── build_progress.py
│
├── docs/
│   ├── BUILD_PIPELINE.md
│   ├── REALTIME_UPDATE_FLOW.md
│   ├── FULL_TEXT_SCAN.md
│   └── translation-rules.md
│
├── tests/
└── reference-resources/        ← 獨立 Git 分支，不放 main
```

## 注意事項

### 不要直接修改遊戲目錄

工具應在工作區產生：

```text
output/
output_taiwan/
```

測試完成後再由使用者自行備份並覆蓋到遊戲目錄。

### 不要提交大型遊戲原始資源

大型 PAK、XML、RDF、DAT 等參考檔請放在 `reference-resources`，不要塞進 `main`。

### 不要猜測未知翻譯

無法可靠判斷的文字應保留待確認，而不是為了提高完成率亂填。

### `tbl2.pak` 必須 fail-closed

定位、來源文字、長度或結構驗證任何一項失敗，都應停止寫入，不猜 offset、不做全檔替換。

## License

程式碼採用 [MIT License](LICENSE)。

遊戲本體、遊戲資源、圖片、文字、商標與其他相關內容，其權利歸原權利人所有。
