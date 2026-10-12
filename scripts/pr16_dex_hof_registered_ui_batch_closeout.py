#!/usr/bin/env python3
"""有限参照deltaの終端確認。分類・ROM・host・nativeを再実行しない。"""
import copy,datetime,hashlib,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_registered_ui_batch_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
current,bindings=w.prior.current,w.prior.bindings
INITIAL='c2059ee805d978575b319e7a113b3edf0a676f1e'
BASE='77b059876c459d58c4dce0f460429f27194fd531';SOURCE='b56b00d604b010c1730cf146a830cdbc3930af65';RUN=37467101922;JOB=112280782858
ARCHIVE=(11415933223, 37467101922, 1521292, 'c022631718a847f62af8efad7801cc19109f54dc42516f3761c0418fb2e053d2')
EXPECTED=dict(unit_tests=171,**w.EXPECTED,retained_sample_witnesses=50)
WF='.github/workflows/pr16-dex-hof-registered-ui-batch-closeout.yml';SELF='scripts/pr16_dex_hof_registered_ui_batch_closeout.py'
CLOSEOUT_TESTS=38 # 新終端source-only suite実測。旧suite実績へ流用しない。
DEVELOPMENT='content/modernization/pr16_dex_hof_registered_ui_batch_closeout_validation.json'
CODE={w.WF,WF,SELF,'tests/test_pr16_dex_hof_registered_ui_batch_closeout.py',DEVELOPMENT};OUT=ROOT/'.local/pr16-dex-hof-registered-ui-batch-closeout';PUBLIC=ROOT/'public-dex-hof-registered-ui-batch-closeout';ARTIFACT='pr16-dex-hof-registered-ui-batch-closeout-text-only'

# 実測済み全11textの全byteを固定。探索用workや実行ログ本文は公開しない。
MEASUREMENT_FILES = {'fixed-checkpoint.json': {'size': 305095, 'sha256': 'e0115e1a47dfb5db7f0730c3fa3acae69c8bb75f0ec2d6182bf8757d2077b7da'}, 'fixed-resume.md': {'size': 141509, 'sha256': '9d842a4c5ab0621d3d3e4da55d2a1a3e5dca3709d6085eb7e5b5f12ea0c0e9c3'}, 'fixed-run-log.md': {'size': 2131134, 'sha256': '90cf6a77a6b9eb044c1ff573ff0516388bd436ee8799bed729f590b9122ff8b5'}, 'fixed-state.json': {'size': 3651907, 'sha256': '85ff9b7fc2b8aa2a150646b1ff618bcd18167323bd46c745c4cb728085693138'}, 'fixed-version-log.md': {'size': 1742532, 'sha256': 'e49c644c8847fd31b34c860a2661c79a80b1e46816caa7a34809158f7339cdb1'}, 'measurement.json': {'size': 303438, 'sha256': 'c7037920515c3b458b1079358fd26446e3df02e02d19382e61f7be0e3b975d12'}, 'partial-space.json': {'size': 49689, 'sha256': '3a4e89c17a5ab8a1d099ffaa3481f909f6c24a24da49fdf9a0f12769198108c0'}, 'record.json': {'size': 3014, 'sha256': 'ccbf34480d07cc9516dfc73108d823049d3167031392b5e79f30ba8755f8603a'}, 'reference-chain.json': {'size': 339411, 'sha256': '217052875ea454411851c20ac9fa8a60f3910fa2c3819e4e372cdf4f544af501'}, 'registered-ui-batch-tests.txt': {'size': 27019, 'sha256': 'a5f0f7a921d0db525f727627ccf1878b6dd6c94033fb017ffe4043d311642d77'}, 'unknown-frontier.json': {'size': 41705, 'sha256': 'bd22a7361baba6957c95bb2757376c9f1c6be4e0fb482e408b5242cece5dcaca'}}
MEASUREMENT_DEVELOPMENT = {'size': 3377, 'sha256': '3779ce6646903baba83d4ccdef7b0c409d7bec94f296dccc5948eda4d10ac51c'}
EXECUTION_HISTORY = {'failed_measurement_attempts': [], 'failed_closeout_attempts': [], 'failed_current_rom_reconstructions': 0, 'accepted_current_rom_reconstructions': 1, 'total_current_rom_reconstructions': 1, 'accepted_measurement_runs': 1, 'failed_measurement_runs': 0, 'failed_closeout_runs': 0, 'failed_closeout_current_rom_reconstructions': 0, 'closeout_additional_rom_reconstructions': 0, 'closeout_additional_arm_compiles': 0, 'closeout_additional_native_processes': 0, 'closeout_old_suite_runs': 0, 'failed_attempt_promoted_to_success': False}
PARENT_CLOSEOUT = 'content/modernization/pr16_dex_hof_registered_state_batch_closeout_validation.json'
NEXT_ROOTS = () # 次の独立根は未確定。今回UI候補を次scopeの未受入根へ重複計上しない。
NEXT_GOAL_PREFIX = '次の独立登録根は0件。083DDEE1/083DE02B/083DE6ABは受入候補へ数えず未知保持。固定JP symbol出力または生成crosswalkから、うち1件の両側text symbol/EOS込みextent・現配置の実literal/table cell・APIを独立に結合できるまで、新ROM windowも正式分類も追加しない。'

