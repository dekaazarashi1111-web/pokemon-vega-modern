#!/usr/bin/env python3
"""PLR1 numeric記録の終端。既受入分類/host/ARM/native再走なし。"""
import datetime,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_numeric_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
current,bindings=w.prior.current,w.prior.bindings
BASE='b56149dfd3e66e829e3814e621f6f973942de4a2';SOURCE='be9e90f8625a73cd00fe76ccf784890a76f1bf79';RUN=37290157793;JOB=111698424964
ARCHIVE=(11336112410,RUN,1415505,'8ec18cca59f76d374d5968a88ff5dbf25b271917ac4d956295f1f2f8bd4a5659')
WF='.github/workflows/pr16-dex-hof-numeric-closeout.yml';SELF='scripts/pr16_dex_hof_numeric_closeout.py'
CODE={w.WF,WF,SELF};OUT=ROOT/'.local/pr16-dex-hof-numeric-closeout';PUBLIC=ROOT/'public-dex-hof-numeric-closeout';ARTIFACT='pr16-dex-hof-numeric-closeout-text-only'

def source_guard():
 import pr16_learnset_runtime_record as g
 current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()

def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not PUBLIC.exists(),'one terminal numeric record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/w.STATE).read_bytes());protected=dict(state['source_bindings'])
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'every earlier bound original '+path)
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode();need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'only successful measurement trigger retired')
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB));need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==RUN and len(job['steps'])==13 and all(s['conclusion']=='success'for s in job['steps']),'all thirteen record steps successful')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);z,_=t.archive(ARCHIVE)
 with z:
  names=set(w.PROOF)|{'record.json',*(name for name,_ in w.SNAPSHOTS)};need(set(z.namelist())==names and len(z.infolist())==len(names) and all(not i.is_dir()and i.external_attr>>28!=10 for i in z.infolist()),'complete closed nonsymlink original texts')
  receipt=json.loads(z.read('record.json'));measure=json.loads(z.read('measurement.json'));need(receipt['final_head']==BASE and receipt['source_head']==SOURCE,'exact source and final record lineage')
  for name,path in w.SNAPSHOTS:
   raw=z.read(name);need(raw==(ROOT/path).read_bytes()==git('show',BASE+':'+path)and raw.endswith(b'\n'),'all committed original bytes including LF '+path);b=receipt['final_blobs'][path];need(identity(raw)=={k:b[k]for k in('size','sha256')}and git('rev-parse',BASE+':'+path).decode().strip()==b['git_blob_sha'],'exact original blob '+path)
  for name in w.PROOF:need(z.read(name)==(ROOT/w.EVIDENCE/name).read_bytes(),'each measured original text retained')
 cp=json.loads((ROOT/w.CP).read_bytes());need(cp['candidate']==measure['candidate']and cp['source_bindings']==measure['source_bindings']and cp['inherited_bindings']==measure['inherited_bindings'],'whole candidate/source/inherited receipts')
 need(cp['unit_tests']==37 and cp['classified']==455 and cp['unclassified']==419 and cp['newly_classified']==12 and cp['old_inventory_candidates']==874,'exact bounded numeric counters')
 need(not any(cp[k]for k in('candidate_changed','donor_leased','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','arm_compiles','current_rom_reconstructions','accepted_source_regenerations')),'no unproved donor or runtime promotion')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only measured run pending');state['pending_runs']=[]
 result=dict(status='PASS_TERMINAL_EXACT_PLR1_NUMERIC_RECORD',source_head=SOURCE,record_head=BASE,run=RUN,job=JOB,all13_steps_success=True,archive=ARCHIVE,all5_snapshots_full_bytes_and_lf_verified=True,checkpoint=w.CP,checkpoint_identity=identity((ROOT/w.CP).read_bytes()),classified=455,unclassified=419,newly_classified=12,unit_tests=37,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),tests_rerun=0,arm_compiles=0,native_processes=0,candidate_changed=False,donor_leased=False,runtime_lease_enabled=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['hof_numeric']['recording']=result;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all13_steps_success=True,whole_receipt_equals_checkpoint=True)
 state['source_bindings'].update(bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-NUMERIC / PLR1数値consumer証拠の終端\n- Version: hof-numeric-closeout\n- Status: STOPPED（限定検証・記録完了、donor/本番接続は未完）\n- Summary: run{RUN}/job{JOB}全13step成功。artifact{ARCHIVE[0]}全原本と固定MDJSON/CP/両ログの全byte・末尾LF・Git blobを照合してpending解除。成功measurement起動条件だけmanual-onlyへ。\n- Files changed: closeout source/workflow、measurement起動条件、固定MDJSONと両ログ。\n- Verify: 新37unit/PLR1数値consumer分類12件を原本再利用。分類455・未分類419・全874inventory保持・旧443accepted不変。追加host/ARM/native/ROM再構成0。\n- Boundary: 現候補全SHA/115owner不変。全1483spanの隙間/重複/型/終端を検査し、12件のspecies行境界跨ぎを両側の数値型へ結合。donor0、Ccontroller未配線、正式ROM/Save101不変。一般CI既知QOL source不一致・action_required/job0・Stage79cacheは別扱い。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/text原本のみ。ROM断片/rawhex/ROM/save/runtime/runner/credential追加公開0。\n'
 for path in w.LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 write(PUBLIC/'closeout.json',result)
 for name,path in w.SNAPSHOTS:(PUBLIC/name).write_bytes((ROOT/path).read_bytes())
 owned={w.STATE,*w.LOGS}
 if(ROOT/w.DOC).read_bytes()!=git('show','HEAD:'+w.DOC):owned.add(w.DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'all committed closeout bytes')
 for name,path in w.SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(PUBLIC/name).read_bytes()and raw.endswith(b'\n'),'complete committed snapshots');receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in w.LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'whole old logs append-only')
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-NUMERIC VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC,success='closeout.json',failure=None)
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in{'closeout.json',*(n for n,_ in w.SNAPSHOTS)},'closed nonhidden nonsymlink text');raw=path.read_bytes();need(0<len(raw)<4000000 and raw.endswith(b'\n')and b'\0'not in raw,'nonempty complete bounded text');raw.decode('utf8')
  if path.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed terminal numeric modes');globals()[sys.argv[1]]()
