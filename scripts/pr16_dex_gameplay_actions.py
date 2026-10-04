#!/usr/bin/env python3
"""候補限定の通常ゲームlifecycle。入力原本・正式進行を変更しない。"""
from __future__ import annotations
import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_gameplay as game
import pr16_dex_lifecycle_actions as accepted
life=game.lifecycle;s=life.scheduler;p=s.placement;need,identity,write=accepted.need,accepted.identity,accepted.write
BASE='60fdfd27d08db121387becfd615a594d7a75729b'
MEASURE=(11313494497,37230810454,17359,'1c8c7a615a613c2887f2054d66d0c9f6a1ba2546fb9ae12e22abc8174c067944')
CODE={'scripts/pr16_dex_gameplay.py','scripts/pr16_dex_gameplay_actions.py',game.HEADER,'tests/test_pr16_dex_gameplay.py','.github/workflows/pr16-dex-gameplay.yml'}
REUSE_SOURCE='0ff7227157be8622ffee965fa5027cefa67b0b93'
REUSE=(11314120736,37231227293,33381,'1909a59da8ea84adaf05c7a48ff309e75dd5c02df9a62c6a7b64fb301caaf65c')
OUT=ROOT/'.local/pr16-dex-gameplay';PUBLIC=ROOT/'public-dex-gameplay'
def guard():
 import pr16_story_live_probe as transport
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized one current branch')
 pr=transport.api('pulls/16');need(pr['state']=='open'and pr['draft']and not pr['merged']and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
 changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only bounded ordinary lifecycle files')
 state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'previous records terminal')
 for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'accepted dependency unchanged '+path)