def validate_execution_history(value):
 fields={'failed_measurement_attempts','failed_closeout_attempts','failed_current_rom_reconstructions','accepted_current_rom_reconstructions','total_current_rom_reconstructions','accepted_measurement_runs','failed_measurement_runs','failed_closeout_runs','failed_closeout_current_rom_reconstructions','closeout_additional_rom_reconstructions','closeout_additional_arm_compiles','closeout_additional_native_processes','closeout_old_suite_runs','failed_attempt_promoted_to_success'}
 need(type(value)is dict and set(value)==fields,'closed actual new-scope execution history')
 lists=('failed_measurement_attempts','failed_closeout_attempts')
 for name in lists:
  need(type(value[name])is list,'explicit complete failed attempts')
  for row in value[name]:
   need(type(row)is dict and set(row)=={'source_head','run','job','status','current_rom_reconstructions','native_processes','recorded','classification_accepted','artifacts'},'closed failed attempt provenance')
   need(type(row['source_head'])is str and re.fullmatch('[0-9a-f]{40}',row['source_head'])and row['source_head']!=SOURCE,'independent failed source never accepted source')
   need(all(type(row[k])is int and row[k]>0 for k in('run','job'))and row['run']!=RUN,'strict failed run/job, never accepted run')
   need(row['status']=='DIAGNOSTIC_NOT_ACCEPTED'and row['recorded']is False and row['classification_accepted']is False,'failed attempts remain unaccepted')
   need(type(row['current_rom_reconstructions'])is int and row['current_rom_reconstructions']>=0 and type(row['native_processes'])is int and row['native_processes']==0 and type(row['artifacts'])is int and row['artifacts']==0,'no fabricated native or successful artifact')
 counters=fields-set(lists)-{'failed_attempt_promoted_to_success'}
 need(all(type(value[k])is int and value[k]>=0 for k in counters),'strict actual execution counters')
 need(value['accepted_measurement_runs']==value['accepted_current_rom_reconstructions']==1,'one accepted current-only measurement')
 need(value['failed_measurement_runs']==len(value[lists[0]])and value['failed_closeout_runs']==len(value[lists[1]]),'every failed run retained')
 need(value['failed_current_rom_reconstructions']==sum(r['current_rom_reconstructions']for r in value[lists[0]])and value['failed_closeout_current_rom_reconstructions']==sum(r['current_rom_reconstructions']for r in value[lists[1]])==0,'exact failed reconstruction totals; no closeout reconstruction')
 need(value['total_current_rom_reconstructions']==value['failed_current_rom_reconstructions']+1,'accepted and failed reconstruction totals distinct')
 need(all(value[k]==0 for k in('closeout_additional_rom_reconstructions','closeout_additional_arm_compiles','closeout_additional_native_processes','closeout_old_suite_runs'))and value['failed_attempt_promoted_to_success']is False,'no old-suite reruns or fabricated closeout work')
 return True

def validate_history_binding(raw):
 need(w.delta.valid_identity(MEASUREMENT_DEVELOPMENT)and identity(raw)==MEASUREMENT_DEVELOPMENT,'entire accepted development original unchanged')
 value=json.loads(raw)
 need(type(value)is dict,'whole accepted development envelope')
 validate_execution_history(EXECUTION_HISTORY)
 return copy.deepcopy(EXECUTION_HISTORY)

