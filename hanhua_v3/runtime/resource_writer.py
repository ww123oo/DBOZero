# -*- coding: utf-8 -*-
"""Safe writer for the DBO localization resource set."""
from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from pathlib import Path

from . import lang0_gbk_patch as lang0
from . import tbl_utf16_patch as tbl

RESOURCE_EXTENSIONS = {".rdf", ".xml", ".dat"}
TBL_FILES = {"tbl0.pak", "tbl1.pak", "tbl2.pak"}
PAK_FILES = {"lang0.pak", *TBL_FILES}

class WriteError(RuntimeError):
    pass

@dataclass(frozen=True)
class QueueRow:
    file: str
    locator: str
    source: str
    translation: str
    encoding: str
    kind: str

def read_queue(path: Path) -> list[QueueRow]:
    if not path.is_file():
        raise WriteError(f"Missing translation queue: {path}")
    rows=[]
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        for row in csv.DictReader(handle,delimiter="\t"):
            source=(row.get("source_text") or row.get("原文") or "").strip()
            translation=(row.get("zh_cn") or row.get("填写中文") or "").strip()
            if not source or not translation: continue
            status=(row.get("status") or "").strip().lower()
            if status in {"skip","ignored","disabled"}: continue
            file_name=(row.get("file") or row.get("文件") or "").strip()
            if not file_name: continue
            rows.append(QueueRow(file_name,(row.get("id") or row.get("ID") or row.get("位置") or "").strip(),source,translation,(row.get("encoding") or "").strip().lower(),(row.get("kind") or "").strip().lower()))
    return rows

def _find_resource(root: Path,name: str)->Path:
    wanted=name.replace("\\","/").strip(); direct=root/wanted
    if direct.is_file(): return direct
    matches=[p for p in root.rglob(Path(wanted).name) if p.is_file()]
    if len(matches)==1: return matches[0]
    if not matches: raise WriteError(f"Resource not found: {name}")
    raise WriteError(f"Resource name is ambiguous: {name}")

def _encode(text: str,encoding: str)->bytes:
    if encoding in {"utf-16le","utf16","utf-16"}: return text.encode("utf-16le")
    if encoding.startswith("gbk") or encoding in {"gb18030","gb2312"}: return text.encode("gb18030" if encoding=="gb18030" else "gbk")
    if encoding in {"utf-8","utf-8-sig","ascii",""}: return text.encode("utf-8")
    return text.encode(encoding)

def _offset(locator: str)->int:
    value=locator.strip()
    if value.lower().startswith("offset:"): value=value.split(":",1)[1]
    if value.lower().startswith("0x"): return int(value,16)
    return int(value)

def _patch_text_rows(data: bytes,rows: list[QueueRow],file_name: str)->tuple[bytes,int]:
    patched=bytearray(data); operations=[]
    for row in rows:
        try: offset=_offset(row.locator)
        except ValueError as exc: raise WriteError(f"Non-offset locator cannot patch generic resource: {row.locator!r}") from exc
        if offset<0 or offset>=len(data): raise WriteError(f"Offset outside resource: 0x{offset:X}")
        is_dat=file_name.lower().endswith(".dat") or row.kind=="dat_entry"
        if is_dat:
            enc="gb18030" if row.encoding=="gb18030" else "utf-8"
            escaped=row.source.replace("\\","\\\\").replace('"','\\"')
            candidates=[((f'"{escaped}"').encode(enc),(f'"{row.translation.replace(chr(92),chr(92)+chr(92)).replace(chr(34),chr(92)+chr(34))}"').encode(enc)),((f"'{row.source.replace(chr(92),chr(92)+chr(92)).replace(chr(39),chr(92)+chr(39))}'").encode(enc),(f"'{row.translation.replace(chr(92),chr(92)+chr(92)).replace(chr(39),chr(92)+chr(39))}'").encode(enc))]
            old,new=next(((a,b) for a,b in candidates if data[offset:offset+len(a)]==a),(b"",b""))
            if not old: raise WriteError(f"DAT source mismatch at 0x{offset:X}: {row.source!r}")
        else:
            old=_encode(row.source,row.encoding); new=_encode(row.translation,row.encoding)
            if data[offset:offset+len(old)]!=old: raise WriteError(f"Source mismatch at 0x{offset:X} in {row.file}")
        operations.append((offset,old,new,row))
    for offset,old,new,row in sorted(operations,key=lambda item:item[0],reverse=True):
        if patched[offset:offset+len(old)]!=old: raise WriteError(f"Overlapping/invalid patch at 0x{offset:X} in {row.file}")
        patched[offset:offset+len(old)]=new
    return bytes(patched),len(operations)

