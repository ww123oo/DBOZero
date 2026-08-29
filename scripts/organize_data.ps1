# 將 data/ 下歷史 delta 歸檔，讓結構更清楚。
# 使用前請先：git pull；python scripts\merge_translations.py（確認主表已合併）
# 然後在倉庫根目錄執行：powershell -ExecutionPolicy Bypass -File scripts\organize_data.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$data = Join-Path $root "data"
$arch = Join-Path $data "archive"

New-Item -ItemType Directory -Force -Path (Join-Path $arch "batches") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $arch "term_fixes") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $arch "ui_deltas") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $arch "misc") | Out-Null

function Move-Glob($pattern, $dest) {
    Get-ChildItem -Path $data -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Force $_.FullName (Join-Path $dest $_.Name)
        Write-Host "moved $($_.Name) -> $dest"
    }
}

Move-Glob "tbl_batch*_delta.tsv" (Join-Path $arch "batches")
Move-Glob "tbl_batch_delta.tsv" (Join-Path $arch "batches")
Move-Glob "tbl0_full_delta.tsv" (Join-Path $arch "batches")
Move-Glob "term_*.tsv" (Join-Path $arch "term_fixes")
Move-Glob "place_*.tsv" (Join-Path $arch "term_fixes")
Move-Glob "length_*.tsv" (Join-Path $arch "term_fixes")
Move-Glob "tbl_length_*.tsv" (Join-Path $arch "term_fixes")
Move-Glob "lang0_*.tsv" (Join-Path $arch "term_fixes")
Move-Glob "ui_*.tsv" (Join-Path $arch "ui_deltas")
Move-Glob "translations_to_merge.tsv" (Join-Path $arch "misc")

if (Test-Path (Join-Path $data "tbl_batch3_chunks")) {
    Move-Item -Force (Join-Path $data "tbl_batch3_chunks") (Join-Path $arch "batches\tbl_batch3_chunks")
}
if (Test-Path (Join-Path $data "merge_parts")) {
    Move-Item -Force (Join-Path $data "merge_parts") (Join-Path $arch "misc\merge_parts")
}

Write-Host "Done. data/ should mainly keep new_translations.tsv + translations.tsv + gui_font.ini"
Write-Host "Review with: git status"
}, {