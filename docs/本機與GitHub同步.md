# 本機與 GitHub 同步說明

倉庫：https://github.com/ww123oo/DBOZero  
本機路徑範例：`J:\OpenDBO-Localization-main\DBOZero-main`

---

## 一、從 GitHub 更新到本機（最常用）

別人（或遠端）改了翻譯／腳本，本機要跟上：

```powershell
cd J:\OpenDBO-Localization-main\DBOZero-main
git pull
python scripts\install_tbl_batch3.py
python scripts\merge_translations.py
dboc build --force
```

有未完成的 merge 時，先看狀態再處理（見下方「常見問題」）。

---

## 二、本機改動上傳到 GitHub

### 建議流程

```powershell
cd J:\OpenDBO-Localization-main\DBOZero-main

# 1. 先拉遠端，減少衝突
git pull

# 2. 看改了哪些檔
git status

# 3. 只加入「要進倉庫」的檔（見下方白名單）
git add data/new_translations.tsv
# 若有自己的 delta：
# git add data/我的修正_delta.tsv
# git add scripts/merge_translations.py

# 4. 提交
git commit -m "i18n: 說明這次改了什麼"

# 5. 推上 GitHub
git push
```

### 第一次若提示身分未知

```powershell
git config user.name "dboc"
git config user.email "dboc-local@localhost"
```

（僅本機倉庫即可，不一定要 `--global`。）

---

## 三、可以上傳（白名單）

| 路徑 | 說明 |
|------|------|
| `data/new_translations.tsv` | 主翻譯表 |
| `data/*_delta.tsv` | 分批譯文（如 `tbl_batch19_delta.tsv`） |
| `data/lang0_s2t_delta.tsv` | lang0 簡→繁修正 |
| `scripts/merge_translations.py` | 合併腳本 |
| `scripts/install_tbl_batch3.py` | batch3 安裝 |
| `hanhua_v3/` 下正式程式 | CLI／進度條等 |
| `docs/` | 說明文件 |

---

## 四、本機的不要上傳到 GitHub（黑名單）

這些是本機掃描、除錯或暫存，**不要 `git add`、不要 push**：

| 檔案／目錄 | 原因 |
|------------|------|
| `untranslated_only.tsv` | 本機掃未譯清單，隨時可變 |
| `debug.log` | 除錯日誌 |
| `output/`、`output_taiwan/` | 建置產物，體積大且可重建 |
| `src_file/` 遊戲本體複本 | 若有，屬本機資源 |
| `__pycache__/`、`*.pyc` | Python 快取 |
| `.env`、含密碼／Token 的檔 | 機密 |
| 個人備註、暫存 zip、截圖資料夾 | 與倉庫無關 |

若已被 Git 追蹤、想停止追蹤但保留本機檔：

```powershell
git rm --cached untranslated_only.tsv
git commit -m "chore: 停止追蹤本機掃描檔"
git push
```

可在倉庫根目錄 `.gitignore` 加入例如：

```
untranslated_only.tsv
debug.log
output/
output_taiwan/
__pycache__/
*.pyc
```

---

## 五、常見問題

### 1. `MERGE_HEAD exists` / 未完成合併

```powershell
git status
```

- **衝突已解、只差結束合併：**

```powershell
git commit -m "merge: 完成合併"
git pull
git push
```

- **這次合併不要了：**

```powershell
git merge --abort
```

### 2. `Your branch and origin/main have diverged`

本機與遠端各有不同 commit。先：

```powershell
git pull
```

若自動開編輯器寫 merge 訊息，存檔離開即可；再 `git push`。

### 3. push 被拒絕（rejected）

```powershell
git pull
git push
```

### 4. 大檔 `new_translations.tsv`

可直接改主表再 push；若只改少數條，也可另存 `data/xxx_delta.tsv`，本機：

```powershell
python scripts\merge_translations.py
```

再決定要不要把 delta 與主表一起 commit。

---

## 六、建議日常節奏

1. 開工前：`git pull` → `merge_translations` → 需要時再 `dboc build`  
2. 本機改完翻譯：只 `add` 白名單 → `commit` → `push`  
3. 不要把 `untranslated_only.tsv`、`output*`、log 推上 GitHub  
