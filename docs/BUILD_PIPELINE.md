# DBOZero 建置與發布流程

本文件定義 DBOZero 的雙語建置規則。兩個語言產品使用同一份 canonical source tree 與同一份翻譯佇列，但各自獨立執行寫入與格式驗證。

## 1. Canonical pipeline

```text
官方原版資源
     ↓
 dboc refresh
     ↓
完整 scanner
     ↓
translation queue
     ↓
翻譯／術語正規化
     ↓
 canonical builder
     ↓
 resource_writer
     ↓
 resource_validator
     ↓
語言產品輸出
```

`build_output.py` 是目前 canonical builder。寫入前從 pristine source mirror 建立輸出樹，避免直接在原始資源上修改。

## 2. 兩個產品

| 產品 | CLI 變體 | 輸出目錄 | Builder 內部名稱 |
|---|---|---|---|
| 簡體中文 | `simplified` | `output/DBOZero/` | `mainland` |
| 台灣繁體中文 | `taiwan` | `output_taiwan/DBOZero/` | `taiwan` |

雙語一次建置：

```bash
dboc build --variant all --force
```

只建單一產品：

```bash
dboc build --variant simplified --force
dboc build --variant taiwan --force
```

`--queue` 可指定目前要使用的翻譯佇列：

```bash
dboc build --variant taiwan --queue data/new_translations.tsv --force
```

## 3. 寫入策略

`resource_writer` 依資源格式選擇專用 writer：

| 資源 | 寫入方式 |
|---|---|
| `lang0.pak` | key 導向、依原始檔 UTF-8/GBK 判定 |
| `tbl0.pak` / `tbl1.pak` | UTF-16LE 固定欄位、offset 定位 |
| `tbl2.pak` | stable ID 結構化定位、UTF-16LE 固定欄位 |
| 其他 `.pak` | offset 定位的固定寬度文字欄位；UTF-16 可補 NUL，其他編碼必須維持 byte 寬度 |
| `*.rdf` / `*.xml` | 文字內容 offset 定位，可依原文長度改變檔案大小 |
| `*.dat` | 結構化 key/value 或 offset 定位 |

所有 writer 都採 fail-closed：source mismatch、offset 無效、欄位過長、格式條件不符合時停止。

## 4. `tbl2.pak` 規則

`tbl2.pak` 翻譯不得依賴全檔搜尋到的任意 UTF-16 字串位置。

目前 structured scanner 會保留 stable numeric ID；builder 只接受該 ID 作為正式 `tbl2` record locator。寫入前後會檢查：

- uint32 record ID
- record type
- UTF-16 code-unit length
- 原固定欄位大小
- 翻譯後 UTF-16LE bytes 與 NUL padding
- source → output 的 deterministic patch 是否完全一致

翻譯超過固定欄位時直接失敗，不會擴大 `tbl2.pak`。

## 5. Deterministic validation

`resource_validator` 會從 pristine source 重建每個 touched resource 的預期輸出，再與實際 build output 做 byte-for-byte 比對；`tbl2` 另外做 stable-ID 結構檢查。

全域輸出檢查包括：

- source/output 檔案樹完全一致
- `.pak` 檔案大小不變
- 所有翻譯 rows 都能重建
- 輸出內容與 deterministic patch result 相同

這些是程式與資源格式檢查，不包含遊戲內測試要求。

## 6. Scan → Queue

`dboc scan` 會：

1. 從 `src_file/DBOZero` 掃描 `lang0/tbl0/tbl1/tbl2/*.pak/*.rdf/*.xml/*.dat`。
2. 結構化項目保留穩定 locator。
3. `translation_queue` 先以完整相對路徑匹配，再安全地使用唯一 basename/hash fallback，以支援舊佇列遷移。
4. 更新 `data/new_translations.tsv` 與候選報告。

同一個 structured hit 不會再被 generic UTF-16 scanner 重複加入 queue。

## 7. Release Gate

正式發布使用：

```bash
dboc release --force
```

Release Gate 依序：

1. 建置簡體中文。
2. 通過 build validation 後才建置台灣繁體中文。
3. 台灣繁體中文也通過 build validation。
4. 兩者都 PASS 才輸出 Release Gate PASS。

Release Gate 不會啟動遊戲，也不把遊戲內測試當成自動化通過條件。

## 8. Update 流程

遊戲更新後：

```text
官方原版遊戲目錄
       ↓
dboc update
       ↓
refresh
       ↓
完整掃描
       ↓
歷史譯文繼承
       ↓
新增詞條翻譯
       ↓
dboc build --variant all
       ↓
writer + validator
```

打過補丁的資源不要反向作為 refresh source。

## 9. CI 與實際資源

CI 會在 Windows / Linux × Python 3.9 / 3.12 執行：

- package install
- Python compile check
- unit tests
- CLI smoke test

CI 不包含使用者本機的完整 DBO 遊戲資源，因此 CI 綠燈代表工具程式與測試通過，不代表 CI 已產生正式遊戲資源包。

拿到官方新版本完整資源後，應在具備資源的環境執行 `dboc scan` 與 `dboc release`。

## 10. Git 與資源管理

Git `main` 只保留程式、翻譯資料、測試與文件，不提交大型實際遊戲資源。

大型參考資源維持在 `reference-resources`，而 `src_file/`、`output*` 與遊戲本體維持本機使用。
