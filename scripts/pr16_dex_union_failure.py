#!/usr/bin/env python3
"""Union Room Chat保存の文字列、成功音、失敗入力待ちを局所安全化。"""
from __future__ import annotations
import copy,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='overlays/dex_owner/dex_union_save_failure.S'
BINDINGS='content/modernization/pr16_dex_union_failure_bindings.json'
CP='content/modernization/pr16_dex_mystery_checkpoint.json'
BASE=0x09FFFB28
END=0x0A000000
EXPORTS=('VegaDexMysterySaveResultGate','VegaDexMysterySaveMessageTail','VegaDexUnionSaveResultGate','VegaDexUnionSaveTextTail','VegaDexUnionSaveWaitTail','VegaDexUnionResultDisplayGuard','VegaDexUnionResultDisplayRestored')
MYSTERY_SOURCE='overlays/dex_owner/dex_mystery_save_failure.S'
def need(x,m):
 if not x:raise ValueError(m)
def identity(b):return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def signed(before):
 import pr16_dex_mystery_failure as old
 old.signed(before)
 need(identity(before)==checkpoint()['isolated']['parent_candidate'],'exact intact pre-Mystery outer parent')
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
 objects=[]
 for source in (MYSTERY_SOURCE,SOURCE):
  obj=folder/(Path(source).stem+'.o');run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(ROOT/source),'-o',str(obj)]);objects.append(obj)
 ld=folder/'union.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'union.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,'+EXPORTS[0],'-Wl,-T,'+str(ld),*map(str,objects),'-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all union symbols resolved')
 symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable suffix payload');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need(0<len(payload)<=416 and len(payload)%4==0,'bounded new allocator tail owner')
 exports={n:symbols[n]['address']|1 for n in EXPORTS}
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports=exports,compile_units=2,arm_links=1,new_mutable_owners=0,error_text=proof()['error_text'])

def apply(before,payload,linked):
 import pr16_dex_battle_consumers as b
 import pr16_dex_subowners as sub
 import pr16_dex_tail_lease as tail
 signed(before);cp=checkpoint();outer=json.loads((ROOT/'content/modernization/pr16_dex_outer_qol_checkpoint.json').read_bytes())
 need(identity(before)==outer['candidate'],'intact outer candidate reconstructed without old corrupt overlay')
 need(before[0xDB360:0xDB368]==b.tail_patch(0x080DB360,0x095FFEF1),'exact original outer gate')
 allocation=copy.deepcopy(outer['measurement']['placement']['allocation']);owners=allocation['allocations'];need(len(owners)==112,'all112 healthy existing owners')
 lo=BASE-0x08000000;hi=lo+len(payload);reference_audit=tail.validate(before)
 need(identity(before[lo:])==proof()['new_tail_preimage']and before[lo:]==b'\xff'*(END-BASE),'signed whole unallocated tail is actually FF')
 need(all(row['end_exclusive']<=lo or row['start']>=END-0x08000000 for row in owners),'no existing allocator owner in new tail')
 need(linked['exports']['VegaDexMysterySaveResultGate']==BASE+1 and linked['exports']['VegaDexUnionSaveResultGate']==BASE+128+1,'original Mystery128 byte semantic layout before new Union')
 after=bytearray(before);after[lo:hi]=payload;windows=[(lo,hi)]
 for address,name,size in [(0x080DB360,'VegaDexUnionSaveResultGate',8),(0x08143288,'VegaDexMysterySaveMessageTail',8),(0x0812AF64,'VegaDexUnionSaveTextTail',12),(0x08129AC4,'VegaDexUnionSaveWaitTail',12)]:
  at=address-0x08000000;after[at:at+size]=b.tail_patch(address,linked['exports'][name])+struct.pack('<H',0x46C0)*((size-8)//2);windows.append((at,at+size))
 slot=0x0041A774;need(struct.unpack_from('<I',before,slot)[0]==0x0812AC99,'exact original Union handler17 pointer');after[slot:slot+4]=struct.pack('<I',linked['exports']['VegaDexUnionResultDisplayGuard']);windows.append((slot,slot+4))
 cursor=0
 for x,y in sorted(windows):need(before[cursor:x]==after[cursor:x],'every undeclared ROM byte');cursor=y
 need(before[cursor:]==after[cursor:],'whole remaining tail exact')
 audit=[]
 for row in owners:
  x,y=row['start'],row['end_exclusive'];pre=identity(before[x:y]);post=identity(after[x:y]);need(pre==post,'all112 current owner bytes retained '+row['name']);audit.append(dict(name=row['name'],address=x+0x08000000,size=y-x,declared_sha256=row['content_sha256'],before_sha256=pre['sha256'],after_sha256=post['sha256'],changed=False))
 scheduler=[]
 for row in sub.occupied():
  x=row['address']-0x08000000;y=x+row['size'];need(before[x:y]==after[x:y],'entire original codec/scheduler subowner preserved');scheduler.append(dict(**row,sha256=identity(after[x:y])['sha256']))
 for row in allocation['allocations']:
  if row['name']=='pr16_dex_runtime_reserved':row['purpose']='PR16 codec plus current save scheduler sections; free subspans derived from current linker sections, never historical suffix labels'
 allocation['allocations'].append(dict(name='pr16_dex_nonstart_notifications',region='future_tail',start=lo,size=len(payload),alignment=4,placement='EXPLICIT',owner='USER-20261005-DEX-UNION-FAILURE',purpose='Relocated Mystery and Union truthful failure/result notification gates',content_sha256=identity(payload)['sha256']))
 rebuilt=b.p.rebuild_allocation(allocation);need(len(rebuilt['allocations'])==113 and rebuilt['summaries']['overlap_count']==0,'one new real tail allocation;113owners no overlap')
 reverse=bytearray(after)
 for x,y in windows:reverse[x:y]=before[x:y]
 need(bytes(reverse)==before,'whole ROM exact rollback to intact outer parent')
 need(identity(payload[:360])==dict(size=360,sha256='99731924db9cb13c6c813a6a1703c8467c3bf98700447180e86859e0f8e5caf4'),'all accepted notification code bytes unchanged before new formatter wrapper')
 old=cp['isolated']['link'];repaired_at=old['base']-0x08000000;need(identity(payload[:128])==old['payload'],'relocated Mystery keeps exact128 authored bytes')
 displaced=dict(address=old['base'],size=old['payload']['size'],old_overlay_sha256=old['payload']['sha256'],restored_scheduler_sha256=identity(before[repaired_at:repaired_at+128])['sha256'])
 return bytes(after),dict(allocation=rebuilt,tail_reference_audit=reference_audit,displaced_overlay_correction=displaced,owner_byte_audit=audit,unchanged_owners=112,restored_scheduler_subowners=scheduler,actual_codec_free_subspans=sub.available(),old_mystery_allocation_acceptance_revoked=True,old_mystery_ui_scope_retained=True,prior_failure_gates_unchanged=True,prior_outer_qol_unchanged=True,whole_rom_rollback_exact=True,remaining_tail_start=BASE+len(payload),remaining_tail_bytes=END-BASE-len(payload),patches=[dict(address=x+0x08000000,size=y-x,sha256=identity(after[x:y])['sha256'])for x,y in sorted(windows)],formal_rom_changed=False,formal_save_changed=False)
