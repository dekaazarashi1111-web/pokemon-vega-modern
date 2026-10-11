#!/usr/bin/env python3
"""fallback255のQOL台帳だけ。元候補・実owner・全未変更byteを固定する。"""
from __future__ import annotations
import copy,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_failure as previous
need,identity=previous.need,previous.identity
SOURCE='overlays/dex_owner/dex_fallback_qol.S'
HOST_REFERENCE='overlays/dex_owner/dex_fallback_qol.c'
CP='content/modernization/pr16_dex_hof_checkpoint.json'
BASE=0x09FFFDC4
LIMIT=0x09FFFF00
BINDINGS='content/modernization/pr16_dex_fallback_qol_bindings.json'
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def entries():
 import pr16_dex_lifecycle as life
 p=json.loads((ROOT/'content/modernization/pr16_dex_lifecycle_checkpoint.json').read_bytes())
 return life.abi_header()+''.join('#define '+n+' '+hex(a)+'u\n'for n,a in dict(FALLBACK_PREVIOUS_LOAD=p['isolated']['link']['exports']['VegaDexPostQolLoad'],FALLBACK_SHIFTED_SAVE_VALIDATE=0x092D12E1).items())
def link(folder):
 import pr16_dex_placement as p,pr16_dex_scheduler as s
 need(not folder.exists(),'fresh fallback link');folder.mkdir(parents=True);header=folder/'entries.h';header.write_text(entries())
 def run(args):
  r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict fallback compiler '+r.stderr[-1800:]);return r.stdout
 obj=folder/'fallback.o';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-DDEX_FALLBACK_ENTRIES="'+str(header)+'"','-c',str(ROOT/SOURCE),'-o',str(obj)])
 ld=folder/'fallback.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'fallback.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,-e,VegaDexFallbackQolLoad','-Wl,-T,'+str(ld),str(obj),'-lgcc','-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all fallback imports resolved');symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable fallback section');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need(0<len(payload)<=LIMIT-BASE and len(payload)%4==0,'fits real remaining span before high-mask cluster: size='+str(len(payload)))
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,entry=symbols['VegaDexFallbackQolLoad']['address']|1,sections=[{k:x[k]for k in('name','address','size')}for x in sections],compile_units=1,arm_links=1,new_mutable_owners=0)
def apply(before,payload,linked):
 import pr16_dex_battle_consumers as b,pr16_dex_subowners as sub,pr16_dex_fallback_tail_lease as lease
 cp=checkpoint();need(identity(before)==cp['candidate'],'exact accepted HOF candidate')
 p=json.loads((ROOT/BINDINGS).read_bytes())
 for path,binding in p['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'exact validator ABI source '+path)
 for w in p['windows']:
  a=w['address']-0x08000000;need(identity(before[a:a+w['size']])=={k:w[k]for k in('size','sha256')},'whole signed fallback callable '+w['id'])
 need(linked['payload']['size']==len(payload)==296 and linked['entry']==BASE+1,'exact compact296byte current owner')
 lo=BASE-0x08000000;hi=lo+len(payload);at=0x01391114;old=p['previous_load']
 need(struct.unpack_from('<I',before,at)[0]==old,'previous post-QOL entry exact')
 allocation=copy.deepcopy(cp['isolated']['placement']['allocation']);owners=allocation['allocations'];need(len(owners)==114,'current114 owners')
 need(all(r['end_exclusive']<=lo or r['start']>=hi for r in owners),'no allocator overlap')
 need(all(r['address']+r['size']<=BASE or r['address']>=BASE+len(payload)for r in sub.occupied()),'all real codec/scheduler sections retained')
 audit=lease.validate(before,size=296);after=bytearray(before);after[lo:hi]=payload;struct.pack_into('<I',after,at,linked['entry']);windows=sorted([(lo,hi),(at,at+4)]);cursor=0
 for a,z in windows:need(before[cursor:a]==after[cursor:a],'every undeclared ROM byte retained');cursor=z
 need(before[cursor:]==after[cursor:],'whole trailing ROM unchanged');owner_audit=[];changed=[]
 for r in owners:
  a,z=r['start'],r['end_exclusive'];pre=identity(before[a:z]);post=identity(after[a:z]);same=pre==post
  if not same:
   need(r['name']=='mirage_production_stage38_payload'and a<=at<at+4<=z and r['content_sha256']==pre['sha256'],'one exact existing literal owner');r['content_sha256']=post['sha256'];changed.append(r['name'])
  owner_audit.append(dict(name=r['name'],address=a+0x08000000,size=z-a,before_sha256=pre['sha256'],after_sha256=post['sha256'],unchanged=same))
 need(changed==['mirage_production_stage38_payload'],'only four-byte post-QOL pointer changed')
 allocation['allocations'].append(dict(name='pr16_dex_fallback_qol',region='future_tail',start=lo,size=len(payload),alignment=4,placement='EXPLICIT',owner='USER-20261005-DEX-FALLBACK-QOL',purpose='Selected fallback255 idle durable QOL ledger restoration',content_sha256=identity(payload)['sha256']))
 rebuilt=b.p.rebuild_allocation(allocation);need(len(rebuilt['allocations'])==115 and rebuilt['summaries']['overlap_count']==0,'115owners overlap0')
 reverse=bytearray(after)
 for a,z in windows:reverse[a:z]=before[a:z]
 need(bytes(reverse)==before,'whole ROM inverse exact')
 return bytes(after),dict(allocation=rebuilt,tail_reference_audit=audit,owner_byte_audit=owner_audit,unchanged_owners=113,modified_owners=changed,whole_rom_rollback_exact=True,patches=[dict(address=a+0x08000000,size=z-a,sha256=identity(after[a:z])['sha256'])for a,z in windows],remaining_tail_start=BASE+296,remaining_tail_bytes=0x0A000000-BASE-296,formal_rom_changed=False,formal_save_changed=False)
