# DBOZero 即時更新／翻譯流程交接文件

> 給下一個 AI / 開發者接手用。本文描述目前已完成、目前問題，以及下一步必須實作的「遊戲更新 → 掃描 → 繼承舊譯文 → 新增翻譯 → 寫入資源 → 建置驗證」完整流程。

## 1. 專案目標

本專案不是只維護舊的 `data/translations.tsv`，而是要建立一套可持續更新的 DBO 資源翻譯系統。

每次遊戲更新後，實際遊戲原始資源是唯一的「目前需要翻譯什麼」的來源。

需要掃描：

- `lang0.pak`
- `tbl0.pak`
- `tbl1.pak`
- `tbl2.pak`
- 所有 `*.rdf`
- 所有 `*.xml`
- 所有 `*.dat`

明確排除：

- `*.bin`：不可掃描、不可修改、不可加入翻譯流程。

## 2. 翻譯資料的角色

### `data/translations.tsv`

原作者留下的歷史翻譯資料。

- 只作為歷史參考、舊譯文繼承來源。
- 不能假設它完整。
- 原作者停止維護後新增的遊戲資源不會自動存在其中。

### `data/new_translations.tsv`

現在的主要工作表。

- 每日新增翻譯放這裡。
- 每次遊戲更新掃描出的新詞條也放這裡。
- 已經翻譯的項目必須盡量透過穩定 ID／來源雜湊繼承，不能因檔案更新就重新翻譯。
- 不應把它當成掃描器的唯一來源；實際遊戲資源才是 source of truth。

### `reports/internal/untranslated_candidates.tsv`

掃描與翻譯比對後產生的候選報告。

- 供 AI／人工翻譯工作使用。
- 不應拿它直接當遊戲資源。

## 3. 已完成的掃描器

檔案：`hanhua_v3/runtime/full_text_scanner.py`

目前支援：

- `lang0.pak` key/value
- `tbl0.pak`
- `tbl1.pak`
- `tbl2.pak`
- `*.rdf`
- `*.xml`
- `*.dat`

輸出欄位：

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

### `tbl2.pak` 特別規則

已確認 `tbl2.pak` 有結構化記錄：

```text
uint32 ID
uint8 type
uint16 UTF-16 code-unit length
UTF-16LE text
```

掃描器會把這類記錄標成：

```text
kind=tbl2_record
id=<穩定數字 ID>
```

不能把 `tbl2.pak` 當普通 UTF-16 檔案做全域取代。

## 4. 已完成的 tbl2 安全寫入

檔案：`hanhua_v3/runtime/tbl_utf16_patch.py`

已具備：

- 固定長度 UTF-16LE 替換
- 原文驗證
- 長度驗證
- `tbl2` 穩定 ID 定位
- 找不到／重複 ID 時 fail-closed
- 不允許改變資源檔案大小

`tbl2` 應優先使用：

```text
id:<ID>
```

而不是單純 offset。

## 5. 已完成的通用資源寫入器

檔案：`hanhua_v3/runtime/resource_writer.py`

支援：

- `.pak`
- `.rdf`
- `.xml`
- `.dat`
- `.bin` 明確拒絕
- `lang0.pak` 使用 key 定位
- `tbl0/tbl1/tbl2` 使用 tbl patcher
- DAT 支援 key/value 字串

寫入器目前的設計原則是：

> 翻譯錯誤時停止，不要猜位置，不要破壞原始資源。

## 6. 目前 CLI 流程

檔案：`hanhua_v3/cli.py`

目前 `dboc update` 已經是：

```text
[1/5] 同步實際遊戲源檔案
        ↓
[2/5] 掃描新版詞條
        ↓
[3/5] 翻譯新增詞條
        ↓
[4/5] 寫入翻譯資源
        ↓
[5/5] 構建並驗證補丁
```

但是這條流程目前仍有兩個重要缺口，下一個 AI 必須先處理。

