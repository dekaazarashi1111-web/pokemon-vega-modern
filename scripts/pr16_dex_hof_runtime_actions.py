#!/usr/bin/env python3
"""既存save後継配置と新Ccontroller ARM命令の変更scopeだけを検証。"""
import ctypes,json,os,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_storage_actions as prior
import pr16_dex_hof_successor as successor
import pr16_dex_publication as publication
need,identity,write=prior.need,prior.identity,prior.write
BASE='70fa9bb3888c1aa5e08f93d857e86479152c2cc6'
WF='.github/workflows/pr16-dex-hof-runtime.yml';SELF='scripts/pr16_dex_hof_runtime_actions.py';GUIDE='docs/PR16_DEX_HOF_CONTROLLER_JA.md'
CODE={WF,SELF,GUIDE,'scripts/pr16_dex_hof_successor.py','scripts/pr16_dex_hof_successor_source.py','content/modernization/pr16_dex_hof_successor_host.json','tools/mgba_pr16_dex_hof_successor.h','tools/mgba_pr16_dex_hof_controller.c','tools/pr16_hof_controller_arm_probe.c'}
OUT=ROOT/'.local/pr16-dex-hof-runtime';PUBLIC=ROOT/'public-dex-hof-runtime';ARTIFACT='pr16-dex-hof-runtime-text-only'
ARM_ARCHIVE=(11329089434,37274287686,2723,'0376b3a9f896a101913fd866bcc46df50ef37f56e2f8268fde1a5aa846763e8e')
def guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/prior.STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all bound originals unchanged')

def command(argv):
 r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict changed compile/link '+r.stderr[-2000:]);return r.stdout

