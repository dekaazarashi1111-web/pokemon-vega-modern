#!/usr/bin/env python3
"""現schedulerの実section間へmode3専用処理を配置。元ARMの再linkはしない。"""
from __future__ import annotations
import copy,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_fallback_qol as previous
need,identity=previous.need,previous.identity
SOURCE='overlays/dex_owner/dex_hof_main_cow.S'
BINDINGS='content/modernization/pr16_dex_hof_main_cow_bindings.json'
CP='content/modernization/pr16_dex_fallback_checkpoint.json'
SCHED='content/modernization/pr16_dex_scheduler_checkpoint.json'
OWNER='display_npc_event_audit_stage61_payload'
LAYOUT={'.text.hof_cow_entry':(0x09448FE8,38),'.text.hof_cow_return':(0x09449388,22),'.text.hof_cow_second':(0x0944A680,32),'.text.hof_cow_prepare':(0x0944A9F4,50),'.text.hof_cow_first':(0x0944AA70,48)}
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def free_spans():
 import pr16_dex_scheduler as scheduler
 cp=json.loads((ROOT/SCHED).read_bytes());out=[]
 for lo,hi in scheduler.windows(cp['link']['extra_lease_size']):
  spans=sorted((max(lo,x['address']),min(hi,x['address']+x['size']))for x in cp['link']['sections']if x['address']<hi and lo<x['address']+x['size']);cursor=lo
  for a,z in spans:
   if cursor<a:out.append((cursor,a))
   cursor=max(cursor,z)
  if cursor<hi:out.append((cursor,hi))
 need(sum(z-a for a,z in out)==cp['link']['free_bytes']==366,'exact current scheduler free subspans')
 return out
def signed(before):
 need(identity(before)==checkpoint()['candidate'],'exact accepted d773a123 parent')
 p=proof()
 for path,b in p['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'bound current source '+path)
 for row in p['windows']+p['subowner_preimages']:
  at=row['address']-0x08000000;need(identity(before[at:at+row['size']])=={k:row[k]for k in('size','sha256')},'whole signed mode3 boundary '+row['id'])
 gaps=free_spans()
 for name,(address,size)in LAYOUT.items():
  need(any(a<=address and address+size<=z for a,z in gaps),'one actual free reservation '+name)
  need(any(x['section']==name and x['address']==address and x['size']==size for x in p['subowner_preimages']),'exact separately signed reservation '+name)
 return p
def link(folder):
 import pr16_dex_placement as p,pr16_dex_scheduler as s
 need(not folder.exists(),'fresh new mode3 link');folder.mkdir(parents=True)
 def run(args):
  r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict new mode3 compiler '+r.stderr[-1800:]);return r.stdout
 obj=folder/'hof-cow.o';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-c',str(ROOT/SOURCE),'-o',str(obj)])
 ld=folder/'hof-cow.ld';ld.write_text('SECTIONS {\n'+''.join(' . = '+hex(address)+'; '+name+' : { KEEP(*('+name+')) }\n'for name,(address,_)in LAYOUT.items())+' .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n}\n')
 elf=folder/'hof-cow.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,VegaDexHofMainCow','-Wl,-T,'+str(ld),str(obj),'-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all mode3 imports resolved');symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));raw=elf.read_bytes();sections=[x for x in s.elf_sections(raw)if x['flags']&2 and x['size']]
 need(len(sections)==len(LAYOUT)and {x['name']for x in sections}==set(LAYOUT),'five immutable declared sections only')
 patches=[]
 for row in sections:
  address,maximum=LAYOUT[row['name']];need(row['address']==address and 0<row['size']<=maximum and row['size']%4==0,'current reserved section fits '+row['name']+' size='+str(row['size']))
  patches.append((address,raw[row['offset']:row['offset']+row['size']]))
 need(symbols['VegaDexHofMainCow']['address']==LAYOUT['.text.hof_cow_entry'][0],'even dispatch address')
 return patches,dict(sections=[{k:x[k]for k in('name','address','size')}for x in sections],symbols=symbols,entry=symbols['VegaDexHofMainCow']['address'],payload_bytes=sum(len(b)for _,b in patches),compile_units=1,arm_links=1,new_mutable_owners=0,existing_scheduler_relinks=0)
def apply(before,patches,linked):
 import pr16_dex_placement as placement
 signed(before);p=proof();need(linked['entry']==LAYOUT['.text.hof_cow_entry'][0],'one exact mode3 destination');cp=checkpoint();allocation=copy.deepcopy(cp['current_build']['placement']['allocation']);owners=allocation['allocations'];need(len(owners)==115,'current115 owners')
 old_sections=json.loads((ROOT/SCHED).read_bytes())['link']['sections'];occupied=[]
 for address,data in patches:
  need(any(a==address and len(data)<=size for a,size in LAYOUT.values()),'compiled section in one declared current gap')
  need(all(address+len(data)<=s['address']or s['address']+s['size']<=address for s in old_sections),'all accepted scheduler sections retained')
  need(all(address+len(data)<=a or z<=address for a,z in occupied),'new subowners nonoverlapping');occupied.append((address,address+len(data)))
 patches=[*patches,(0x080DB264,struct.pack('<I',linked['entry']))];after=bytearray(before);windows=[]
 for address,data in patches:
  at=address-0x08000000;after[at:at+len(data)]=data;windows.append((at,at+len(data)))
 cursor=0
 for a,z in sorted(windows):need(before[cursor:a]==after[cursor:a],'every undeclared ROM byte retained');cursor=z
 need(before[cursor:]==after[cursor:],'whole trailing ROM unchanged');changed=[];audit=[]
 for r in owners:
  a,z=r['start'],r['end_exclusive'];pre=identity(before[a:z]);post=identity(after[a:z]);same=pre==post
  if not same:
   need(r['name']==OWNER and r['content_sha256']==pre['sha256'],'only exact current Stage61 owner modified');r['content_sha256']=post['sha256'];changed.append(r['name'])
  audit.append(dict(name=r['name'],address=a+0x08000000,size=z-a,before_sha256=pre['sha256'],after_sha256=post['sha256'],unchanged=same))
 need(changed==[OWNER],'one changed existing owner');rebuilt=placement.rebuild_allocation(allocation);need(len(rebuilt['allocations'])==115 and rebuilt['summaries']['overlap_count']==0,'115owners overlap0 no new allocation')
 reverse=bytearray(after)
 for a,z in windows:reverse[a:z]=before[a:z]
 need(bytes(reverse)==before,'whole ROM inverse exact')
 need(before[0xDB258:0xDB264]==after[0xDB258:0xDB264]and before[0xDB268:0xDB34C]==after[0xDB268:0xDB34C],'all other dispatch rows and stock bodies retained')
 return bytes(after),dict(allocation=rebuilt,owner_byte_audit=audit,unchanged_owners=114,modified_owners=changed,new_subowners=linked['sections'],new_subowner_bytes=linked['payload_bytes'],prior_scheduler_sections=len(old_sections),prior_scheduler_sections_all_unchanged=True,whole_rom_rollback_exact=True,patches=[dict(address=a+0x08000000,**identity(after[a:z]))for a,z in sorted(windows)],new_rom_tail_bytes=0,formal_rom_changed=False,formal_save_changed=False)
