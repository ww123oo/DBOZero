# GitHub vs 本機（2026-09-02）

## 已在 GitHub（近期）
- 進度條 B 版、MemoryError 修復、制→製 規則、SCS SEND=驗證 等（Sep 1 commits）
- 你上傳的 `table_*.xml`（commit af272239）

## 仍落後 / 殘缺
| 項目 | GitHub 現況 | 本機 artifacts |
|------|-------------|----------------|
| `build_output.py` | **437B stub**（要跑 installer） | ~50KB 完整版 |
| `scripts/install_real_progress.py` | 958B 委派腳本 | 完整自包含 installer 在 artifacts |
| client `local_*.dat` | `data/client_local/` 只有 README | 有 LOCKED 私服版 |
| 台服原版對照 | 無 | `舊譯表/台服原版/` |

## 為何看起來像「前幾天」
完整 `build_output.py` 因體積／工具限制長期用 stub + installer 方式，沒有整份進 repo 根目錄。
若 `git pull` 後沒再跑 installer，本機就會回到 stub，以為「退回舊版」。

## 本機正確流程
```
python scripts/install_real_progress.py
# 或用 artifacts 的 install_parallel_build.py
dboc build --variant taiwan
```
