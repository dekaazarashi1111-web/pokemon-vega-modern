#!/usr/bin/env python3
"""保存候補へ新しい供給ARM moduleだけを配置。旧生成/ARM/受入試験は再実行しない。"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_supply_abi as saved
from tools.pr16_learnset_runtime import free_span
WORK=ROOT/'.local/pr16-learnset-supply-link'
BASE=0x08000000
TASK='USER-20260922-LEARNSET-SUPPLY-ABI'
ABI_ARTIFACT={'id':10695132022,'name':'pr16-learnset-supply-abi','size_in_bytes':24909,
    'digest':'sha256:c823b11ff7ee9a1b4558598ade9cfe9604cbc2d8d8a674d18cc69bf239b573b7'}
ABI_HEAD='c5d60474c51d3b7d635468af72c568b5f19edce8'
CODE=('src/modernization/pr16_learnset_supply.c','src/modernization/pr16_learnset_supply_game.c',
      'src/modernization/pr16_learnset_supply_native.c','src/modernization/pr16_learnset_supply.h',
      'src/modernization/pr16_learnset_supply_game.h','src/modernization/pr16_learnset_runtime.h',
      'src/modernization/pr16_learnset_owner.h','tests/test_pr16_learnset_supply_native.py',
      'scripts/pr16_learnset_supply_abi.py','scripts/pr16_learnset_supply_link.py',
      '.github/workflows/pr16-learnset-supply-link.yml')
need,identity,write=saved.need,saved.identity,saved.write


def command(args, destination=None):
    run=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240)
    if destination:destination.write_bytes(run.stdout+run.stderr)
    need(run.returncode==0, '工程失敗: '+str(args[:3])+' '+run.stderr.decode(errors='replace')[-2000:])
    return run.stdout


def direct_bl(raw,address,target):
    found=[]
    for at in range(0,len(raw)-3,2):
        hi,lo=struct.unpack_from('<HH',raw,at)
        if hi&0xf800==0xf000 and lo&0xf800==0xf800:
            delta=((hi&0x7ff)<<12)|((lo&0x7ff)<<1)
            if delta&0x400000:delta-=0x800000
            if address+at+4+delta==target:found.append(address+at)
    return found


def row(name,region,start,blob,sequence):
    return {'name':name,'region':region,'start':start,'end_exclusive':start+len(blob),
        'size':len(blob),'alignment':4,'placement':'FIRST_FIT','owner':TASK,
        'purpose':'PLA1供給とTutor特殊ABIの明示owner接続','content_sha256':identity(blob)['sha256'],
        'sequence':sequence,'gba_start':BASE+start,'gba_end_exclusive':BASE+start+len(blob)}


def bind(prior,data_start):
    symbols=prior['symbols']
    reader=symbols['Pr16ReadCompactConditional']|1
    compact=symbols['Pr16ConditionalImage']
    parent=symbols['Pr16_GameGetConditionalRelearnerMoves']|1
    return f'''#ifndef PR16_SUPPLY_BINDINGS_H
#define PR16_SUPPLY_BINDINGS_H
#include "pr16_learnset_runtime.h"
uint8_t Pr16_SupplyOriginalTutor(void *,uint8_t);
#define PR16_SUPPLY_GET_MON_DATA ((uint32_t (*)(void *,int,uint8_t *))0x0803F355u)
#define PR16_SUPPLY_READ_CONDITIONAL(s,c,v) (((uint8_t (*)(const uint8_t *,uint32_t,uint16_t,uint8_t,struct Pr16RuntimeView *)){hex(reader)}u)((const uint8_t *){hex(compact)}u,31014u,(s),(c),(v)))
#define PR16_SUPPLY_IMAGE ((const uint8_t *){hex(BASE+data_start)}u)
#define PR16_SUPPLY_IMAGE_SIZE 21383u
#define PR16_SUPPLY_FLAG_GET ((uint8_t (*)(uint16_t))0x0806DEC5u)
#define PR16_SUPPLY_MEMORY_MODE ((volatile uint8_t *)0x0203EC00u)
#define PR16_SUPPLY_PARENT_RELEARNER ((uint8_t (*)(void *,uint16_t *)){hex(parent)}u)
#define PR16_SUPPLY_GET_TUTOR_MOVE ((uint16_t (*)(uint8_t))0x091103A9u)
#define PR16_SUPPLY_SPECIAL_TUTOR Pr16_SupplyOriginalTutor
#define PR16_SUPPLY_PARTY_SELECTION ((volatile uint16_t *)0x02036FF4u)
#define PR16_SUPPLY_RESULT ((volatile uint16_t *)0x02037004u)
#define PR16_SUPPLY_PARTY ((uint8_t *)0x020241E4u)
#endif
'''


def link(folder):
    folder.mkdir()
    parent=(WORK/'input/parent.gba').read_bytes()
    prior=json.loads((WORK/'input/compact/link.json').read_bytes())
    abi=json.loads((WORK/'abi/abi.json').read_bytes())
    need(identity(parent)==abi['candidate']==prior['candidate'],'保存ABI親不一致')
    for entry in abi['entries'].values():
        raw=bytes.fromhex(entry['window_hex']);at=entry['offset']
        need(parent[at:at+len(raw)]==raw and entry['address']==BASE+at,'保存ABI window不一致')
    callers={}
    for name,start,end in (('Prepare',0x0953A1D4,0x0953A1FC),('Open',0x0953A2B0,0x0953A32C),
                           ('Commit',0x0953A1FC,0x0953A23C)):
        calls=direct_bl(parent[start-BASE:end-BASE],start,0x09539D78)
        need(len(calls)==1,'raw行数helper共有契約不一致: '+name);callers[name]=calls
    need(parent[0x1110228:0x1110230].hex()=='f8b500220c00544f'
         and parent[0x1110230:0x1110234].hex()=='0b210600'
         and parent[0x1110238:0x111023C].hex()=='3f2c29d8'
         and parent[0x1110380:0x1110384].hex()=='55f30308'
         and parent[0x11103A8:0x11103D8].hex()==abi['entries']['CanMonLearnTutorMove']['window_hex'][0x180*2:0x1b0*2],
         '通常64/特殊152..160/親prologue/literal契約不一致')
    image=(WORK/'input/supply/archive-image.bin').read_bytes()
    need(identity(image)==abi['archive'],'PLA1固定image不一致')
    plan=copy.deepcopy(prior['allocation'])
    data_start,data_region=free_span(plan,len(image))
    need(data_start==23045368,'受入配置計画不一致')
    plan['allocations'].append(row('pr16_supply_pla1',data_region,data_start,image,len(plan['allocations'])))
    start,region=free_span(plan,4028)
    rel=folder.relative_to(ROOT).as_posix()
    (folder/'pr16_learnset_supply_bindings.h').write_text(bind(prior,data_start))
    # 元prologueのPC相対loadだけを固定literalへ展開し、残る特殊bodyへ戻る。
    (folder/'original_tutor.S').write_text('''.syntax unified
.cpu arm7tdmi
.thumb
.section .text.Pr16_SupplyOriginalTutor,"ax",%progbits
.balign 4
.global Pr16_SupplyOriginalTutor
.type Pr16_SupplyOriginalTutor,%function
.thumb_func
Pr16_SupplyOriginalTutor:
 push {r3,r4,r5,r6,r7,lr}
 movs r2,#0
 movs r4,r1
 ldr r7,=0x0803F355
 ldr r3,=0x09110231
 bx r3
 .ltorg
.section .note.GNU-stack,"",%progbits
''')
    (folder/'supply.ld').write_text('SECTIONS { . = '+hex(BASE+start)+'; .text : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } ASSERT(SIZEOF(.data)==0,"data forbidden") ASSERT(SIZEOF(.bss)==0,"BSS forbidden") }\n')
    flags=['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin',
        '-fno-common','-fno-pic','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
        '-fno-jump-tables','-Wall','-Wextra','-Werror','-Isrc/modernization','-I'+rel]
    objects=[]
    for name in ('pr16_learnset_supply','pr16_learnset_supply_game','pr16_learnset_supply_native'):
        target=rel+'/'+name+'.o';objects.append(target)
        command(['arm-none-eabi-gcc',*flags,'-c','src/modernization/'+name+'.c','-o',target])
    objects.append(rel+'/original_tutor.o')
    command(['arm-none-eabi-gcc',*flags,'-c',rel+'/original_tutor.S','-o',objects[-1]])
    elf=rel+'/supply.elf'
    command(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-T,'+rel+'/supply.ld',*objects,'-lgcc','-o',elf])
    need(not command(['arm-none-eabi-nm','-u',elf]).strip(),'未解決ARM symbol')
    command(['arm-none-eabi-objcopy','-O','binary',elf,rel+'/supply.bin'])
    (folder/'disassembly.txt').write_bytes(command(['arm-none-eabi-objdump','-d',elf]))
    symbols={}
    for line in command(['arm-none-eabi-nm','-n',elf]).decode().splitlines():
        p=line.split()
        if len(p)==3:symbols[p[2]]=int(p[0],16)
    blob=(folder/'supply.bin').read_bytes()
    need(0<len(blob)<=4028,'新ARM容量超過')
    plan['allocations'].append(row('pr16_supply_arm',region,start,blob,len(plan['allocations'])))
    segments=[dict(row_,file=name,sha256=row_['content_sha256']) for row_,name in zip(plan['allocations'][-2:],('archive-image.bin','supply.bin'))]
    out=bytearray(parent)
    for seg,raw in zip(segments,(image,blob)):
        at=seg['start'];need(parent[at:at+len(raw)]==b'\xff'*len(raw),'新segment preimage不一致')
        out[at:at+len(raw)]=raw
    hooks=[]
    for name,at in (('Pr16_GameCanLearnTutor',0x1110228),('Pr16_GameSupplyRelearner',0x11141D4),
                    ('Pr16_GameSupplySelectedRowCount',0x1539D78),('Pr16_GameSupplySelectedPageHasMoves',0x153A23C)):
        target=symbols[name];need(at%4==0 and target%2==0 and BASE+start<=target<BASE+start+len(blob),'新hook範囲不正')
        after=b'\x00\x4b\x18\x47'+struct.pack('<I',target|1)
        hooks.append({'symbol':name,'offset':at,'before':parent[at:at+8].hex(),'after':after.hex(),'target':target|1})
        out[at:at+8]=after
    rollback=bytearray(out);spans=[]
    for seg in segments:spans.append((seg['start'],seg['end_exclusive']))
    for patch in hooks:spans.append((patch['offset'],patch['offset']+8))
    for a,b in spans:rollback[a:b]=parent[a:b]
    spans.sort();need(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])) and bytes(rollback)==parent,'宣言外変更/重複')
    for at in prior['protected_root_offsets']:need(out[at:at+4]==parent[at:at+4],'共有root変更')
    for seg in prior['segments']:need(out[seg['start']:seg['start']+seg['size']]==parent[seg['start']:seg['start']+seg['size']],'受入PLC2/code変更')
    need(out[0x1110230:0x11103D8]==parent[0x1110230:0x11103D8],'特殊body/catalog変更')
    touched=[]
    for alloc in plan['allocations'][:-2]:
        if any(alloc['start']<=p['offset']<alloc['end_exclusive'] for p in hooks):
            alloc['content_sha256']=identity(out[alloc['start']:alloc['end_exclusive']])['sha256'];touched.append(alloc['name'])
    summary=plan['summaries']
    for seg in segments:
        summary['allocation_count']+=1;summary['allocated_bytes']+=seg['size'];summary['remaining_allocatable_bytes']-=seg['size']
        for usage in summary['region_usage']:
            if usage['region']==seg['region']:
                usage['allocation_count']+=1;usage['allocated_bytes']+=seg['size'];usage['remaining_bytes']-=seg['size']
    special=list(struct.unpack_from('<9H',parent,0x1167798))
    need(all(1<=move<=1062 for move in special),'特殊Tutor move catalog不正')
    report={'status':'LINKED_PLA1_TUTOR_AND_ARCHIVE','parent':identity(parent),'candidate':identity(out),
        'candidate_crc32':f'{zlib.crc32(out)&0xffffffff:08X}','segments':segments,'hooks':hooks,
        'code_start':BASE+start,'code_end':BASE+start+len(blob),'symbols':{k:v for k,v in symbols.items() if k.startswith('Pr16')},
        'allocation':plan,'updated_allocation_hashes':touched,'page_count_callers':callers,
        'special_tutor_ids':list(range(152,161)),'special_tutor_moves':special,
        'protected_root_offsets':prior['protected_root_offsets'],'outside_declared_ranges':0,
        'parent_compact_segments_unchanged':True,'special_body_unchanged':True,'ordinary_mode_delegate':prior['symbols']['Pr16_GameGetConditionalRelearnerMoves']|1,
        'old_arm_compiles':0,'accepted_payload_regenerations':0,'accepted_tests_rerun':0,'accepted_native_reruns':0,
        'rom_hooks_installed':True,'gameplay_e2e_accepted':False,'physical_supply_verified':False,'issue19_complete':False,'release_ready':False}
    (folder/'candidate.gba').write_bytes(out);(folder/'archive-image.bin').write_bytes(image);write(folder/'link.json',report)
    return report


def verify():
    WORK.mkdir(parents=True);proof=WORK/'proof';proof.mkdir()
    command([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_supply_native','-v'],proof/'unit.txt')
    need((proof/'unit.txt').read_bytes().count(b' ... ok\n')==14,'新規14試験数不一致')
    saved.WORK=WORK/'input';saved.WORK.mkdir();saved.restore()
    saved.completed_run(35730505925,ABI_HEAD,'.github/workflows/pr16-learnset-supply-abi.yml','supply-abi')
    # metadataと外側hashを先に固定し、exact member bindingを読み取る。
    from pr16_wiki_reconcile import fetch
    import io,zipfile
    artifact=fetch('actions/artifacts/'+str(ABI_ARTIFACT['id']))
    need(all(artifact[k]==ABI_ARTIFACT[k] for k in ('id','name','size_in_bytes','digest')) and not artifact['expired']
         and artifact['workflow_run']['head_sha']==ABI_HEAD,'ABI artifact binding不一致')
    raw=fetch('actions/artifacts/'+str(ABI_ARTIFACT['id'])+'/zip',binary=True)
    need(identity(raw)=={'size':ABI_ARTIFACT['size_in_bytes'],'sha256':ABI_ARTIFACT['digest'].split(':')[1]},'ABI ZIP不一致')
    folder=WORK/'abi';folder.mkdir()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(z.namelist()==['abi.json','source.zip'],'ABI member集合不一致')
        for name in z.namelist():(folder/name).write_bytes(z.read(name))
    abi=json.loads((folder/'abi.json').read_bytes())
    need(abi['source_head']==ABI_HEAD and abi['run_id']==35730505925 and identity((folder/'source.zip').read_bytes())==abi['source_archive'],'ABI内側binding不一致')
    before={name:(identity((ROOT/name).read_bytes()),(ROOT/name).stat().st_mtime_ns) for name in CODE}
    results=[]
    for seed in (11,29):
        result=link(WORK/('build'+str(seed)));results.append(result)
    need(results[0]==results[1],'独立ARM link/candidate不一致')
    for name in ('supply.bin','archive-image.bin','supply.elf'):
        need((WORK/'build11'/name).read_bytes()==(WORK/'build29'/name).read_bytes(),'独立ARM/image byte不一致: '+name)
    need(before=={name:(identity((ROOT/name).read_bytes()),(ROOT/name).stat().st_mtime_ns) for name in CODE},'固定source変更')
    data=WORK/'data';data.mkdir()
    for name in ('link.json','supply.bin','archive-image.bin','supply.elf','disassembly.txt','pr16_learnset_supply_bindings.h','original_tutor.S'):
        shutil.copyfile(WORK/'build11'/name,data/name)
    shutil.copyfile(data/'link.json',proof/'link.json')
    command([sys.executable,'-B','scripts/pr16_resume.py','check'],proof/'resume.json')
    command([sys.executable,'-B','scripts/validate_task_graph.py'],proof/'task-graph.txt')
    command(['git','diff','--exit-code'],proof/'tracked-diff.txt')
    write(proof/'verification.json',{'task':TASK,'status':'PASS_NEW_SUPPLY_ARM_LINK',
        'scope':'REAL_ROM_LINK_NOT_NATIVE_OR_GAMEPLAY_ACCEPTANCE','source_head':os.environ['GITHUB_SHA'],
        'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':results[0]['candidate'],
        'candidate_crc32':results[0]['candidate_crc32'],'new_tests':14,'new_arm_compiles':8,'new_arm_links':2,
        'independent_candidate_match':True,'accepted_tests_rerun':0,'accepted_native_reruns':0,
        'accepted_payload_regenerations':0,'old_arm_compiles':0,'new_native_processes':0,
        'active_baseline_changed':False,'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,'release_ready':False,
        'code_bindings':{n:identity((ROOT/n).read_bytes()) for n in CODE},
        'data_files':{p.name:identity(p.read_bytes()) for p in data.iterdir()},
        'proof_files':{p.name:identity(p.read_bytes()) for p in proof.iterdir()}})
    print(json.dumps({'status':'PASS_NEW_SUPPLY_ARM_LINK','candidate':results[0]['candidate']}))


if __name__=='__main__':
    try:verify()
    except Exception as exc:
        (WORK/'proof').mkdir(parents=True,exist_ok=True)
        write(WORK/'proof/failure.json',{'status':'FAIL','error':str(exc).replace(str(ROOT),'$REPO')})
        raise
