#!/usr/bin/env python3
"""有限参照deltaの終端確認。分類・ROM・host・nativeを再実行しない。"""
import datetime,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_consumer_references_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
current,bindings=w.prior.current,w.prior.bindings
BASE='e8e12148e198efb20f4c287b2310e303eea6798f';SOURCE='c9d442c21aa85a4ae170fd05a478d742247cf8fc';RUN=37341731986;JOB=111870203582
ARCHIVE=(11358558077,RUN,1367105,'828d54e92285f24dad093e3d5731cdfe2bcf3d6d618b63654805fb47d82a8d7e')
EXPECTED=dict(unit_tests=193,classified=726,unclassified=148,newly_classified=3,new_data=2,new_code=1,new_song=0,combined_song_models=133,owner_unknown=0,unowned_unknown=148,retained_sample_witnesses=50)
WF='.github/workflows/pr16-dex-hof-consumer-references-closeout.yml';SELF='scripts/pr16_dex_hof_consumer_references_closeout.py'
CODE={w.WF,WF,SELF,'tests/test_pr16_dex_hof_consumer_references_closeout.py'};OUT=ROOT/'.local/pr16-dex-hof-consumer-references-closeout';PUBLIC=ROOT/'public-dex-hof-consumer-references-closeout';ARTIFACT='pr16-dex-hof-consumer-references-closeout-text-only'


def source_guard():
 import pr16_learnset_runtime_record as g
 current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()


