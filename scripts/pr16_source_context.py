#!/usr/bin/env python3
"""Read hash-pinned prior instructions/catalogs and physical-facility sources.

Export text only. No ROM/save restoration, extraction, mutation, or acceptance.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/pr16-continuation/context'


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def text(raw):
    for encoding in ('utf-8-sig','cp932'):
        try:return raw.decode(encoding)
        except UnicodeDecodeError:pass
    return None


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'.local/pr16-source-inputs';cache.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'config/github_private_environment.json').read_text())
    sources={};bindings={};inventories={};hits=[]
    archive_names=['pokemon-vega-private-env-v1-modernization-inputs.zip','pokemon-vega-private-env-v1-state.zip']
    for archive_name in archive_names:
        expected=next(x for x in config['archives'] if x['name']==archive_name)
        path=cache/archive_name
        if not path.exists():subprocess.run(['gh','release','download','private-environment-v1','--repo','dekaazarashi1111-web/pokemon-vega-modern','--pattern',archive_name,'--dir',str(cache)],check=True,timeout=240)
        raw=path.read_bytes();assert identity(raw)=={k:expected[k] for k in ('size','sha256')},'archive hash differs'
        bindings[archive_name]=identity(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            inventories[archive_name]=outer.namelist()
            if 'modernization-inputs' in archive_name:
                for name in outer.namelist():
                    if name.endswith('/') or Path(name).suffix.lower() in ('.gba','.sav','.srm'):continue
                    if name.endswith('.zip'):
                        data=outer.read(name);bindings[name]=identity(data)
                        with zipfile.ZipFile(io.BytesIO(data)) as inner:
                            inventories[name]=inner.namelist()
                            for member in inner.namelist():
                                low=member.lower();suffix=Path(low).suffix
                                if suffix in ('.md','.txt') or (suffix in ('.csv','.json') and any(k in low for k in ('crosswalk','move_catalog','catalog_moves','moves_catalog'))):
                                    payload=inner.read(member)
                                    if len(payload)>4_000_000:continue
                                    value=text(payload)
                                    if value is not None:
                                        key=name+'!'+member;sources[key]=value;bindings[key]=identity(payload)
                    elif Path(name).suffix.lower() in ('.txt','.md','.json','.csv'):
                        payload=outer.read(name)
                        if len(payload)<4_000_000:
                            value=text(payload)
                            if value is not None:sources[name]=value;bindings[name]=identity(payload)
            else:
                for name in outer.namelist():
                    p=Path(name)
                    if p.suffix.lower() not in ('.c','.h','.inc','.s','.asm','.json','.yml','.yaml','.txt','.md') or not name.startswith(('vendor/','generated/')):continue
                    info=outer.getinfo(name)
                    if info.file_size>4_000_000:continue
                    payload=outer.read(name);value=text(payload)
                    if value is None or 'circus' not in value.lower():continue
                    lines=value.splitlines();matches=[i for i,line in enumerate(lines) if 'circus' in line.lower()]
                    selected=sorted({j for i in matches for j in range(max(0,i-8),min(len(lines),i+14))})
                    hits.append({'path':name,'identity':identity(payload),'matches':[{'line':i+1,'text':lines[i]} for i in selected]})
                    if 'circus' in name.lower():sources[name]=value;bindings[name]=identity(payload)
    (OUT/'source-context.json').write_text(json.dumps({'status':'SOURCE_CONTEXT_NOT_ACCEPTANCE','sources':sources,'bindings':bindings,'inventories':inventories,'physical_circus_source_hits':hits,'rom_save_restored':False},ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'text_sources':len(sources),'circus_source_files':len(hits),'rom_save_restored':False}))

if __name__=='__main__':run()
