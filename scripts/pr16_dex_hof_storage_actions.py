#!/usr/bin/env python3
"""新32sector scheduler/codecと未測定実HOF ABIだけを検証・記録。"""
import datetime,io,json,os,subprocess,sys,unittest
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as previous
import pr16_dex_publication as publication
need,identity,write,git=previous.need,previous.identity,previous.write,previous.git
BASE='9231aafd576ca9ec3cba7db1c56f72ca727a5192'
WF='.github/workflows/pr16-dex-hof-storage.yml';GUIDE='docs/PR16_DEX_HOF_STORAGE_JA.md'
BIND='content/modernization/pr16_dex_hof_abi_bindings.json';HEADER='tools/mgba_pr16_dex_hof_abi.h'
CODE={WF,GUIDE,BIND,HEADER,'scripts/pr16_dex_hof_storage.py','scripts/pr16_dex_hof_storage_actions.py','tests/test_pr16_dex_hof_storage.py','overlays/hof_journal/hof_journal.c','overlays/hof_journal/hof_journal.h'}
STATE=previous.STATE;DOC=previous.DOC;LOGS=previous.LOGS
CP='content/modernization/pr16_dex_hof_storage_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_storage_evidence'
OUT=ROOT/'.local/pr16-dex-hof-storage';PUBLIC=ROOT/'public-dex-hof-storage';ARTIFACT='pr16-dex-hof-storage-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]
bindings=previous.bindings;current=previous.current

def source_guard():
 import pr16_learnset_runtime_record as g
 current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_storage_actions.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[] and bindings(state['source_bindings'])==state['source_bindings'],'all prior source bytes and terminal state retained');previous.capacity.audit()
 p=json.loads((ROOT/BIND).read_bytes());need(bindings(p['probe']['source_bindings'])==p['probe']['source_bindings'],'whole fixed ABI probe source')

