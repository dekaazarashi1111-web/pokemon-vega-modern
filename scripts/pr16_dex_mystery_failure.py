#!/usr/bin/env python3
"""Mystery Gift保存の誤成功通知を、既存menu window内で閉じる。"""
from __future__ import annotations
import copy,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='overlays/dex_owner/dex_mystery_save_failure.S'
BINDINGS='content/modernization/pr16_dex_mystery_failure_bindings.json'
CP='content/modernization/pr16_dex_outer_qol_checkpoint.json'
BASE=0x09FC1D38
END=0x09FC22EC
EXPORTS=('VegaDexMysterySaveResultGate','VegaDexMysterySaveMessageTail')
def need(x,m):
 if not x:raise ValueError(m)
def identity(b):return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def signed(before):
 need(identity(before)==checkpoint()['candidate'],'exact accepted outer parent')
 for w in proof()['windows']:
  a=w['address']-0x08000000;need(identity(before[a:a+w['size']])==dict(size=w['size'],sha256=w['sha256']),'signed boundary '+w['id'])
 text=proof()['error_text'];a=text['address']-0x08000000
 need(identity(before[a:a+text['size']])==dict(size=text['size'],sha256=text['sha256']),'signed existing error text')
 encoded=before[a:a+text['size']]
 need(encoded[-1]==255 and encoded.count(bytes([254]))==1 and all(x not in encoded for x in (bytes([250]),bytes([251]),bytes([252]),bytes([253]))),'two lines without page/placeholder/control')
def link(folder,before):
 import pr16_dex_placement as p
 import pr16_dex_scheduler as s
 signed(before);need(not folder.exists(),'fresh owned suffix link');folder.mkdir(parents=True)
 def run(args):
  r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict mystery link '+r.stderr[-1500:]);return r.stdout
 obj=folder/'mystery.o';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(ROOT/SOURCE),'-o',str(obj)]);objects=[obj]
 ld=folder/'mystery.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'mystery.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,'+EXPORTS[0],'-Wl,-T,'+str(ld),*map(str,objects),'-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all mystery symbols resolved')
 symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable suffix payload');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need(0<len(payload)<=END-BASE and len(payload)%4==0,'bounded existing reserved suffix')
 exports={n:symbols[n]['address']|1 for n in EXPORTS}
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports=exports,compile_units=1,arm_links=1,new_mutable_owners=0,error_text=proof()['error_text'])

def apply(before,payload,linked):
 import pr16_dex_battle_consumers as b
 signed(before);need(before[0xDB360:0xDB368]==b.tail_patch(0x080DB360,0x095FFEF1),'exact existing precursor target');cp=checkpoint();allocation=copy.deepcopy(cp['measurement']['placement']['allocation'])
 owner=[x for x in allocation['allocations']if x['name']=='pr16_dex_runtime_reserved'];need(len(owner)==1,'one reserved codec owner');owner=owner[0]
 lo=BASE-0x08000000;hi=lo+len(payload);a,z=owner['start'],owner['end_exclusive']
 need(a+5022<=lo and hi<=z==END-0x08000000 and identity(before[a:z])['sha256']==owner['content_sha256'],'exact codec owner and reserved suffix')
 need(identity(before[a:a+5022])==proof()['retained_codec'],'all accepted5022 codec bytes before suffix')
 after=bytearray(before);after[lo:hi]=payload;windows=[(lo,hi)]
 for address,name in [(0x080DB360,EXPORTS[0]),(0x08143288,EXPORTS[1])]:
  at=address-0x08000000;after[at:at+8]=b.tail_patch(address,linked['exports'][name]);windows.append((at,at+8))
 cursor=0
 for x,y in sorted(windows):need(before[cursor:x]==after[cursor:x],'every undeclared ROM byte');cursor=y
 need(before[cursor:]==after[cursor:]and before[a:a+5022]==after[a:a+5022],'whole suffix and codec retained')
 changed=[]
 for row in allocation['allocations']:
  x,y=row['start'],row['end_exclusive']
  if before[x:y]!=after[x:y]:need(row['name']==owner['name'],'only owned reserved codec suffix');changed.append(row['name']);row['content_sha256']=identity(after[x:y])['sha256']
 need(changed==[owner['name']],'one updated reservation owner')
 rebuilt=b.p.rebuild_allocation(allocation);need(rebuilt['summaries']==cp['measurement']['placement']['allocation']['summaries'],'no added allocation/overlap/free-space drift')
 reverse=bytearray(after)
 for x,y in windows:reverse[x:y]=before[x:y]
 need(bytes(reverse)==before,'whole ROM exact inverse')
 return bytes(after),dict(allocation=rebuilt,modified_owners=changed,unchanged_owners=111,retained_codec_bytes=5022,prior_failure_gates_unchanged=True,prior_outer_qol_unchanged=True,whole_rom_rollback_exact=True,patches=[dict(address=x+0x08000000,size=y-x,sha256=identity(after[x:y])['sha256'])for x,y in sorted(windows)],formal_rom_changed=False,formal_save_changed=False)