def next_goal(original):
 need(original==w.data.NEXT_GOAL,'exact unproved runtime and save boundaries retained')
 return NEXT_GOAL_PREFIX+original


def validate_successful_job(run,job):
 need(type(run)is dict and type(job)is dict,'complete successful Actions metadata')
 need(type(run.get('id'))is int and run.get('id')==RUN and run.get('head_sha')==SOURCE and run.get('status')=='completed'and run.get('conclusion')=='success'and type(run.get('run_attempt'))is int and run['run_attempt']==1,'exact successful source/run/attempt')
 need(type(job.get('id'))is int and type(job.get('run_id'))is int and type(job.get('run_attempt'))is int and job['run_attempt']==1 and job.get('id')==JOB and job.get('run_id')==RUN and job.get('head_sha')==SOURCE and job.get('status')=='completed'and job.get('conclusion')=='success','exact completed accepted job identity')
 steps=job.get('steps');need(type(steps)is list and len(steps)==14 and all(type(s)is dict and s.get('conclusion')=='success'and s.get('status')=='completed'for s in steps),'all fourteen accepted measurement steps completed successfully')
 return True


def terminal_constants():
 require_measured_bindings()
 result=dict(status='PASS_TERMINAL_EXACT_REGISTERED_UI_BATCH_RECORD',source_head=SOURCE,record_head=BASE,run=RUN,job=JOB,
  all14_steps_success=True,archive=list(ARCHIVE),all5_snapshots_full_bytes_and_lf_verified=True,checkpoint=w.CP,
  checkpoint_identity=copy.deepcopy(MEASUREMENT_FILES['fixed-checkpoint.json']),**EXPECTED,
  delta_identity=copy.deepcopy(MEASUREMENT_FILES['reference-chain.json']),baseline_identity=copy.deepcopy(w.delta.BASELINE_ID),
  parent_identity=copy.deepcopy(w.delta.PARENT_ID),earlier_identity=copy.deepcopy(w.delta.EARLIER_ID),capacity_identity=copy.deepcopy(MEASUREMENT_FILES['partial-space.json']),
  old776_accepted_and_all874_identities_retained=True,all_twenty_five_old_delta_families_preserved=True,
  independent_final_source_review_completed=False,tests_rerun=0,new_export_guard_tests=CLOSEOUT_TESTS,
  arm_compiles=0,native_processes=0,current_rom_reconstructions=0,candidate=copy.deepcopy(w.data.CANDIDATE),candidate_changed=False,donor_leased=False,formal_rom_changed=False,formal_save_changed=False,
  initial_head=INITIAL,minimum_new_type_bytes=w.data.MINIMUM_BYTES,total_namespaces=26,total_changes=157+EXPECTED['newly_classified'],total_witnesses=147+EXPECTED['newly_classified'],
  new_registered_ui_closeout_source_review_completed=True,old_independent_final_review_retried=False,
  natural_full_play_proven=False,universal_irq_or_heap_lifetime_proven=False,indirect_reference_completeness_claimed=False,retirement_proven=False,owner_transfer_proven=False,
  controller_runtime_wired=False,donor_safe_bytes=0,protected_egg_bytes=15118,controller_measured_bytes=6528,heap_bytes=13352,stock_save_evacuation_bytes=53300,
  current_owner_count=115,current_save_owner_count=52,current_save_free_bytes=804,
  next_scope_candidates=list(NEXT_ROOTS),next_scope_current_classifications_added=0,next_scope_current_measured=False,next_scope_finite_consumer_live_epoch_proven=False)
 result.update(copy.deepcopy(EXECUTION_HISTORY));return result


def validate_terminal_record(value):
 fixed=terminal_constants();dynamic={'closeout_source','closeout_run','export_guard_test_log'}
 need(type(value)is dict and set(value)==set(fixed)|dynamic,'complete closed terminal recording fields')
 need(w.data.canonical({k:value[k]for k in fixed})==w.data.canonical(fixed),'exact terminal IDs, counters, failed history and unproved boundaries')
 need(type(value['closeout_source'])is str and re.fullmatch('[0-9a-f]{40}',value['closeout_source'])is not None,'full terminal source SHA')
 need(type(value['closeout_run'])is int and value['closeout_run']>0,'strict positive terminal run')
 need(w.delta.valid_identity(value['export_guard_test_log'])and value['export_guard_test_log']['size']>0,'complete exact new terminal suite log identity')
 return True


