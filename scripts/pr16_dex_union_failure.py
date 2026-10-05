#!/usr/bin/env python3
"""Union Room Chat保存の文字列、成功音、失敗入力待ちを局所安全化。"""
from __future__ import annotations
import copy,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='overlays/dex_owner/dex_union_save_failure.S'
BINDINGS='content/modernization/pr16_dex_union_failure_bindings.json'
CP='content/modernization/pr16_dex_mystery_checkpoint.json'
BASE=0x09FC1DB8
END=0x09FC22EC
EXPORTS=('VegaDexUnionSaveResultGate','VegaDexUnionSaveTextTail','VegaDexUnionSaveWaitTail')
def need(x,m):
 if not x:raise ValueError(m)
def identity(b):return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def signed(before):
 need(identity(before)==checkpoint()['candidate'],'exact accepted Mystery Gift parent')
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
  r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict union link '+r.stderr[-1500:]);return r.stdout
 obj=folder/'union.o';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(ROOT/SOURCE),'-o',str(obj)]);objects=[obj]
 ld=folder/'union.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'union.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,'+EXPORTS[0],'-Wl,-T,'+str(ld),*map(str,objects),'-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all union symbols resolved')
 symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable suffix payload');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need(0<len(payload)<=END-BASE and len(payload)%4==0,'bounded existing reserved suffix')
 exports={n:symbols[n]['address']|1 for n in EXPORTS}
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports=exports,compile_units=1,arm_links=1,new_mutable_owners=0,error_text=proof()['error_text'])

def apply(before,payload,linked):
 import pr16_dex_battle_consumers as b
 signed(before);cp=checkpoint();old=cp['isolated']['link']
 need(before[0xDB360:0xDB368]==b.tail_patch(0x080DB360,old['exports']['VegaDexMysterySaveResultGate']),'exact current Mystery gate chain')
 allocation=copy.deepcopy(cp['isolated']['placement']['allocation'])
 owners=allocation['allocations'];need(len(owners)==112,'all current112 allocator owners')
 owner=[x for x in owners if x['name']=='pr16_dex_runtime_reserved'];need(len(owner)==1,'one existing codec reservation');owner=owner[0]
 lo=BASE-0x08000000;hi=lo+len(payload);a,z=owner['start'],owner['end_exclusive']
 need(lo==old['base']-0x08000000+old['payload']['size'] and hi<=z==END-0x08000000,'strictly after the current Mystery payload')
 need(identity(before[a:z])['sha256']==owner['content_sha256'],'whole current reservation signed')
 need(before[lo:z]==b'\xff'*(z-lo),'every prospective suffix byte actually blank; no historical reservation assumption')
 after=bytearray(before);after[lo:hi]=payload;windows=[(lo,hi)]
 for address,name,size in [(0x080DB360,EXPORTS[0],8),(0x0812AF64,EXPORTS[1],12),(0x08129AC4,EXPORTS[2],12)]:
  at=address-0x08000000;after[at:at+size]=b.tail_patch(address,linked['exports'][name])+struct.pack('<H',0x46C0)*((size-8)//2);windows.append((at,at+size))
 cursor=0
 for x,y in sorted(windows):need(before[cursor:x]==after[cursor:x],'every undeclared ROM byte');cursor=y
 need(before[cursor:]==after[cursor:]and before[a:lo]==after[a:lo],'whole previous codec and Mystery payload retained')
 audit=[];changed=[]
 for row in owners:
  x,y=row['start'],row['end_exclusive'];pre=identity(before[x:y]);post=identity(after[x:y]);modified=pre!=post
  audit.append(dict(name=row['name'],address=x+0x08000000,size=y-x,declared_sha256=row['content_sha256'],before_sha256=pre['sha256'],after_sha256=post['sha256'],changed=modified))
  if modified:need(row['name']==owner['name'],'only existing codec owner changes');changed.append(row['name']);row['content_sha256']=post['sha256']
 need(changed==[owner['name']],'one explicitly updated owner')
 rebuilt=b.p.rebuild_allocation(allocation);need(rebuilt['summaries']==cp['isolated']['placement']['allocation']['summaries'],'no allocation/overlap/free-space drift')
 reverse=bytearray(after)
 for x,y in windows:reverse[x:y]=before[x:y]
 need(bytes(reverse)==before,'whole ROM exact inverse')
 return bytes(after),dict(allocation=rebuilt,owner_byte_audit=audit,modified_owners=changed,unchanged_owners=111,retained_codec_and_mystery_bytes=lo-a,prior_failure_gates_unchanged=True,prior_outer_qol_unchanged=True,whole_rom_rollback_exact=True,remaining_reserved_start=BASE+len(payload),remaining_reserved_bytes=END-BASE-len(payload),patches=[dict(address=x+0x08000000,size=y-x,sha256=identity(after[x:y])['sha256'])for x,y in sorted(windows)],formal_rom_changed=False,formal_save_changed=False)
