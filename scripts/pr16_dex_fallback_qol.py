#!/usr/bin/env python3
"""fallback255のQOL台帳だけ。元候補・実owner・全未変更byteを固定する。"""
from __future__ import annotations
import copy,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_failure as previous
need,identity=previous.need,previous.identity
SOURCE='overlays/dex_owner/dex_fallback_qol.c'
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
 obj=folder/'fallback.o';run(['arm-none-eabi-gcc',*p.FLAGS,'-DDEX_FALLBACK_ENTRIES="'+str(header)+'"','-c',str(ROOT/SOURCE),'-o',str(obj)])
 ld=folder/'fallback.ld';ld.write_text('SECTIONS { . = '+hex(BASE)+'; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'fallback.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,-e,VegaDexFallbackQolLoad','-Wl,-T,'+str(ld),str(obj),'-lgcc','-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'all fallback imports resolved');symbols=p.parse_symbols(run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]));sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']]
 need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==BASE,'one immutable fallback section');sec=sections[0];raw=elf.read_bytes();payload=raw[sec['offset']:sec['offset']+sec['size']]
 need(0<len(payload)<=LIMIT-BASE and len(payload)%4==0,'fits real remaining span before high-mask cluster')
 return payload,dict(base=BASE,payload=identity(payload),symbols=symbols,entry=symbols['VegaDexFallbackQolLoad']['address']|1,sections=[{k:x[k]for k in('name','address','size')}for x in sections],compile_units=1,arm_links=1,new_mutable_owners=0)
