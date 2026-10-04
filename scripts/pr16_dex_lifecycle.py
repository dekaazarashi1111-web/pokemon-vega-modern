#!/usr/bin/env python3
"""候補限定load/newgame接続。元schedulerと全未変更ownerを保持する。"""
from __future__ import annotations
import copy,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_scheduler as scheduler
placement=scheduler.placement;need,identity=scheduler.need,scheduler.identity
CP='content/modernization/pr16_dex_scheduler_checkpoint.json'
CHAIN='content/modernization/pr16_dex_loadchain_audit.json'
STATUS='content/modernization/pr16_dex_load_status_audit.json'
BASE=scheduler.EXTRA_BASE+1084
END=scheduler.EXTRA_BASE+scheduler.EXTRA_MAX
NAME='pr16_dex_load_newgame_boundary'
SOURCES=['overlays/dex_owner/dex_lifecycle.c','overlays/dex_owner/dex_newgame_tail.S']
PATCHES=(('post_qol_patch_literal','VegaDexPostQolLoad',0x09377695),('newgame_continuation_literal','VegaDexNewGameTail',0x0805432D))
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def abi_header():
 return ''.join('#define DEX_ENTRY_'+n+' '+hex(placement.BASE+i*placement.STRIDE+1)+'\n'for i,n in enumerate(placement.EXPORTS))
def signed_windows():return json.loads((ROOT/CHAIN).read_bytes())['windows']
def validate_windows(rom):
 for w in signed_windows()+json.loads((ROOT/STATUS).read_bytes())['windows']:
  at=int(w['address'],16)-0x08000000
  # 保存coreは前工程で置換済み。それ以外のload/newgame窓を固定する。
  if w['id'].startswith('stage61_'):continue
  need(identity(rom[at:at+w['size']])==dict(size=w['size'],sha256=w['sha256']),'signed lifecycle window '+w['id'])
def link(folder):
 need(not folder.exists(),'fresh lifecycle link');folder.mkdir(parents=True)
 header=folder/'entries.h';header.write_text(abi_header())
 def run(args):
  p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
  need(p.returncode==0 and not p.stderr,'strict lifecycle compiler: '+p.stderr[-2000:]);return p.stdout
 objects=[]
 for path in SOURCES:
  obj=folder/(Path(path).stem+'.o')
  flags=placement.FLAGS if path.endswith('.c')else ['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork']
  run(['arm-none-eabi-gcc',*flags,'-DDEX_LIFECYCLE_ENTRIES="'+str(header)+'"','-c',str(ROOT/path),'-o',str(obj)]);objects.append(obj)
 ld=folder/'lifecycle.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) *(.rodata*) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'lifecycle.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,--gc-sections','-Wl,-e,VegaDexPostQolLoad','-Wl,-T,'+str(ld),*map(str,objects),'-lgcc','-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all lifecycle symbols resolved')
 sections=[s for s in scheduler.elf_sections(elf.read_bytes())if s['flags']&2 and s['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'single immutable owner')
 symbols=placement.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]))
 for n in ('VegaDexPostQolLoad','VegaDexNewGameTail'):need(symbols[n]['kind']=='T'and symbols[n]['size']>0,'real lifecycle symbol '+n)
 raw=elf.read_bytes();s=sections[0];payload=raw[s['offset']:s['offset']+s['size']]
 need(BASE+len(payload)<=END and len(payload)%4==0,'fits remaining audited allocatable span')
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports={n:symbols[n]['address']|1 for _,n,_ in PATCHES},compile_units=2,arm_links=1,new_mutable_owners=0)
def apply(before,payload,linked):
 cp=checkpoint();need(identity(before)==cp['candidate'],'exact accepted scheduler candidate')
 need(cp['link']['extra_lease_size']==1084 and cp['allocation']['summaries']['allocation_count']==108,'exact parent allocation')
 validate_windows(before)
 need(BASE+len(payload)<=END and len(payload)>0 and len(payload)%4==0,'bounded lifecycle payload')
 lo=BASE-0x08000000;hi=lo+len(payload)
 need(before[lo:END-0x08000000]==b'\xff'*(END-BASE),'untouched suffix of previously audited full gap')
 after=bytearray(before);after[lo:hi]=payload;windows=[(lo,hi)]
 audit={w['id']:w for w in signed_windows()}
 for ident,symbol,old in PATCHES:
  w=audit[ident];at=int(w['address'],16)-0x08000000
  need(w['size']==4 and struct.unpack_from('<I',before,at)[0]==old,'signed literal target '+ident)
  new=linked['exports'][symbol];need(BASE<=new-1<BASE+len(payload)and new&1,'owned Thumb entry')
  struct.pack_into('<I',after,at,new);windows.append((at,at+4))
 cursor=0
 for a,b in sorted(windows):need(before[cursor:a]==after[cursor:a],'no undeclared ROM change');cursor=b
 need(before[cursor:]==after[cursor:],'remaining ROM unchanged')
 out=copy.deepcopy(cp['allocation']);changed=[]
 for row in out['allocations']:
  a,b=row['start'],row['end_exclusive']
  if before[a:b]!=after[a:b]:
   need(row['name']=='mirage_production_stage38_payload','only explicit allocated literal owner')
   need(identity(before[a:b])['sha256']==row['content_sha256'],'changed owner preimage')
   row['content_sha256']=identity(after[a:b])['sha256'];changed.append(row['name'])
 need(changed==['mirage_production_stage38_payload'],'exact allocated literal owner hash change')
 cfru=next(r for r in out['regions']if r['name']=='cfru_payload')
 need(cfru['kind']=='reserved'and cfru['start']<=0x01097178<0x0109717c<=cfru['end_exclusive'],'signed newgame literal belongs to reserved CFRU region')
 out['allocations'].append(dict(name=NAME,region='integration_modules',size=len(payload),alignment=4,owner='USER-20261004-DEX-LIFECYCLE',purpose='Post-QOL fail-closed MDX load and post-wipe newgame tail boundary',content_sha256=identity(payload)['sha256'],start=lo,placement='EXPLICIT'))
 report=placement.rebuild_allocation(out)
 need(len(report['allocations'])==109 and report['allocations'][:-1]==out['allocations'][:-1]and report['summaries']['overlap_count']==0,'108 existing owner ranges and order retained, zero overlap')
 return bytes(after),dict(allocation=report,modified_literal_owners=changed,patches=[dict(address=0x08000000+a,size=b-a,sha256=identity(after[a:b])['sha256'])for a,b in sorted(windows)],unchanged_save_scheduler=True,unchanged_codec=True,formal_rom_changed=False,formal_save_changed=False)