def reconstruct():
 import pr16_story_live_probe as transport
 z,_=transport.archive(MEASURE)
 with z:report=json.loads(z.read('build.json'))
 need(report['source_head']==BASE and report['run_id']==MEASURE[1]and report['native']['cases']==52 and report['candidate']==game.CANDIDATE,'exact successful isolated parent')
 for path,b in report['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'isolated lifecycle source retained')
 run=transport.api('actions/runs/'+str(MEASURE[1]));need(run['head_sha']==BASE and run['status']=='completed'and run['conclusion']=='success','parent terminal success')
 z,_=transport.archive(transport.SAVE24)
 with z:formal=z.read('candidate.gba')
 need(identity(formal)==p.lease.CANDIDATE,'formal original exact')
 codec,linked=p.link(OUT/'codec');placed,old=p.place(formal,codec,linked['symbols'])
 patches,scheduler=s.link(OUT/'scheduler');parent=s.apply(placed,patches,scheduler['extra_lease_size']);need(identity(parent)==life.checkpoint()['candidate'],'scheduler exact reconstruction')
 payload,linked=life.link(OUT/'lifecycle');candidate,allocation=life.apply(parent,payload,linked);need(identity(candidate)==game.CANDIDATE and allocation==report['placement'],'unchanged accepted boundary candidate')
 path=OUT/'candidate.gba';path.write_bytes(candidate);path.chmod(0o444)
 return path

def reuse_save101(seed,expected):
 import pr16_story_live_probe as transport
 run=transport.api('actions/runs/'+str(REUSE[1]));need(run['head_sha']==REUSE_SOURCE and run['status']=='completed'and run['conclusion']=='failure','exact earlier diagnostic retained')
 z,_=transport.archive(REUSE)
 with z:
  failure=json.loads(z.read('failure.json'));need(failure['attempts']==['save101-save','save101-cold','newgame-save']and failure['message']=='Save preserves all stock_flags_vars_sha256','earlier Save101 pair completed before NewGame diagnosis')
  saved=z.read('save101-candidate-only.srm');need(game.physical(saved,102)['mdx']==expected,'retained candidate Save102 full MDX')
  processes=[]
  for cold in (False,True):
   case='save101-'+('cold'if cold else 'save');folder=PUBLIC/case;folder.mkdir()
   for member in z.namelist():
    if member.startswith(case+'/'):
     name=member.split('/')[1];need('/'.join((case,name))==member and (name in{'stdout.txt','stderr.txt','commands.txt','screen-0000.ppm','screen-0001.ppm'}),'exact reused member');(folder/name).write_bytes(z.read(member))
   need(not(folder/'stderr.txt').read_bytes(),'old clean native process')
   initial=saved if cold else seed
   parsed=game.validate_trace((folder/'stdout.txt').read_bytes(),folder,'continue-story',initial,expected,101+int(cold),dict(map=[3,24],xy=[53,13],party_count=4),not cold)
   processes.append(dict(case=case,input=identity(initial),output=identity(saved),trace=parsed,returncode=0,reused=True,source=REUSE_SOURCE,run=REUSE[1]))
  for key in ('map','xy','live_xy','facing','party_count','party_sha256','save_counter','flash_sha256'):need(processes[0]['trace']['observations'][-1][key]==processes[1]['trace']['observations'][0][key],'reused cold retains '+key)
  for key in ('live_sha256','legacy_sha256','bag_sha256','stock_flags_vars_sha256'):need(processes[0]['trace']['mdx'][-1][key]==processes[1]['trace']['mdx'][0][key],'reused cold owner '+key)
 (PUBLIC/'save101-candidate-only.srm').write_bytes(saved)
 return dict(status='PASS_ORDINARY_SAVE_AND_INDEPENDENT_CONTINUE',fresh_processes=2,ordinary_saves=1,counter_before=101,counter_after=102,processes=processes,formal_save_changed=False,reused=True,source=REUSE_SOURCE,run=REUSE[1],artifact=REUSE[0])

def run():
 import pr16_story_live_probe as transport
 need(not OUT.exists()and not PUBLIC.exists(),'new candidate-only lifecycle attempt');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  tested=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_gameplay.py','-v'],cwd=ROOT,capture_output=True)
  need(tested.returncode==0 and not tested.stdout and tested.stderr.count(b' ... ok\n')==6,'six new observer/validator tests');(PUBLIC/'host-tests.txt').write_bytes(tested.stderr)
  candidate=reconstruct()
  package=subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip();need(package=='0.10.2+dfsg-1.1build3','fixed mGBA package')
  need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA binary')
  source=OUT/'gameplay.c';source.write_bytes(game.generate());exe=OUT/'gameplay'
  cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),str(source),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
  compiled=subprocess.run(cmd,capture_output=True,text=True);need(compiled.returncode==0 and not compiled.stdout and not compiled.stderr,'strict key-only compile: '+compiled.stderr[-2000:])
  z,_=transport.archive(transport.SAVE101)
  with z:seed=z.read('story-fast.srm')
  need(identity(seed)==transport.SEED,'exact Save101 original');old=game.physical(seed,101);need(old['mdx']==bytes(522),'Save101 legacy blank MDX')
  result={'save101':reuse_save101(seed,game.record(old['legacy']))}
  for name,initial,counter,location,expected in [('newgame',b'\xff'*131072,0,dict(map=[4,0],xy=[10,2],party_count=0),game.record())]:
   process=[];saved=None
   for cold in (False,True):
    case=name+('-cold'if cold else '-save');folder=OUT/case;folder.mkdir();input_bytes=saved if cold else initial;save=folder/'story.srm';save.write_bytes(input_bytes)
    mode='continue-story'if cold or name=='save101'else 'new-game-story';commands='quit\n'if cold else 'save\nobserve 1\nquit\n';argv=[str(exe),str(candidate),str(save),mode]
    if mode=='continue-story':argv.append(identity(input_bytes)['sha256'])
    attempts.append(case);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts,accepted=False))
    native=subprocess.run(argv,cwd=folder,input=commands,capture_output=True,text=True,timeout=180)
    (folder/'stdout.txt').write_text(native.stdout);(folder/'stderr.txt').write_text(native.stderr);(folder/'commands.txt').write_text(commands)
    # 診断もraw ROM/save/runnerを含まない専用text/screensへ限定する。
    public=PUBLIC/case;public.mkdir()
    for f in folder.iterdir():
     if f.suffix in('.txt','.ppm'):shutil.copyfile(f,public/f.name)
    need(native.returncode==0 and not native.stderr,'ordinary '+case+' rc='+str(native.returncode)+' '+native.stderr[-1200:])
    if not cold:(PUBLIC/(name+'-candidate-only.srm')).write_bytes(save.read_bytes())
    parsed=game.validate_trace(native.stdout.encode(),folder,mode,input_bytes,expected,counter+int(cold),location,not cold)
    final=save.read_bytes();physical=game.physical(final,counter+1);need(physical['mdx']==expected,'physical complete MDX equals expected canonical migration/init')
    if cold:
     need(final==input_bytes,'all Flash and RTC bytes unchanged during independent Continue')
     a,b=process[0]['trace']['observations'][-1],parsed['observations'][0]
     for key in ('map','xy','live_xy','facing','party_count','party_sha256','save_counter','flash_sha256'):need(a[key]==b[key],'cold retains '+key)
     a,b=process[0]['trace']['mdx'][-1],parsed['mdx'][0]
     for key in ('live_sha256','legacy_sha256','bag_sha256','stock_flags_vars_sha256'):need(a[key]==b[key],'cold retains '+key)
    else:saved=final;need(saved!=initial,'normal Save persisted new generation')
    process.append(dict(case=case,input=identity(input_bytes),output=identity(final),trace=parsed,returncode=0))
   (PUBLIC/(name+'-candidate-only.srm')).write_bytes(saved)
   result[name]=dict(status='PASS_ORDINARY_SAVE_AND_INDEPENDENT_CONTINUE',fresh_processes=2,ordinary_saves=1,counter_before=counter,counter_after=counter+1,processes=process,formal_save_changed=False)
  need(identity(seed)==transport.SEED and identity(candidate.read_bytes())==game.CANDIDATE,'original input and candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_CANDIDATE_ORDINARY_DEX_SAVE_CONTINUE_NEWGAME',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=game.CANDIDATE,parent_run=MEASURE[1],cases=result,native_processes=2,reused_native_processes=2,accepted_native_processes=4,reused_save101=dict(source=REUSE_SOURCE,run=REUSE[1],artifact=REUSE[0]),host_compiles=1,host_tests=6,ordinary_saves=2,newgame_introductions=1,new_high_owner_gameplay_registration=False,formal_rom_changed=False,formal_save_changed=False,formal_save=101,all_consumers_wired=False,all_save_modes_accepted=False,source_bindings={path:identity((ROOT/path).read_bytes())for path in sorted(CODE)}))
 except Exception as e:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=len(attempts),attempts=attempts,formal_rom_changed=False,formal_save_changed=False));raise

def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public evidence directory')
 for f in PUBLIC.rglob('*'):
  rel=f.relative_to(PUBLIC);need(not f.is_symlink()and all(not x.startswith('.')for x in rel.parts),'no hidden or symlink')
  if f.is_dir():need(len(rel.parts)==1 and f.name in {'save101-save','save101-cold','newgame-save','newgame-cold'},'explicit session directories');continue
  raw=f.read_bytes()
  if f.suffix=='.srm':need(len(rel.parts)==1 and f.name in {'save101-candidate-only.srm','newgame-candidate-only.srm'}and len(raw)in(131072,131088),'only authorized new candidate saves')
  elif f.suffix=='.ppm':need(len(rel.parts)==2 and f.name in {'screen-0000.ppm','screen-0001.ppm'}and len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'bounded actual screen')
  else:
   need(f.suffix in {'.json','.txt'}and f.name in {'host-tests.txt','attempts.json','measurement.json','failure.json','stdout.txt','stderr.txt','commands.txt'},'explicit text filename')
   need(len(raw)<200000 and b'\0'not in raw and (not raw or raw.endswith(b'\n')),'bounded complete text');raw.decode('utf-8')
   if f.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'bounded action');globals()[sys.argv[1]]()