def require_measured_bindings():
 w.data.require_contract()
 need(type(CLOSEOUT_TESTS)is int and CLOSEOUT_TESTS>0,'actual complete new terminal test count required')
 need(INITIAL==w.BASE and SOURCE!=BASE and INITIAL not in(BASE,SOURCE),'distinct immutable original, accepted and recording sources')
 need(all(type(v)is str and re.fullmatch('[0-9a-f]{40}',v) for v in(BASE,SOURCE)),'independently verified measured source and actual recording commit required')
 need(all(type(v)is int and v>0 for v in(RUN,JOB,EXPECTED['unit_tests'],*ARCHIVE[:3]))and ARCHIVE[1]==RUN and type(ARCHIVE[3])is str and re.fullmatch('[0-9a-f]{64}',ARCHIVE[3]),'exact successful measurement job, archive whole identity and complete test count required')
 need(w.data.canonical({k:v for k,v in EXPECTED.items()if k not in('unit_tests','retained_sample_witnesses')})==w.data.canonical(w.EXPECTED)and type(EXPECTED['retained_sample_witnesses'])is int and EXPECTED['retained_sample_witnesses']==50,'exact independently frozen measurement expectations')
 w.validate_binding_map(MEASUREMENT_FILES,w.PROOF|{'record.json',*(n for n,_ in w.SNAPSHOTS)})
 need(w.delta.valid_identity(MEASUREMENT_DEVELOPMENT)and MEASUREMENT_DEVELOPMENT['size']>0,'whole accepted development identity required')
 validate_execution_history(EXECUTION_HISTORY)
 return True

def validate_development(value):
 need(type(value)is dict and set(value)=={'schema_version','status','review_scope','old_independent_final_review_retried','open_findings','source_bindings'}and type(value.get('schema_version'))is int and value['schema_version']==1,'closed independently reviewed terminal development schema')
 need(value.get('status')=='PASS_NEW_REGISTERED_UI_CLOSEOUT_SOURCE_REVIEW' and
      value.get('review_scope')=='new_registered_ui_closeout_sources_only' and
      value.get('old_independent_final_review_retried')is False and
      type(value.get('open_findings'))is list and value['open_findings']==[],
      'new terminal source review must have exactly zero unresolved findings')
 source=value.get('source_bindings')
 need(type(source)is dict and set(source)==CODE-{DEVELOPMENT} and bool(source),
      'complete terminal reviewed source set without self-attestation')
 w.validate_binding_map(source,CODE-{DEVELOPMENT})
 need(w.data.canonical(bindings(CODE-{DEVELOPMENT}))==w.data.canonical(source),'entire independently reviewed terminal source bytes unchanged')
 return True


def normalized_measurement_workflow(old):
 """固定した測定workflowの2箇所だけを変更し、他の全byteを保持する。"""
 need(type(old)is bytes,'whole original measurement workflow bytes required')
 trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 old_name=b'run-name: registered-ui-unreviewed-draft\n'
 new_name=b'run-name: registered-ui-minimum-text-consumers\n'
 need(old.startswith(b'name: pr16-dex-hof-registered-ui-batch\n'+old_name+b'on:\n'+trigger),'exact original measurement workflow header')
 need(old.count(trigger)==1 and old.count(b'  push:\n')==1 and old.count(old_name)==1 and old.count(b'run-name: ')==1 and b'  workflow_dispatch:\n'not in old,'unique original trigger and run-name; no hidden alternate start')
 return old.replace(trigger,b'  workflow_dispatch:\n',1).replace(old_name,new_name,1)

def validate_measurement_retirement(old,new,original_binding):
 need(w.delta.valid_identity(original_binding)and identity(old)==original_binding,'entire original measured workflow independently bound')
 need(type(new)is bytes and new==normalized_measurement_workflow(old),'only exact measurement trigger retirement and run-name correction permitted')
 return True

