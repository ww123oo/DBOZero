#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tbl_batch_helper.py - 重新抓取当前未填 TBL 清单，并切片出下一批待译原文。

用法:
  python scripts/tbl_batch_helper.py extract            # 重建 tmp/tbl_merge_probe/tbl_unfilled_now.tsv
  python scripts/tbl_batch_helper.py next N [offset]    # 打印下一批 N 行原文(从 offset 开始, 默认接上次)
  python scripts/tbl_batch_helper.py status             # 打印 TBL 已填/未填统计

说明:
  - 来源主表: data/new_translations.tsv (UTF-8 BOM, 列: 来源 文件 位置 原文 参考译文 填写中文 长度状态)
  - 未填判定: 来源=='TBL' 且 填写中文 为空
  - 生成的未填清单含去重后的 原文(按主表出现顺序)
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "new_translations.tsv"
OUT_DIR = ROOT / "tmp" / "tbl_merge_probe"
NOW = OUT_DIR / "tbl_unfilled_now.tsv"
PROGRESS = OUT_DIR / "tbl_batch_progress.txt"


def extract():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    rows = []
    with open(MASTER, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        header = next(r)
        # 来源=0 填写中文=5 原文=3
        for row in r:
            if len(row) < 6:
                continue
            if row[0] == "TBL" and not row[5].strip():
                ori = row[3]
                if ori not in seen:
                    seen.add(ori)
                    rows.append(ori)
    with open(NOW, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["原文"])
        for ori in rows:
            w.writerow([ori])
    print(f"wrote {len(rows)} unique unfilled TBL 原文 -> {NOW}")


def status():
    filled = unfilled = 0
    with open(MASTER, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        next(r)
        for row in r:
            if len(row) < 6:
                continue
            if row[0] == "TBL":
                if row[5].strip():
                    filled += 1
                else:
                    unfilled += 1
    print(f"TBL total {filled+unfilled} | filled {filled} | unfilled {unfilled}")


def next_batch(n=150, offset=None):
    if not NOW.exists():
        extract()
    lines = NOW.read_text(encoding="utf-8").splitlines()
    # lines[0] = header
    data = [l for l in lines[1:] if l]
    if offset is None:
        offset = load_progress()
    chunk = data[offset : offset + n]
    print(f"# batch start offset={offset} count={len(chunk)} (next offset={offset+len(chunk)})")
    for i, ori in enumerate(chunk):
        print(f"{offset+i+1}\t{ori}")
    save_progress(offset + len(chunk))


def load_progress():
    if PROGRESS.exists():
        try:
            return int(PROGRESS.read_text().strip())
        except Exception:
            return 0
    return 0


def save_progress(v):
    PROGRESS.write_text(str(v), encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "extract":
        extract()
    elif cmd == "status":
        status()
    elif cmd == "next":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 150
        off = int(sys.argv[3]) if len(sys.argv) > 3 else None
        next_batch(n, off)
    else:
        print("unknown cmd", cmd)
