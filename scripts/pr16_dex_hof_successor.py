#!/usr/bin/env python3
"""現save-only所有窓の明示後継。旧owner全体をfree扱いしない。"""
from __future__ import annotations
import copy,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_scheduler as scheduler
import pr16_dex_hof_main_cow as previous
need,identity=previous.need,previous.identity
CP='content/modernization/pr16_dex_hof_main_checkpoint.json'
SOURCES={'scripts/pr16_dex_hof_successor.py','scripts/pr16_dex_hof_successor_source.py','overlays/hof_journal/hof_journal.c','overlays/hof_journal/hof_journal.h'}

def checkpoint():return json.loads((ROOT/CP).read_bytes())
def old_sections():
 return json.loads((ROOT/scheduler.SCHEDULER).read_bytes())['link']['sections'] if hasattr(scheduler,'SCHEDULER') else json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['sections']
def preserved_hof():return checkpoint()['isolated']['link']['sections']
def windows():
 ranges=scheduler.windows(1084);hof=preserved_hof();out=[]
 for lo,hi in ranges:
  spans=sorted((max(lo,x['address']),min(hi,x['address']+x['size']))for x in hof if x['address']<hi and lo<x['address']+x['size']);cursor=lo
  for a,z in spans:
   if cursor<a:out.append((cursor,a))
   cursor=max(cursor,z)
  if cursor<hi:out.append((cursor,hi))
 need(sum(b-a for a,b in out)==9252,'9560 current save owner minus128fixed entry and180HOF code')
 return out

def generated_source():
 import pr16_dex_hof_successor_source as source
 body=source.generated_source();codec=(ROOT/'overlays/hof_journal/hof_journal.c').read_text().replace('#include "hof_journal.h"','#include "'+str(ROOT/'overlays/hof_journal/hof_journal.h')+'"')
 for name in('HJ_Build','HJ_Validate','HJ_Rollback'):
  old='int '+name+'(';new='__attribute__((section(".text.DexImpl_Stage61State_'+name+'")))\n'+old;need(codec.count(old)==1,'one immutable codec definition '+name);codec=codec.replace(old,new)
 return body+'\n/* 明示ROM ABIとしてKEEP。既存mainへHJ32を発行する配線ではない。 */\n'+codec

def link(folder):
 # 元linkerの符号付きsource/非mutable/data/far veneer検査をそのまま使い、
 # 借用範囲だけ現所有窓へ固定する。旧1704byte最大値へ拡張させない。
 old=(scheduler.generated_source,scheduler.windows,scheduler.EXTRA_MAX)
 allowed=windows()
 try:
  scheduler.generated_source=generated_source
  scheduler.windows=lambda unused=0:allowed
  scheduler.EXTRA_MAX=0
  patches,linked=scheduler.link(folder)
 finally:scheduler.generated_source,scheduler.windows,scheduler.EXTRA_MAX=old
 linked.update(status='LINKED_CURRENT_SAVE_SUCCESSOR_AND_HJ_CODEC',total_owner_capacity=9560,preserved_hof_bytes=180,fixed_entry_bytes=128,available_body_bytes=9252,new_additional_rom_bytes=0,controller_rom_placed=False,controller_runtime_wired=False)
 for n in('HJ_Build','HJ_Validate','HJ_Rollback'):need(n in linked['symbols'],'explicit successor codec ABI '+n)
 return patches,linked

