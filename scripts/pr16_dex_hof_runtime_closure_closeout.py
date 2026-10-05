#!/usr/bin/env python3
"""有限参照deltaの終端確認。分類・ROM・host・nativeを再実行しない。"""
import datetime,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_runtime_closure_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
current,bindings=w.prior.current,w.prior.bindings
BASE='a761f5322716544cbad870017d8b854bf5d7728a';SOURCE='a060cd5539cf633c3abe99761b6844c3c45ccdf7';RUN=37378915043;JOB=111995392180
ARCHIVE=(11372937159, 37378915043, 1420991, 'a58815f442be26ba936262312f7c9c08ca6f743bb843c07560813a72af16920c')
EXPECTED=dict(unit_tests=237,**w.EXPECTED,retained_sample_witnesses=50)
WF='.github/workflows/pr16-dex-hof-runtime-closure-closeout.yml';SELF='scripts/pr16_dex_hof_runtime_closure_closeout.py'
CODE={w.WF,WF,SELF,'tests/test_pr16_dex_hof_runtime_closure_closeout.py'};OUT=ROOT/'.local/pr16-dex-hof-runtime-closure-closeout';PUBLIC=ROOT/'public-dex-hof-runtime-closure-closeout';ARTIFACT='pr16-dex-hof-runtime-closure-closeout-text-only'


def source_guard():
 import pr16_learnset_runtime_record as g
 current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()


def failed_admission_record(run,jobs,artifacts):
 need((run['id'],run['head_sha'],run['status'],run['conclusion'],run['run_attempt'])==(37365137571,'bd44806f310f15115af50dec604ad1ff228b68ef','completed','failure',1),'exact prior failed admission run')
 need(len(jobs)==1 and (jobs[0]['id'],jobs[0]['run_id'],jobs[0]['status'],jobs[0]['conclusion'])==(111948357013,37365137571,'completed','cancelled')and jobs[0].get('steps')==[],'prior job cancelled with no execution steps')
 need(artifacts==[],'no prior measurement artifact; never fabricate lost evidence')
 return dict(run=run['id'],source=run['head_sha'],run_conclusion=run['conclusion'],job=jobs[0]['id'],job_conclusion=jobs[0]['conclusion'],observed_steps=0,artifacts=0,measurement_accepted=False,official_incident='https://www.githubstatus.com/incidents/3q1yb5m7ltvb',official_mitigation_announced_utc='2026-10-05T21:32:00Z',individual_cancellation_cause_proven=False)


