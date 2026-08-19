# 貢獻說明

感謝願意幫忙。本專案是非官方玩家工具，目標是穩定產出**台灣繁中**與大陸簡中複製式補丁。

開始前請先閱讀 [README.md](README.md) 與 [docs/faq.md](docs/faq.md)。

---

## 可以怎麼貢獻

| 類型 | 說明 |
|------|------|
| 翻譯／潤稿 | 補 `data/new_translations.tsv`、改 `data/translations.tsv` |
| 台灣用字 | 追加 `TAIWAN_SIMPLIFY_FIXUPS`（登錄、帳號、伺服器…） |
| 工具／文件 | 修 bug、補 FAQ、改進說明 |
| **不建議** | 把 `legacy/` 當主戰場大改；歷史檔可能不完整、有錯字 |

---

## 翻譯貢獻（最常見）

### 規則

1. **只改該改的欄**  
   - 新詞：`data/new_translations.tsv` → 只填 **`填写中文`**  
   - 舊譯：`data/translations.tsv` → 只改 **`zh_cn`**  
2. **不要改** ID、原文、檔名、位置等欄，也不要改表頭名稱。  
3. TSV 必須是**製表符（Tab）**分隔，不要用對齊用的空白取代 Tab。  
4. 用試算表時匯出仍須保持 UTF-8 與 Tab 分隔。  
5. 長度敏感欄位（如 lang0）過長可能塞不進去，見 [docs/translation-rules.md](docs/translation-rules.md)。

### 建議流程

```powershell
git clone https://github.com/ww123oo/DBOZero.git
cd DBOZero
pip install -e .
dboc config --game-dir "你的遊戲路徑"
dboc update          # 或至少 dboc scan
# 編輯 data/new_translations.tsv 或 data/translations.tsv
dboc build
```

能的話在遊戲裡點一次相關介面再提交。

### Pull Request 請註明

- 改了哪些詞／場景（例如「角色建立畫面」）  
- 若改用字表：列出新增的對照  
- 是否已 `dboc build` 成功  

---

## 台灣用字修正

檔案：`hanhua_v3/runtime/taiwan_fixups.py`（**唯一來源**；由 `install_hanhua.py` 匯入）

格式：

```python
("正確台灣用字", "簡體原文"),
```

- 長詞放在短詞前面  
- 本 fork 偏好：**登錄**（非僅登入）、**帳號／帳戶**（非賬號）  
- 改完執行 `dboc build`，用 `output_taiwan` 驗證  

---

## 程式與測試

```powershell
pip install -e .[dev]
python -m compileall -q build_output.py hanhua_v3
pytest
```

- 優先改 `hanhua_v3/`，不要把邏輯寫回 `legacy/tools/`。  
- 保持標準庫為主；新依賴需有充分理由並寫入 `pyproject.toml`。  
- 模組說明見 [docs/development.md](docs/development.md)。

---

## 關於 `legacy/`

- 舊工具與歷史 TSV，掃描時可能當「建議譯法」讀取。  
- **內容可能不完整、過期或有錯別字**，請勿直接當正式譯文大批合併進 `data/`。  
- 正式譯文以 `data/translations.tsv`、`data/new_translations.tsv` 為準。  

---

## 行為與授權

- 勿提交遊戲資源（`src_file` 內實際檔案已被 gitignore）。  
- 勿提交 `output/`、`dboc.toml`、本機路徑隱私。  
- 程式碼授權見 [LICENSE](LICENSE)（MIT）。遊戲資源與商標歸原權利人。  

有疑問可先開 Issue 說明場景與重現步驟。
