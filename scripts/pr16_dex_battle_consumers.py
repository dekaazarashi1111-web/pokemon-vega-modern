#!/usr/bin/env python3
"""図鑑battle seen5窓と公式countの最小consumer縦切り。"""
from __future__ import annotations
import copy,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_lifecycle as lifecycle
p=lifecycle.placement;need,identity=lifecycle.need,lifecycle.identity
CP='content/modernization/pr16_dex_lifecycle_checkpoint.json'
BINDINGS='content/modernization/pr16_dex_battle_bindings.json'
SOURCES=['overlays/dex_owner/dex_battle_consumers.c','overlays/dex_owner/dex_battle_consumers.S']
BASE=p.BASE+5024
END=p.lease.BASE+p.lease.END
EXPORTS=('VegaDexBattleSeen','VegaDexBattleOfficialCount')
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def seen_patch(address,target):
    need(address%4==2 and target&1,'aligned fourteen-byte Thumb call window')
    # ADR r1,continuation; ADD r1,#1; LDR r3,target; BX r3; NOP; literal.
    # continuation address=address+14, caller-saved r1/r3, raw SID stays in r0.
    return struct.pack('<5HI',0xA103,0x3101,0x4B01,0x4718,0x46C0,target)
def tail_patch(address,target):
    need(address%4==0 and target&1,'aligned Thumb tail entry')
    return struct.pack('<2HI',0x4B00,0x4718,target)
def link(folder):
    need(not folder.exists(),'fresh consumer linkage');folder.mkdir(parents=True)
    header=folder/'entries.h';header.write_text(lifecycle.abi_header())
    def run(args):
        r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
        need(r.returncode==0 and not r.stderr,'consumer compiler: '+r.stderr[-2000:]);return r.stdout
    objects=[]
    for path in SOURCES:
        obj=folder/(Path(path).name+'.o');flags=p.FLAGS if path.endswith('.c') else ['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork']
        run(['arm-none-eabi-gcc',*flags,'-DDEX_CONSUMER_ENTRIES="'+str(header)+'"','-c',str(ROOT/path),'-o',str(obj)]);objects.append(obj)
    ld=folder/'consumer.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text.dex_consumer_entries)) KEEP(*(.text*)) *(.rodata*) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
    elf=folder/'consumer.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,--gc-sections','-Wl,-e,VegaDexBattleSeen','-Wl,-T,'+str(ld),*map(str,objects),'-lgcc','-o',str(elf)])
    need(not run(['arm-none-eabi-nm','-u',str(elf)]),'no unresolved consumers')
    sections=[s for s in lifecycle.scheduler.elf_sections(elf.read_bytes())if s['flags']&2 and s['size']]
    need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable existing reserved owner suffix')
    symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]))
    raw=elf.read_bytes();sec=sections[0];payload=raw[sec['offset']:sec['offset']+sec['size']]
    need(0<len(payload)<=END-BASE and len(payload)%4==0,'bounded aligned payload')
    exports={n:symbols[n]['address']|1 for n in EXPORTS}
    need(all(BASE<=a-1<BASE+len(payload)for a in exports.values()),'all exports owned')
    return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports=exports,compile_units=2,arm_links=1,new_mutable_owners=0)
def apply(before,payload,linked):
    cp=checkpoint();audit=proof();need(identity(before)==cp['candidate']==audit['parent_candidate'],'exact accepted lifecycle candidate')
    need(cp['isolated']['placement']['allocation']['summaries']['allocation_count']==109,'accepted full allocation')
    need(0<len(payload)<=END-BASE and len(payload)%4==0,'bounded consumer payload')
    after=bytearray(before);lo=BASE-0x08000000;after[lo:lo+len(payload)]=payload
    changed=[(lo,lo+len(payload))]
    for w in audit['windows']:
        a=w['address'];at=a-0x08000000
        need(identity(before[at:at+w['size']])==dict(size=w['size'],sha256=w['sha256']),'exact preimage '+w['id'])
        if w['id']=='active_switch_opcode':need(struct.unpack_from('<I',before,at)[0]==0x080238D5,'active switch root');continue
        patch=tail_patch(a,linked['exports'][EXPORTS[1]]) if w['id']=='cfru_official_count' else seen_patch(a,linked['exports'][EXPORTS[0]])
        need(len(patch)<=w['size'],'whole instruction patch bounded');after[at:at+len(patch)]=patch;changed.append((at,at+len(patch)))
    cursor=0
    for a,b in sorted(changed):need(before[cursor:a]==after[cursor:a],'all non-patch ROM bytes retained');cursor=b
    need(before[cursor:]==after[cursor:],'whole ROM suffix retained')
    allocation=copy.deepcopy(cp['isolated']['placement']['allocation']);owners=[]
    for row in allocation['allocations']:
        a,b=row['start'],row['end_exclusive']
        if before[a:b]!=after[a:b]:
            need(row['name']==p.NAME and identity(before[a:b])['sha256']==row['content_sha256'],'only reserved codec suffix owner changed')
            need(a<=lo<lo+len(payload)<=b and before[a:lo]==after[a:lo]and before[lo+len(payload):b]==after[lo+len(payload):b],'codec and reserved rest remain exact')
            row['content_sha256']=identity(after[a:b])['sha256'];owners.append(row['name'])
    need(owners==[p.NAME],'one existing owner suffix used')
    result=p.rebuild_allocation(allocation);need(result==allocation,'all owner ranges and allocation totals preserved')
    reverse=bytearray(after)
    for a,b in changed:reverse[a:b]=before[a:b]
    need(bytes(reverse)==before,'entire ROM rollback exact')
    return bytes(after),dict(allocation=result,changed_existing_owners=owners,patches=[dict(address=a+0x08000000,size=b-a,sha256=identity(after[a:b])['sha256'])for a,b in sorted(changed)],whole_rom_rollback_exact=True,codec_unchanged=True,save_scheduler_unchanged=True,load_newgame_unchanged=True,battle_seen_sites_wired=5,cfru_official_count_wired=True,all_consumers_wired=False,formal_rom_changed=False,formal_save_changed=False)
