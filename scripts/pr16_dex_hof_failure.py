#!/usr/bin/env python3
"""HOFの局所保存通知。全既存owner不変と実section占有を機械検査する。"""
from __future__ import annotations
import copy,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='overlays/dex_owner/dex_hof_save_failure.S'
BINDINGS='content/modernization/pr16_dex_hof_failure_bindings.json'
CP='content/modernization/pr16_dex_union_checkpoint.json'
BASE=0x09FFFCC0;SIZE=260;END=BASE+SIZE
EXPORTS=('VegaDexHofSaveResultGate','VegaDexHofSaveNotifyTail','VegaDexHofSaveFailureWait')
def need(x,m):
 if not x:raise ValueError(m)
def identity(b):
 import hashlib
 return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def signed(before):
 cp=checkpoint();need(identity(before)==cp['candidate'],'exact accepted Union candidate')
 for row in proof()['windows']+[proof()['error_text']]:
  at=row['address']-0x08000000;need(identity(before[at:at+row['size']])=={k:row[k]for k in('size','sha256')},'complete signed HOF boundary '+row['id'])
def link(folder,before):
 import pr16_dex_placement as p,pr16_dex_scheduler as s
 signed(before);need(not folder.exists(),'fresh HOF link');folder.mkdir(parents=True)
 def run(args):
  r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict HOF link '+r.stderr[-1800:]);return r.stdout
 obj=folder/'hof.o';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(ROOT/SOURCE),'-o',str(obj)])
 ld=folder/'hof.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'hof.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,'+EXPORTS[0],'-Wl,-T,'+str(ld),str(obj),'-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all HOF symbols resolved');symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE and sections[0]['size']==SIZE,'one immutable audited260byte owner');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need([symbols[n]['address']for n in EXPORTS]==[BASE,BASE+80,BASE+236],'exact three authored subowners')
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports={n:symbols[n]['address']|1 for n in EXPORTS},sections=[{k:x[k]for k in('name','address','size')}for x in sections],compile_units=1,arm_links=1,new_mutable_owners=0)
def apply(before,payload,linked):
 import pr16_dex_battle_consumers as b,pr16_dex_subowners as sub
 import pr16_dex_hof_tail_lease as lease
 signed(before);cp=checkpoint();allocation=copy.deepcopy(cp['current_build']['placement']['allocation']);owners=allocation['allocations'];need(len(owners)==113,'all113 current owners')
 lo=BASE-0x08000000;hi=END-0x08000000;need(len(payload)==SIZE and identity(payload)==linked['payload'],'complete current compiled payload')
 need(before[lo:hi]==b'\xff'*SIZE,'every actual new byte blank');need(all(r['end_exclusive']<=lo or r['start']>=hi for r in owners),'no allocator collision')
 need(all(r['address']+r['size']<=BASE or r['address']>=END for r in sub.occupied()),'no actual codec/scheduler section collision')
 audit=lease.validate(before);need(before[0xDB360:0xDB368]==b.tail_patch(0x080DB360,0x09FFFBA9),'exact prior Union dispatcher')
 after=bytearray(before);after[lo:hi]=payload;after[0xDB360:0xDB368]=b.tail_patch(0x080DB360,linked['exports'][EXPORTS[0]]);after[0xF3194:0xF319C]=b.tail_patch(0x080F3194,linked['exports'][EXPORTS[1]])
 windows=sorted([(lo,hi),(0xDB360,0xDB368),(0xF3194,0xF319C)]);cursor=0
 for a,z in windows:need(before[cursor:a]==after[cursor:a],'every undeclared ROM byte');cursor=z
 need(before[cursor:]==after[cursor:],'whole trailing ROM bytes')
 owner_audit=[]
 for r in owners:
  a,z=r['start'],r['end_exclusive'];pre=identity(before[a:z]);post=identity(after[a:z]);need(pre==post,'every existing owner byte '+r['name']);owner_audit.append(dict(name=r['name'],address=a+0x08000000,size=z-a,sha256=pre['sha256'],unchanged=True))
 allocation['allocations'].append(dict(name='pr16_dex_hof_notification',region='future_tail',start=lo,size=SIZE,alignment=4,placement='EXPLICIT',owner='USER-20261005-DEX-HOF-FAILURE',purpose='HOF truthful failure wait and exact caller result guard',content_sha256=identity(payload)['sha256']))
 rebuilt=b.p.rebuild_allocation(allocation);need(len(rebuilt['allocations'])==114 and rebuilt['summaries']['overlap_count']==0,'114owners overlap0')
 reverse=bytearray(after)
 for a,z in windows:reverse[a:z]=before[a:z]
 need(bytes(reverse)==before,'whole ROM exact inverse')
 return bytes(after),dict(allocation=rebuilt,tail_reference_audit=audit,owner_byte_audit=owner_audit,unchanged_owners=113,whole_rom_rollback_exact=True,patches=[dict(address=a+0x08000000,size=z-a,sha256=identity(after[a:z])['sha256'])for a,z in windows],remaining_tail_start=END,remaining_tail_bytes=0x0A000000-END,formal_rom_changed=False,formal_save_changed=False)
