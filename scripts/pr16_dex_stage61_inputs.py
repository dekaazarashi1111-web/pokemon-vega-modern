#!/usr/bin/env python3
"""Verify recovered Stage61 macros/symbols against pinned original archive members."""
from __future__ import annotations
import hashlib,json,re,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='content/modernization/pr16_dex_stage61_relink_inputs.json'
def need(value,message):
    if not value:raise ValueError(message)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def member(folder,spec):
    path=folder/spec['name'];expected=spec['archive'];h=hashlib.sha256();size=0
    with urllib.request.urlopen(spec['url'],timeout=120) as response,path.open('wb') as f:
        while True:
            chunk=response.read(1024*1024)
            if not chunk:break
            size+=len(chunk);need(size<=expected['size'],'bounded pinned archive');h.update(chunk);f.write(chunk)
    need(dict(size=size,sha256=h.hexdigest())==expected,'whole pinned source archive identity')
    with zipfile.ZipFile(path) as z:
        need(z.namelist().count(spec['member'])==1,'one exact original member')
        entry=z.getinfo(spec['member']);need(not entry.is_dir() and entry.external_attr>>28!=10 and entry.file_size==spec['member_identity']['size'],'bounded regular original metadata')
        raw=z.read(entry)
    need(identity(raw)==spec['member_identity'],'whole original metadata member');return raw
def validate(proof,metadata_raw,symbol_raw,rom):
    need(proof['rom_bytes_included'] is False and proof['source_regeneration_runs']==proof['arm_compiles']==proof['native_runs']==0,'read-only source recovery boundary')
    need(identity(metadata_raw)==proof['archives'][0]['member_identity'] and identity(symbol_raw)==proof['archives'][1]['member_identity'],'original source members')
    metadata=json.loads(metadata_raw);symbols=json.loads(symbol_raw);runtime=metadata['runtime'];toolchain=runtime['toolchain']
    need(identity((ROOT/runtime['source']).read_bytes())==dict(size=proof['source']['size'],sha256=runtime['source_sha256']) and proof['source']['path']==runtime['source'] and proof['source']['sha256']==runtime['source_sha256'],'unchanged original Stage61 source')
    need(runtime['toolchain_manifest_sha256']==symbols['toolchain_manifest_sha256']==proof['toolchain_manifest_sha256']==toolchain['manifest_sha256'],'same original compiler/linker manifest')
    dependencies={}
    for row in toolchain['preprocessor_dependency_manifest']['files']:
        if '/workspace/' in row['resolved_realpath']:
            path=row['resolved_realpath'].rsplit('/workspace/',1)[1]
            dependencies[path]=dict(size=row['binary_size'],sha256=row['binary_sha256'])
    need(dependencies==proof['project_dependencies'] and len(dependencies)==2,'exact source and sole project header dependencies')
    for path,b in dependencies.items():need(identity((ROOT/path).read_bytes())==b,'original source dependency unchanged '+path)
    for name in ('compile_argv_canonical','link_argv_canonical','linker_script'):need(proof[name]==toolchain[name],'exact original toolchain field '+name)
    macros={}
    for arg in toolchain['compile_argv_canonical']:
        if arg.startswith('-D'):
            m=re.fullmatch(r'-D([A-Z0-9_]+)=(0x[0-9A-Fa-f]+)u',arg);need(m is not None,'canonical original macro')
            need(m[1]not in macros,'unique macro');macros[m[1]]=int(m[2],16)
    need(macros==proof['runtime_macros'] and len(macros)==proof['macro_count']==24,'all24 original macros')
    need(identity(rom)==proof['candidate'],'exact fixed candidate for function preimages')
    code=proof['original_code'];offset=code['address']-0x08000000
    need(code['size']==runtime['code_size']==12568 and code['sha256']==runtime['code_sha256'] and code['end_exclusive']==code['address']+code['size'],'exact original code owner')
    need(identity(rom[offset:offset+code['size']])==dict(size=code['size'],sha256=code['sha256']),'whole current code equals original generated code')
    rows=[];aliases=[]
    for line in symbols['nm'].splitlines():
        fields=line.split()
        if len(fields)==3:
            address,kind,name=fields;address=int(address,16)
            need(code['address']<=address<code['end_exclusive'],'bounded unsized runtime alias')
            aliases.append(dict(name=name,address=address,kind=kind));continue
        need(len(fields)==4,'known nm row structure')
        address,size,kind,name=fields;address=int(address,16);size=int(size,16)
        need(code['address']<=address<address+size<=code['end_exclusive'],'bounded original symbol')
        at=address-0x08000000;rows.append(dict(name=name,address=address,address_hex=f'0x{address:08X}',size=size,kind=kind,preimage_sha256=hashlib.sha256(rom[at:at+size]).hexdigest()))
    need(len(rows)==proof['symbol_count']==99 and len({x['name']for x in rows})==99,'all99 unique symbol windows')
    need({x['name']:x['address']for x in rows}==runtime['symbols']==symbols['symbols'],'independent metadata and nm symbol addresses')
    need(rows==proof['symbols'],'all99 exact symbol sizes and current ROM preimage hashes')
    need(len(aliases)==proof['unsized_alias_count']==4 and aliases==proof['unsized_aliases'],'retain all4 unsized libgcc aliases without guessing their sizes')
    return dict(status='PASS_ORIGINAL_STAGE61_METADATA_MACROS_SYMBOLS_AND_ROM',macros=24,sized_symbols=99,unsized_aliases=4,code_bytes=12568,source_regeneration_runs=0,arm_compiles=0,native_processes=0,rom_changed=False)
