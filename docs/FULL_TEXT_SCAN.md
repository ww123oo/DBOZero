# DBO 全面文字掃描

本工具把「找文字」與「修改 PAK」分開，避免把二進位資料誤當成文字而造成遊戲閃退。

## 掃描

在 DBOZero 根目錄執行：

```text
python scan_all_text.py
```

預設掃描 `src_file/DBOZero`，包含：

- `lang0.pak`
- `tbl0.pak`
- `tbl1.pak`
- `tbl2.pak`
- 其他 `.pak` / `.rdf` / `.xml` / `.dat` / `.bin`

結果輸出為 `translation_scan.tsv`，包含檔名、offset、編碼、長度、可信度與原文。

## 重要安全規則

掃描器是唯讀的，不會直接修改遊戲檔案。

`tbl2.pak` 目前使用已確認的記錄格式驗證後才允許 patch：`uint32 id + uint8 type + uint16 little-endian 字元數 + UTF-16LE 文字`。任何無法驗證的 offset 都會拒絕修改。

翻譯文字若超過原固定欄位長度也會拒絕寫入，不會自動插入 bytes 或移動後面的資料。
