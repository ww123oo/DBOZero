# tbl2.pak 暫不漢化（閃退规避）

目前套用 `tbl2.pak` 譯文會導致客戶端一開就閃退。

## 建議本機 build_output 行為

`SKIP_TBL_PATCH_FILES = {"tbl2.pak"}`：

- **tbl2**：只複製**原版**（不套翻譯）
- **lang0 / tbl0 / tbl1**：照常漢化

遊戲可開；tbl2 相關字串可能仍是原文／簡中。

## 本機急救（不重 build）

```powershell
# 用源或啟動器修復後的原版蓋回遊戲
Copy-Item "（原版）\DBOZero\pack\tbl2.pak" "（遊戲）\DBOZero\pack\tbl2.pak" -Force
```

## 恢復漢化 tbl2

修好 `tbl_utf16_patch` 後，在 `build_output.py`：

```python
SKIP_TBL_PATCH_FILES = frozenset()
```

再 `dboc build --variant taiwan --force`。
