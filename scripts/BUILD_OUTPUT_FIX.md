# 本機取得最新 build_output / 進度條

## 1. 拉進度條（已在 repo）

```powershell
cd J:\OpenDBO-Localization-main\DBOZero-main
git pull
# hanhua_v3/runtime/build_progress.py 已含：分秒、完成時間、busy_line
```

## 2. 完整 build_output（約 52KB，含多線程 +「正在寫入中…」）

GitHub 上根目錄 `build_output.py` 可能仍是 stub。請用其中一種：

### A. 從 artifacts / 同步資料夾拷完整檔（推薦）

```powershell
Copy-Item "（artifacts）\build_output_FULL_49997.py" .\build_output.py -Force
(Get-Item .\build_output.py).Length
# 應約 50000+
```

### B. 分片展開（若 scripts/bo_pay_0..3.txt 齊全）

```powershell
python scripts\install_build_output_parts.py
```

若 bo_pay 仍是佔位或缺失，請用方式 A。

## 3. 清快取後 build

```powershell
Remove-Item -Recurse -Force .\hanhua_v3\runtime\__pycache__ -ErrorAction SilentlyContinue
dboc build --variant taiwan --force
```

## 進度條預期

- 階段完成：`完成 (18s)` / `完成 (1分05秒)`
- tbl 等待：`正在寫入中. .. ...`（同一行、多線程）
- 不做 `0/3` 假百分比
