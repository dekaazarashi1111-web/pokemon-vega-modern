#!/usr/bin/env python3
"""Stage84 + exact historical V4 Vega-move layer, never a P03 baseline rewrite.

The original requirement and accepted preservation are recorded in the spec.
The 472-row old projection and 27 canonically named aliases remain distinct.
Builds are fail-closed on capacities, unknown roots, source or allocation drift.
Native UI/save acceptance is separate and cannot be inferred from this build.
"""
from __future__ import annotations
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import pr16_integration_continuation as source
from pr16_source_acceptance import reconcile_legacy_count
from tools.rom_allocator import build_allocation_report_from_csv
from tools.release.bps import create_bps,apply_bps
BASE=0x08000000
COUNT=1671
WORK=ROOT/'.local/pr16-integrated-p07'
ALLOCATION='build/stages/78_modernization_p05_eelevate_switch_ai_allocation.json'
ALLOCATION_SHA='b92ef83b96482c6fc5f751af87a4dc7eb4783a10258b1c193fa298cc485d8d3b'
REGIONS_SHA='f5dcb0ecf2f726bfff1e9c8382204e79b1354ee9071f8d9ac00a83de7a9b3553'
SRC='overlays/modernization_p07_preserved_layer/runtime.c'
SPEC='content/modernization/p07_preserved_layer_spec.json'
LAYER='official_to_vega_legacy_preservation'
EGG_HOOK=0x10EB970
MEMORY_HOOK=0x091141D4-BASE
EGG_TARGET=0x095348E5
MEMORY_TARGET=0x0954B281
SHARED_INDEX=0x1534C9E
SHARED_MOVES=0x153594A
REMINDER_INDEX=0x1538088
REMINDER_MOVES=0x1538D34
# These are the seven adopted P03 baby/incense collision handlers, not new rows.
EXACT_SPECIES={203,324,364,608,719,724,727}
need=source.need
identity=source.identity
stable=source.stable


def indexed(parent,index,table,species):
    start,end=struct.unpack_from('<HH',parent,index+species*2)
    need(start<=end and table+end*2<=len(parent),'indexed table outside parent')
    return list(struct.unpack_from('<'+'H'*(end-start),parent,table+start*2))


def project(parent,selected):
    rows=selected[LAYER];audit=reconcile_legacy_count(rows)
    for r in rows:
        need(r['form_key']=='' and r['source_class']=='CURRENT_PRESERVED','unexpected form/new adoption')
    ls={r['species_id'] for r in rows if r['route']=='level_up'}
    tables=source.RomTables(parent,COUNT,selected_species=ls)
    need(tables.roots['level']==0x0958B95C and tables.roots['egg']==0x09FF0BD4,'Stage84 table roots differ')
    by_route={k:defaultdict(list) for k in ('level_up','egg')}
    for r in rows:by_route[r['route']][r['species_id']].append(r)
    level={};egg={sid:list(v) for sid,v in tables.egg.items()};capacity=[]
    for sid,items in by_route['level_up'].items():
        old=tables.level[sid]
        additions=[(r['move_id'],int(r['source_parameters']['level'])) for r in sorted(items,key=lambda r:int(r['source_parameters']['order']))]
        need(not set(old)&set(additions),'layer row already in baseline; do not double-apply')
        # Stable order: P03 rows first at a tied level, then V4 order among deltas.
        merged=sorted(old+additions,key=lambda item:item[1]);level[sid]=merged
        reminder=indexed(parent,REMINDER_INDEX,REMINDER_MOVES,sid)
        need(len(merged)<=40,f'level scan capacity exceeded species={sid} rows={len(merged)}')
        n=len(set(m for m,_ in merged)|set(reminder))
        need(n<=40,f'normal memory capacity exceeded species={sid} moves={n}')
        need([x for x in merged if x not in additions]==old,'P03 relative level order changed')
        capacity.append({'species':sid,'route':'level','rows':len(merged),'maximum_memory_candidates':n})
    special=[]
    for sid,items in by_route['egg'].items():
        additions=[r['move_id'] for r in sorted(items,key=lambda r:int(r['source_parameters']['order']))]
        need(not set(egg[sid])&set(additions),'egg layer already in baseline')
        need(len(additions)==len(set(additions)),'duplicate source egg move')
        egg[sid]+=additions
        need(len(egg[sid])<=50,f'breeding egg capacity exceeded species={sid}')
        shared=indexed(parent,SHARED_INDEX,SHARED_MOVES,sid)
        n=len(set(egg[sid])|set(shared))
        need(n<=40,f'egg/shared memory capacity exceeded species={sid} moves={n}')
        capacity.append({'species':sid,'route':'egg','rows':len(egg[sid]),'maximum_memory_candidates':n})
        if sid in EXACT_SPECIES:special.extend(items)
    need({r['species_id'] for r in special}=={364} and [r['move_id'] for r in special]==[461,464,357],
         'unaccounted conditional egg collision')
    return tables,level,egg,{'source_reconciliation':audit,'capacities':capacity,'exact_egg_adapter_rows':special}


