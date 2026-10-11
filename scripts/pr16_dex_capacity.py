#!/usr/bin/env python3
"""新compact codecのARMv4T footprintのみ測定。ROM/Save/nativeは操作しない。"""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_compact as compact
BASE='2d53c0adb0a0c3f9b8b1e252692e55c19245ded1'
CODE={compact.TABLE,compact.ADAPTER,compact.META,'overlays/dex_owner/dex_compact_map.c','overlays/dex_owner/dex_compact_map.h','scripts/pr16_dex_compact.py','tests/test_pr16_dex_compact.py','scripts/pr16_dex_capacity.py','.github/workflows/pr16-dex-capacity.yml','docs/PR16_DEX_COMPACT_CAPACITY_JA.md'}
OUT=ROOT/'.local/pr16-dex-capacity';PUBLIC=ROOT/'public-dex-capacity'
SOURCES=['overlays/dex_owner/'+x for x in('dex_owner.c','dex_compact_adapter.c','dex_compact_map.c','dex_save_bridge.c')]
FLAGS=['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-std=c11','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-fdata-sections','-ffunction-sections','-fno-common']
def need(v,m):
 if not v:raise ValueError(m)
def identity(b):return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def guard():
 import pr16_story_live_probe as transport
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','one authorized branch attempt')
 pr=transport.api('pulls/16');need(pr['state']=='open'and pr['draft']and not pr['merged']and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
 need(set(git('diff','--name-only',BASE,'HEAD').decode().splitlines())==CODE,'exact new compact source scope')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'old jobs closed')
 for path,expected in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==expected,'accepted source unchanged '+path)
 for path,data in compact.build().items():need((ROOT/path).read_bytes()==data,'generated compact bytes '+path)

def measure():
 need(not OUT.exists()and not PUBLIC.exists(),'fresh measure directories');OUT.mkdir(parents=True);PUBLIC.mkdir()
 test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_compact.py','-v'],cwd=ROOT,capture_output=True)
 need(test.returncode==0 and not test.stdout and test.stderr.count(b' ... ok\n')==51 and b'\nOK\n'in test.stderr,'51 compact C tests including262144 exact inputs')
 (PUBLIC/'host-tests.txt').write_bytes(test.stderr)
 tools={};objects=[];compile_count=0
 for name in ('gcc','ld','nm','objcopy'):
  name='arm-none-eabi-'+name;version=subprocess.check_output([name,'--version'],text=True).splitlines()[0];tools[name]=dict(version=version)
 def run(argv):
  p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);need(p.returncode==0 and not p.stderr,'strict ARM command failed '+Path(argv[0]).name+': '+p.stderr[-3000:]);return p.stdout
 for source in SOURCES:
  obj=OUT/(Path(source).stem+'.o');run(['arm-none-eabi-gcc',*FLAGS,'-c',str(ROOT/source),'-o',str(obj)]);objects.append(obj);compile_count+=1
 # footprint VMAだけ。実ROM owner/leaseへの書込みを許可するmapではない。
 linker=OUT/'footprint.ld';linker.write_text('SECTIONS { . = 0x08000000; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7) *(.glue_7t) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=OUT/'footprint.elf';run(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-nostdlib','-Wl,--build-id=none','-Wl,--gc-sections','-Wl,-e,VegaDexValidate','-Wl,-T,'+str(linker),*map(str,objects),'-lgcc','-o',str(elf)])
 need(not run(['arm-none-eabi-nm','-u',str(elf)]),'no undefined ARM symbols')
 symbols=[]
 for line in run(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]).splitlines():
  fields=line.split()
  if len(fields)==4:
   address,size,kind,name=fields;need(kind not in'BbCcDdGgSs','no new mutable linker owners');symbols.append(dict(name=name,offset=int(address,16)-0x08000000,size=int(size,16),kind=kind))
 binary=OUT/'footprint.bin';run(['arm-none-eabi-objcopy','-j','.text','-O','binary',str(elf),str(binary)])
 size=binary.stat().st_size;data=json.loads(compact.build()[compact.META]);need(size>data['compact_logical_bytes']and size<16384,'bounded complete codec footprint')
 report=dict(schema_version=1,status='PASS_COMPACT_C_AND_ARM_FOOTPRINT_ROM_UNWIRED',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),host_tests=51,c_mapping_comparisons=262144,host_compiles=1,arm_translation_units=compile_count,arm_links=1,toolchain=tools,compile_flags=FLAGS,footprint=identity(binary.read_bytes()),symbols=symbols,compact_mapping=data,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE|set(SOURCES)|{'overlays/dex_owner/dex_owner.h','overlays/dex_owner/dex_adapter.h','overlays/dex_owner/dex_save_bridge.h'})},native_processes=0,rom_changed=False,save_changed=False,runtime_wired=False,lease_accepted=False,formal_save=101,public_binary_included=False)
 write(PUBLIC/'measurement.json',report)
 print(json.dumps({k:report[k]for k in('status','host_tests','arm_translation_units','arm_links','footprint','native_processes','rom_changed')},ensure_ascii=False))

def export():
 # 公開対象を新規text2本だけに固定。ARM object/ELF/binやROMは絶対に含めない。
 if not PUBLIC.exists():return
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'measurement.json','host-tests.txt'},'strict text-only publication')
  raw=p.read_bytes();need(0<len(raw)<100000 and b'\0'not in raw,'bounded UTF8 text');raw.decode('utf-8')
 if(PUBLIC/'measurement.json').exists():need(json.loads((PUBLIC/'measurement.json').read_bytes())['public_binary_included']is False,'explicit private binary exclusion')

if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('guard','measure','export'),'bounded action');globals()[sys.argv[1]]()