def reference_audit(before):
 # 現save-only bodyへ入る外部aligned word/Thumb BL形を全ROMで再列挙。
 # 退役body内の旧callは除外し、既署名のtyped data3件だけ再利用する。
 spans=windows();exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];origins=spans+[(a,a+16)for a in exports.values()]
 def inside(n,rows):return any(a<=n<z for a,z in rows)
 prior=json.loads((ROOT/'content/modernization/pr16_dex_save_body_references.json').read_bytes());known={int(r['scan_window']['address'],16):r for r in prior['references']};hits=[]
 def accept(address,target,kind):
  if inside(address,origins):return
  row=known.get(address);at=address-0x08000000;b=before[at:at+4]
  accepted=bool(row and int(row['apparent_target']['address'],16)==target and identity(b)==dict(size=4,sha256=row['scan_window']['sha256']))
  hits.append(dict(address=address,target=target,scan_kind=kind,**identity(b),classification=row['finding']if accepted else 'UNCLASSIFIED',accepted=accepted))
 for i,(value,)in enumerate(struct.iter_unpack('<I',before)):
  if 0x09448000<=(value&~1)<0x09FC22EC and inside(value&~1,spans):accept(0x08000000+4*i,value&~1,'ALIGNED_U32')
 for i in range(0,len(before)-3,2):
  hi,lo=struct.unpack_from('<HH',before,i)
  if hi&0xF800==0xF000 and lo&0xF800==0xF800:
   off=((hi&0x7FF)<<12)|((lo&0x7FF)<<1)
   if off&(1<<22):off-=1<<23
   target=0x08000000+i+4+off
   if inside(target,spans):accept(0x08000000+i,target,'THUMB_BL_SHAPE')
 return dict(candidate=identity(before),scope='whole ROM aligned u32 and Thumb BL shape into replaced save-only body',hits=hits,unclassified=sum(not x['accepted']for x in hits),indirect_reference_completeness_claimed=False,raw_rom_included=False)

def apply(before,patches,linked):
 import pr16_dex_placement as placement
 cp=checkpoint();need(identity(before)==cp['candidate'],'exact current88be fullROM parent');allocation=copy.deepcopy(cp['isolated']['placement']['allocation']);need(len(allocation['allocations'])==115,'current115owners')
 allowed=windows();exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];allowed.extend((a,a+16)for a in exports.values())
 after=bytearray(before);touched=[]
 for address,data in patches:
  need(data and any(a<=address and address+len(data)<=z for a,z in allowed),'one current save-only subowner perpatch')
  a=address-0x08000000;z=a+len(data);need(all(z<=x or y<=a for x,y in touched),'nonoverlapping successor patches');after[a:z]=data;touched.append((a,z))
 cursor=0
 for a,z in sorted(touched):need(after[cursor:a]==before[cursor:a],'every undeclaredROM byte unchanged');cursor=z
 need(after[cursor:]==before[cursor:],'whole trailingROM retained');audit=[];modified=[]
 expected={'display_npc_event_audit_stage61_payload','pr16_dex_runtime_reserved','pr16_dex_scheduler_bridge'}
 for r in allocation['allocations']:
  a,z=r['start'],r['end_exclusive'];pre=identity(before[a:z]);post=identity(after[a:z]);need(pre['sha256']==r['content_sha256'],'all115 actual current owner hashes')
  if pre!=post:
   need(r['name']in expected,'only declared existing save owner successors');r['content_sha256']=post['sha256'];modified.append(r['name'])
  audit.append(dict(name=r['name'],address=a+0x08000000,size=z-a,before_sha256=pre['sha256'],after_sha256=post['sha256'],unchanged=pre==post))
 for row in preserved_hof():
  a=row['address']-0x08000000;need(before[a:a+row['size']]==after[a:a+row['size']],'all5 existing HOF sections retained')
 updated=placement.rebuild_allocation(allocation);need(len(updated['allocations'])==115 and updated['summaries']['overlap_count']==0,'115 exact owner boundaries overlap0')
 reverse=bytearray(after)
 for a,z in touched:reverse[a:z]=before[a:z]
 need(bytes(reverse)==before,'wholeROM rollback exact')
 return bytes(after),dict(allocation=updated,owner_byte_audit=audit,modified_owners=modified,unchanged_owners=115-len(modified),preserved_hof_sections=preserved_hof(),whole_rom_rollback_exact=True,patches=[dict(address=a+0x08000000,**identity(after[a:z]))for a,z in sorted(touched)],formal_rom_changed=False,formal_save_changed=False,controller_runtime_wired=False)