## 7. 第一個重要缺口：`run_scan()` 尚未接入完整掃描器

目前 `run_scan()` 呼叫舊的：

```python
scan.main(...)
```

而不是直接把：

```python
hanhua_v3.runtime.full_text_scanner
```

的結果併入新的翻譯佇列。

下一步應建立安全的 bridge / inventory layer，最好新增模組，不要大幅重寫舊 `hanhua_v3/scan.py`。

建議：

```text
actual game resources
        ↓
full_text_scanner.py
        ↓
canonical inventory / queue
        ↓
legacy translations.tsv + new_translations.tsv
        ↓
inherit existing translations
        ↓
new_translations.tsv
```

## 8. 第二個重要缺口：寫入後建置來源不一致

目前 `run_update()` 的第 4 步會：

```text
source_dir → resource_writer → output_taiwan
```

但第 5 步 `run_build()` 目前仍把：

```text
args.source_dir
```

傳給 `build_output`。

也就是說「寫入後的 `output_taiwan`」與「builder 使用的來源」目前沒有完全對齊。

下一個 AI 必須先確認 `build_output` 的真正輸入／輸出語意，再修改流程。

**不要猜。**

`build_output.py` 是 launcher，真正實作位於：

```text
scripts/build_output_p0.b64
scripts/build_output_p1.b64
scripts/build_output_p2.b64
```

目前 `p0` 在 GitHub 上顯示為 `PLACEHOLDER`，因此在 builder 尚未確認前，不要宣稱 build 已完整可用。

## 9. 正確的即時更新流程（目標設計）

遊戲發布新版本後：

```text
官方未修改／未打補丁的遊戲目錄
        │
        ▼
[1] dboc update
        │
        ├─ 建立 Git checkpoint
        │
        ├─ refresh 實際遊戲資源
        │
        ▼
[2] 完整掃描
        │
        ├─ lang0.pak
        ├─ tbl0.pak
        ├─ tbl1.pak
        ├─ tbl2.pak
        ├─ *.rdf
        ├─ *.xml
        └─ *.dat
        │
        ▼
[3] 建立 canonical inventory
        │
        ├─ 穩定 ID 優先
        ├─ key 優先
        ├─ 必要時使用 offset
        └─ source_hash 作為內容變更判斷
        │
        ▼
[4] 翻譯繼承
        │
        ├─ new_translations.tsv
        ├─ translations.tsv
        └─ Git 歷史 recovery
        │
        ▼
[5] 產生真正的新候選
        │
        └─ 只把「目前 source 中尚未有可靠譯文」的項目列為 new
        │
        ▼
[6] AI／人工翻譯
        │
        └─ 寫入 data/new_translations.tsv
        │
        ▼
[7] resource_writer
        │
        ├─ tbl2 用 ID 安全寫入
        ├─ lang0 用 key
        ├─ DAT 用 key / 結構定位
        └─ 其他格式驗證原文後寫入
        │
        ▼
[8] build
        │
        ├─ 使用已寫入資源
        ├─ 產生 output/release
        └─ 驗證大小／格式／可回滾
        │
        ▼
[9] Git commit
        │
        └─ 只提交程式、翻譯表、報告／文件
           不提交 src_file/DBOZero 遊戲資源
```

## 10. 每次遊戲更新的預期操作

使用者只需要準備：

1. 官方新版本遊戲完整目錄。
2. 不要先自行把中文補丁打進去。
3. 執行：

```bash
python -m hanhua_v3.cli update --game-dir "你的遊戲目錄" --translate-all
```

如果要只處理本次新增項目，預設不要 `--translate-all`。

日常檢查：

```bash
dboc status --game-dir "你的遊戲目錄"
```

只刷新官方源：

```bash
dboc refresh --game-dir "你的遊戲目錄"
```

只掃描：

```bash
dboc scan
```

手動翻譯：

```bash
dboc translate
```

寫入：

```bash
dboc write
```

建置：

```bash
dboc build --variant taiwan
```

