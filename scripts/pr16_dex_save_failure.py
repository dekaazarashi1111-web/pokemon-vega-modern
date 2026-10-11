#!/usr/bin/env python3
"""invalid MDXのTrySavingData誤成功とSaveFailed破壊的retryを遮断。"""
from __future__ import annotations
import copy,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_battle_consumers as b
need,identity=b.need,b.identity
CP='content/modernization/pr16_dex_battle_checkpoint.json'
BINDINGS='content/modernization/pr16_dex_save_failure_bindings.json'
SOURCE='overlays/dex_owner/dex_save_failure.S'
BASE=b.BASE+160;END=b.END
EXPORTS=('VegaDexSaveResultGate','VegaDexSafeWipeGate')
def checkpoint():return json.loads((ROOT/CP).read_bytes())
def proof():return json.loads((ROOT/BINDINGS).read_bytes())
def link(folder):
 need(not folder.exists(),'fresh failure boundary link');folder.mkdir(parents=True)
 header=folder/'entries.h';header.write_text(b.lifecycle.abi_header())
 def run(args):
  r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'failure gate compiler: '+r.stderr[-1500:]);return r.stdout
 obj=folder/'gate.o';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-DDEX_SAVE_FAILURE_ENTRIES="'+str(header)+'"','-c',str(ROOT/SOURCE),'-o',str(obj)])
 ld=folder/'failure.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) *(.rodata*) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'failure.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,VegaDexSaveResultGate','-Wl,-T,'+str(ld),str(obj),'-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'no undefined gate symbols')
 symbols=b.p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[s for s in b.lifecycle.scheduler.elf_sections(elf.read_bytes())if s['flags']&2 and s['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable new gate owner');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need(0<len(payload)<=END-BASE and len(payload)%4==0,'gate payload fits audited residual272bytes')
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,exports={n:symbols[n]['address']|1 for n in EXPORTS},compile_units=1,arm_links=1,new_mutable_owners=0)
def apply(before,payload,linked):
 cp=checkpoint();need(identity(before)==cp['candidate'],'exact accepted battle candidate')
 lo=BASE-0x08000000;need(before[lo:END-0x08000000]==b'\xff'*(END-BASE),'entire unallocated residual blank');need(0<len(payload)<=END-BASE and len(payload)%4==0,'bounded gate payload')
 after=bytearray(before);after[lo:lo+len(payload)]=payload;windows=[(lo,lo+len(payload))]
 for w in proof()['windows']:
  a=w['address'];at=a-0x08000000;need(identity(before[at:at+w['size']])==dict(size=w['size'],sha256=w['sha256']),'signed failure boundary '+w['id'])
  if w['id']not in('try_save_result_gate','save_failed_wipe'):continue
  entry=linked['exports'][EXPORTS[0 if w['id']=='try_save_result_gate'else 1]];patch=b.tail_patch(a,entry);after[at:at+8]=patch;windows.append((at,at+8))
 cursor=0
 for a,z in sorted(windows):need(before[cursor:a]==after[cursor:a],'all non-patch ROM retained');cursor=z
 need(before[cursor:]==after[cursor:],'whole ROM suffix retained')
 allocation=copy.deepcopy(cp['measurement']['placement']['allocation']);b.preserve_allocated_owners(before,after,allocation)
 allocation['allocations'].append(dict(name='pr16_dex_save_failure_gates',region='integration_modules',size=len(payload),alignment=4,owner='USER-20261004-DEX-SAVE-FAILURE',purpose='Fail-closed save result and invalid-MDX non-destructive SaveFailed guard',content_sha256=identity(payload)['sha256'],start=lo,placement='EXPLICIT'))
 result=b.p.rebuild_allocation(allocation);need(len(result['allocations'])==111 and result['allocations'][:-1]==allocation['allocations'][:-1]and result['summaries']['overlap_count']==0,'all110 old allocated owners retained')
 reverse=bytearray(after)
 for a,z in windows:reverse[a:z]=before[a:z]
 need(bytes(reverse)==before,'whole ROM inverse exact')
 return bytes(after),dict(allocation=result,patches=[dict(address=a+0x08000000,size=z-a,sha256=identity(after[a:z])['sha256'])for a,z in sorted(windows)],all110_old_owners_byte_identical=True,whole_rom_rollback_exact=True,save_scheduler_unchanged=True,formal_rom_changed=False,formal_save_changed=False)
