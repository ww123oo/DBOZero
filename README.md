# DBO Zero 繁中漢化工具鏈（台灣用字加強）

從本機遊戲原始資源，生成 **台灣繁中（CP950）** 與 **大陸簡中（GBK）** 兩套「複製式」漢化補丁。  
把產出檔案覆蓋到遊戲目錄即可生效，**不修改**遊戲程式、不寫註冊表。

> **免責聲明**：非官方玩家自製工具，與遊戲開發商／營運商無關。  
> 倉庫**不含**遊戲資源；補丁由你在本機生成。使用前請先備份遊戲目錄。

Fork 自 [kalworth/DBOZero](https://github.com/kalworth/DBOZero)，本倉庫著重：

- **台灣繁中用字**（登錄、帳號、伺服器、強化石、氣合藥水、進階、稀少度…）
- **真實進度條**（依實際列數，不是假的固定 9 步）
- **翻譯主表整理**（`new_translations.tsv` + `舊譯表/`，避免 data/ 堆滿 delta）

**文件：** [FAQ](docs/faq.md) · [貢獻說明](CONTRIBUTING.md) · [翻譯規則](docs/translation-rules.md)

---

## 目錄

| 我想… | 看這裡 |
|--------|--------|
| 只打漢化、進遊戲 | [A. 只使用補丁](#a-只使用補丁) |
| 自己從遊戲產生補丁 | [B. 自己構建](#b-自己構建) |
| 改幾個詞再重建 | [C. 日常改翻譯](#c-日常改翻譯) |
| 遊戲更新了 | [D. 遊戲更新後](#d-遊戲更新後) |
| 各命令差在哪 | [E. 命令對照](#e-命令對照) |
| 倉庫怎麼放檔 | [倉庫結構](#倉庫結構) |
| 台灣用字 | [台灣繁中用字](#台灣繁中用字) |
| 出錯了 | [docs/faq.md](docs/faq.md) |

---

## A. 只使用補丁

不需要 Python，也不需要 clone。

1. 到 [Releases](https://github.com/ww123oo/DBOZero/releases) 下載最新補丁（繁中或簡中）。  
   > **目前暫無正式 Release**（需多輪實測）。請改走下方 **B. 自己構建**。
2. **先備份**遊戲目錄（或至少備份 `DBOZero` 資料夾）。
3. 解壓後，把裡面的 `DBOZero` 內容複製到遊戲裡的 `DBOZero`，**覆蓋同名檔案**。
4. 啟動遊戲檢查。

**還原官方原文**：用啟動器「檔案校驗／修復」，或把備份蓋回去。

---

## B. 自己構建

### 需要準備

- Windows（建議）
- [Python 3.9+](https://www.python.org/downloads/)（勾選 **Add Python to PATH**）
- [Git](https://git-scm.com/downloads)
- 本機 **DBO Zero 官方原版**（不要先打過漢化）

### 第一次構建

```powershell
git clone https://github.com/ww123oo/DBOZero.git
cd DBOZero

pip install -e .

# 遊戲目錄指到含 DBOZero 的根目錄（只需一次）
dboc config --game-dir "E:\\DBO Zero 2.0"

# 同步源檔 → 掃描 → 填可自動翻譯的詞 → 產出兩套補丁
dboc update

dir output\\DBOZero
dir output_taiwan\\DBOZero
```

### 只構建台灣繁中（日常推薦）

```powershell
dboc build --variant taiwan
```

進度列會依實際工作量顯示，最後一行類似：

```text
[████████████████████████████] 100% 總進度 (53773/53773) 完成
```

### 套進遊戲

```text
繁中：output_taiwan\\DBOZero\\*  →  遊戲目錄\\DBOZero\\
簡中：output\\DBOZero\\*          →  遊戲目錄\\DBOZero\\
```

覆蓋前請備份。工具**只讀**遊戲目錄，不會自動寫入遊戲。

### 常見第一次錯誤

| 現象 | 怎麼辦 |
|------|--------|
| 找不到遊戲目錄／缺少源檔 | 路徑指到含 `DBOZero` 的根目錄；有空格請加引號 |
| 疑似已打補丁 | 用啟動器**修復原版**後再 `dboc update` |
| `pip` / `dboc` 不是命令 | 重裝 Python 並勾選 PATH，或用 `python -m pip install -e .` |
| `build_output` 解壓 EOFError | `git pull` 後確認 `scripts/build_output_p*.b64` 齊全，或向維護者索取完整 `build_output.py` |

更多見 [docs/faq.md](docs/faq.md)。  
`dboc config --show` ｜ `dboc --help`

---

## C. 日常改翻譯

**只動這兩個表：**

| 檔案 | 你要做的事 |
|------|------------|
| `data/new_translations.tsv` | **主翻譯表**：只填／改 **`填写中文`** |
| `data/translations.tsv` | 舊譯／已接受詞：只改 **`zh_cn`** |

```powershell
dboc build --variant taiwan
# 或兩套：dboc build
```

- `output/DBOZero` → 大陸簡中（GBK）
- `output_taiwan/DBOZero` → 台灣繁中（CP950）

規則詳見 [docs/translation-rules.md](docs/translation-rules.md)。

> **重要：** 不要隨便跑 `dboc scan` 覆蓋已填好的主表。  
> `scan` 會**重寫** `data/new_translations.tsv`（改成「待翻譯佇列」），列數可能從五萬多變成兩萬多。  
> 日常改詞 → 只編 TSV → `dboc build` 即可。

---

## D. 遊戲更新後

1. 用啟動器把遊戲更新／修復成**官方原版**。
2. 在本倉庫執行：

```powershell
dboc update
```

3. 再把 `output_taiwan`（或 `output`）覆蓋回遊戲。

若你已有大量手填的 `new_translations.tsv`，更新前請先**備份該檔**，再決定是否合併 scan 產生的新列。

---

## E. 命令對照

| 命令 | 做什麼 | 什麼時候用 |
|------|--------|------------|
| `dboc build --variant taiwan` | 用現有翻譯表產出繁中補丁 | **日常最常用** |
| `dboc build` | 產出簡中 + 繁中 | 要兩套時 |
| `dboc update` | 同步遊戲源 → scan → 自動填能填的 → build | 遊戲大更新後 |
| `dboc scan` | 掃描 `src_file`，**重寫**翻譯佇列與 reports | 開發／對帳；**慎用** |
| `dboc translate` | 批次填可自動確定的佇列 | scan 之後 |
| `dboc status` | 源快照與本機遊戲是否一致 | 檢查 |
| `dboc config` | 查看／設定遊戲目錄 | 第一次 |
| `dboc --help` | 全部參數 | — |

### `dboc scan` 輸出在說什麼？

| 項目 | 含義 |
|------|------|
| `catalog entries` | 從本機源檔掃到的字串總數（含不必翻譯的內部 token） |
| `active translations` | `data/translations.tsv` 裡已有的譯條 |
| `legacy candidates` | 舊譯／legacy 可參考的候選 |
| `data/new_translations.tsv` | **這次 scan 寫出的佇列列數**（不是「遊戲全部字」） |
| `reports/internal/*` | 內部對帳、衝突、重疊報告（給翻譯維護用） |
| `warnings` | 掃描過程的警告數 |

建置打補丁時，真正用的是你維護的 **`data/new_translations.tsv` + `translations.tsv`**，不是 reports。

---

## 倉庫結構

```text
DBOZero/
├── README.md                 ← 本說明
├── CONTRIBUTING.md
├── build_output.py           ← 構建入口（小檔時會從 scripts/ 展開完整版）
├── pyproject.toml
│
├── data/                     ← ★ 日常只改這裡的翻譯表
│   ├── new_translations.tsv  ← 主表（填 填写中文）
│   ├── translations.tsv      ← 舊譯／已接受表
│   ├── gui_font.ini
│   ├── deltas/               ← 少量現行增量（可選）
│   ├── 舊譯表/               ← 歷史合併 delta、台服原版（參考）
│   └── archive/              ← 已歸檔 batch delta
│
├── hanhua_v3/                ← 工具本體
│   └── runtime/
│       ├── taiwan_fixups.py ← 繁中用字（唯一來源）
│       └── build_progress.py ← 真實進度條
│
├── scripts/                  ← 維護腳本（新手可忽略）
├── docs/
├── tests/
├── legacy/
├── reports/                  ← scan 產生（通常不進 Git／可忽略）
│
├── src_file/                 ← 從遊戲同步的源（不進 Git）
├── output/                   ← 簡中產出（不進 Git）
└── output_taiwan/            ← 繁中產出（不進 Git）
```

**新手請忽略：** `scripts/`、`data/archive/`、`data/舊譯表/`、`legacy/`、`reports/`。

歷史增量已合併進 `data/舊譯表/deltas_merged/`，**不必**在 `data/` 根目錄堆一堆 `*_delta.tsv`。

---

## 台灣繁中用字

構建時會轉繁體，再套用 `hanhua_v3/runtime/taiwan_fixups.py`。

| 簡中／舊譯 | 本倉庫繁中 |
|------------|------------|
| 登录 | **登錄** |
| 账号／账户 | **帳號／帳戶** |
| 服务器 | **伺服器** |
| 升级石 | **強化石**（勿用「升級石」） |
| 气力／气功／能量药水 | **氣合藥水** |
| 升阶（裝備） | **進階** |
| 稀有度 | **稀少度** |
| 高级（道具品質） | **高級**（勿與「進階」混淆） |
| 连接（伺服器） | **連線** |

狀態／職業等固定譯名見專案用語表（翻譯時請一併遵守）。

---

## 開發者

```powershell
pip install -e .[dev]
python -m compileall -q build_output.py hanhua_v3
pytest
dboc build --variant taiwan
```

詳見 [docs/development.md](docs/development.md)。

---

## License

程式碼：[MIT License](LICENSE)  
遊戲資源與商標歸原權利人所有。
