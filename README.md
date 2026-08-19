# DBO Zero 繁中漢化工具鏈

從本機遊戲原始資源，生成 **台灣繁中** 與 **大陸簡中** 兩套「複製式」漢化補丁。  
把產出的檔案覆蓋到遊戲目錄即可生效，**不修改**遊戲程式、不寫註冊表。

> **免責聲明**：非官方玩家自製工具，與遊戲開發商／營運商無關。  
> 倉庫**不含**任何遊戲資源；補丁由你在本機生成。使用前請先備份遊戲目錄。

本倉庫由 [kalworth/DBOZero](https://github.com/kalworth/DBOZero) fork，並加強**台灣繁中用字**（例如「登錄」「帳號」）。

**相關文件：** [常見問題 FAQ](docs/faq.md) · [貢獻說明](CONTRIBUTING.md) · [翻譯規則](docs/translation-rules.md)

---

## 你是哪一種使用者？

| 我想… | 請看 |
|--------|------|
| 只想打上漢化、進遊戲 | [A. 只使用補丁](#a-只使用補丁) |
| 自己從遊戲產生補丁／改翻譯 | [B. 新手快速開始（自己構建）](#b-新手快速開始自己構建) |
| 日常改幾個詞再重建 | [C. 日常改翻譯](#c-日常改翻譯) |
| 遊戲更新了要重做補丁 | [D. 遊戲更新後](#d-遊戲更新後) |
| 遇到錯誤訊息 | [docs/faq.md](docs/faq.md) |
| 想幫忙翻譯／修工具 | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## A. 只使用補丁

不需要 Python，也不需要 clone 本倉庫。

1. 到 [Releases](https://github.com/ww123oo/DBOZero/releases) 下載最新補丁（繁中或簡中）。  
   > **目前暫無正式 Release**（遊戲每週更新，需多輪實測後再打包）。請改走下方 **B. 自己構建**。
2. **先備份**遊戲目錄（或至少備份 `DBOZero` 資料夾）。
3. 解壓後，把裡面的 `DBOZero` 內容，複製到遊戲裡的 `DBOZero`，**覆蓋同名檔案**。
4. 啟動遊戲檢查。

**還原官方原文**：用遊戲啟動器的「檔案校驗／修復」，或把備份蓋回去。

---

## B. 新手快速開始（自己構建）

### 需要準備

- Windows（建議；遊戲是 Windows 版）
- [Python 3.9+](https://www.python.org/downloads/)（安裝時勾選 **Add Python to PATH**）
- [Git](https://git-scm.com/downloads)
- 本機已安裝的 **DBO Zero**（必須是**官方原版**檔案，不要先打過漢化）

### 五步完成第一次構建

在 **PowerShell** 執行（把路徑改成你的遊戲目錄）：

```powershell
# 1) 下載工具
git clone https://github.com/ww123oo/DBOZero.git
cd DBOZero

# 2) 安裝命令 dboc（只裝在這個資料夾，可安全重跑）
pip install -e .

# 3) 告訴工具遊戲在哪（只需做一次，會寫入本機 dboc.toml）
dboc config --game-dir "E:\DBO Zero 2.0"

# 4) 一鍵：同步源檔 → 掃描 → 填可自動翻譯的詞 → 產出兩套補丁
dboc update

# 5) 確認有產出
dir output\DBOZero
dir output_taiwan\DBOZero
```

### 把補丁套進遊戲

```text
繁中：把  output_taiwan\DBOZero\*  覆蓋到  遊戲目錄\DBOZero\
簡中：把  output\DBOZero\*          覆蓋到  遊戲目錄\DBOZero\
```

覆蓋前請先備份。工具**只讀**遊戲目錄，不會自動寫入遊戲。

### 常見第一次錯誤

| 現象 | 怎麼辦 |
|------|--------|
| `找不到遊戲目錄` / `缺少必要源檔案` | 路徑要指到含 `DBOZero` 的遊戲根目錄，或直接指到 `...\DBOZero`；路徑有空格請加引號 |
| `疑似已打補丁` / 拒絕同步 | 遊戲已被漢化過。用啟動器**修復原版**後再 `dboc update` |
| `pip` / `dboc` 不是內部或外部命令 | 重裝 Python 並勾選 PATH，或改用 `python -m pip install -e .`、`python -m hanhua_v3` |
| 必須用可編輯安裝 | 請用 `pip install -e .`（有 `-e`），不要只 `pip install .` |

更多見 [docs/faq.md](docs/faq.md)。  
查看目前設定：`dboc config --show`　｜　全部參數：`dboc --help`

---

## C. 日常改翻譯

平時**只動這兩個表**，不要改其他欄位名稱：

| 檔案 | 你要做的事 |
|------|------------|
| `data/new_translations.tsv` | 新詞：只填 **`填写中文`** 這一欄 |
| `data/translations.tsv` | 改舊譯：只改 **`zh_cn`** 這一欄 |

改完後：

```powershell
dboc build
```

- `output/DBOZero` → 大陸簡中（GBK）
- `output_taiwan/DBOZero` → 台灣繁中（CP950／Big5）

更細的規則：[docs/translation-rules.md](docs/translation-rules.md)  
迷你檢查清單：[reports/what_to_do_next.md](reports/what_to_do_next.md)

---

## D. 遊戲更新後

**正確順序：**

1. 用啟動器把遊戲更新／修復成**官方原版**（不要帶著舊漢化去同步）。
2. 在本倉庫執行：

```powershell
dboc update
```

3. 再把新的 `output_taiwan`（或 `output`）覆蓋回遊戲。

`dboc update` 會：建立 Git 恢復點 → 同步源 → 掃描新詞 → 盡量自動填譯 → 構建兩套補丁。

---

## 常用命令一覽

```text
dboc update      # 遊戲更新後一鍵重做（建議）
dboc status      # 看源快照與本機遊戲是否一致
dboc refresh     # 只同步必要源檔（會先建恢復點）
dboc scan        # 只掃描並刷新翻譯佇列
dboc translate   # 批量填可確定的佇列譯文
dboc build       # 只構建補丁（改完 TSV 後用這個）
dboc config      # 查看／寫入遊戲目錄
dboc --help      # 全部說明
```

---

## 台灣繁中用字

構建繁中時會先轉繁體，再套用 `TAIWAN_SIMPLIFY_FIXUPS`（**唯一來源**：`hanhua_v3/runtime/taiwan_fixups.py`）。

| 簡中 | 本倉庫繁中 |
|------|------------|
| 登录 | **登錄** |
| 账号／账户 | **帳號／帳戶** |
| 服务器 | **伺服器** |
| 信息 | **訊息** |
| 窗口 | **視窗** |
| 默认 | **預設** |
| 设置 | **設定** |

若遊戲裡仍看到不順的用字，在修正表追加 `("正確台灣用字", "簡體")`，長詞放前面，再 `dboc build`。

---

## 倉庫裡什麼要動、什麼別動

```text
DBOZero/
├── README.md              ← 你正在看的說明
├── CONTRIBUTING.md        ← 如何貢獻翻譯／程式
├── data/                  ← ★ 翻譯表（日常改這裡）
├── hanhua_v3/             ← 工具本體（一般不用改）
│   └── runtime/taiwan_fixups.py  ← 繁中用字修正表（唯一來源）
├── docs/                  ← FAQ、規則、開發說明
├── src_file/              ← 從遊戲同步來的源（不進 Git）
├── output/                ← 簡中補丁產出（不進 Git）
├── output_taiwan/         ← 繁中補丁產出（不進 Git）
├── tests/                 ← 測試
└── legacy/                ← 舊版歸檔（僅參考；可能不完整／有錯字）
```

**新手請忽略：** `legacy/`、`scripts/`、`reports/internal/`。  
`legacy/` 說明見 [legacy/README.md](legacy/README.md)。

---

## 開發者驗證

```powershell
pip install -e .[dev]
python -m compileall -q build_output.py hanhua_v3
pytest
dboc status
dboc build
```

模組說明見 [docs/development.md](docs/development.md)。

---

## License

程式碼：[MIT License](LICENSE)  
遊戲資源與商標歸原權利人所有。