def _tbl_override(row: QueueRow,name: str)->tbl.TblOverride:
    if name=="tbl2.pak" and row.locator.lower().startswith("id:"):
        try: item_id=int(row.locator.split(":",1)[1],0)
        except ValueError as exc: raise WriteError(f"Invalid tbl2 stable ID: {row.locator!r}") from exc
        return tbl.TblOverride(name,None,row.source,row.translation,item_id)
    if name=="tbl2.pak" and row.kind=="tbl2_record":
        try: item_id=int(row.locator,0)
        except ValueError as exc: raise WriteError(f"Invalid tbl2 stable ID: {row.locator!r}") from exc
        return tbl.TblOverride(name,None,row.source,row.translation,item_id)
    try: off=_offset(row.locator) if row.locator else None
    except ValueError as exc: raise WriteError(f"Invalid tbl locator: {row.locator!r}") from exc
    return tbl.TblOverride(name,off,row.source,row.translation)

def _write_one(path: Path,rows: list[QueueRow],output_root: Path,source_root: Path)->tuple[Path,int]:
    name=path.name.lower(); original=path.read_bytes()
    if name=="lang0.pak":
        keyed=[]
        for row in rows:
            if not row.locator or row.locator.lower().startswith("offset:"): raise WriteError("lang0.pak requires scanner-provided keys; offset rows are rejected")
            keyed.append((row.locator,row.translation))
        patched,stats=lang0.patch_lang0_bytes(original,keyed); changed=stats["changed"]
    elif name in TBL_FILES:
        patched,stats=tbl.patch_tbl_bytes(original,[_tbl_override(row,name) for row in rows]); changed=stats["changed"]
        if stats["missing"]: raise WriteError(f"{name}: {stats['missing']} translation rows did not match the original resource")
    elif path.suffix.lower() in RESOURCE_EXTENSIONS:
        patched,changed=_patch_text_rows(original,rows,name)
    else:
        raise WriteError(f"Unsupported resource type: {path}")
    if len(patched)!=len(original) and name in PAK_FILES: raise WriteError(f"Fixed-size resource changed size: {name}")
    relative=path.relative_to(source_root)
    output=output_root/relative
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(patched)
    return output,changed

def _mirror_source_tree(source_root: Path,output_root: Path)->int:
    """Create the Taiwan build tree from the untouched source.

    All files are copied unchanged first, including .bin. The translation
    writer only replaces supported text resources afterwards; .bin is never
    scanned or modified by this module.
    """
    source_root=source_root.resolve(); output_root=output_root.resolve()
    if not source_root.is_dir(): raise WriteError(f"Source root not found: {source_root}")
    output_root.mkdir(parents=True,exist_ok=True)
    copied=0
    for source in source_root.rglob("*"):
        if not source.is_file(): continue
        relative=source.relative_to(source_root)
        target=output_root/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        copied+=1
    return copied

def write_queue(queue: Path,source_root: Path,output_root: Path)->dict[str,int]:
    rows=read_queue(queue)
    if any(r.file.lower().endswith(".bin") for r in rows): raise WriteError(".bin is not a supported translation target and will never be written")
    _mirror_source_tree(source_root,output_root)
    grouped={}
    for row in rows: grouped.setdefault(row.file.replace("\\","/").lower(),[]).append(row)
    result={}
    for key,file_rows in sorted(grouped.items()):
        path=_find_resource(source_root,key); output,changed=_write_one(path,file_rows,output_root,source_root); result[output.relative_to(output_root).as_posix()]=changed
    return result

def main(argv: list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="Write translated DBO localization resources safely")
    parser.add_argument("queue",type=Path,nargs="?",default=Path("data/new_translations.tsv")); parser.add_argument("--source-root",type=Path,required=True); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args(argv)
    if args.dry_run: print(f"translated rows: {len(read_queue(args.queue))}\ndry-run: no resource files were written"); return 0
    for name,changed in write_queue(args.queue,args.source_root,args.output_root).items(): print(f"{name}: changed={changed}")
    return 0

if __name__=="__main__": raise SystemExit(main())
