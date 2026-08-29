# data/ — 翻譯資料

## ★ 主表（務必保留）

| 檔案 | 用途 |
|------|------|
| **`new_translations.tsv`** | 新詞主表（欄位：来源／文件／位置／原文／参考译文／填写中文／长度状态） |
| **`translations.tsv`** | 舊譯主表 |

**不要手動刪改欄位名。** 整理 `archive/` 時只動 `*_delta.tsv`，**不要動**這兩張主表。

若懷疑主表壞掉，可從歷史還原（列數應約 **28935**）：

```text
merge 前（tbl2 中文較少、較不易閃退）:
  https://raw.githubusercontent.com/ww123oo/DBOZero/ee96361013ba07d19751754fba4c9b1fafea6a2b/data/new_translations.tsv

merge 後（tbl2 幾乎全中，需跑 fix_tbl2_overlong）:
  https://raw.githubusercontent.com/ww123oo/DBOZero/fa7d4711c7bc83bb38843358a457cebe77ad76c1/data/new_translations.tsv
```

### tbl2 閃退時

```powershell
python scripts\fix_tbl2_overlong.py
dboc build --variant taiwan
```

會清空「中文字節數 > 英文原文」的 tbl2 譯文（約數百條），其餘保留。

---

## 其他

- `*_delta.tsv` / `archive/`：歷史增量，可歸檔
- `gui_font.ini`：字型設定
