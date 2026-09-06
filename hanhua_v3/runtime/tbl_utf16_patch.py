# -*- coding: utf-8 -*-
"""DBO Zero tbl0/tbl1 fixed-field patcher."""
from __future__ import annotations
import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
__all__=["ALL_OFFSETS","PatchError","TBL_FILES","TblOverride","encoded_text_bytes","find_all","fixed_replacement","fixed_single_byte_replacement","has_length_prefix","inside_length_prefixed_field","length_prefixed_offsets","length_prefixed_source_variants","main","parse_offset","tool_dir"]
TBL_FILES=("tbl0.pak","tbl1.pak")
ALL_OFFSETS={"","*","all","ALL"}
class PatchError(RuntimeError): pass
@dataclass(frozen=True)
class TblOverride:
    file_name:str
    offset:int|None
    source_text:str
    translation:str
def tool_dir()->Path:
    if getattr(sys,"frozen",False): return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent
def default_source_dir()->Path: return tool_dir()/"src_file"
def dbo_root(source_dir:Path)->Path: return source_dir/"DBOZero"
def tbl_path(source_dir:Path,file_name:str)->Path: return dbo_root(source_dir)/"pack"/file_name
def parse_offset(value:str,row_no:int)->int|None:
    value=value.strip()
    if value in ALL_OFFSETS:return None
    try:return int(value,16) if value.lower().startswith("0x") else int(value)
    except ValueError as exc:raise PatchError(f"Invalid tbl_overrides.tsv offset at row {row_no}: {value}") from exc
def read_overrides(path:Path|None)->list[TblOverride]:
    if path is None:path=tool_dir()/"tbl_overrides.tsv"
    if not path.exists():raise PatchError(f"Missing tbl overrides file: {path}")
    rows=[]
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.reader(handle,delimiter="\t")
        for row_no,row in enumerate(reader,1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):continue
            if len(row)<4:raise PatchError(f"Invalid tbl_overrides.tsv row {row_no}; need file, id, source_text, translation")
            file_name=row[0].strip()
            if file_name.lower()=="file":continue
            if file_name not in TBL_FILES:raise PatchError(f"Unsupported tbl file at row {row_no}: {file_name}")
            source_text=row[2]; translation=row[3]
            if not source_text or not translation:continue
            rows.append(TblOverride(file_name,parse_offset(row[1],row_no),source_text,translation))
    return rows
def utf16le(text:str,label:str)->bytes:return text.encode("utf-16le")
def encoded_text_bytes(text:str,label:str,encoding:str)->bytes:return text.encode(encoding)
def fixed_replacement(source_text,translation,pad_unit=b"\x00\x00"):
    source=utf16le(source_text,"Source text"); replacement=utf16le(translation,"Translation")
    if len(replacement)>len(source):raise PatchError(f"Translation is too long for fixed tbl field: {source_text!r} -> {translation!r}")
    return replacement+pad_unit*((len(source)-len(replacement))//2)
def fixed_single_byte_replacement(source,source_text,translation,encoding="gbk"):
    replacement=encoded_text_bytes(translation,"Translation",encoding)
    if len(replacement)>len(source):raise PatchError(f"Translation is too long for fixed single-byte tbl field: {source_text!r} -> {translation!r}")
    return replacement+b"\x00"*(len(source)-len(replacement))
def has_length_prefix(data,file_name,offset,source_units):
    return file_name=="tbl1.pak" and offset>=2 and int.from_bytes(data[offset-2:offset],"little")==source_units
def inside_length_prefixed_field(data,file_name,offset,source_units,max_scan_units=256):
    if file_name!="tbl1.pak" or offset<2:return False
    for back_units in range(1,min(offset//2,max_scan_units)+1):
        length_pos=offset-back_units*2; units=int.from_bytes(data[length_pos:length_pos+2],"little")
        if 0<units<=max_scan_units and length_pos+2<=offset and offset+source_units*2<=length_pos+2+units*2:return length_pos+2!=offset or units!=source_units
    return False
def find_all(data,needle):
    if hasattr(data,"obj") and not isinstance(data,(bytes,bytearray)):data=data.obj if isinstance(data.obj,(bytes,bytearray)) else bytes(data)
    offsets=[];start=0
    if not needle:return offsets
    while True:
        idx=data.find(needle,start)
        if idx<0:return offsets
        offsets.append(idx);start=idx+len(needle)
def length_prefixed_offsets(data,file_name,source_text):
    source=utf16le(source_text,"Source text"); units=len(source)//2
    return [o for o in find_all(data,source) if has_length_prefix(data,file_name,o,units)]
def length_prefixed_source_variants(data,row,max_trim_chars=4):return []
def patch_tbl_bytes(data,rows,single_byte_encoding="gbk",missing_rows=None):
    patched=bytearray(data);changed=missing=0
    for row in rows:
        source=utf16le(row.source_text,"Source text")
        offsets=[row.offset] if row.offset is not None else find_all(patched,source)
        for offset in offsets:
            if offset is not None and 0<=offset<=len(patched)-len(source) and patched[offset:offset+len(source)]==source:
                patched[offset:offset+len(source)]=fixed_replacement(row.source_text,row.translation);changed+=1
        if not offsets:missing+=1
    return bytes(patched),{"rows":len(rows),"changed":changed,"missing":missing,"relocated":0,"normalized":0,"ambiguous":0,"space_padded":0}
def patch_tbl_pack(source_dir,out_pack_dir,rows,single_byte_encoding="gbk"):
    grouped={name:[] for name in TBL_FILES}
    for row in rows:grouped[row.file_name].append(row)
    out_pack_dir.mkdir(parents=True,exist_ok=True);stats={}
    for file_name in TBL_FILES:
        if not grouped[file_name]:continue
        source=tbl_path(source_dir,file_name)
        if not source.is_file():raise PatchError(f"Missing source tbl file: {source}")
        patched,stats[file_name]=patch_tbl_bytes(source.read_bytes(),grouped[file_name],single_byte_encoding)
        (out_pack_dir/file_name).write_bytes(patched)
    return stats
def build_parser():
    parser=argparse.ArgumentParser();parser.add_argument("--source-dir",type=Path,default=default_source_dir());parser.add_argument("--overrides",type=Path,default=tool_dir()/"tbl_overrides.tsv");sub=parser.add_subparsers(dest="command",required=True);sub.add_parser("plan");return parser
def main(argv=None):
    args=build_parser().parse_args(argv)
    if args.command=="plan":
        rows=read_overrides(args.overrides); print(f"Source dir: {args.source_dir.resolve()}"); print("No files were changed by plan mode."); return 0
    return 0
if __name__=="__main__":raise SystemExit(main())