## 11. 穩定定位規則

優先級：

### lang0

```text
id = key
```

例如：

```text
DST_SCOUTER_ON_MENU
```

### tbl2

```text
id = numeric stable ID
kind = tbl2_record
```

例如：

```text
id=1001
kind=tbl2_record
```

### DAT

```text
id = DAT key
kind = dat_entry
```

### XML / RDF

若能取得穩定 key / ID，優先使用 key / ID；否則使用 offset + source_hash。

### tbl0 / tbl1

目前主要依賴安全的 offset + 原文驗證；如果後續能解析出穩定 ID，應升級為 ID 定位。

## 12. 不能做的事

禁止：

- 掃描 `.bin`
- 修改 `.bin`
- 把 `.bin` 加入 scanner whitelist
- 用全域 UTF-16 replace 修改 `tbl2.pak`
- 找不到翻譯位置時自行猜 offset
- 翻譯表直接覆蓋掉已有可靠譯文
- 把實際遊戲資源 commit 到 Git
- 把 `reference-resources` 的大型參考檔搬回 `main`

## 13. `reference-resources` 分支

大型參考資源保留在：

```text
reference-resources
```

`main` 不應放大型原始資源。

已知曾保留於 reference branch 的大型 XML：

- `table_quest_text_data.xml`
- `table_quest_text_data(台服原版).xml`
- `table_text_all_data.xml`
- `table_text_all_data(台服原版).xml`

指定的 RDF / DAT 參考檔若未存在於目前 Git tree，不可自行捏造加入。

## 14. 下一個 AI 的實作順序

請嚴格依照這個順序：

### P0 — 先修 builder 流程

1. 找出 `build_output` 真正實作。
2. 確認 source_dir / output_dir 的真正語意。
3. 確保 update 的第 4 步寫入內容會真正進入第 5 步 build。
4. 加測試。

### P1 — 完整 scanner bridge

1. 不重寫舊 `scan.py`。
2. 建立新 bridge。
3. 接入 `full_text_scanner`。
4. 把 scanner 結果轉成 canonical queue。
5. 保留 legacy translation。
6. 保留 daily translation。
7. 優先使用 stable ID / key。

### P2 — 修正 update 的新增判斷

目前 `queue_keys_from_rows()` 仍主要使用：

```text
(file, source_text)
```

這對 stable ID 不夠理想。

應升級為：

```text
(file, id, source_text)
```

並對沒有 ID 的項目退回：

```text
(file, source_hash)
```

不要只靠 source text 全域匹配。

### P3 — malformed legacy TSV

`data/translations.tsv` 已知曾出現過欄位數異常的資料列。

下一個 AI 使用它前，應先：

1. 找出異常列。
2. 判斷是內容中的 tab 還是欄位真的錯誤。
3. 最小修改修復。
4. 加 TSV validation test。

### P4 — end-to-end test

至少測試：

```text
官方新資源
  ↓
scanner
  ↓
new candidate
  ↓
舊譯文繼承
  ↓
新翻譯
  ↓
writer
  ↓
output
  ↓
build
```

並特別測：

- tbl2 ID patch
- tbl2 missing ID fail-closed
- tbl2 duplicate ID fail-closed
- DAT key/value patch
- lang0 key patch
- XML/RDF patch
- `.bin` rejected
- output size unchanged where fixed-size format requires it

## 15. Git 操作原則

每完成一個邏輯單元就 commit，例如：

```text
docs: add realtime translation update handoff flow
fix: align build input with patched output
feat: bridge full resource scanner into translation queue
fix: use stable ids for update diff
fix: repair legacy translation TSV row
 test: add end-to-end translation update flow
```

不要一次把所有東西混在一個巨大 commit。

## 16. 最重要的一句話

> **遊戲更新後，重新掃描實際資源；翻譯表只是用來繼承已知譯文，不是用來決定目前遊戲有哪些文字。**

這是整個「即時更新翻譯系統」的核心。
