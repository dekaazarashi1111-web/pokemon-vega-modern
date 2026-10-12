#!/usr/bin/env python3
"""固定UTF-8 source/観測textをGit blobs経由で展開。ROM/save/画像は含まない。

会話toolのサイズ制限用の一時転送。最終treeは読みやすい通常textのみ。
blobは不透明な実行物として使わず、全圧縮/展開hash・preimage・pathを先に検証する。
"""
from __future__ import annotations
import base64
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
BASE='90203c6c81d610a80ec3f7ca44c5f2bfe9420860'
OUT=ROOT/'.local/pr16-natural-record'
BLOBS=[
 '67c60a6f1f3e2bad9b20327f919ae9feb3497b94',
 '4b9161c53e2568a7cf333385d5c090d03bae16eb',
 '39833b4d9f971e1a34fb0dc447c6a5d9763ebeeb',
 'a6fe7733d20a6d4520f8a80f2b7b4f1a40e13f2d',
 '9d61a3c3eb91ef91fa3c236ef459aca1d2ee2f8b',
 'e0d33acdddbda32ccb28ae6103f8250931f3a4a7',
 '9c7ea28ad2551fa37032fb7eb6e647b1f4008d6f',
 '7647e2c1c19e3691c6813e4c5b9e057d12791812']
PACKED=dict(size=43372,sha256='195d9bae7534d493cd84995129d2c2af6086dabd442c6559acae4349209d3aac')
RAW=dict(size=532686,sha256='b038e63eba71f3c5b06b78cc3928132f39f714048c622d3763e6ad3fec40846b')
CODE={
 'tools/pr16_research_shop_ui.S','scripts/pr16_research_shop_ui.py','tests/test_pr16_research_shop_ui.py',
 'tools/mgba_pr16_research_natural_spending.c','tools/mgba_pr16_research_shop_ui_only.c',
 'scripts/pr16_research_natural_spending_probe.py','scripts/pr16_research_natural_spending_oracle.py',
 'scripts/pr16_research_natural_spending_record.py','tests/test_pr16_research_natural_spending.py',
 'content/modernization/pr16_research_shop_ui_recipe.json'}
EVIDENCE='content/modernization/pr16_research_natural_spending_evidence/'

def need(value,reason):
    if not value:raise ValueError(reason)

def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def pairs(rows):
    value={}
    for k,v in rows:
        need(k not in value,'duplicate JSON key');value[k]=v
    return value

def decode(parts):
    need(len(parts)==8,'closed eight-part transport')
    for part,sha in zip(parts,BLOBS):
        need(hashlib.sha1(b'blob '+str(len(part)).encode()+b'\0'+part).hexdigest()==sha,'part identity')
    packed=b''.join(parts);need(identity(packed)==PACKED,'compressed source identity')
    dec=lzma.LZMADecompressor(memlimit=64*1024*1024)
    raw=dec.decompress(packed,max_length=RAW['size']+1)
    need(dec.eof and not dec.unused_data and identity(raw)==RAW,'bounded complete source identity')
    obj=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
    need(obj['schema_version']==1 and obj['base_head']==BASE and len(obj['files'])==50,'closed source version/count')
    need(CODE<=set(obj['files']) and sum(p.startswith(EVIDENCE) for p in obj['files'])==40,'closed source/evidence scopes')
    for name,row in obj['files'].items():
        p=PurePosixPath(name)
        need(not p.is_absolute() and '..' not in p.parts and str(p)==name and '\\' not in name,'safe relative path')
        need(name in CODE or name.startswith(EVIDENCE) and p.suffix in ('.json','.txt'),'source text only')
        need(set(row)=={'binding','before','content'} and type(row['content']) is str,'entry schema')
        b=row['content'].encode('utf-8');need(b'\0' not in b and identity(b)==row['binding'],'UTF-8 content identity')
    return obj

def main():
    os.chdir(ROOT);sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
    import pr16_research_lifecycle_actions as d
    d.current();subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    parts=[]
    for sha in BLOBS:
        row=d.inputs.api('git/blobs/'+sha)
        need(row['sha']==sha and row['encoding']=='base64','GitHub blob response')
        b=base64.b64decode(''.join(row['content'].split()),validate=True)
        need(len(b)==row['size']<=6000,'part bounds');parts.append(b)
    obj=decode(parts)
    # Validate all paths and preimages before changing any file.
    for name,row in obj['files'].items():
        path=ROOT/name
        need(not path.is_symlink() and all(not p.is_symlink() for p in path.parents if p!=ROOT),'no symlink writes')
        if row['before'] is None:need(not path.exists(),'new file already exists: '+name)
        else:need(path.is_file() and identity(path.read_bytes())==row['before'],'exact preimage: '+name)
    for name,row in obj['files'].items():
        path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(row['content'].encode('utf-8'))
    OUT.mkdir(parents=True,exist_ok=True)
    summary=dict(files=sorted(obj['files']),source_base_head=BASE,source=RAW,transport=PACKED,blobs=BLOBS,
                 tracked_binary_files=0,rom_save_image_files=0,all_preimages_confirmed=True)
    (OUT/'transfer.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print('PASS: exact 50 UTF-8 source/evidence files restored; no binary tracked file')

if __name__=='__main__':main()
