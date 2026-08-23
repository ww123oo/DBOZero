# merge_parts

分段翻译对照表（原文 → 填写中文）。

## 本机用法

1. `git pull`
2. 若仓库内已有 `part1.tsv`～`part4.tsv`：

```powershell
python scripts/combine_merge_parts.py
python scripts/merge_translations.py
dboc build --force
```

3. 若只有 `parts_a.b64` / `parts_b.b64`：

```powershell
python scripts/decode_merge_parts.py
python scripts/merge_translations.py
dboc build --force
```

## 说明

- 完整约 1700+ 组优质中文对在对话产物 `translations_to_merge.tsv`。
- 上传时因单次 API 体积限制，GitHub 上可能需分段或压缩包。
- `merge_translations.py` 会：合并 parts → 写入 `data/translations_to_merge.tsv` → 填入 `data/new_translations.tsv` 空白「填写中文」。