def egg_markers(parent,root):
    cursor=root-BASE;markers=[]
    for _ in range(50000):
        value=struct.unpack_from('<H',parent,cursor)[0];cursor+=2
        if value==65535:return markers
        if value>=20000:
            sid=value-20000
            need(sid not in markers,'duplicate egg marker')
            markers.append(sid)
    raise ValueError('unterminated egg markers')


def egg_bytes(rows,markers):
    data=[]
    for sid in markers:
        data.extend([20000+sid,*rows[sid]])
    data.append(65535)
    return struct.pack('<'+'H'*len(data),*data)


def level_bytes(parent,tables,rows,start):
    root=tables.roots['level']-BASE
    data=bytearray(parent[root:root+COUNT*4])
    need(len(data)==COUNT*4,'truncated original pointer table')
    for sid,items in sorted(rows.items()):
        struct.pack_into('<I',data,sid*4,BASE+start+len(data))
        for move,level in items:data.extend(struct.pack('<HB',move,level))
        data.extend(struct.pack('<HB',0,255))
    return bytes(data)


def allocation_requests(parent,old):
    need(old['schema_version']==1 and len(old['allocations'])==82,'parent layout row count differs')
    out=[]
    for seq,r in enumerate(old['allocations']):
        need(r['sequence']==seq and r['end_exclusive']==r['start']+r['size'],'parent layout sequence/span')
        out.append({k:r[k] for k in ('name','region','size','alignment','start','owner','purpose')})
        # Actual Stage84 bytes, never the Stage78 content hashes on a new ROM.
        out[-1]['content_sha256']=identity(parent[r['start']:r['end_exclusive']])['sha256']
    return out


def allocate(parent,old,payloads):
    requests=allocation_requests(parent,old)
    for name,raw in zip(('level','egg','runtime'),payloads,strict=True):
        requests.append({'name':'modernization-p07-preserved-'+name,'region':'integration_modules',
                         'size':len(raw),'alignment':4,'owner':'P07','purpose':'exact adopted V4 preservation '+name,
                         'content_sha256':identity(raw)['sha256']})
    out=build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests)
    need(out['summaries']['overlap_count']==0,'P07 allocation overlap')
    return out


def compile_runtime(start,moves):
    with tempfile.TemporaryDirectory(prefix='p07-link-',dir=ROOT/'.local') as td:
        td=Path(td)
        (td/'bindings.h').write_text('#define P07_PARENT_EGG 0x095348E5u\n#define P07_PARENT_MEMORY 0x0954B281u\n#define P07_HAPPINY_EGG {'+','.join(str(x)+'u' for x in moves)+'}\n')
        (td/'link.ld').write_text('SECTIONS { . = '+hex(BASE+start)+'; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) } }')
        cmd=['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-Os','-std=c11','-ffreestanding','-fno-builtin','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-nostdlib','-I'+str(td),str(ROOT/SRC),'-Wl,-T,'+str(td/'link.ld'),'-o',str(td/'runtime.elf')]
        subprocess.run(cmd,check=True,capture_output=True)
        subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(td/'runtime.elf'),str(td/'runtime.bin')],check=True)
        syms={}
        for line in subprocess.check_output(['arm-none-eabi-nm','-n',str(td/'runtime.elf')],text=True).splitlines():
            parts=line.split()
            if len(parts)==3 and parts[2] in ('P07_GetAllEggMoves','P07_GetMoveRelearnerMoves'):syms[parts[2]]=int(parts[0],16)|1
        need(len(syms)==2,'P07 link omitted consumers')
        return (td/'runtime.bin').read_bytes(),syms


