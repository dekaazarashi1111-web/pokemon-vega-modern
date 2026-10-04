#!/usr/bin/env python3
"""外側QOL保存の失敗伝播だけを既存owner署名と全ROM逆変換で接続する。"""
from __future__ import annotations
import copy,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_valid_failure as prior
b=prior.old.b
need,identity=prior.need,prior.identity
SOURCE='overlays/dex_owner/dex_outer_qol_failure.S'
BINDINGS='content/modernization/pr16_dex_outer_qol_bindings.json'
CP='content/modernization/pr16_dex_start_failure_checkpoint.json'
BASE=0x095FFFB0
END=0x09600000
NAME='pr16_dex_outer_qol_failure'
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def thumb_bl(address,target):
    delta=target-address-4
    need(address%2==target%2==0 and -0x400000<=delta<0x400000,'signed Thumb BL reach')
    return struct.pack('<HH',0xF000|((delta>>12)&0x7FF),0xF800|((delta>>1)&0x7FF))
def link(folder):
    need(not folder.exists(),'fresh outer-only link');folder.mkdir(parents=True)
    def run(args):
        r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
        need(r.returncode==0 and not r.stderr,'strict outer compiler: '+r.stderr[-1200:]);return r.stdout
    obj=folder/'outer.o'
    run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(ROOT/SOURCE),'-o',str(obj)])
    ld=folder/'outer.ld'
    ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) *(.rodata*) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
    elf=folder/'outer.elf'
    run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,VegaDexOuterQolResultTail','-Wl,-T,'+str(ld),str(obj),'-o',str(elf)])
    need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all symbols resolved')
    symbols=b.p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]))
    sections=[s for s in b.lifecycle.scheduler.elf_sections(elf.read_bytes())if s['flags']&2 and s['size']]
    need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable owner')
    sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
    need(0<len(payload)<=END-BASE and len(payload)%4==0,'fits audited80byte suffix')
    return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,entry=symbols['VegaDexOuterQolResultTail']['address']|1,compile_units=1,arm_links=1,new_mutable_owners=0)
def apply(before,payload,linked):
    cp=checkpoint();need(identity(before)==cp['candidate'],'accepted START parent')
    for w in proof()['windows']:
        at=w['address']-0x08000000
        need(identity(before[at:at+w['size']])==dict(size=w['size'],sha256=w['sha256']),'signed outer window '+w['id'])
    lo=BASE-0x08000000;hi=lo+len(payload);at=proof()['patch_call']-0x08000000
    need(before[lo:END-0x08000000]==b'\xff'*(END-BASE),'entire suffix unallocated and blank')
    need(before[at:at+6]==struct.pack('<HHH',0xBC10,0xBC02,0x4708),'exact original8byte-frame epilogue')
    after=bytearray(before);after[lo:hi]=payload;after[at:at+4]=thumb_bl(proof()['patch_call'],linked['entry']&~1)
    windows=[(at,at+4),(lo,hi)];cursor=0
    for a,z in sorted(windows):need(before[cursor:a]==after[cursor:a],'all undeclared bytes retained');cursor=z
    need(before[cursor:]==after[cursor:],'whole suffix retained')
    allocation=copy.deepcopy(cp['measurement']['reconstructed_gate']['placement']['allocation'])
    need(len(allocation['allocations'])==111,'all111 prior owners')
    changed=[]
    for row in allocation['allocations']:
        a,z=row['start'],row['end_exclusive']
        if before[a:z]!=after[a:z]:
            need(row['name']=='qol_production_stage36_payload'and a<=at<at+4<=z,'only exact QOL call owner')
            signed=proof()['qol_owner_preimage']
            need(row['content_sha256']==signed['allocation_legacy_sha256'] and a+0x08000000==signed['address'] and z-a==signed['size'],'known historical owner container')
            need(identity(before[a:z])==dict(size=signed['size'],sha256=signed['sha256']),'current whole-QOL signed preimage')
            row['content_sha256']=identity(after[a:z])['sha256'];changed.append(row['name'])
    need(changed==['qol_production_stage36_payload'],'one explicit old owner edit')
    allocation['allocations'].append(dict(name=NAME,region='integration_modules',start=lo,size=len(payload),alignment=4,placement='EXPLICIT',owner='USER-20261004-DEX-OUTER-QOL',purpose='Outer QOL common result tail, return and attempt propagation only',content_sha256=identity(payload)['sha256']))
    rebuilt=b.p.rebuild_allocation(allocation)
    need(len(rebuilt['allocations'])==112 and rebuilt['summaries']['overlap_count']==0,'112 declared owners zero overlap')
    reverse=bytearray(after)
    for a,z in windows:reverse[a:z]=before[a:z]
    need(bytes(reverse)==before,'whole ROM inverse exact')
    return bytes(after),dict(allocation=rebuilt,patches=[dict(address=a+0x08000000,size=z-a,sha256=identity(after[a:z])['sha256'])for a,z in sorted(windows)],unchanged_owners=110,modified_owner=changed[0],historical_owner_hash_reconciled=proof()['qol_owner_preimage'],changed_old_owner_bytes=4,whole_rom_rollback_exact=True,formal_rom_changed=False,formal_save_changed=False)