def run():
 import test_pr16_dex_hof_storage as tests
 import pr16_dex_hof_main_cow_actions as parent
 current();need(not OUT.exists()and not PUBLIC.exists(),'fresh changed-scope observation');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));(PUBLIC/'host-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful()and result.testsRun==16,'16 new actual-geometry host suites')
  write(PUBLIC/'host-metrics.json',tests.METRICS)
  obj=OUT/'journal.o';r=subprocess.run(['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','-c',str(ROOT/'overlays/hof_journal/hof_journal.c'),'-o',str(obj)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'new portable journal ARM compile '+r.stderr[-1000:])
  unresolved=subprocess.check_output(['arm-none-eabi-nm','-u',str(obj)],text=True);need(not unresolved,'journal has no unresolved runtime dependencies')
  size=subprocess.check_output(['arm-none-eabi-size',str(obj)],text=True).splitlines()[-1].split();arm=dict(text=int(size[0]),data=int(size[1]),bss=int(size[2]),arm_compiles=1,rom_placed=False,new_runtime_owner=False);write(PUBLIC/'codec-arm.json',arm)
  parent.OUT=OUT/'parent';parent.OUT.mkdir();candidate,before,after,link,placement=parent.reconstruct();p=json.loads((ROOT/BIND).read_bytes());need(identity(after)==p['target_candidate'],'exact current88be private reconstruction')
  for x in p['windows']:
   at=x['address']-0x08000000;need(identity(after[at:at+x['size']])=={k:x[k]for k in('size','sha256')},'actual current ROM ABI unchanged '+x['id'])
  write(PUBLIC/'abi-windows.json',dict(candidate=identity(after),windows=p['windows'],formal_window_identity_same=True,current_rom_owners=len(placement['allocation']['allocations']),current_scheduler_subowners=43,current_scheduler_free_bytes=186))
  exports=json.loads((ROOT/'content/modernization/pr16_dex_scheduler_checkpoint.json').read_bytes())['link']['exports'];entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in exports.items()))
  source=(ROOT/'tools/mgba_pr16_dex_scheduler.c').read_text();need(source.count('int main(int argc,char **argv)')==1,'one unused old test entry');src=OUT/'abi.c';src.write_text(source.replace('int main(int argc,char **argv)','int accepted_scheduler_main_not_called(int argc,char **argv)')+'\n'+(ROOT/HEADER).read_text());exe=OUT/'abi'
  r=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)],capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict new native ABI compile '+r.stderr[-1800:])
  attempts.append('new-hof-existing-abi');write(PUBLIC/'attempts.json',dict(native_processes=1,cases=attempts));r=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300)
  if r.stdout:(PUBLIC/'abi-stdout.txt').write_text(r.stdout)
  if r.stderr:(PUBLIC/'abi-stderr.txt').write_text(r.stderr)
  need(r.returncode==0 and not r.stderr,'new ABI native rc='+str(r.returncode)+' '+r.stderr[-1800:]);native=json.loads(r.stdout);need(native['cases']==228 and native['status']=='PASS_ISOLATED_ARM_HOF_EXISTING_ABI','all228 new ABI conditions');need(candidate.read_bytes()==after,'private candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_32SECTOR_HOF_STORAGE_DESIGN_AND_NATIVE_ABI',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),host_tests=16,host_metrics=tests.METRICS,codec_arm=arm,native_abi=native,native_processes=1,unaffected_native_reruns=0,flash_bytes=131072,flash_sectors=32,hof_history_teams=50,hof_opaque_suffix_retained=1936,journal_bytes=256,journal_logical_sector=4,journal_offset=3776,scratch_logical_sectors=[8,9],final_commit_logical_sector=13,auxiliary_sectors_modified=[],candidate=identity(after),candidate_changed=False,formal_rom_changed=False,formal_save_changed=False,runtime_generation_binding=False,runtime_cross_store_atomicity=False,all_species_accepted=False,initial_migration_wired=False,source_bindings=bindings(CODE)))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts),attempts=attempts));raise

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and not(ROOT/CP).exists(),'prior originals retained and unique new checkpoint')
 measure=json.loads((PUBLIC/'measurement.json').read_bytes());need(measure['source_bindings']==bindings(CODE),'whole new source bindings');paths=set()
 for name in('measurement.json','host-tests.txt','host-metrics.json','codec-arm.json','abi-windows.json','abi-stdout.txt','attempts.json'):
  dest=EVIDENCE+'/'+name;need(not(ROOT/dest).exists(),'one immutable measured original');(ROOT/dest).parent.mkdir(parents=True,exist_ok=True);(ROOT/dest).write_bytes((PUBLIC/name).read_bytes());paths.add(dest)
 cp=dict(schema_version=1,**measure,guide=GUIDE,evidence_bindings=bindings(paths),runtime_integration_accepted=False,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA']);write(ROOT/CP,cp)
 summary='現32sector内のHOF保存設計を実装。非選択main2sectorを一時scratch、logical4に256byte逆差分journal、最後logical13commit。50履歴・opaque1936byte・sector30/31保持、追加容量/圧縮/有限log不要。16hostと新228隔離ARMで実HOF ABIを検証。C codecはARM object compile済みだがROM配置/全writer・load接続は未完。候補88be8811と正式ROM/Save101不変。'
 goal='現115owner/43subowner/186byteを保持して、新journal codec/schedulerのROM配置と既存save ownerへの接続を進める。全mode/normal/Link clone/readback/selector/HOF-only loadに未完journal解決を統合し、INITIALはhas-recordsとloaderの組合せを検証する。9bit HOF speciesの後継typed owner、共通SaveFailed/早期31/全cold owner/残typedconsumerも未完。検証後に正式候補切替とtrainer131後半、最終シオウ通常回復・保存・独立cold Continue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_storage']=dict(checkpoint=CP,guide=GUIDE,status=measure['status'],candidate=measure['candidate'],host_tests=16,native_abi_cases=228,journal_bytes=256,flash_sectors=32,history_teams=50,runtime_generation_binding=False,runtime_cross_store_atomicity=False,record_run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='INTEGRATE_32SECTOR_HOF_JOURNAL_WITH_SAVE_OWNERS',goal_ja=goal,read_paths=[GUIDE,CP,BIND,'docs/PR16_DEX_HOF_MAIN_COW_JA.md','docs/PR16_DEX_HOF_GENERATION_CONTRACT_JA.md'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='実32sector geometryのscheduler/Ccodecと固定ROMの新ABI隔離試験source。稼働ROM保存世代結合の受入ではない。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(CODE|paths|{CP}));state['do_not_repeat'].append('HOF32sector storageの16host/新228ABIを専用checkpointから再利用。候補88be8811不変。50履歴/1936byte suffixを削減せず非選択mainの一時scratchを使う。Ccodecとhost schedulerを実ROM接続済みにしない。species9bitとINITIAL移行は未修復。次は現ownerへの配置・全writer/load接続。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],host_tests=16,native_processes=1,new_native_cases=228,new_codec_arm_compiles=1,candidate_changed=False,runtime_generation_binding=False,runtime_cross_store_atomicity=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-STORAGE / 実32sector scratchとHOF逆差分journal\n- Version: dex-hof-storage-v1\n- Status: DONE（容量方式/Ccodec/host scheduler/実ROM ABIの限定検証。保存runtime接続は未完）\n- Summary: {summary}\n- Files changed: 新storage source/tests/Ccodec/ABI binding/Actions/guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: host16suite PASS; metrics={json.dumps(measure["host_metrics"],sort_keys=True)}; new ABI228case/native1; codec ARM={json.dumps(measure["codec_arm"],sort_keys=True)}。旧native再走0、候補再構築はprivateのみ。\n- Boundary: 128KiB/NOR model、完全source mainSHA、exact HOF token、rollback再起動・通常Save。現species9bit切捨ては観測のみ。main parserは既存全validatorの代用でなく、INITIAL flag/loader実接続・全writer/clone/load/cold/ROM配置は未完。\n- Owners: logical4 EC0へ256byte/残48zeroの新schema案、非選択logical8/9一時scratch、logical13最後。selectedmain全14sector、HOF opaque1936、sector30/31保持。現115owner/43subowner/186byteと正式ROM/Save101不変。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存artifactによるprivate再構築のみ。公開はsource・address-size-SHA/text、ROM断片/rawhex/ROM/save/runtime/runner/credential追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'all previously bound bytes retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')

