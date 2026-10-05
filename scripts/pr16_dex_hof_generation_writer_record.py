#!/usr/bin/env python3
"""下位writerと容量/RAM前提の原本を保存。検証を再実行しない。"""
import datetime,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_generation_writer_actions as w
import pr16_dex_hof_storage_actions as prior
import pr16_dex_publication as publication
import pr16_story_live_probe as t
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='c1aa1dbece3dd3cf5221321ad77c1d1fae29d75c';SOURCE=BASE;RUN=37282589643;JOB=111673873801;ARCHIVE=(11333175429,37282589643,97528,'7f8087216e07429a85b29628d601a4c1028460ce4fa6da14968c3a35319ffabd')
SELF='scripts/pr16_dex_hof_generation_writer_record.py';WF='.github/workflows/pr16-dex-hof-generation-writer-record.yml'
CP='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_generation_writer_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=prior.LOGS
OUT=ROOT/'.local/pr16-dex-hof-generation-writer-record';PUBLIC=ROOT/'public-dex-hof-generation-writer-record';ARTIFACT='pr16-dex-hof-generation-writer-record-text-only'
CODE={SELF,WF,w.WF}
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
def guard_source():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 before=git('show',BASE+':'+w.WF);after=(ROOT/w.WF).read_bytes();trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode();need(before.count(trigger)==1 and after==before.replace(trigger,b'  workflow_dispatch:\n'),'retire only successful measurement trigger')
def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();need(not OUT.exists()and not PUBLIC.exists()and not(ROOT/CP).exists(),'one immutable generation writer record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and state['pending_runs']==[],'all earlier bound originals retained')
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB));need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and job['run_id']==RUN and all(s['conclusion']=='success'for s in job['steps']),'exact successful source/job all steps')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);z,_=t.archive(ARCHIVE);files={}
 with z:
  for item in z.infolist():
   need(not item.is_dir()and item.external_attr>>28!=10 and Path(item.filename).name==item.filename,'flat nonsymlink text');raw=z.read(item);need(raw and raw.endswith(b'\n')and b'\0'not in raw,'whole complete text');raw.decode('utf8');files[item.filename]=raw
 m=json.loads(files['measurement.json']);need(m['source_head']==SOURCE and m['run_id']==RUN and m['status']=='PASS_ROM_LOWER_GENERATION_WRITER_CAPACITY','exact completed measurement')
 need(m['native']['save_owner_cases']==22 and m['native']['new_journal_validator_cases']==257 and m['native_processes']==1 and m['capacity_reclaimed_bytes']>0,'changed scoped native and capacity')
 need(not any(m[k]for k in('controller_runtime_wired','controller_rom_placed','runtime_cross_store_atomicity','workspace_runtime_owned','formal_rom_changed','formal_save_changed')),'no unproved runtime claim')
 for path,binding in m['source_bindings'].items():need(identity(git('show',BASE+':'+path)if path==w.WF else(ROOT/path).read_bytes())==binding,'exact measured source '+path)
 paths=set()
 for name,raw in files.items():
  dest=ROOT/EVIDENCE/name;need(not dest.exists(),'immutable fresh evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);paths.add(dest.relative_to(ROOT).as_posix())
 egg=json.loads(files['egg-capacity-audit.json']);heap=json.loads(files['heap-binding.json']);need(egg['donor_leased']is False and heap['runtime_lease_enabled']is False,'no donor or heap lease enabled')
 cp=dict(schema_version=1,**m,guide=w.GUIDE,verified_run=RUN,verified_job=JOB,archive=ARCHIVE,evidence_bindings=prior.bindings(paths),capacity_donor_audit=egg,heap_prerequisites=heap,prior_failed_runs=[dict(run=37281161559,source='fb7ecfdc5eb5176351084816f99b903b1e5eb93b',artifact=11332866150,reason='Stage73 historical egg root differs from live P07 root',native_processes=0),dict(run=37281735894,source='b904f7fc396488f5e464462f7f30c512e6dbc987',artifact=11332906869,reason='three-mode writer far-call sections require9254bytes vs9252body, packing limit',native_processes=0)],record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']))
 write(ROOT/CP,cp);candidate=m['candidate']['sha256'];free=m['link']['free_bytes'];count=len(m['link']['sections'])+len(m['placement']['preserved_hof_sections'])
 summary=f'exact-source cloneとLink source-recordを下位writerへ統合し実ROM全8入口22case＋移設HJ validator257caseを変更影響検証。候補{candidate[:8]}、115owner／save subowner{count}／残{free}byte。旧egg表は現P07 root移行を確認したが参照形{egg["unclassified"]}件未分類でleaseなし。heap既存10窓688byteは現ROMに一致、実arena所有は未証明。HOF全世代配線・正式ROM/Save101切替は未完。'
 goal='現lower writer候補を基準に、旧Stage67 egg表の全byte開始位置/mirror/Thumb参照形をtyped asset/consumerで分類し、必要量だけ明示donor移管する。controllerと実S61E/MDX callbackをLink exact-source/no-main/INITIAL/全writer/loadへ接続。heap事前chain admission、raw13359/round13360/align8、allocator scratch02020004/08/0C、0804B85C退避前解放、全入口heap-readyと非再入を実証する。全mode/早期31/species9bit/残typed・正式切替後trainer131後半、最終シオウ通常回復/保存/coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_generation_writer']=dict(checkpoint=CP,guide=w.GUIDE,status=m['status'],candidate=m['candidate'],parent_candidate=m['parent_candidate'],source=SOURCE,run=RUN,job=JOB,current_save_subowners=count,current_save_owner_free_bytes=free,capacity_reclaimed_bytes=m['capacity_reclaimed_bytes'],egg_unclassified=egg['unclassified'],egg_donor_leased=False,heap_windows_bound=10,heap_runtime_lease_enabled=False,controller_runtime_wired=False,record_run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='CLASSIFY_HOF_DONOR_AND_WIRE_EXPLICIT_GENERATIONS',goal_ja=goal,read_paths=[w.GUIDE,CP,'docs/PR16_DEX_HOF_CONTROLLER_JA.md','content/modernization/pr16_dex_hof_controller_checkpoint.json'])
 state['observed_head']=SOURCE;state['observed_head_semantics']='変更下位writerの実保存入口と現ROM donor/heap前提監査。HOF Ccontrollerは未接続。';state['pending_runs']=[]
 state['source_bindings'].update(prior.bindings(w.CODE|CODE|{CP}|paths));state['do_not_repeat'].append('下位generation writer run'+str(RUN)+'の183host全媒体差分・全8入口22ARMcase・移設HJ257caseを候補/source不変なら再走しない。旧egg参照形は未分類/lease0、heap10窓はbindingのみ/実arena0。正式ROM/Save101・HOF世代結合未完。')
 state['observed_head_checks']=dict(scope_head=SOURCE,host_differential_cases=183,existing_host_cases=20,new_native_processes=1,save_entry_cases=22,journal_cases=257,current_candidate=m['candidate'],free_bytes=free,controller_runtime_wired=False,egg_donor_leased=False,heap_runtime_lease_enabled=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-GENERATION / exact-source下位writerとROM/RAM前提\n- Version: hof-generation-writer-v1\n- Status: STOPPED（安全な実配置縦切り完了、HOF全配線は未完）\n- Summary: {summary}\n- Files changed: 新source generator/Actions/guide/CP/evidence、固定MDJSON、両ログ。\n- Verify: run{RUN}/job{JOB}全step成功、artifact{ARCHIVE[0]}全text/SHA照合。183host全媒体/MDX/selector/callback数一致、20既存hostcase、native22+257、115owner/非save全byte/既HOF5section保持、capacity回収{m["capacity_reclaimed_bytes"]}byte。\n- Failures retained: run37281161559 historical Stage73 root仮定→P07移行を確認。run37281735894 三mode統合9254>9252byte/farcall/packing上限→source clone/rewriteのみ共通化。両方native0、失敗を成功へ読替えなし。\n- Boundary: Ccontroller/全writer/load/INITIAL/LinkFull未接続。旧egg donorは未分類{egg["unclassified"]}件で未使用。heap10窓688byteのcurrent bindingのみ、malloc/OOM/同期lifetimeは未受入。一般CI QOL不一致/Stage79cachedは別記。50HOF履歴/1936suffix/正式ROM/Save101/baseline/release不変。\n- Next: {goal}\n- Commit: tested source={SOURCE}; record source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private入力。公開はsource/minimal address-size-SHA/textのみ、ROM断片/rawhex/ROM/save/runtime/runner/credential追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'all previous source bytes retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_TERMINAL_GENERATION_WRITER_RECORD',source_head=SOURCE,run=RUN,job=JOB,archive=ARCHIVE,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),tests_rerun=0,native_processes=0))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed owned text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed text newline');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'old logs append-only')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-GENERATION VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC,success='record.json',failure=None)
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and path.name in{'record.json',*(n for n,_ in SNAPSHOTS)},'explicit regular snapshots only');raw=path.read_bytes();need(0<len(raw)<3500000 and raw.endswith(b'\n')and b'\0'not in raw,'whole bounded text');raw.decode('utf8')
  if path.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard_source','record','guard','snapshot','export'),'closed record');globals()[sys.argv[1]]()