def controller_link():
 import pr16_dex_scheduler as s
 folder=OUT/'controller';folder.mkdir();objects=[]
 for name,path in(('journal','overlays/hof_journal/hof_journal.c'),('controller','overlays/hof_journal/hof_transaction.c'),('probe','tools/pr16_hof_controller_arm_probe.c')):
  obj=folder/(name+'.o');command(['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-c',str(ROOT/path),'-o',str(obj)]);objects.append(str(obj))
 ld=folder/'controller.ld';ld.write_text('SECTIONS { . = 0x02002000; .text : { KEEP(*(.text*)) KEEP(*(.rodata*)) *(.v4_bx) *(.glue_7*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
 elf=folder/'controller.elf';command(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,HT_Commit','-Wl,-T,'+str(ld),*objects,'-lgcc','-o',str(elf)]);need(not command(['arm-none-eabi-nm','-u',str(elf)]),'controller private RAM link resolves')
 symbols={}
 for line in command(['arm-none-eabi-nm','-n','-S','--defined-only',str(elf)]).splitlines():
  p=line.split()
  if len(p)==4:need(p[2]not in'BbCcDdGgSs','no mutable RAM probe code');symbols[p[3]]=int(p[0],16)
 sections=[x for x in s.elf_sections(elf.read_bytes())if x['flags']&2 and x['size']];need(len(sections)==1 and sections[0]['name']=='.text'and sections[0]['address']==0x02002000 and sections[0]['size']<=0x6000,'one exact isolated RAM code lease')
 sec=sections[0];binary=folder/'controller.bin';binary.write_bytes(elf.read_bytes()[sec['offset']:sec['offset']+sec['size']]);header=folder/'entries.h';header.write_text(''.join('#define '+n+' '+hex(symbols[n])+'u\n'for n in('HT_Resolve','HT_Recover','HT_Commit','HT_Normal','HPC_Init','HPC_ReadResult')))
 return binary,header,dict(bytes=sec['size'],base=sec['address'],exports={n:symbols[n]for n in('HT_Resolve','HT_Recover','HT_Commit','HT_Normal','HPC_Init','HPC_ReadResult')},rom_placed=False,isolated_ram_only=True)

def native_cases():
 import pr16_dex_hof_storage as m
 from test_pr16_dex_hof_storage import fixture,payload,append,shifted
 from test_pr16_dex_hof_controller import Controller,U8
 folder=OUT/'cases';folder.mkdir();so=OUT/'controller-host.so';command(['cc','-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(ROOT/'overlays/hof_journal/hof_transaction.c'),str(ROOT/'overlays/hof_journal/hof_journal.c'),str(ROOT/'tools/pr16_hof_controller_host.c'),'-o',str(so)]);lib=ctypes.CDLL(str(so))
 base=fixture();new=shifted(payload());pending={}
 def capture(route):
  f=m.Flash(base)
  def event(f,kind,sector,offset):
   hit=(route=='fixed-old'and f.phase=='journal'and kind=='verified')or(route=='scratch'and f.phase=='hof'and kind=='after_erase'and sector==28)or(route=='inverse'and f.phase=='hof'and kind=='verified'and sector==29)
   if hit:pending[route]=bytes(f.data);raise m.PowerCut()
  f.observe=event
  try:m.commit(f,new,m.SHIFT)
  except m.PowerCut:pass
  need(route in pending,'one generated pending fixture')
 for route in('fixed-old','scratch','inverse'):capture(route)
 f=m.Flash(base);m.commit(f,new,m.SHIFT);committed=bytes(f.data);bad=bytearray(committed);main=m.select(bad);bad[(main.base+main.by_id[4])*4096+0xEC0+100]^=1
 cases=[('resolve-legacy',0,base,new,m.SHIFT,0),('commit-shift',2,base,new,m.SHIFT,0),('normal-token',3,committed,new,m.SHIFT,0),('resolve-fixed-old',0,pending['fixed-old'],new,m.SHIFT,0),('resolve-inverse',0,pending['inverse'],new,m.SHIFT,0),('resolve-scratch',0,pending['scratch'],new,m.SHIFT,0),('recover-inverse',1,pending['inverse'],new,m.SHIFT,0),('normal-pending-scratch',3,pending['scratch'],new,m.SHIFT,0),('initial-commit',2,fixture(absent=True),append(bytes(m.HOF_SIZE)),m.INITIAL,1),('bad-selected-journal',0,bytes(bad),new,m.SHIFT,0)]
 evidence=[];(folder/'count.txt').write_text(str(len(cases))+'\n')
 for i,(name,method,data,next,kind,absence)in enumerate(cases):
  c=Controller(lib,data);rc=c.run(method,next,kind,0,bool(absence));need((rc!=0)==(name=='bad-selected-journal'),'expected new native fixture outcome');prefix=folder/f'case{i:02}';Path(str(prefix)+'.meta').write_text(f'{method} {kind} 0 {absence} {rc}\n')
  for suffix,raw in(('.input.srm',data),('.next.bin',next),('.expected.srm',c.data()),('.expected.hof',c.payload()),('.expected.result',struct.pack('<9I',*c.info()[:9]))):Path(str(prefix)+suffix).write_bytes(raw)
  evidence.append(dict(case=i,name=name,method=method,kind=kind,expected_return=rc,host_oracle_full_flash_identity=identity(c.data())))
 return folder,evidence

def run():
 import pr16_story_live_probe as t
 import pr16_dex_hof_main_cow_actions as parent
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'fresh new successor/probe run');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  host=json.loads((ROOT/'content/modernization/pr16_dex_hof_successor_host.json').read_bytes());need(prior.bindings(host['source_bindings'])==host['source_bindings']and host['results']['differential_cases']==183,'reuse exact new183host differential');write(PUBLIC/'successor-host.json',host)
  publication.consumer(t.api('actions/artifacts/'+str(ARM_ARCHIVE[0])),'pr16-dex-hof-controller-text-only',ARM_ARCHIVE[1]);z,_=t.archive(ARM_ARCHIVE)
  with z:
   arm=json.loads(z.read('measurement.json'));need(arm['source_head']==BASE and arm['arm']['total_allocated_bytes']==6528 and prior.bindings(arm['source_bindings'])==arm['source_bindings'],'exact12host6528ARM original reused');write(PUBLIC/'controller-footprint.json',arm)
  patches,linked=successor.link(OUT/'successor-link');write(PUBLIC/'successor-link.json',linked)
  binary,entries,ram_link=controller_link();write(PUBLIC/'controller-link.json',ram_link)
  parent.OUT=OUT/'parent';parent.OUT.mkdir();_,_,before,_,old_place=parent.reconstruct();need(identity(before)==successor.checkpoint()['candidate'],'private exact88be parent')
  refs=successor.reference_audit(before);write(PUBLIC/'reference-audit.json',refs);need(refs['unclassified']==0,'all apparent external body references classified')
  after,placed=successor.apply(before,patches,linked);candidate=OUT/'candidate.gba';candidate.write_bytes(after);write(PUBLIC/'build.json',dict(candidate=identity(after),parent_candidate=identity(before),link=linked,placement=placed))
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed accepted mGBA runtime identity')
  # 実ROMで再配置されたsave全8entryが変更影響。旧ゲームプレイの再実行ではない。
  exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];header=OUT/'save-entries.h';header.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in exports.items())+'#define HJ_VALIDATE_ENTRY '+hex(linked['symbols']['HJ_Validate']['address'])+'u\n')
  source=(ROOT/'tools/mgba_pr16_dex_scheduler.c').read_text();need(source.count('int main(int argc,char **argv)')==1 and source.count('mCoreConfigDeinit(&c->config);c->deinit(c);return 0;')==1,'unique old caller harness boundaries');source=source.replace('int main(int argc,char **argv)','int accepted_scheduler_main_not_called(int argc,char **argv)').replace('mCoreConfigDeinit(&c->config);c->deinit(c);return 0;','return 0;')+'\n'+(ROOT/'tools/mgba_pr16_dex_hof_successor.h').read_text();src=OUT/'successor-native.c';src.write_text(source);exe=OUT/'successor-native';command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(header)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/hof_journal/hof_journal.c'),'-lmgba','-lm','-o',str(exe)])
  attempts.append('changed-save-owner-and-ROM-HJ-validator');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(exe),str(candidate)],capture_output=True,text=True,timeout=600);(PUBLIC/'successor-native.txt').write_text(r.stdout or 'no stdout\n');
  if r.stderr:(PUBLIC/'successor-native-stderr.txt').write_text(r.stderr)
  need(r.returncode==0 and not r.stderr,'changed ROM save native rc='+str(r.returncode)+' '+r.stderr[-1800:]);native_save=json.loads(r.stdout.splitlines()[-1]);need(native_save['status']=='PASS_CHANGED_ARM_SAVE_SUCCESSOR_AND_ROM_JOURNAL_VALIDATOR','exact changed native receipt')
  cases,case_evidence=native_cases();write(PUBLIC/'controller-cases.json',case_evidence);exe=OUT/'controller-native';command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),'-DHOF_CONTROLLER_ENTRIES="'+str(entries)+'"',str(ROOT/'tools/mgba_pr16_dex_hof_controller.c'),'-lmgba','-lm','-o',str(exe)])
  attempts.append('isolated-C-controller-ARM-ten-cases');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(exe),str(candidate),str(binary),str(cases)],capture_output=True,text=True,timeout=900);(PUBLIC/'controller-native.txt').write_text(r.stdout or 'no stdout\n');
  if r.stderr:(PUBLIC/'controller-native-stderr.txt').write_text(r.stderr)
  need(r.returncode==0 and not r.stderr,'new controller ARM rc='+str(r.returncode)+' '+r.stderr[-1800:]);native_controller=json.loads(r.stdout.splitlines()[-1]);need(candidate.read_bytes()==after,'private candidate and all files retain expected ROM')
  write(PUBLIC/'measurement.json',dict(status='PASS_SAVE_OWNER_SUCCESSOR_CODEC_PLACEMENT_AND_ISOLATED_ARM_CONTROLLER',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(after),parent_candidate=identity(before),link=linked,placement=placed,reference_audit=refs,host_controller_cases=12,host_successor_differential_cases=183,successor_native=native_save,controller_native=native_controller,controller_ram_link=ram_link,native_processes=len(attempts),unaffected_native_reruns=0,controller_rom_placed=False,journal_codec_rom_placed=True,runtime_generation_binding=False,runtime_cross_store_atomicity=False,initial_migration_wired=False,all_species_accepted=False,formal_rom_changed=False,formal_save_changed=False,source_bindings=prior.bindings(CODE)))
 except Exception as e:
  diagnostic=OUT/'successor-link/link-diagnostic.json'
  if diagnostic.exists():(PUBLIC/'link-diagnostic.json').write_bytes(diagnostic.read_bytes())
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def export():
 publication.output(PUBLIC)
 allowed={'measurement.json','failure.json','successor-host.json','controller-footprint.json','successor-link.json','controller-link.json','reference-audit.json','build.json','attempts.json','successor-native.txt','successor-native-stderr.txt','controller-cases.json','controller-native.txt','controller-native-stderr.txt','link-diagnostic.json'}
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in allowed and not p.name.startswith('.'),'explicit regular text only');raw=p.read_bytes();need(0<len(raw)<1000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed changed runtime workflow');globals()[sys.argv[1]]()