def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not PUBLIC.exists(),'one terminal reference closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/w.STATE).read_bytes());protected=dict(state['source_bindings'])
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'every earlier bound original '+path)
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'only completed measurement trigger retired')
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB))
 need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==RUN and len(job['steps'])==14 and all(s['conclusion']=='success'for s in job['steps']),'all fourteen reference measurement steps successful')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);archive,_=t.archive(ARCHIVE)
 with archive:
  names=set(w.PROOF)|{'record.json',*(name for name,_ in w.SNAPSHOTS)}
  need(set(archive.namelist())==names and len(archive.infolist())==len(names)and all(not i.is_dir()and i.external_attr>>28!=10 for i in archive.infolist()),'complete closed nonsymlink measured text archive')
  receipt=json.loads(archive.read('record.json'));measure=json.loads(archive.read('measurement.json'))
  need(receipt['final_head']==BASE and receipt['source_head']==SOURCE and receipt['record_run']==RUN and measure['source_head']==SOURCE and measure['run_id']==RUN,'exact measured source/record lineage')
  for name,path in w.SNAPSHOTS:
   raw=archive.read(name);need(raw==(ROOT/path).read_bytes()==git('show',BASE+':'+path)and raw.endswith(b'\n'),'all committed original snapshot bytes and LF')
   binding=receipt['final_blobs'][path];need(identity(raw)=={k:binding[k]for k in('size','sha256')}and git('rev-parse',BASE+':'+path).decode().strip()==binding['git_blob_sha'],'whole exact original Git blob')
  for name in w.PROOF:need(archive.read(name)==(ROOT/w.EVIDENCE/name).read_bytes(),'all original reference measurements retained')
 cp=json.loads((ROOT/w.CP).read_bytes())
 need(cp['independent_final_source_review_completed']is False and measure['independent_final_source_review_completed']is False,'explicit independently unreviewed final scope remains disclosed')
 need(all(cp[k]==v and measure[k]==v for k,v in EXPECTED.items())and cp['candidate']==measure['candidate']==w.data.CANDIDATE,'exact source and candidate counters')
 need(cp['source_bindings']==measure['source_bindings']and cp['inherited_bindings']==measure['inherited_bindings'],'exact measured source identities')
 need(cp['delta_identity']==measure['delta_identity']and cp['reference_baseline']==w.delta.BASELINE,'one immutable baseline/delta identity')
 inherited=w.delta.parent(*[(ROOT/path).read_bytes()for path in w.delta.PARENT_INPUTS]);delta=w.delta.read_measured((ROOT/w.EVIDENCE/'reference-chain.json').read_bytes(),cp['delta_identity'],inherited);full=w.delta.materialize(inherited,delta)
 need(len(full['hits'])==874 and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all prior723 and remainingunknowns exactly retained')
 need(all(full[k]==inherited[k]for k in('reference_delta','reference_chain','remaining_reference_chain','script_reference_chain')),'all four full original delta families and witnesses retained')
 need(cp['historical_input_run']==37338921508 and cp['historical_input_tests_reused']==16 and cp['historical_rom_reconstructions']==0 and cp['battle_unknown_count']==10 and cp['battle_partial_models']==16 and cp['prior_failed_runs']==w.FAILED_PREPARE,'exact historical input reuse, battle frontier and unmodified failed preparation')
 need(cp['current_owner_count']==115 and cp['current_rom_reconstructions']==1 and cp['tutor_upper_word_remains_unknown']is False and not any(cp[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs','accepted_heap_reruns')),'no unproved runtime or donor promotion')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only exact original measurement pending');state['pending_runs']=[]
 tests=(ROOT/'.local/pr16-consumer-references-closeout-tests.txt').read_bytes();need(tests.count(b' ... ok\n')==9 and b'\nOK\n'in tests,'nine new synthetic final-publication guards')
 result=dict(status='PASS_TERMINAL_EXACT_CONSUMER_REFERENCE_CHAIN_RECORD',source_head=SOURCE,record_head=BASE,run=RUN,job=JOB,all14_steps_success=True,archive=ARCHIVE,all5_snapshots_full_bytes_and_lf_verified=True,checkpoint=w.CP,checkpoint_identity=identity((ROOT/w.CP).read_bytes()),**EXPECTED,delta_identity=cp['delta_identity'],baseline_identity=w.delta.BASELINE_ID,parent_identity=w.delta.PARENT_ID,earlier_identity=w.delta.EARLIER_ID,old723_accepted_and_all874_identities_retained=True,all_four_old_delta_families_preserved=True,independent_final_source_review_completed=False,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),tests_rerun=0,historical_run=37338921508,historical_tests_reused=16,battle_unknown_count=10,battle_partial_models=16,prior_failed_runs=cp['prior_failed_runs'],new_export_guard_tests=9,export_guard_test_log=identity(tests),arm_compiles=0,native_processes=0,current_rom_reconstructions=0,candidate_changed=False,donor_leased=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['hof_consumer_references']['recording']=result;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all14_steps_success=True,whole_receipt_equals_checkpoint=True)
 state['source_bindings'].update(bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-CONSUMER-REFERENCES / 追加3参照chainの終端\n- Version: hof-consumer-references-closeout\n- Status: STOPPED（3件の分類・記録を受入。donor/本番controllerは未完）\n- Summary: run{RUN}/job{JOB}全14step成功。artifact{ARCHIVE[0]}の全10text原本、固定MDJSON/CP/両ログの全byte・LF・Git blobを照合しpending解除。measurement起動条件だけmanual-onlyへ。\n- Files changed: closeout source/workflow、measurement起動条件、固定MDJSON、両append-onlyログ。\n- Verify: 原本193tests、history16再利用、palette1/engine1/T09historical1の3追加、726分類/148未知（owner内0/外148）を再利用。旧723全行・644delta25行/22witness・661chain17行/16witness・694chain33行/33witness・723chain29行/23witness・残unknown全field不変。既存133曲/50sample/finite-root rolesと全親証拠継承を確認。新公開guard9tests PASS。旧分類/host/ARM/ROM/native再走0。独立最終source再レビュー未実施を保持し、専用unitと現候補の機械検査へ受入範囲を限定。\n- Publication: 619原本4.1MB＋644delta149772byte＋661chain95619byte＋694chain71138byte＋723chain134951byteは参照保持。child {cp["delta_identity"]["size"]}byte、独立measurement全SHA・closed schema・typed geometry・全量上限。公開metadataは必要なsource identity/address-size-SHAへ縮小、private archive名/member path/不要relocation情報を除去。\n- Boundary: 現候補0641/115owner/52saveowner/804byte/正式ROM/Save101不変。donor0、実controller/heap lifetimeは未完、heap13352の保存退避53300跨ぎ禁止。静的有限根を自然story到達/描画/再生へ昇格しない。実歴史Stage38の独立proofからT09を閉じ、現PLC2転用なし。battle部分16caseは新分類0、残10未知。一般CI既知QOL不一致/action_required job0/Stage79cacheを別扱い。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/text原本のみ。ROM断片/rawhex/ROM/save/runtime/runner/credentials追加公開0。\n'

 for path in w.LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 write(PUBLIC/'closeout.json',result)
 for name,path in w.SNAPSHOTS:(PUBLIC/name).write_bytes((ROOT/path).read_bytes())
 # 最終snapshot receiptを含む保守的な上限をpush前に検査。
 projected=dict(result,final_head='0'*40,final_blobs={path:dict(**identity((PUBLIC/name).read_bytes()),git_blob_sha='0'*40,trailing_newline=True)for name,path in w.SNAPSHOTS})
 planned={name:(PUBLIC/name).read_bytes()for name,_ in w.SNAPSHOTS};planned['closeout.json']=(json.dumps(projected,ensure_ascii=False,indent=2)+'\n').encode();w.bounded_files(planned)
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
  raw=git('show','HEAD:'+path);need(raw==(PUBLIC/name).read_bytes()and raw.endswith(b'\n'),'whole committed snapshot LF');receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in w.LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'old logs are exact prefixes')
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-CONSUMER-REFERENCES VERIFY=PASS COMMIT='+receipt['final_head'])
def validate_export(files,head):
 expected={'closeout.json',*(name for name,_ in w.SNAPSHOTS)}
 need(set(files)==expected,'complete six-file terminal artifact, never a partial success')
 w.bounded_files(files);receipt=json.loads(files['closeout.json'])
 need(receipt.get('final_head')==head and len(head)==40 and receipt.get('status')=='PASS_TERMINAL_EXACT_CONSUMER_REFERENCE_CHAIN_RECORD','completed snapshot receipt and current commit')
 proofs=receipt.get('final_blobs',{});need(set(proofs)=={path for _,path in w.SNAPSHOTS},'all final snapshot receipts')
 for name,path in w.SNAPSHOTS:
  raw=files[name];binding=proofs[path]
  need(binding.get('trailing_newline')is True and raw.endswith(b'\n')and identity(raw)=={k:binding[k]for k in('size','sha256')},'complete committed final snapshot identity')
  import hashlib
  need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha'],'exact final Git blob content')
 return True

def export():
 publication.output(PUBLIC,success='closeout.json',failure=None);files={}
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in{'closeout.json',*(n for n,_ in w.SNAPSHOTS)},'closed terminal flat text set');files[path.name]=path.read_bytes()
 validate_export(files,git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed terminal reference modes');globals()[sys.argv[1]]()