def measurement_retirement_guard():
 original_state=json.loads(git('show',BASE+':'+w.STATE))
 original_binding=original_state['source_bindings'][w.WF]
 old=git('show',BASE+':'+w.WF)
 validate_measurement_retirement(old,(ROOT/w.WF).read_bytes(),original_binding)
 return old


def source_guard():
 import pr16_learnset_runtime_record as g
 require_measured_bindings();current();measurement_retirement_guard();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard();validate_development(json.loads((ROOT/DEVELOPMENT).read_bytes()))


def validate_received_measurement(files):
 # 前測定receiptの全本文も閉じてから受信する。部分field比較だけで代用しない。
 w.validate_export(files,BASE)
 need(w.data.canonical({n:identity(b)for n,b in files.items()})==w.data.canonical(MEASUREMENT_FILES),'all eleven exact measured text bodies, not self-resealed receipts')
 return True


def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 require_measured_bindings();current();validate_development(json.loads((ROOT/DEVELOPMENT).read_bytes()));need(not OUT.exists()and not PUBLIC.exists(),'one terminal reference closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/w.STATE).read_bytes());protected=dict(state['source_bindings'])
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'every earlier bound original '+path)
 old=measurement_retirement_guard()
 need(identity(old)==protected[w.WF],'current protected measurement workflow equals immutable accepted original')
 history=validate_history_binding((ROOT/w.DEVELOPMENT).read_bytes())
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB));validate_successful_job(run,job)
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);archive,_=t.archive(ARCHIVE)
 with archive:
  names=set(w.PROOF)|{'record.json',*(name for name,_ in w.SNAPSHOTS)}
  need(set(archive.namelist())==names and len(archive.infolist())==len(names)and all(not i.is_dir()and i.external_attr>>28!=10 for i in archive.infolist()),'complete closed nonsymlink measured text archive')
  files={name:archive.read(name) for name in names}
  validate_received_measurement(files)
  receipt=json.loads(files['record.json']);measure=json.loads(files['measurement.json'])
  need(receipt['final_head']==BASE and receipt['source_head']==SOURCE and receipt['record_run']==RUN and measure['source_head']==SOURCE and measure['run_id']==RUN,'exact measured source/record lineage')
  for name,path in w.SNAPSHOTS:
   raw=archive.read(name);need(raw==(ROOT/path).read_bytes()==git('show',BASE+':'+path)and raw.endswith(b'\n'),'all committed original snapshot bytes and LF')
   binding=receipt['final_blobs'][path];need(identity(raw)=={k:binding[k]for k in('size','sha256')}and git('rev-parse',BASE+':'+path).decode().strip()==binding['git_blob_sha'],'whole exact original Git blob')
  for name in w.PROOF:need(archive.read(name)==(ROOT/w.EVIDENCE/name).read_bytes(),'all original reference measurements retained')
 cp=json.loads((ROOT/w.CP).read_bytes())
 need(cp['independent_final_source_review_completed']is False and measure['independent_final_source_review_completed']is False,'explicit independently unreviewed final scope remains disclosed')
 need(cp['new_registered_ui_batch_source_review_completed']is True and measure['new_registered_ui_batch_source_review_completed']is True,'new scoped source review remains explicitly accepted')
 need(all(type(cp[k])is int and type(measure[k])is int and cp[k]==v and measure[k]==v for k,v in EXPECTED.items())and cp['candidate']==measure['candidate']==w.data.CANDIDATE,'exact source and candidate counters')
 need(w.data.canonical(cp['source_bindings'])==w.data.canonical(measure['source_bindings'])and w.data.canonical(cp['inherited_bindings'])==w.data.canonical(measure['inherited_bindings']),'exact measured source identities')
 need(cp['development_validation']==measure['development_validation']==MEASUREMENT_DEVELOPMENT,'execution history bound to whole accepted development original')
 need(cp['delta_identity']==measure['delta_identity']and cp['reference_baseline']==w.delta.BASELINE,'one immutable baseline/delta identity')
 inherited=w.delta.parent(*[(ROOT/path).read_bytes()for path in w.delta.PARENT_INPUTS]);delta=w.delta.read_measured((ROOT/w.EVIDENCE/'reference-chain.json').read_bytes(),cp['delta_identity'],inherited);full=w.delta.materialize(inherited,delta)
 need(len(full['hits'])==874 and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all prior776 and remainingunknowns exactly retained')
 need(all(full[k]==inherited[k]for k in w.delta.INHERITED_NAMES),'all twenty-five full original delta families and witnesses retained')
 need(type(cp['current_owner_count'])is int and cp['current_owner_count']==115 and type(cp['current_rom_reconstructions'])is int and cp['current_rom_reconstructions']==1,'exact current owner and reconstruction counters');w.validate_closed_boundaries(cp);w.validate_closed_boundaries(measure)
 capacity_raw=(ROOT/w.EVIDENCE/'partial-space.json').read_bytes()
 need(identity(capacity_raw)==cp['capacity_identity']==measure['capacity_identity'] and json.loads(capacity_raw)==w.capacity_report(full,inherited),'whole new bounded-space report preserved')
 need(w.data.canonical(state['pending_runs'])==w.data.canonical([dict(run_id=RUN,tested_head=SOURCE,status='in_progress')]),'only exact original measurement pending');state['pending_runs']=[]
 tests=(ROOT/'.local/pr16-registered-ui-batch-closeout-tests.txt').read_bytes();need(tests.count(b' ... ok\n')==CLOSEOUT_TESTS and b'\nOK\n'in tests,'new complete-publication guards')
 result=dict(terminal_constants(),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),export_guard_test_log=identity(tests))
 need(all(w.data.canonical(result[k])==w.data.canonical(v)for k,v in history.items()),'terminal execution history uses actual retained original')
 validate_terminal_record(result)
 # 未完の次根は受入済み最小型と分離し、実終端の時だけ次工程へ載せる。
 goal=next_goal(state['next_action']['goal_ja']);state['bp']['next_step']=goal;state['next_action']['goal_ja']=goal
 for path in ('scripts/pr16_dex_hof_runtime_party.py','scripts/pr16_dex_hof_callback_party.py','scripts/pr16_dex_hof_callback_party_task.py','content/modernization/pr16_dex_hof_runtime_party_review.json','content/modernization/pr16_dex_hof_callback_party_review.json'):
  if path not in state['next_action']['read_paths']:state['next_action']['read_paths'].append(path)
 state['story_dex_owner']['runtime_integration']['hof_registered_ui_batch']['recording']=result;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all14_steps_success=True,measurement_checkpoint_fields_verified=True,failed_measurement_runs=history['failed_measurement_runs'],failed_closeout_runs=history['failed_closeout_runs'],failed_attempt_accepted=False,total_current_rom_reconstructions=history['total_current_rom_reconstructions'],closeout_additional_rom_reconstructions=0)
 state['source_bindings'].update(bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261006-DEX-HOF-REGISTERED-UI-BATCH / 登録UI consumer最小型batchの終端\n- Version: hof-registered-ui-batch-closeout\n- Status: STOPPED（新登録UI consumer必要最小型、残root/donor/本番controller未完）\n- Summary: run{RUN}/job{JOB}全14step成功。artifact{ARCHIVE[0]}全11text原本と固定MDJSON/CP/両ログ全byte/LF/Git blobを照合しpending解除。完了measurement起動条件をmanual-onlyへ戻しrun-nameをregistered-ui-minimum-text-consumersへ訂正。他の全byteは不変。新scopeの失敗measurement{history["failed_measurement_runs"]}件・失敗closeout{history["failed_closeout_runs"]}件は独立履歴に全保持。旧state失敗履歴は親原本に保存し新UI実績へ流用しない。\n- Files changed: closeout source/workflow/tests、measurement起動条件/run-nameの2箇所のみ、固定MDJSON、両append-onlyログ。\n- Verify: 原本{EXPECTED["unit_tests"]}tests、新分類{EXPECTED["newly_classified"]}、{EXPECTED["classified"]}分類/{EXPECTED["unclassified"]}未知。全776親行・25namespace157changes147witnessと残unknown全field、133曲/50assetを保持。新scope後は{result["total_namespaces"]}namespace/{result["total_changes"]}changes/{result["total_witnesses"]}witness。新公開guard{CLOSEOUT_TESTS}tests。最小型を自然play/普遍IRQ/全allocation lifetimeへ昇格しない。新scope累計ROM再構成{history["total_current_rom_reconstructions"]}、closeout追加ROM/ARM/native/旧suite0。旧独立最終source再レビュー拒否・未実施を保持。\n- Capacity: 全15118byte保護・安全0。間接参照/退役/owner移管未完。global511とsave804の上限1315は単一controller6528に不足。点target仮想空隙を安全容量へ昇格しない。\n- Publication: 全親原本参照保持、新delta{cp["delta_identity"]["size"]}byte。閉じた非空success set・whole size/SHA/LF・hidden/symlink/未知file拒否。\n- Boundary: 現0641/115owner/52saveowner/804byte/正式ROM/Save101不変。heap13352の保存退避53300跨ぎ禁止。全保存入口heap-ready/同期非再入/0804B85C退避前Free未接続。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/text原本のみ。ROM断片/rawhex/ROM/save/runtime/runner/credentials追加公開0。\n' 


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
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261006-DEX-HOF-REGISTERED-UI-BATCH VERIFY=PASS COMMIT='+receipt['final_head'])
def validate_export(files,head):
 expected={'closeout.json',*(name for name,_ in w.SNAPSHOTS)}
 need(set(files)==expected,'complete six-file terminal artifact, never a partial success')
 w.bounded_files(files);receipt=json.loads(files['closeout.json'])
 need(type(head)is str and re.fullmatch('[0-9a-f]{40}',head)is not None and receipt.get('final_head')==head and receipt.get('status')=='PASS_TERMINAL_EXACT_REGISTERED_UI_BATCH_RECORD','completed snapshot receipt and current commit')
 proofs=receipt.get('final_blobs',{});need(type(proofs)is dict and set(proofs)=={path for _,path in w.SNAPSHOTS},'all final snapshot receipts')
 for name,path in w.SNAPSHOTS:
  raw=files[name];binding=proofs[path]
  need(type(binding)is dict and set(binding)=={'size','sha256','git_blob_sha','trailing_newline'}and w.delta.valid_identity({k:binding[k]for k in('size','sha256')})and binding['size']>0,'closed strict terminal snapshot binding')
  need(binding.get('trailing_newline')is True and raw.endswith(b'\n')and identity(raw)=={k:binding[k]for k in('size','sha256')},'complete committed final snapshot identity')
  need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha'],'exact final Git blob content')
 state=json.loads(files['fixed-state.json'])
 need(type(state)is dict and type(state.get('pending_runs'))is list and state['pending_runs']==[],'terminal fixed state has exact empty pending list')
 recording=state
 for key in ('story_dex_owner','runtime_integration','hof_registered_ui_batch','recording'):
  need(type(recording)is dict and key in recording,'complete committed terminal provenance path');recording=recording[key]
 payload={key:value for key,value in receipt.items()if key not in('final_head','final_blobs')}
 validate_terminal_record(payload)
 need(identity(files['fixed-checkpoint.json'])==payload['checkpoint_identity'],'terminal snapshot retains whole immutable accepted checkpoint')
 need(type(recording)is dict and w.data.canonical(recording)==w.data.canonical(payload),'entire terminal receipt equals independently committed state recording')
 expected_receipt=dict(recording,final_head=head,final_blobs={path:dict(**identity(files[name]),git_blob_sha=hashlib.sha1(b'blob '+str(len(files[name])).encode()+b'\0'+files[name]).hexdigest(),trailing_newline=True)for name,path in w.SNAPSHOTS})
 need(w.data.canonical(receipt)==w.data.canonical(expected_receipt),'entire closed terminal receipt reconstructed independently')
 return True

def export():
 publication.output(PUBLIC,success='closeout.json',failure=None);files={}
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in{'closeout.json',*(n for n,_ in w.SNAPSHOTS)},'closed terminal flat text set');files[path.name]=path.read_bytes()
 head=git('rev-parse','HEAD').decode().strip();validate_export(files,head)
 receipt=json.loads(files['closeout.json'])
 for name,path in w.SNAPSHOTS:
  need(git('show',head+':'+path)==files[name],'terminal upload snapshot independent committed bytes')
  need(git('rev-parse',head+':'+path).decode().strip()==receipt['final_blobs'][path]['git_blob_sha'],'terminal upload snapshot independent Git blob')
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed terminal reference modes');globals()[sys.argv[1]]()