def veneer(width,target):
    return struct.pack('<HHI',0x4b00,0x4718,target|1) if width==8 else struct.pack('<HHHHI',0x469c,0x4b01,0x4718,0x46c0,target|1)


def build(parent,selected,old):
    need(identity(parent)=={'size':33554432,'sha256':source.ROM_SHA},'exact Stage84 parent required')
    need(parent[EGG_HOOK:EGG_HOOK+12]==veneer(12,EGG_TARGET),'egg hook is not the Stage73 delegate')
    need(parent[MEMORY_HOOK:MEMORY_HOOK+8]==veneer(8,MEMORY_TARGET),'memory hook is not the Stage75 delegate')
    tables,level,egg,projection=project(parent,selected)
    markers=egg_markers(parent,tables.roots['egg'])
    new_markers=sorted(set(markers)|{r['species_id'] for r in selected[LAYER] if r['route']=='egg'})
    e=egg_bytes(egg,new_markers);l=level_bytes(parent,tables,level,0)
    c,_=compile_runtime(0x1200000,[r['move_id'] for r in projection['exact_egg_adapter_rows']])
    plan=allocate(parent,old,(l,e,c));a=plan['allocations'][-3:]
    l=level_bytes(parent,tables,level,a[0]['start'])
    c,syms=compile_runtime(a[2]['start'],[r['move_id'] for r in projection['exact_egg_adapter_rows']])
    final_plan=allocate(parent,old,(l,e,c))
    need([(r['start'],r['size']) for r in final_plan['allocations'][-3:]]==[(r['start'],r['size']) for r in a],'non-deterministic link placement')
    spans=[];candidate=bytearray(parent)
    def write(off,raw,expected,label):
        need(parent[off:off+len(raw)]==expected,'preimage mismatch: '+label)
        need(all(off+len(raw)<=s['start'] or off>=s['end_exclusive'] for s in spans),'overlapping write')
        candidate[off:off+len(raw)]=raw
        spans.append({'label':label,'start':off,'end_exclusive':off+len(raw),'before':identity(expected),'after':identity(raw)})
    for r,raw in zip(a,(l,e,c),strict=True):write(r['start'],raw,b'\xff'*len(raw),r['name'])
    for site in (0x4346c,0x1fda1f8):write(site,struct.pack('<I',BASE+a[0]['start']),struct.pack('<I',tables.roots['level']),'level-consumer-root')
    for site in (0x45214,0x4528c):write(site,struct.pack('<I',BASE+a[1]['start']),struct.pack('<I',tables.roots['egg']),'egg-consumer-root')
    old_egg=egg_bytes(tables.egg,markers)
    need(parent[tables.roots['egg']-BASE:tables.roots['egg']-BASE+len(old_egg)]==old_egg,'egg parser did not preserve exact parent sequence')
    write(0x45288,struct.pack('<I',len(e)//2-2),struct.pack('<I',len(old_egg)//2-2),'egg-scan-limit')
    write(EGG_HOOK,veneer(12,syms['P07_GetAllEggMoves']),veneer(12,EGG_TARGET),'exact-happiny-egg-consumer')
    write(MEMORY_HOOK,veneer(8,syms['P07_GetMoveRelearnerMoves']),veneer(8,MEMORY_TARGET),'exact-happiny-memory-consumer')
    result=bytes(candidate)
    final_plan=allocate(result,old,(l,e,c))
    cursor=0
    for s in sorted(spans,key=lambda r:r['start']):
        need(parent[cursor:s['start']]==result[cursor:s['start']],'undeclared byte change')
        cursor=s['end_exclusive']
    need(parent[cursor:]==result[cursor:],'undeclared trailing byte change')
    groups,roots=source.reconcile(result,selected)
    need(all(g['summary']['missing']==0 for g in groups.values()),'preserved physical row missing after build')
    re=source.RomTables(result,COUNT,selected_species=set(level))
    need(re.egg==egg and all(re.level[sid]==v for sid,v in level.items()),'layer readback differs')
    old_root=tables.roots['level']-BASE;new_root=re.roots['level']-BASE
    for sid in range(COUNT):
        if sid not in level:need(result[new_root+sid*4:new_root+sid*4+4]==parent[old_root+sid*4:old_root+sid*4+4],'unselected species pointer changed')
    return result,{'schema_version':1,'status':'BUILT_NOT_NATIVE_ACCEPTED','parent':identity(parent),'candidate':identity(result),
        'crc32':f'{zlib.crc32(result)&0xffffffff:08X}','allocation':final_plan,'writes':spans,'projection':projection,'roots':roots,'symbols':syms,
        'reconciliation':{k:v['summary'] for k,v in groups.items()},'level_rows_added':310,'egg_rows_added':189,'baseline_records_modified':0,
        'existing_four_move_slots_rewritten':False,'new_adoptions':0,'release_ready':False,'native_acceptance':False,'active_baseline_changed':False}


def run(output):
    output=output.absolute();output.resolve().relative_to((ROOT/'.local').resolve())
    need(not any(p.is_symlink() for p in (output,*output.parents)),'unsafe output path')
    output.mkdir(parents=True,exist_ok=True)
    parent_path=ROOT/'.local/final-integration-candidate/candidate.gba'
    parent=source.checked(parent_path,source.ROM_SHA)
    v4=source.checked(ROOT/'userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip',source.V4_SHA)
    species=source.checked(ROOT/'manifests/species_ids.csv',source.SPECIES_SHA)
    moves=source.checked(ROOT/'manifests/move_ids.csv',source.MOVES_SHA)
    raw_layout=source.checked(ROOT/ALLOCATION,ALLOCATION_SHA)
    source.checked(ROOT/'config/rom_regions.csv',REGIONS_SHA)
    selected,members=source.recover(v4,species,moves)
    result,report=build(parent,selected,json.loads(raw_layout))
    report['source_inputs']={'v4':identity(v4),'members':members,'species_manifest':identity(species),'move_manifest':identity(moves),'parent_layout':identity(raw_layout)}
    report['source_bindings']={p:identity((ROOT/p).read_bytes()) for p in (SRC,SPEC,'scripts/pr16_p07_preserved_layer.py','scripts/pr16_integration_continuation.py','scripts/pr16_source_acceptance.py','tools/rom_allocator.py')}
    (output/'candidate.gba').write_bytes(result)
    for name,left,right in (('stage84-to-integrated-p07.bps',parent,result),('integrated-p07-to-stage84.bps',result,parent)):
        patch=create_bps(left,right);need(apply_bps(left,patch)==right,'BPS roundtrip failed')
        (output/name).write_bytes(patch)
    report['patches']={p.name:identity(p.read_bytes()) for p in sorted(output.glob('*.bps'))}
    need(identity(parent_path.read_bytes())==identity(parent),'Stage84 parent modified')
    (output/'candidate.json').write_bytes(stable(report));(output/'selected-source.json').write_bytes(stable(selected))
    print(json.dumps({k:report[k] for k in ('status','candidate','crc32','reconciliation')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=WORK)
    try:run(p.parse_args().output)
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as e:
        if isinstance(e,subprocess.CalledProcessError) and e.stderr:print(e.stderr.decode() if isinstance(e.stderr,bytes) else e.stderr,file=sys.stderr)
        print(str(e),file=sys.stderr);raise SystemExit(1)
