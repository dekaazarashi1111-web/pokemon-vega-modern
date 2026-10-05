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
 allowed=windows();source=generated_source()
 try:
  scheduler.generated_source=lambda:source
  scheduler.windows=lambda unused=0:allowed
  scheduler.EXTRA_MAX=0
  patches,linked=scheduler.link(folder)
 finally:scheduler.generated_source,scheduler.windows,scheduler.EXTRA_MAX=old
 linked.update(status='LINKED_CURRENT_SAVE_SUCCESSOR_AND_HJ_CODEC',total_owner_capacity=9560,preserved_hof_bytes=180,fixed_entry_bytes=128,available_body_bytes=9252,new_additional_rom_bytes=0,controller_rom_placed=False,controller_runtime_wired=False)
 for n in('HJ_Build','HJ_Validate','HJ_Rollback'):need(n in linked['symbols'],'explicit successor codec ABI '+n)
 return patches,linked

def typed_reference_bindings(before,allow_formal=False):
 def number(v):return int(v,16)if isinstance(v,str)else v
 def bound(row):
  address=number(row['address'])if 'address'in row else number(row['offset'])+0x08000000
  raw=before[address-0x08000000:address-0x08000000+row['size']]
  need(identity(raw)==dict(size=row['size'],sha256=row['sha256']),'whole typed external reference window')
  return raw
 def u32(a):return struct.unpack_from('<I',before,number(a)-0x08000000)[0]
 def roots(items):
  for row in items:
   bound(row['row'])
   for a in row.get('root_sites',[]):need(u32(a)==number(row['root']),'unchanged active typed table root')
   need(u32(row['asset_pointer_site'])==number(row['asset_pointer']),'unchanged typed asset pointer')
 prior=json.loads((ROOT/'content/modernization/pr16_dex_save_body_references.json').read_bytes());known={}
 for row in prior['references']:
  bound(row['scan_window'])
  if 'typed_roots'in row:roots(row['typed_roots'])
  if 'audio'in row:bound(row['audio']['header']);bound(row['audio']['decoder_read_extent'])
  if 'compression'in row:bound(row['compression']['compressed_stream'])
  if 'tileset'in row:
   tiles=row['tileset'];bound(tiles['header'])
   for layout in tiles['layout_roots']:
    bound(layout['header']);need(u32(layout['secondary_tileset_pointer_site'])==number(tiles['header']['address']),'rooted tileset header')
  known[number(row['scan_window']['address'])]=dict(target=number(row['apparent_target']['address']),binding=row['scan_window'],classification=row['finding'])
 # 現bridgeは既にcodeなので、過去の空きpreimageを再要求せず、typed assetのみ再検証。
 extra=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_extra_lease.json').read_bytes())['reference_audit'];raw=bound(extra['asset']);decoded=bytearray();cursor=4
 need(raw[0]==0x10 and int.from_bytes(raw[1:4],'little')==32,'typed palette LZ10 exact32byte')
 for unused in range(4):
  need(raw[cursor]==0,'palette consists only of literal groups');cursor+=1;decoded.extend(raw[cursor:cursor+8]);cursor+=8
 need(cursor==len(raw)==40 and identity(decoded)==dict(size=32,sha256=extra['asset']['decoded_sha256']),'whole palette decoded identity')
 for row in extra['table_rows']:bound(row);need(u32(row['address'])==extra['asset']['address'],'all typed palette rows')
 for a in extra['root_sites']:need(u32(a)==extra['current_palette_root'],'live palette consumer roots')
 ap=extra['apparent_reference'];bound(ap);known[ap['address']]=dict(target=ap['target'],binding=ap,classification='FALSE_POSITIVE_LZ10_PALETTE_LITERAL')
 # codec donorの既知aligned候補。音声全体と全固定pointer siteを保持する。
 lease=json.loads((ROOT/'content/modernization/pr16_dex_capacity_lease.json').read_bytes());row=lease['range_candidates'][33]
 need(row['type']=='M4A_DELTA_COMPRESSED_SAMPLE'and row['alignment']==0,'one exact typed codec range hit');bound(row);bound(row['encoded_range_binding'])
 for offset in row['wave_pointer_sites']:need(u32(offset+0x08000000)==row['wave_header_offset']+0x08000000,'all old codec typed wave pointers')
 known[row['offset']+0x08000000]=dict(target=row['value']&~1,binding=row,classification='FALSE_POSITIVE_DPCM_CRY_SAMPLE_CODEC')
 # 新規Thumb BL形のtyped音声証明は別の固定text bindingから読み込む。
 new=json.loads((ROOT/'content/modernization/pr16_dex_hof_successor_references.json').read_bytes())
 need(identity(before)==new['formal_candidate'if allow_formal else 'target_candidate'],'new typed proof exact declared candidate')
 for path,binding in new['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'unchanged typed proof source '+path)
 for root in new['roots']:
  bound(root);bound(root['header']);need(root['kind']=='dpcm4'and root['address']+root['size']==root['decoder_read_end_exclusive'],'exact signed DPCM extent')
  for table in root['typed_tables']:
   for site in table['table_root_sites']:bound(site);need(u32(site['address'])==table['table_address'],'active DPCM table root')
   for item in table['rows']:bound(item['row']);need(u32(item['wave_pointer_site'])==root['address'],'active DPCM table row')
  for site in root['reference_windows']:bound(site);need(u32(site['address'])==root['address'],'all signed DPCM references')
 for row in new['candidates']:
  bound(row);root=next(x for x in new['roots']if x['address']==row['root'])
  need(root['address']+16<=row['address']and row['address']+4<=root['decoder_read_end_exclusive'],'hit wholly within encoded DPCM data')
  known[row['address']]=dict(target=row['target'],binding=row,classification=row['classification'])
 return known

def reference_audit(before):
 # 現save-only bodyへ入る外部aligned word/Thumb BL形を全ROMで再列挙。
 # 退役body内の旧callは除外し、既署名のtyped data3件だけ再利用する。
 spans=windows();exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];origins=spans+[(a,a+16)for a in exports.values()]
 def inside(n,rows):return any(a<=n<z for a,z in rows)
 known=typed_reference_bindings(before);hits=[]
 def accept(address,target,kind):
  if inside(address,origins):return
  row=known.get(address);at=address-0x08000000;b=before[at:at+4]
  accepted=bool(row and row['target']==target and identity(b)==dict(size=4,sha256=row['binding']['sha256']))
  hits.append(dict(address=address,target=target,scan_kind=kind,**identity(b),classification=row['classification']if accepted else 'UNCLASSIFIED',accepted=accepted))
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
 actual_owners={r['name']:r for r in cp['isolated']['placement']['owner_byte_audit']};need(len(actual_owners)==115 and set(actual_owners)=={r['name']for r in allocation['allocations']},'complete latest measured115owner audit')
 after=bytearray(before);touched=[]
 for address,data in patches:
  need(data and any(a<=address and address+len(data)<=z for a,z in allowed),'one current save-only subowner perpatch')
  a=address-0x08000000;z=a+len(data);need(all(z<=x or y<=a for x,y in touched),'nonoverlapping successor patches');after[a:z]=data;touched.append((a,z))
 cursor=0
 for a,z in sorted(touched):need(after[cursor:a]==before[cursor:a],'every undeclaredROM byte unchanged');cursor=z
 need(after[cursor:]==before[cursor:],'whole trailingROM retained');audit=[];modified=[];inherited_hash_differences=[]
 expected={'display_npc_event_audit_stage61_payload','pr16_dex_runtime_reserved','pr16_dex_scheduler_bridge'}
 for r in allocation['allocations']:
  a,z=r['start'],r['end_exclusive'];pre=identity(before[a:z]);post=identity(after[a:z]);need(pre['sha256']==actual_owners[r['name']]['after_sha256'],'all115 latest measured current owner hashes')
  if pre['sha256']!=r['content_sha256']:inherited_hash_differences.append(r['name'])
  if pre!=post:
   need(r['name']in expected and r['content_sha256']==pre['sha256'],'only exact current save owner successors');r['content_sha256']=post['sha256'];modified.append(r['name'])
  audit.append(dict(name=r['name'],address=a+0x08000000,size=z-a,before_sha256=pre['sha256'],after_sha256=post['sha256'],unchanged=pre==post))
 for row in preserved_hof():
  a=row['address']-0x08000000;need(before[a:a+row['size']]==after[a:a+row['size']],'all5 existing HOF sections retained')
 updated=placement.rebuild_allocation(allocation);need(len(updated['allocations'])==115 and updated['summaries']['overlap_count']==0,'115 exact owner boundaries overlap0')
 reverse=bytearray(after)
 for a,z in touched:reverse[a:z]=before[a:z]
 need(bytes(reverse)==before,'wholeROM rollback exact')
 return bytes(after),dict(allocation=updated,owner_byte_audit=audit,inherited_allocator_hash_differences=inherited_hash_differences,modified_owners=modified,unchanged_owners=115-len(modified),preserved_hof_sections=preserved_hof(),whole_rom_rollback_exact=True,patches=[dict(address=a+0x08000000,**identity(after[a:z]))for a,z in sorted(touched)],formal_rom_changed=False,formal_save_changed=False,controller_runtime_wired=False)
