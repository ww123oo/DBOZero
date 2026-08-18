# 開發者文件

面向想修改工具鏈本身或深入了解流程的開發者。日常翻譯規則見
`docs/translation-rules.md`。

## 模組結構

- `hanhua_v3/cli.py`：`update/refresh/scan/translate/recover/build/status/config` 命令編排。
- `hanhua_v3/config.py`：本機設定（`dboc.toml`）、環境變數與遊戲目錄自動探測。
- `hanhua_v3/source.py`：從遊戲目錄只讀同步 9 個必要源資源，逐檔案 SHA-256 校驗。
- `hanhua_v3/scan.py`：掃描 Taiwan、lang0 和 TBL，刷新翻譯佇列與內部稽核表。
- `hanhua_v3/batch_translate_queue.py`：保留格式、佔位符和內部識別邊界的批量翻譯器。
- `hanhua_v3/glossary.py`：人工校訂的精確術語。
- `hanhua_v3/recover.py`：從 Git 歷史 TSV 恢復仍匹配當前源的譯文。
- `hanhua_v3/policy.py`：掃描與構建共用的源保留策略（如 TBL 內部權杖黑名單）。
- `hanhua_v3/runtime/`：構建／掃描實際依賴的補丁模組（`install_hanhua`、`lang0_gbk_patch`、`tbl_utf16_patch`、`console_color`、`auto_translate_new_source`）。它們來自 `legacy/tools`，此處是唯一維護副本；`legacy/tools/` 只保留相容墊片。
- `build_output.py`：構建大陸簡中／台灣繁中兩套輸出的入口，由 `dboc build` 呼叫。

## 安裝與執行

```powershell
pip install -e .        # 提供跨平台 dboc 命令（可編輯安裝，工作區即倉庫）
dboc config --game-dir "E:\DBO Zero 2.0"   # 或依賴自動探測 / DBOC_GAME_DIR
dboc update
```

注意：工具以倉庫根目錄為工作區（`data/`、`src_file/`、`output/` 都是相對它的），
因此只支援**可編輯安裝**（`pip install -e .`）或在倉庫根目錄直接
`python -m hanhua_v3`。非可編輯的全域安裝會讓工作區定位失效。

## 工作區目錄

- `data/`：翻譯主表與日常佇列（入庫，核心資產）。
- `src_file/DBOZero/`：源快照，從本機遊戲只讀同步（不入庫，見 `src_file/README.md`）。
- `output/`、`output_taiwan/`：產生的補丁（不入庫）。
- `release/`：本機打包的歷史發布（不入庫）。
- `reports/internal/`：掃描與稽核產物（不入庫）。
- `legacy/`：歸檔的舊工具、舊 TSV 和歷史參考資料；`legacy/translations/`、`legacy/candidates/` 仍被掃描器作為歷史譯法來源讀取。
- `scripts/`：專項恢復工具，不是日常入口。

## 驗證

改動程式碼後按以下順序自檢：

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
dboc status
dboc build
```

構建完成後重點檢查 `pack/lang0.pak`、`pack/tbl0.pak`、`pack/tbl1.pak` 的
`missing` 計數（應為 0）。不要把 `legacy/tools/validate_output.py` 當作
v3 的驗證門檻。

CI（`.github/workflows/ci.yml`）在 Windows 和 Ubuntu、Python 3.9/3.12 上
執行編譯檢查、單元測試和 CLI 冒煙測試。

## 程式碼約定

- Python 3，只用標準庫；新增依賴需要有明確理由並在 `pyproject.toml` 宣告。
- 測試統一放 `tests/`，用 pytest。
- 改動保持最小化，範圍限於 v3 流程內；legacy 只用於歷史恢復。
