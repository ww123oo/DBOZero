# build_output 展開失敗（Missing p0.b64）時

根目錄 `build_output.py` 若只有 ~1KB，是 stub，需展開成完整 ~50KB。

## 本機急救（推薦）

```powershell
cd J:\OpenDBO-Localization-main\DBOZero-main

# 方式 1：直接蓋完整檔（約 49997 bytes）
# 把 build_output_FULL_49997.py 複製為 build_output.py

# 方式 2：一鍵腳本（會寫 p0-p2 並展開）
python scripts\install_build_output_parts.py

(Get-Item .\build_output.py).Length
# 應接近 50000

dboc build --variant taiwan
```

## 修好後推回 GitHub（本機有 push 權限時）

```powershell
git add build_output.py scripts/build_output_p0.b64 scripts/build_output_p1.b64 scripts/build_output_p2.b64 scripts/install_build_output_parts.py
git commit -m "fix: full build_output payload (StageProgress+ThreadPool)"
git push
```

不要用已截斷的 PLACEHOLDER 分片。
