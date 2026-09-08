# DBOZero 建置與發布流程

本文件定義 DBOZero 的雙語建置規則。**只有兩個語言產品都獨立建置並通過驗證，才可以交付使用者。**

## 1. 兩個產品

| 產品 | CLI 變體 | 輸出目錄 | Builder 內部名稱 |
|---|---|---|---|
| 簡體中文 | `simplified` | `output/` | `mainland` |
| 台灣繁體中文 | `taiwan` | `output_taiwan/` | `taiwan` |

兩個產品共用同一份 canonical source tree，但輸出目錄與語言轉換流程彼此獨立。

## 2. 單獨建置

只建簡體：

```bash
dboc build --variant simplified
```

只建台灣繁體：

```bash
dboc build --variant taiwan
```

需要排除平行工作時：

```bash
dboc build --variant simplified --no-parallel
dboc build --variant taiwan --no-parallel
```

每個 variant 都由 `build_output.py` 個別執行並個別驗證；其中一個失敗，不會被另一個產品的成功掩蓋。

## 3. 雙語 Release Gate

正式發布使用：

```bash
dboc release
```

Release Gate 會依序：

1. 建置簡體中文產品。
2. 驗證簡體中文產品。
3. 簡體 PASS 後才建置台灣繁體中文產品。
4. 驗證台灣繁體中文產品。
5. **兩者都 PASS 才輸出 Release Gate PASS。**

任何一個產品失敗，都立即停止，不能宣稱雙語版本完成。

因此：

```text
             dboc release
                  │
        ┌─────────▼─────────┐
        │ 簡體 build + test │
        └─────────┬─────────┘
                  │ PASS
        ┌─────────▼─────────┐
        │ 繁體 build + test │
        └─────────┬─────────┘
                  │ PASS
                  ▼
          RELEASE GATE PASS
                  │
                  ▼
             才能交付
```

## 4. Update 流程

遊戲更新後，標準流程是：

```text
官方原版遊戲目錄
       ↓
dboc update
       ↓
refresh
       ↓
完整掃描
       ↓
翻譯繼承 + 新增翻譯
       ↓
resource_writer
       ↓
build + validation
```

掃描範圍包含：

- `lang0.pak`
- `tbl0.pak`
- `tbl1.pak`
- `tbl2.pak`
- `*.rdf`
- `*.xml`
- `*.dat`

實際遊戲原始資源是目前需要翻譯內容的 source of truth。

## 5. `tbl2.pak` 安全規則

`tbl2.pak` 必須使用結構化記錄與穩定 ID 寫入。

不得使用全域 UTF-16 字串取代，也不得在定位失敗時猜 offset。

寫入失敗時採 fail-closed：停止流程，不產生可能損壞的發布包。

## 6. Git 與資源管理

Git `main` 只保留程式、翻譯資料、測試與文件，不提交大型實際遊戲資源。

大型參考資源放在：

```text
reference-resources
```

正式發布前應確認工作樹沒有意外加入遊戲原始資源。

## 7. 驗證標準

CI 至少必須通過：

- Python 3.9 / 3.12
- Linux / Windows
- compile check
- unit tests
- CLI smoke test

實際發布則另外要求：

- 簡體產品 build + validation PASS
- 台灣繁體產品 build + validation PASS
- 兩者均使用同一版本的 canonical source
- 不得因其中一個成功而跳過另一個驗證

## 8. 目前限制

GitHub CI 不包含使用者本機的完整 DBO 遊戲資源，因此 CI 綠燈代表程式碼與測試通過，不等同於已用最新遊戲資源產生實機發布包。

拿到官方新版本完整原始遊戲目錄後，仍需在具備資源的環境執行 `dboc release`，確認兩個實際產品都 PASS，才能交付。
