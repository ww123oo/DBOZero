# 翻译合并说明

## 目标

最终要改的是 **`data/new_translations.tsv`** 的「填写中文」列（约 3.5MB）。

因 GitHub API 单次推送限制，仓库里只能先放对照表 + 脚本；**不会自动改掉主表**。

## 本机（推荐）

```powershell
cd J:\OpenDBO-Localization-main\DBOZero-main
git pull
python scripts/merge_translations.py
git add data/new_translations.tsv
git commit -m "fill 填写中文"
git push
```

## 或：直接覆盖主表

1. 下载对话产物 `new_translations_merged.tsv`
2. 覆盖为 `data/new_translations.tsv`
3. `git add` / `commit` / `push`

## 对照表

- `data/translations_to_merge.tsv` — 精简版
- 完整约 1770 组：对话产物 `translations_to_merge.tsv`