def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not PUBLIC.exists(),'one terminal reference closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/w.STATE).read_bytes());protected=dict(state['source_bindings'])
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'every earlier bound original '+path)
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'only completed measurement trigger retired')
 admission=failed_admission_record(t.api('actions/runs/37365137571'),t.api('actions/runs/37365137571/jobs')['jobs'],t.api('actions/runs/37365137571/artifacts')['artifacts'])
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB))
 need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==RUN and len(job['steps'])==14 and all(s['conclusion']=='success'for s in job['steps']),'all fourteen new root/capacity measurement steps successful')
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
 need(len(full['hits'])==874 and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all prior729 and remainingunknowns exactly retained')
 need(all(full[k]==inherited[k]for k in w.delta.INHERITED_NAMES),'all eight full original delta families and witnesses retained')
 need(cp['current_owner_count']==115 and cp['current_rom_reconstructions']==1 and not any(cp[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs','accepted_heap_reruns','historical_rom_reconstructions')),'no unproved runtime or donor promotion')
 capacity_raw=(ROOT/w.EVIDENCE/'partial-space.json').read_bytes()
 need(identity(capacity_raw)==cp['capacity_identity']==measure['capacity_identity'] and json.loads(capacity_raw)==w.capacity_report(full,inherited),'whole new bounded-space report preserved')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only exact original measurement pending');state['pending_runs']=[]
 tests=(ROOT/'.local/pr16-runtime-closure-closeout-tests.txt').read_bytes();need(tests.count(b' ... ok\n')==15 and b'\nOK\n'in tests,'fifteen publication and prior-admission guards')
 result=dict(status='PASS_TERMINAL_EXACT_RUNTIME_CLOSURE_RECORD',prior_unexecuted_admission=admission,source_head=SOURCE,record_head=BASE,run=RUN,job=JOB,all14_steps_success=True,archive=ARCHIVE,all5_snapshots_full_bytes_and_lf_verified=True,checkpoint=w.CP,checkpoint_identity=identity((ROOT/w.CP).read_bytes()),**EXPECTED,delta_identity=cp['delta_identity'],baseline_identity=w.delta.BASELINE_ID,parent_identity=w.delta.PARENT_ID,earlier_identity=w.delta.EARLIER_ID,capacity_identity=cp['capacity_identity'],old729_accepted_and_all874_identities_retained=True,all_eight_old_delta_families_preserved=True,independent_final_source_review_completed=False,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),tests_rerun=0,new_export_guard_tests=15,export_guard_test_log=identity(tests),arm_compiles=0,native_processes=0,current_rom_reconstructions=0,candidate_changed=False,donor_leased=False,formal_save_changed=False)
 next_goal='残142件は実consumer型を閉じる最小rootを優先。次候補0x08142F5DはMystery Giftのmask literal/code境界、実CreateTask→38state表slot11/23の根を結ぶ。異種2要素の完全partitionと専用boundary witnessを設け、同kind streamへ無理に包含しない。次点0x080A006FはGPUscalar/VBlankcallback境界で外側root未特定。MoveTutor・普遍epoch/IRQ/opaque非干渉は別義務として保持。保存済237試験・ReadMailコピー後Free・Leer連続6194命令・QuestLog同期型を無影響再走しない。部分leaseは最大access/間接参照/対象退役/owner移管が揃う場合だけ採用。単一controller6528byteの容量確保後、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、全保存入口heap-ready/同期非再入/0804B85C退避前Freeを接続。正式切替後trainer131後半→シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
 state['bp']['next_step']=next_goal;state['next_action']['goal_ja']=next_goal
 state['story_dex_owner']['runtime_integration']['hof_runtime_closure']['recording']=result;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all14_steps_success=True,whole_receipt_equals_checkpoint=True)
 state['source_bindings'].update(bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-RUNTIME-CLOSURE / 実consumer型と最小寿命境界の終端\n- Version: hof-runtime-closure-closeout\n- Status: STOPPED（条件付き実consumer型3件を受入、残root/donor/本番controller未完）\n- Summary: run{RUN}/job{JOB}全14step成功。artifact{ARCHIVE[0]}全11text原本と固定MDJSON/CP/両ログ全byte/LF/Git blobを照合しpending解除。完了measurement起動条件のみmanual-onlyへ。旧run37365137571はstep0/artifact0のcancelled jobで未受入のまま保持し、公式21:32UTC緩和後に同契約を新attempt1で検証。\n- Files changed: closeout source/workflow/tests、measurement起動条件、固定MDJSON、両append-onlyログ。\n- Verify: 原本{EXPECTED["unit_tests"]}tests、新分類{EXPECTED["newly_classified"]}、{EXPECTED["classified"]}分類/{EXPECTED["unclassified"]}未知（owner内0）を再利用。全729親行・全八段110changes/100witnessと残unknown全field、133曲/50assetを保持。新公開/未開始履歴guard15tests PASS。新direct/sprite/ReadMail source-only独立確認を実施。r12/MUL-C仮定、current用wrapper負例、静的BL successor表記を修正。初回sprite2失敗は原因と全文log上書きの制限をdevelopment記録へ保存。旧分類/host/ARM/ROM/native再走0。旧独立最終sourceレビュー未実施を保持。\n- Capacity: 未知の最大アクセス範囲が未証明なら全15118byte保護。間接参照/退役/owner移管も未完でsafe0byte。global511＋save804の上限1315は単一controller6528に不足5213。点targetの仮想空隙は安全容量ではなく、今後の追加分類で変わり得る。実配線時の追加容量も未確定。\n- Publication: 全親は参照保持、新delta{cp["delta_identity"]["size"]}byteとpartial-space独立envelope。閉じた非空success set・whole size/SHA/LF・hidden/symlink/未知file拒否。\n- Boundary: 現0641/115owner/52saveowner/804byte/正式ROM/Save101不変。heap13352の保存退避53300跨ぎ禁止。一般CI既知QOL不一致/action_required job0/runner割当中のcancelled job/Stage79cacheは別扱い。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/text原本のみ。ROM断片/rawhex/ROM/save/runtime/runner/credentials追加公開0。\n'


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
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-RUNTIME-CLOSURE VERIFY=PASS COMMIT='+receipt['final_head'])
def validate_export(files,head):
 expected={'closeout.json',*(name for name,_ in w.SNAPSHOTS)}
 need(set(files)==expected,'complete six-file terminal artifact, never a partial success')
 w.bounded_files(files);receipt=json.loads(files['closeout.json'])
 need(receipt.get('final_head')==head and len(head)==40 and receipt.get('status')=='PASS_TERMINAL_EXACT_RUNTIME_CLOSURE_RECORD','completed snapshot receipt and current commit')
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
