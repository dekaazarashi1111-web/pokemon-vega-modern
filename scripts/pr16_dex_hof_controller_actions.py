#!/usr/bin/env python3
"""C controllerの新ARM footprintを先に測る。ROM接続/保存受入ではない。"""
import io,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_storage_actions as prior
import pr16_dex_publication as publication
need,identity,write=prior.need,prior.identity,prior.write
BASE='4e203067304b604824ef706f221a14302ae01371'
WF='.github/workflows/pr16-dex-hof-controller.yml';SELF='scripts/pr16_dex_hof_controller_actions.py'
CODE={WF,SELF,'overlays/hof_journal/hof_transaction.c','overlays/hof_journal/hof_transaction.h','tools/pr16_hof_controller_host.c','tests/test_pr16_dex_hof_controller.py'}
OUT=ROOT/'.local/pr16-dex-hof-controller';PUBLIC=ROOT/'public-dex-hof-controller';ARTIFACT='pr16-dex-hof-controller-text-only'
def guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/prior.STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all bound originals and terminal prior work retained')
def run():
 import test_pr16_dex_hof_controller as t
 import pr16_dex_scheduler as scheduler
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh controller run');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(t));(PUBLIC/'host-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful(),'new C controller host suite');write(PUBLIC/'host-metrics.json',t.METRICS)
  def run_cmd(args):
   r=subprocess.run(args,capture_output=True,text=True,cwd=ROOT);need(r.returncode==0 and not r.stderr,'strict ARM compile/link '+r.stderr[-2000:]);return r.stdout
  objects=[]
  for name in('hof_journal','hof_transaction'):
   obj=OUT/(name+'.o');run_cmd(['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'overlays/hof_journal'/(name+'.c')),'-o',str(obj)]);objects.append(str(obj))
  ld=OUT/'controller.ld';ld.write_text('SECTIONS { . = 0x09448000; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
  elf=OUT/'controller.elf';run_cmd(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,HT_Commit','-Wl,-T,'+str(ld),*objects,'-lgcc','-o',str(elf)]);need(not run_cmd(['arm-none-eabi-nm','-u',str(elf)]),'all ARM dependencies resolved')
  symbols=[]
  for line in run_cmd(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]).splitlines():
   p=line.split()
   if len(p)==4:
    address,size,kind,name=p;need(kind not in 'BbCcDdGgSs','no static mutable ARM owner');symbols.append(dict(name=name,address=int(address,16),size=int(size,16),kind=kind))
  sections=[{k:x[k]for k in('name','address','size','alignment')}for x in scheduler.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']];stack=[]
  for path in OUT.glob('*.su'):
   for line in path.read_text().splitlines():
    p=line.split('\t');stack.append(dict(function=p[0].split(':')[-1],bytes=int(p[1]),type=p[2]))
  measure=dict(status='PASS_C_CONTROLLER_HOST_AND_ARM_FOOTPRINT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),host_tests=result.testsRun,host_metrics=t.METRICS,arm=dict(compile_units=2,links=1,sections=sections,symbols=symbols,stack=stack,total_allocated_bytes=sum(x['size']for x in sections)),source_bindings=prior.bindings(CODE),runtime_generation_binding=False,runtime_cross_store_atomicity=False,rom_placed=False,native_processes=0,formal_rom_changed=False,formal_save_changed=False,candidate_changed=False,unaffected_native_reruns=0)
  write(PUBLIC/'measurement.json',measure)
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.')));raise

def export():
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'measurement.json','failure.json','host-tests.txt','host-metrics.json'},'explicit nonsymlink regular public text only');raw=p.read_bytes();need(0<len(raw)<100000 and raw.endswith(b'\n')and b'\0'not in raw,'nonempty complete text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed controller measurement');globals()[sys.argv[1]]()