def snapshot():
 receipt=dict(status='PASS_COMMITTED_32SECTOR_HOF_STORAGE_RECORD',source_head=os.environ['GITHUB_SHA'],final_head=git('rev-parse','HEAD').decode().strip(),record_run=int(os.environ['GITHUB_RUN_ID']),final_blobs={})
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed text')
 for name,p in SNAPSHOTS:
  raw=git('show','HEAD:'+p);need(raw==(ROOT/p).read_bytes()and raw.endswith(b'\n'),'complete text with newline');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][p]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=True)
 for p in LOGS:need(git('show','HEAD:'+p).startswith(git('show',BASE+':'+p)),'entire old log prefix preserved')
 write(PUBLIC/'record.json',receipt);print('RESULT=DONE TASK=USER-20261005-DEX-HOF-STORAGE VERIFY=PASS COMMIT='+receipt['final_head'])

def export():
 publication.output(PUBLIC)
 allowed={'measurement.json','failure.json','host-tests.txt','host-metrics.json','codec-arm.json','abi-windows.json','abi-stdout.txt','abi-stderr.txt','attempts.json','record.json',*(n for n,_ in SNAPSHOTS)}
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in allowed,'explicit regular text only');raw=p.read_bytes();need(0<len(raw)<3500000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded nonempty complete text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed changed-scope workflow');globals()[sys.argv[1]]()
