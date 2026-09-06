# DBOZero — Dragon Ball Online 繁體中文漢化工具鏈

> **目前專案定位：** 以實際遊戲資源為準，建立可持續更新的 DBO Zero 繁中漢化工具鏈。

本專案是玩家自製的 Dragon Ball Online（DBO Zero）繁體中文翻譯工具，不修改遊戲程式、不寫入系統登錄檔。

> **重要：** 本倉庫不提供遊戲本體或可直接散布的遊戲資源。請只使用你自己取得、並有權使用的 DBO Zero 資源進行掃描與建置。

---

## 目錄

- [專案現在在做什麼](#專案現在在做什麼)
- [翻譯資料的正確觀念](#翻譯資料的正確觀念)
- [目前掃描範圍](#目前掃描範圍)
- [資源檔案與 Git 分支規則](#資源檔案與-git-分支規則)
- [第一次使用](#第一次使用)
- [遊戲更新後](#遊戲更新後)
- [日常翻譯流程](#日常翻譯流程)
- [翻譯與建置資料夾](#翻譯與建置資料夾)
- [台灣繁中用字](#台灣繁中用字)
- [開發與測試](#開發與測試)
- [專案結構](#專案結構)
- [注意事項](#注意事項)

---

## 專案現在在做什麼

DBOZero 早期的翻譯資料主要沿用原作者整理的 `translations.tsv`，當時的資源版本較舊，因此主要處理到 `lang0.pak`、`tbl0.pak`、`tbl1.pak`。

後來遊戲經過大型更新，出現新的資源與新的文字資料，例如 `tbl2.pak`。因此現在不能再把舊的 `translations.tsv` 視為「完整遊戲翻譯表」。

目前專案的方向已改成：

```text
實際遊戲資源
    ↓
完整掃描
    ↓
建立最新文字索引
    ↓
與舊翻譯資料比對
    ↓
找出已翻譯 / 未翻譯 / 新增 / 衝突
    ↓
依資源格式使用專用安全寫入器
    ↓
產生漢化結果
```

**遊戲目前實際存在的文字，才是完整度的依據。**

`data/translations.tsv`、`data/new_translations.tsv` 以及歷史翻譯資料，都是翻譯資產與參考資料，不是遊戲資源的完整清單。

---

## 翻譯資料的正確觀念

### `translations.tsv` 不是最新完整表

原作者停止維護後，遊戲又有新的更新，所以其中沒有 `tbl2.pak` 並不代表 `tbl2.pak` 不需要翻譯。

例如掃描器發現：

```text
source: tbl2.pak
text:   Consent

source: tbl2.pak
text:   Negative

source: tbl2.pak
text:   Greetings
```

即使舊的 `translations.tsv` 沒有這些資料，也應該進入新的翻譯索引。

### 舊翻譯的用途

舊表仍然非常重要，主要用來：

- 繼承已經確認的翻譯
- 查找歷史譯名
- 避免重複翻譯
- 比對不同版本的遊戲資源
- 作為新的翻譯詞彙參考

但**不能用來限制掃描範圍**。

---

## 目前掃描範圍

完整文字掃描器目前以以下資源為目標：

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

### 明確不掃描

```text
*.bin
```

目前專案的掃描器**不把 `.bin` 當成翻譯資源**。

### 為什麼 `tbl2.pak` 要特別處理？

`tbl2.pak` 不是單純把所有 UTF-16 字串直接替換即可。它包含結構化資料，例如 ID、旗標、長度與 UTF-16LE 文字等欄位。

因此 `tbl2.pak` 必須使用能理解其記錄邊界與長度欄位的方式處理，不能做全檔盲目字串替換。

---

## 資源檔案與 Git 分支規則

### `main` 的原則

`main` 是**程式碼、翻譯資料與文件的主要分支**。

大型遊戲原始資源、台服原版參考檔以及容易造成 Git repository 膨脹的資源，不放進 `main`。

目前以下大型參考檔已移到專用分支：

```text
reference-resources
```

該分支用來保存開發、比對、研究時需要的參考資源。

### 目前列入資源分支的檔案

```text
table_quest_text_data.xml
table_quest_text_data(台服原版).xml
table_text_all_data.xml
table_text_all_data(台服原版).xml
```

另外，下列資源若需要進行版本比對，也應放在 `reference-resources`，**不要加入 `main`**：

```text
table_quest_text_data.rdf
table_text_all_data.rdf
local_data.dat
local_sync_data.dat
```

如果日後還有其他大型遊戲資源，也採用同一原則：

```text
main
└── 程式碼 / 翻譯表 / 測試 / 文件

reference-resources
└── 大型原始資源 / 台服原版 / 比對用資料
```

這樣每次修改程式或翻譯表時，Git repository 不會被大量遊戲資源拖慢，也能避免把不必要的遊戲資源一起送進日常 AI 檢查流程。

> **注意：** `src_file/DBOZero/` 本身仍然是本機遊戲來源快照，不應直接提交到 `main`。

---

## 第一次使用

### 需要

- Windows
- Python 3.9+
- Git
- 一份你自己取得的 DBO Zero 官方原版遊戲資源

安裝：

```powershell
pip install -e .
```

設定遊戲目錄：

```powershell
dboc config --game-dir "E:\DBO Zero 2.0"
```

確認設定：

```powershell
dboc config --show
```

---

## 掃描遊戲資源

目前可以直接使用完整文字掃描器：

```powershell
python scan_all_text.py "src_file\DBOZero" -o translation_scan.tsv
```

不指定參數時：

```powershell
python scan_all_text.py
```

預設會掃描：

```text
src_file/DBOZero
```

並產生：

```text
translation_scan.tsv
```

掃描結果主要包含：

```text
file
offset
encoding
byte_length
confidence
kind
source_text
translation
```

其中 `translation` 初始可以保持空白，再與現有翻譯資料合併。

---

## 遊戲更新後

推薦流程：

```powershell
1. 將遊戲更新／修復成官方原版
2. 更新本機 src_file/DBOZero
3. 執行完整掃描
4. 比對舊翻譯資料
5. 翻譯新增文字
6. 執行格式驗證
7. 建置漢化補丁
8. 實際進遊戲測試
```

不要因為舊的 `translations.tsv` 沒有某個新檔案，就直接判定該檔案不需要翻譯。

尤其是大型更新後，要特別檢查：

```text
lang0.pak
tbl0.pak
tbl1.pak
tbl2.pak
*.rdf
*.xml
*.dat
```

---

## 日常翻譯流程

### 翻譯主表

主要翻譯資料位於：

```text
data/new_translations.tsv
data/translations.tsv
```

其中：

- `new_translations.tsv`：新的翻譯佇列／新增翻譯
- `translations.tsv`：舊譯與已確認翻譯資料
- `data/舊譯表/`：歷史翻譯與參考資料

### 建置繁中

```powershell
dboc build --variant taiwan
```

### 建置兩套

```powershell
dboc build
```

輸出位置：

```text
output/DBOZero
    → 簡中版本

output_taiwan/DBOZero
    → 台灣繁中版本
```

覆蓋遊戲前請先備份。

---

## 命令快速對照

| 命令 | 用途 |
|---|---|
| `dboc config` | 設定遊戲目錄 |
| `dboc config --show` | 查看遊戲目錄設定 |
| `dboc status` | 檢查來源狀態 |
| `dboc scan` | 使用既有 DBOZero 掃描流程 |
| `dboc translate` | 處理可自動確定的翻譯 |
| `dboc build --variant taiwan` | 建置台灣繁中 |
| `dboc build` | 建置簡中 + 繁中 |
| `dboc update` | 更新來源、掃描、翻譯與建置的整體流程 |
| `python scan_all_text.py` | 新版完整文字掃描器 |

> `dboc scan` 與新的 `scan_all_text.py` 是不同層級的工具。新的完整掃描器是為了補足舊流程對新資源與 `tbl2.pak` 的覆蓋不足。

---

## 台灣繁中用字

本專案以台灣玩家習慣與台灣官方遊戲用語為優先。

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

固定譯名與詳細規則請參考：

```text
docs/translation-rules.md
```

---

## 專案結構

```text
DBOZero/
│
├── README.md                    ← 專案總說明
├── AGENTS.md                    ← AI / 維護工作規則
├── CONTRIBUTING.md              ← 貢獻規則
├── LICENSE
├── pyproject.toml
├── build_output.py              ← 建置入口
├── scan_all_text.py             ← 完整文字掃描入口
│
├── data/
│   ├── new_translations.tsv     ← 新翻譯資料
│   ├── translations.tsv         ← 舊譯／已確認翻譯
│   ├── gui_font.ini
│   ├── deltas/
│   ├── 舊譯表/
│   └── archive/
│
├── hanhua_v3/                   ← 主要工具程式
│   └── runtime/
│       ├── full_text_scanner.py
│       ├── tbl_utf16_patch.py
│       ├── lang0_gbk_patch.py
│       ├── taiwan_fixups.py
│       └── build_progress.py
│
├── scripts/                     ← 維護與一次性腳本
├── tests/                       ← 自動化測試
├── docs/                        ← 詳細文件
├── legacy/                      ← 歷史程式與資料
├── reports/                     ← 掃描／對帳報告
│
└── src_file/DBOZero/            ← 本機遊戲來源，不提交 Git
```

### 大型參考資源

位於：

```text
reference-resources
```

而不是 `main`。

---

## 開發與測試

修改程式後至少執行：

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
```

如果修改的是翻譯或資源處理流程，另外執行：

```powershell
dboc status
dboc build --variant taiwan
```

### 特別注意

涉及 PAK、DAT、RDF、XML 等資源格式時，不要只確認「程式沒有報錯」。

應該同時確認：

- 原始檔案沒有被破壞
- 記錄數量沒有異常改變
- 長度欄位正確
- 編碼正確
- 輸出檔案可以被遊戲讀取
- 遊戲啟動與進入相關介面正常

尤其是 `tbl2.pak`，必須進行結構與長度驗證後才能正式寫入。

---

## 注意事項

### 1. 不要直接修改遊戲目錄

工具應該在工作區產生輸出：

```text
output/
output_taiwan/
```

測試完成後，再由使用者自行備份並覆蓋到遊戲目錄。

### 2. 不要把遊戲原始資源提交到 main

包括大型 XML、RDF、DAT、PAK 等參考檔。

請使用：

```text
reference-resources
```

作為開發與版本比對用途。

### 3. 不要把 `.bin` 加回掃描器

目前完整掃描範圍是：

```text
lang0.pak
tbl0.pak
tbl1.pak
tbl2.pak
*.rdf
*.xml
*.dat
```

`.bin` 不在範圍內。

### 4. 每次遊戲更新都重新掃描

不要只依賴舊翻譯表。

新版本可能新增：

```text
新的文字
新的 ID
新的 tbl 資料
新的 XML / RDF / DAT
```

掃描器應該以遊戲實際檔案為準，舊翻譯只負責提供翻譯與歷史參考。

---

## 專案狀態

目前重點工作：

- [x] 建立完整文字掃描器
- [x] 掃描 `lang0.pak`
- [x] 掃描 `tbl0.pak`
- [x] 掃描 `tbl1.pak`
- [x] 納入 `tbl2.pak`
- [x] 掃描 `*.rdf`
- [x] 掃描 `*.xml`
- [x] 掃描 `*.dat`
- [x] 明確排除 `.bin`
- [x] 建立 DAT 結構化文字掃描
- [ ] 完整翻譯索引與舊表合併
- [ ] `tbl2.pak` 完整格式驗證與安全寫入
- [ ] RDF / XML / DAT 格式專用安全寫入
- [ ] lang0.pak 完整版本驗證
- [ ] 全流程遊戲實機測試

專案會以「**先掃描、再比對、再翻譯、最後安全寫入**」為原則逐步完成。

---

## License

程式碼採用 [MIT License](LICENSE)。

遊戲本體、遊戲資源、圖片、文字、商標與其他相關內容，其權利歸原權利人所有。
