# Changelog

All notable changes to DBOZero are documented here.

## [v0.1.0] — 2026-09-09

### Added

- 完整文字掃描流程，依實際遊戲資源建立文字索引。
- 掃描 `lang0.pak`、`tbl0.pak`、`tbl1.pak`、`tbl2.pak`。
- 掃描 `*.rdf`、`*.xml`、`*.dat` 文字資源。
- DAT 結構化文字項目辨識。
- 翻譯 inventory 與每日新翻譯佇列。
- 舊翻譯繼承機制，避免重複翻譯。
- `tbl2.pak` 穩定 ID 定位與 fail-closed 寫入策略。
- 原始資源完整鏡像後再套用翻譯的 resource writer 流程。
- 簡體中文與台灣繁體中文獨立建置。
- `dboc release` 雙語 Release Gate：兩個產品都通過驗證後才算發布通過。
- 建置與發布流程文件：`docs/BUILD_PIPELINE.md`。
- 遊戲更新後的即時更新流程文件：`docs/REALTIME_UPDATE_FLOW.md`。

### Validation

- Windows / Python 3.9 — PASS
- Windows / Python 3.12 — PASS
- Ubuntu / Python 3.9 — PASS
- Ubuntu / Python 3.12 — PASS
- Compile check — PASS
- Unit tests — PASS
- CLI smoke test — PASS

### Release scope

這個版本是**工具鏈首個公開基準版本**，不是「所有 DBO 文字都已完成翻譯」的宣告。

GitHub CI 不包含使用者本機的完整 DBO 遊戲資源，因此拿到最新遊戲版本後，仍需在具備實際資源的環境執行：

```powershell
dboc release
```

並完成實機測試後，才適合交付最終漢化包。
