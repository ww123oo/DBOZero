# StageProgress build_output

GitHub `build_output.py` is a **bootstrap**. On first `dboc build` / `python build_output.py` it expands the full ~52KB StageProgress file from payload parts.

## If expand fails (missing segments)

Copy the full file from the project artifacts folder (synced):

```powershell
Copy-Item "<artifacts>\build_output.py" .\build_output.py -Force
(Get-Item .\build_output.py).Length   # expect ~52000
Select-String -Path .\build_output.py -Pattern "begin_stage"
```

Then optionally push so others get it:

```powershell
git add build_output.py
git commit -m "feat: StageProgress build_output full"
git push origin main
```

## Verify progress UI

```powershell
dboc build --variant taiwan --force
```

Expect lines like `[████] 100% (1/1) 讀取翻譯表 完成` not only `Loaded master translations`.
