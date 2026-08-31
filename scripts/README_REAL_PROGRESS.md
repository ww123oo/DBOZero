# 真實 build 進度條

`dboc build` 預設會顯示固定 9 步的假進度。請執行：

```bash
python scripts/install_real_progress.py
```

會安裝：
- `build_output.py`（依 lang0/tbl **實際列數**推進）
- `hanhua_v3/runtime/build_progress.py`（同行 `\\r` 更新）

然後：

```bash
dboc build --variant taiwan
```

進度會顯示類似：

```
  · 實際工作量：lang0 3200 列 + tbl 18000 單位 + 其他 5 步
  [████░░░░…] 23% (1234/5000) lang0 1234/3200
```
