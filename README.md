# DBO Zero 繁中漢化工具鏈

從遊戲原始資源生成 **台灣繁中（CP950/Big5）** 與大陸簡中（GBK）兩套**複製式**漢化補丁。  
把產物覆蓋到遊戲目錄即可生效，不修改遊戲程式、不寫註冊表。

> **免責聲明**：本專案是非官方玩家自製工具，與遊戲開發商／營運商無關。  
> 倉庫不包含任何遊戲資源檔；補丁由工具在你本機安裝的遊戲上生成。  
> 使用風險自負，請先備份遊戲目錄。

本倉庫由 [kalworth/DBOZero](https://github.com/kalworth/DBOZero) fork，並針對**台灣繁中用字**做了加強（例如統一使用「登錄」「帳號」等）。

---

## 只想用漢化補丁的玩家

不需要安裝 Python，也不需要 clone 本倉庫：

1. 到 [Releases 頁面](https://github.com/ww123oo/DBOZero/releases) 下載最新補丁壓縮包（繁中或簡中）；
2. 解壓後，把其中的 `DBOZero` 目錄內容複製到遊戲目錄下的 `DBOZero`，覆蓋同名檔案；
3. 啟動遊戲。

還原原文：用遊戲啟動器的檔案校驗／修復，或把你備份的原始檔案蓋回去。

> 目前若尚無 Release，請使用下方「自己構建」流程產生補丁。

---

## 想參與翻譯或自己構建補丁

### 環境需求

- Windows（遊戲本身是 Windows 程式；工具鏈純 Python 部分也可在 macOS／Linux 執行）
- Python 3.9 或更高
- Git
- 一份已安裝的 DBO Zero 遊戲（只讀提取原始資源）

### 快速開始

```powershell
git clone https://github.com/ww123oo/DBOZero.git
cd DBOZero
pip install -e .            # 安裝跨平台 dboc 命令（可編輯安裝）
dboc config --game-dir "E:\DBO Zero 2.0"   # 設定一次遊戲目錄
dboc update                 # 提取源檔 → 掃描 → 翻譯新增 → 構建兩套補丁
```

遊戲目錄只需設定一次，會寫入倉庫根目錄的 `dboc.toml`（已加入 `.gitignore`）。  
也可使用環境變數 `DBOC_GAME_DIR`，或命令列 `--game-dir` 臨時指定。  
查看目前生效路徑：`dboc config --show`。

### 翻譯入口（日常只改這兩個檔）

| 檔案 | 用途 | 注意 |
|------|------|------|
| `data/new_translations.tsv` | 新增詞條佇列 | **只填「填寫中文」欄** |
| `data/translations.tsv` | 已接受譯文主表 | **只改 `zh_cn` 欄** |

改完後執行：

```powershell
dboc build
```

產出：

- `output/DBOZero` → 大陸簡中（GBK）
- `output_taiwan/DBOZero` → 台灣繁中（CP950／Big5）

翻譯與編碼規則見 [docs/translation-rules.md](docs/translation-rules.md)。

### 常用命令

```text
dboc update        # 遊戲更新後一鍵：恢復點 → 同步源 → 掃描 → 翻譯新增 → 構建
dboc status        # 對比源快照與本機遊戲是否一致
dboc refresh       # 只從遊戲目錄同步必要源檔（會先建 Git 恢復點）
dboc scan          # 只掃描 src_file 並刷新翻譯佇列
dboc translate     # 批量填寫可確定的佇列譯文
dboc build         # 構建兩套補丁（預設並行、增量）
dboc config        # 查看／寫入遊戲目錄設定
dboc --help        # 全部命令與參數
```

遊戲目錄只作為**讀取源**。CLI 不會寫入遊戲目錄，也不會複製帳號資料、日誌、用戶端程式或更新快取。

---

## 倉庫結構

```text
DBOZero/
├── README.md                 # 本說明
├── pyproject.toml            # 套件與 dboc 入口
├── build_output.py           # 構建入口（由 dboc build 呼叫）
├── LICENSE
│
├── hanhua_v3/                # ★ 現行工具鏈（唯一維護的實作）
│   ├── cli.py                # 命令列編排
│   ├── config.py             # 本機設定與遊戲目錄探測
│   ├── source.py             # 從遊戲只讀同步源檔
│   ├── scan.py               # 掃描並刷新翻譯佇列
│   ├── recover.py            # 從 Git 歷史恢復譯文
│   ├── glossary.py           # 人工校訂譯名
│   ├── policy.py             # 政策與黑名單
│   └── runtime/              # 實際補丁模組（繁簡轉換、打包等）
│       └── install_hanhua.py # 含台灣用字修正表 TAIWAN_SIMPLIFY_FIXUPS
│
├── data/                     # ★ 翻譯核心資產（會進 Git）
│   ├── translations.tsv      # 已接受主表
│   ├── new_translations.tsv  # 日常新增佇列
│   └── gui_font.ini          # 可選字型設定
│
├── docs/                     # 文件
│   ├── translation-rules.md  # 翻譯與編碼規範
│   └── development.md        # 開發者說明
│
├── src_file/                 # 源快照（遊戲資源，不進 Git）
│   └── README.md             # 說明要放哪些檔、如何取得
│
├── tests/                    # 單元測試
├── scripts/                  # 特殊恢復腳本（非日常入口）
├── reports/                  # 少數人工備註（產生的 internal 報表不進 Git）
│
├── legacy/                   # 舊版工具與歷史資料（僅供參考／遷移）
│   └── README.md
│
├── output/                   # 構建產物：簡中（不進 Git）
└── output_taiwan/            # 構建產物：繁中（不進 Git）
```

**日常只需要關心：**

1. `data/*.tsv` — 改譯文  
2. `hanhua_v3/runtime/install_hanhua.py` — 調整繁中用字修正表  
3. `dboc build` / `dboc update` — 產出補丁  

其餘 `legacy/`、`scripts/`、`reports/` 為輔助，不必日常動用。

---

## 台灣繁中用字說明

簡中譯文在構建繁中補丁時，會經由 Windows API 轉繁體，再套用 `TAIWAN_SIMPLIFY_FIXUPS` 修正表。

本 fork 已調整的重點包括：

| 簡中 | 本倉庫繁中 | 說明 |
|------|------------|------|
| 登录 | **登錄** | 統一使用「登錄」 |
| 账号／账户 | **帳號／帳戶** | 避免出現「賬」 |
| 服务器 | **伺服器** | 台灣常用 |
| 信息 | **訊息** | 台灣常用 |
| 窗口 | **視窗** | 台灣常用 |
| 默认 | **預設** | 台灣常用 |
| 设置 | **設定** | 台灣常用 |

若實際遊戲中仍看到不理想用字，可在 `hanhua_v3/runtime/install_hanhua.py` 的 `TAIWAN_SIMPLIFY_FIXUPS` 繼續追加，格式為：

```python
("正確台灣用字", "簡體原文"),
```

長詞請放在短詞前面，改完後重新 `dboc build`。

---

## 開發與驗證

```powershell
pip install -e .[dev]
python -m compileall -q build_output.py hanhua_v3
pytest
dboc status
dboc build
```

更多模組職責與約定見 [docs/development.md](docs/development.md)。

---

## License

程式碼以 [MIT License](LICENSE) 發布。  
遊戲本身的資源與商標歸原權利人所有。
