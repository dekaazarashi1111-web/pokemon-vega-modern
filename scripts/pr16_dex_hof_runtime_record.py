#!/usr/bin/env python3
"""終了済みHOF controller/save後継の原本だけを固定正本へ記録する。"""
import datetime,json,os,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_runtime_actions as w
import pr16_dex_hof_controller_actions as controller
import pr16_dex_hof_storage_actions as prior
import pr16_dex_publication as publication
import pr16_story_live_probe as t
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='e49dbc69f4ba91186edf828070537a7653fde7c7';SOURCE='e49dbc69f4ba91186edf828070537a7653fde7c7';RUN=37277602492;JOB=111658005810;ARCHIVE=(11331330296,37277602492,71029,'76d1773af8e82eeb4e81c251206948ede61f3212b5de770361aedc35aef4111f')
WF='.github/workflows/pr16-dex-hof-runtime-record.yml';SELF='scripts/pr16_dex_hof_runtime_record.py'
CODE={WF,SELF,w.WF,controller.WF}
OUT=ROOT/'.local/pr16-dex-hof-runtime-record';PUBLIC=ROOT/'public-dex-hof-runtime-record';ARTIFACT='pr16-dex-hof-runtime-record-text-only'
CP='content/modernization/pr16_dex_hof_controller_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_controller_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=prior.LOGS
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-guide.md',w.GUIDE),('fixed-run-log.md','design/run_log.md'),('fixed-version-log.md','design/version_log.md')]
def guard_source():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 for workflow in(w.WF,controller.WF):
  before=git('show',BASE+':'+workflow);after=(ROOT/workflow).read_bytes();trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+workflow+']\n').encode();need(before.count(trigger)==1 and after==before.replace(trigger,b'  workflow_dispatch:\n'),'successful workflows retire only push trigger')

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();need(not OUT.exists()and not PUBLIC.exists()and not(ROOT/CP).exists(),'one immutable controller record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and state['pending_runs']==[],'prior bound evidence and emptypending retained')
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB));need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==RUN and job['status']=='completed'and job['conclusion']=='success'and len(job['steps'])==9 and all(s['conclusion']=='success'for s in job['steps']),'completed runtime source/job allsteps success')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);z,_=t.archive(ARCHIVE);files={}
 with z:
  need(len(z.infolist())==len(set(z.namelist()))==11,'all eleven distinct original text files')
  for item in z.infolist():
   need(not item.is_dir()and item.external_attr>>28!=10 and Path(item.filename).name==item.filename,'flat non-symlink original text');raw=z.read(item);need(raw and raw.endswith(b'\n')and b'\0'not in raw,'whole complete text');raw.decode('utf8');files[item.filename]=raw
 measure=json.loads(files['measurement.json']);need(measure['source_head']==SOURCE and measure['run_id']==RUN and measure['status']=='PASS_SAVE_OWNER_SUCCESSOR_CODEC_PLACEMENT_AND_ISOLATED_ARM_CONTROLLER','exact isolated runtime result')
 need(measure['journal_codec_rom_placed']and not any(measure[k]for k in('controller_rom_placed','runtime_generation_binding','runtime_cross_store_atomicity','initial_migration_wired','all_species_accepted','formal_rom_changed','formal_save_changed')),'no unfinished acceptance promoted')
 for path,binding in measure['source_bindings'].items():
  if path==w.WF:need(identity(git('show',BASE+':'+path))==binding,'original completed workflow source')
  else:need(identity((ROOT/path).read_bytes())==binding,'every tested runtime source retained')
 paths=set()
 for name,raw in files.items():
  dest=ROOT/EVIDENCE/name;need(not dest.exists(),'new immutable evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);paths.add(dest.relative_to(ROOT).as_posix())
 cp=dict(schema_version=1,**measure,guide=w.GUIDE,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),verified_runtime_run=RUN,verified_runtime_job=JOB,all_runtime_steps_success=True,runtime_archive=ARCHIVE,evidence_bindings=prior.bindings(paths),prior_failed_runs=[37274005427,37275659829,37276165080,37277097069],controller_arm_run=37274287686,controller_arm_bytes=6528)
 write(ROOT/CP,cp)
 free=measure['link']['free_bytes'];count=len(measure['link']['sections'])+len(measure['placement']['preserved_hof_sections']);candidate=measure['candidate']['sha256']
 summary=f'32sector HOF制御をC/ARM化。12host・新ARM10caseで復旧/中断/INITIALを合成検証。既存save sourceを共通化し、現115owner内でHJ codec3関数を配置。全8保存入口22caseとROM journal validator257caseを変更影響検証。後継候補{candidate[:8]}、save subowner{count}／残{free}byte。HOF世代結合controllerの稼働ROM配線・正式ROM/Save101切替は未完。'
 goal='現save後継ownerを基準に、controller6528byteを下位の共通generation writerへ統合し容量を再確保する。Linkのc/source・c+1backup・rotation据置、初回no-main、全mode/LinkFull署名barrierを保持。workspace1320+4096+7936byteのsave中RAM/heap所有、INITIAL has-records/loader、全writer/clone/selector/HOF-only gateを証明して配線。species9bit・共通SaveFailed・早期31・全cold owner・残typedを閉じ、正式候補切替後trainer131後半、最終シオウ通常回復/保存/独立cold Continue。雑魚毎checkpointなし。'
 state['story_dex_owner']['runtime_integration']['hof_controller']=dict(checkpoint=CP,guide=w.GUIDE,status=measure['status'],candidate=measure['candidate'],parent_candidate=measure['parent_candidate'],controller_arm_bytes=6528,journal_codec_rom_placed=True,controller_rom_placed=False,current_save_subowners=count,current_save_owner_free_bytes=free,runtime_generation_binding=False,runtime_cross_store_atomicity=False,initial_migration_wired=False,all_species_accepted=False,source=SOURCE,run=RUN,job=JOB,all_runtime_steps_success=True,record_run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='INTEGRATE_HOF_CONTROLLER_WITH_CURRENT_SAVE_SUCCESSOR',goal_ja=goal,read_paths=[w.GUIDE,CP,'docs/PR16_DEX_HOF_STORAGE_JA.md','content/modernization/pr16_dex_hof_successor_host.json','content/modernization/pr16_dex_hof_successor_references.json'])
 state['observed_head']=SOURCE;state['observed_head_semantics']='save後継/ROM codec変更影響とRAM隔離C controllerの新ARM source。ゲーム/HOF世代結合の受入ではない。';state['pending_runs']=[]
 allnew=controller.CODE|w.CODE|CODE|{CP}|paths;state['source_bindings'].update(prior.bindings(allnew));state['do_not_repeat'].append('HOF controller12host/6528ARM/新10RAM隔離caseとsave後継183hostdiff・実保存8入口22case/ROMjournal257caseは新専用checkpointから再利用。候補'+candidate[:8]+'・115owner/53save subowner/残'+str(free)+'byteが次の基準。CcontrollerはROM未配置、workspace/全writer/load/INITIAL/Link統合未完。失敗runは失敗として保持し、旧gameplayを再走しない。')
 state['observed_head_checks']=dict(scope_head=SOURCE,controller_host_tests=12,successor_host_differential_cases=183,new_native_processes=measure['native_processes'],save_entry_cases=22,journal_cases=257,isolated_controller_cases=10,current_candidate=measure['candidate'],controller_rom_placed=False,journal_codec_rom_placed=True,runtime_generation_binding=False,runtime_cross_store_atomicity=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-CONTROLLER / C transactionと既存save owner後継\n- Version: dex-hof-controller-owner-v1\n- Status: STOPPED（C/ARM・save共通化/codec配置の縦切り完了、全runtime世代結合未完）\n- Summary: {summary}\n- Files changed: C controller/header、新host/ARM probe、save successor generator/linker、typed reference proof、Actions/guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: run{RUN}/job{JOB}全step成功・artifact{ARCHIVE[0]}全text/SHA照合。C12host=51wholebyteshape/224cut-normal/76partialerase/256journal/32recovery/55updates/42rotation/14token/2pre-signaturebarrier。ARM6528byte/mutable0、save host183diff、native22+257+10。115owner境界/非save全byte/HOF5section/逆変換/6typed見かけ参照を保持。\n- Failures retained: 37274005427 ARM memcpy link失敗→field-copy修正。37275659829 generator差替え再帰→source事前凍結。37276165080 外部参照未分類3件→typed wholeasset/root再検証。37277097069 4件のhistorical allocator hashを現物SHAと誤同一視→最新115owner byte auditへ結合し直し。いずれも当該native開始前停止、成功へ読み替えなし。\n- Boundary: controllerは明示RAM隔離testのみ、callbackは合成model。codecはROM配置してvalidator257case、全HOF writer/loader配線は未完。50履歴/1936suffix/32sector/sector30・31保持。正式ROM/Save101・baseline/release不変。一般CI QOL不一致/action_requiredjob0/Stage79cachedを別扱い。\n- Next: {goal}\n- Commit: tested source={SOURCE}; record source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private inputsによる再構築のみ。source/minimal address-size-SHA/textだけ公開。ROM断片/rawhex/ROM/inputsave/runtime/runner/credential追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'every earlier bound byte retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_TERMINAL_HOF_CONTROLLER_RECORD',source_head=SOURCE,run=RUN,job=JOB,archive=ARCHIVE,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),tests_rerun=0,native_processes=0))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed owned text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed text newline');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'entire old logs preserved')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-CONTROLLER VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC,success='record.json',failure=None)
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and path.name in{'record.json',*(n for n,_ in SNAPSHOTS)},'explicit regular snapshots only');raw=path.read_bytes();need(0<len(raw)<3500000 and raw.endswith(b'\n')and b'\0'not in raw,'complete nonempty bounded text');raw.decode('utf8')
  if path.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard_source','record','guard','snapshot','export'),'closed terminal record');globals()[sys.argv[1]]()
