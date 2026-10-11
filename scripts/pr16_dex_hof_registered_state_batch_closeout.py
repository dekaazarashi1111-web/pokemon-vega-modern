#!/usr/bin/env python3
"""有限参照deltaの終端確認。分類・ROM・host・nativeを再実行しない。"""
import copy,datetime,hashlib,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_registered_state_batch_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
current,bindings=w.prior.current,w.prior.bindings
INITIAL='b9be8c6c231df0aac1c5eb163b154a4ec8ff5787'
BASE='22a320d1c8234de23f7015f32221c0254efcd0ad';SOURCE='c9c961bfeee686066c625b5d20b928cfb0df5749';RUN=37455026681;JOB=112240418353
ARCHIVE=(11409007060,37455026681,1509183,'95bd086e26c96fd8f0b861b77db50e81aa1ec9e5fd23a4e7c64c7dcda354a463')
EXPECTED=dict(unit_tests=164,**w.EXPECTED,retained_sample_witnesses=50)
WF='.github/workflows/pr16-dex-hof-registered-state-batch-closeout.yml';SELF='scripts/pr16_dex_hof_registered_state_batch_closeout.py'
CLOSEOUT_TESTS=31 # 新終端suiteの実測値。旧suiteは再走しない。
DEVELOPMENT='content/modernization/pr16_dex_hof_registered_state_batch_closeout_validation.json'
CODE={w.WF,WF,SELF,'tests/test_pr16_dex_hof_registered_state_batch_closeout.py',DEVELOPMENT};OUT=ROOT/'.local/pr16-dex-hof-registered-state-batch-closeout';PUBLIC=ROOT/'public-dex-hof-registered-state-batch-closeout';ARTIFACT='pr16-dex-hof-registered-state-batch-closeout-text-only'

# 実測済み全11textの全byteを固定。探索用workや実行ログ本文は公開しない。
MEASUREMENT_FILES = {'fixed-checkpoint.json': {'size': 128229, 'sha256': '44e6becfd0611c0ac87b2877ef12935d13323d1bbb1a674b93881de7e5640064'}, 'fixed-run-log.md': {'size': 2123622, 'sha256': '8be8ac456bc848845214409310e43acf1a7c06c0a1845ca5364b08c398200572'}, 'fixed-resume.md': {'size': 140092, 'sha256': 'b52e0adc1c953cc279e3e34a47adc276952ecc4f788e1cfab3416e3a4fbeab11'}, 'fixed-state.json': {'size': 3636859, 'sha256': 'cd9b6f91d913ce8b4e2b21e065e9658591640ceb81b79edde71385f88558848c'}, 'fixed-version-log.md': {'size': 1735020, 'sha256': '84ea00d4df1fa1987a97cfcc93d1c3348968a1651d1e60721144abcff4bc4af3'}, 'partial-space.json': {'size': 47250, 'sha256': 'cd26bd2cb71d74363be82517c6207345fda58c7686d2fd773e033d87d545a925'}, 'measurement.json': {'size': 126553, 'sha256': '4c04fd86e67ca41f4862fb733c306b7f6e4a504622d159d357abdad272eb132d'}, 'record.json': {'size': 3020, 'sha256': 'fcb15d003c7c7adfe7cd8dbcf5d730a5f28c37a10fcaa4a7654e245773eba658'}, 'reference-chain.json': {'size': 135004, 'sha256': 'fc71bbca392a2894e819598836b57db02eae2700862b3cd200a5e47cac5e7b4a'}, 'registered-state-batch-tests.txt': {'size': 24972, 'sha256': '77b6c3a32b8062275ab476f2d87d3557664140217a03d13a6fb276d694d10bc2'}, 'unknown-frontier.json': {'size': 43013, 'sha256': 'd9be15f5872c8b720f8d3dd8130de403d00133bff66b5d5cde85d6ab057b4825'}}
MEASUREMENT_DEVELOPMENT = {'size': 6014, 'sha256': 'bd960c50496a87905724ca915c252328b911fb98c4738e35eb7be89cb5924a10'}
FIXTURE_CORRECTION = {'initial_source': 'dcc368dffa3ddb83220ef7967b85e6a2e69f12d5', 'failed_run': 37453822147, 'failed_job': 112236454951, 'failed_test': 'test_pr16_dex_hof_dancer_roots.DancerTests.test_56_source_only_unbound_rom_fails_closed', 'failed_attempt_accepted': False, 'failed_attempt_artifacts': 0, 'current_reconstructions_in_failed_attempt': 1, 'native_processes': 0, 'corrected_test_only': True, 'new_local_targeted_checks': 2, 'new_current_actions_required': True, 'reason_ja': '疎fixture固有の拒否条件を注入current全文から分離し、独立source生成疎fixtureで検査する。consumer本体と旧受入は不変。'}
FAILED_CLOSEOUT = dict(source_head='e1071ce7bab8a8f111999121f4a396b08b153679',run=37457248101,job=112247753034,
 status='SOURCE_GUARD_DIAGNOSTIC_NOT_ACCEPTED',source_guard_failed=True,classification_accepted=False,
 current_rom_reconstructions=0,arm_compiles=0,native_processes=0,new_closeout_suite_tests_executed=0,
 recorded=False,pushes=0,artifacts=0)
FAILED_CLOSEOUT_BOOTSTRAP = dict(source_head='431a16d2cd01938839e5d15b7c08f08159237a8e',run=37458617710,job=112252265422,
 status='MODULE_LOAD_DIAGNOSTIC_NOT_ACCEPTED',source_guard_passed=True,private_guard_passed=True,module_load_failed=True,classification_accepted=False,
 module_load_cause_source='same_source_workflow_command_local_reproduction_not_API_error_text',api_error_text_retrieved=False,
 current_rom_reconstructions=0,arm_compiles=0,native_processes=0,new_closeout_suite_tests_planned=31,new_closeout_suite_tests_executed=0,
 recorded=False,pushes=0,artifacts=0)
NEXT_ROOTS = ('0914100D','09143266','09143415')
NEXT_GOAL_PREFIX = ('残98の次scope候補は0914100Dのspecial057→Frontier task/main callback→CurrentStreak/MaxStreak、および09143266/09143415のChooseMove公開wrapper→effect dispatch→文字境界。'
 '公開固定sourceと旧06c5の有限静的観測だけで、現0641の正式分類追加0。実consumer全読取・future-live/非live消去・同epochの合成と変異/reseal反証は未完。'
 '受入済みDancer/Money2件とは別scopeで新根から限定証明し、保存境界を含む本番接続条件を省略しない。')


def validate_fixture_correction(raw):
 need(identity(raw)==MEASUREMENT_DEVELOPMENT,'entire measured development fixture-correction original unchanged')
 value=json.loads(raw)
 need(w.data.canonical(value.get('fixture_correction'))==w.data.canonical(FIXTURE_CORRECTION),'complete immutable failed-attempt correction contract')
 return dict(source_head=FIXTURE_CORRECTION['initial_source'],run=FIXTURE_CORRECTION['failed_run'],job=FIXTURE_CORRECTION['failed_job'],
  status='DIAGNOSTIC_NOT_ACCEPTED',failed_test=FIXTURE_CORRECTION['failed_test'],artifacts=0,
  current_rom_reconstructions=1,native_processes=0,recorded=False,classification_accepted=False,corrected_test_only=True,
  development_validation=copy.deepcopy(MEASUREMENT_DEVELOPMENT))


def next_goal(original):
 need(original==w.data.NEXT_GOAL,'exact prior unproved runtime and save boundaries retained')
 return NEXT_GOAL_PREFIX+original


def execution_history(failed):
 return dict(failed_attempt=failed,failed_closeout_attempts=[copy.deepcopy(FAILED_CLOSEOUT),copy.deepcopy(FAILED_CLOSEOUT_BOOTSTRAP)],failed_closeout_runs=2,failed_closeout_current_rom_reconstructions=0,failed_current_rom_reconstructions=1,accepted_current_rom_reconstructions=1,
  total_current_rom_reconstructions=2,accepted_measurement_runs=1,failed_measurement_runs=1,
  closeout_additional_rom_reconstructions=0,closeout_additional_arm_compiles=0,closeout_additional_native_processes=0,
  closeout_old_suite_runs=0,failed_attempt_promoted_to_success=False)


def validate_successful_job(run,job):
 need(type(run)is dict and type(job)is dict,'complete successful Actions metadata')
 need(type(run.get('id'))is int and run.get('id')==RUN and run.get('head_sha')==SOURCE and run.get('status')=='completed'and run.get('conclusion')=='success'and type(run.get('run_attempt'))is int and run['run_attempt']==1,'exact successful source/run/attempt')
 need(type(job.get('id'))is int and type(job.get('run_id'))is int and type(job.get('run_attempt'))is int and job['run_attempt']==1 and job.get('id')==JOB and job.get('run_id')==RUN and job.get('head_sha')==SOURCE and job.get('status')=='completed'and job.get('conclusion')=='success','exact completed accepted job identity')
 steps=job.get('steps');need(type(steps)is list and len(steps)==14 and all(type(s)is dict and s.get('conclusion')=='success'and s.get('status')=='completed'for s in steps),'all fourteen accepted measurement steps completed successfully')
 return True


def terminal_constants():
 # 公開するのは固定IDs/全byte identity/counter/境界のみ。ログ本文は含めない。
 failed=dict(source_head=FIXTURE_CORRECTION['initial_source'],run=FIXTURE_CORRECTION['failed_run'],job=FIXTURE_CORRECTION['failed_job'],
  status='DIAGNOSTIC_NOT_ACCEPTED',failed_test=FIXTURE_CORRECTION['failed_test'],artifacts=0,
  current_rom_reconstructions=1,native_processes=0,recorded=False,classification_accepted=False,corrected_test_only=True,
  development_validation=copy.deepcopy(MEASUREMENT_DEVELOPMENT))
 result=dict(status='PASS_TERMINAL_EXACT_REGISTERED_STATE_BATCH_RECORD',source_head=SOURCE,record_head=BASE,run=RUN,job=JOB,
  all14_steps_success=True,archive=list(ARCHIVE),all5_snapshots_full_bytes_and_lf_verified=True,checkpoint=w.CP,
  checkpoint_identity=copy.deepcopy(MEASUREMENT_FILES['fixed-checkpoint.json']),**EXPECTED,
  delta_identity=copy.deepcopy(MEASUREMENT_FILES['reference-chain.json']),baseline_identity=copy.deepcopy(w.delta.BASELINE_ID),
  parent_identity=copy.deepcopy(w.delta.PARENT_ID),earlier_identity=copy.deepcopy(w.delta.EARLIER_ID),capacity_identity=copy.deepcopy(MEASUREMENT_FILES['partial-space.json']),
  old774_accepted_and_all874_identities_retained=True,all_twenty_four_old_delta_families_preserved=True,
  independent_final_source_review_completed=False,tests_rerun=0,new_export_guard_tests=CLOSEOUT_TESTS,
  arm_compiles=0,native_processes=0,current_rom_reconstructions=0,candidate=copy.deepcopy(w.data.CANDIDATE),candidate_changed=False,donor_leased=False,formal_rom_changed=False,formal_save_changed=False,
  initial_head=INITIAL,minimum_new_code_bytes=12,total_namespaces=25,total_changes=157,total_witnesses=147,
  new_registered_state_closeout_source_review_completed=True,old_independent_final_review_retried=False,
  natural_full_play_proven=False,universal_irq_or_heap_lifetime_proven=False,indirect_reference_completeness_claimed=False,retirement_proven=False,owner_transfer_proven=False,
  controller_runtime_wired=False,donor_safe_bytes=0,protected_egg_bytes=15118,controller_measured_bytes=6528,heap_bytes=13352,stock_save_evacuation_bytes=53300,
  current_owner_count=115,current_save_owner_count=52,current_save_free_bytes=804,
  next_scope_candidates=list(NEXT_ROOTS),next_scope_observation='HISTORICAL_06C5_FINITE_STATIC_ONLY',next_scope_current_classifications_added=0,next_scope_current_measured=False,next_scope_finite_consumer_live_epoch_proven=False)
 result.update(execution_history(failed));return result


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
 need(INITIAL==w.BASE and SOURCE!=BASE and FIXTURE_CORRECTION['initial_source']not in(BASE,SOURCE),'distinct immutable original, failed, accepted and recording sources')
 need(all(type(v)is str and re.fullmatch('[0-9a-f]{40}',v) for v in (BASE,SOURCE)),
      'independently verified measured source and actual recording commit required')
 need(all(type(v)is int and v>0 for v in (RUN,JOB,EXPECTED['unit_tests'],*ARCHIVE[:3])) and
      ARCHIVE[1]==RUN and type(ARCHIVE[3])is str and re.fullmatch('[0-9a-f]{64}',ARCHIVE[3]),
      'exact successful measurement job, archive whole identity and complete test count required')
 return True

def validate_development(value):
 need(type(value)is dict and set(value)=={'schema_version','status','review_scope','old_independent_final_review_retried','open_findings','source_bindings'}and type(value.get('schema_version'))is int and value['schema_version']==1,'closed independently reviewed terminal development schema')
 need(value.get('status')=='PASS_NEW_REGISTERED_STATE_CLOSEOUT_SOURCE_REVIEW' and
      value.get('review_scope')=='new_registered_state_closeout_sources_only' and
      value.get('old_independent_final_review_retried')is False and
      type(value.get('open_findings'))is list and value['open_findings']==[],
      'new terminal source review must have exactly zero unresolved findings')
 source=value.get('source_bindings')
 need(type(source)is dict and set(source)==CODE-{DEVELOPMENT} and bool(source),
      'complete terminal reviewed source set without self-attestation')
 w.validate_binding_map(source,CODE-{DEVELOPMENT})
 need(w.data.canonical(bindings(CODE-{DEVELOPMENT}))==w.data.canonical(source),'entire independently reviewed terminal source bytes unchanged')
 return True


def source_guard():
 import pr16_learnset_runtime_record as g
 require_measured_bindings();current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard();validate_development(json.loads((ROOT/DEVELOPMENT).read_bytes()))


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
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'only completed measurement trigger retired')
 failed=validate_fixture_correction((ROOT/w.DEVELOPMENT).read_bytes())
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
 need(cp['new_registered_state_batch_source_review_completed']is True and measure['new_registered_state_batch_source_review_completed']is True,'new scoped source review remains explicitly accepted')
 need(all(type(cp[k])is int and type(measure[k])is int and cp[k]==v and measure[k]==v for k,v in EXPECTED.items())and cp['candidate']==measure['candidate']==w.data.CANDIDATE,'exact source and candidate counters')
 need(w.data.canonical(cp['source_bindings'])==w.data.canonical(measure['source_bindings'])and w.data.canonical(cp['inherited_bindings'])==w.data.canonical(measure['inherited_bindings']),'exact measured source identities')
 need(cp['development_validation']==measure['development_validation']==MEASUREMENT_DEVELOPMENT,'failed diagnostic bound to whole accepted development original')
 need(cp['delta_identity']==measure['delta_identity']and cp['reference_baseline']==w.delta.BASELINE,'one immutable baseline/delta identity')
 inherited=w.delta.parent(*[(ROOT/path).read_bytes()for path in w.delta.PARENT_INPUTS]);delta=w.delta.read_measured((ROOT/w.EVIDENCE/'reference-chain.json').read_bytes(),cp['delta_identity'],inherited);full=w.delta.materialize(inherited,delta)
 need(len(full['hits'])==874 and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all prior774 and remainingunknowns exactly retained')
 need(all(full[k]==inherited[k]for k in w.delta.INHERITED_NAMES),'all twenty-four full original delta families and witnesses retained')
 need(type(cp['current_owner_count'])is int and cp['current_owner_count']==115 and type(cp['current_rom_reconstructions'])is int and cp['current_rom_reconstructions']==1,'exact current owner and reconstruction counters');w.validate_closed_boundaries(cp);w.validate_closed_boundaries(measure)
 capacity_raw=(ROOT/w.EVIDENCE/'partial-space.json').read_bytes()
 need(identity(capacity_raw)==cp['capacity_identity']==measure['capacity_identity'] and json.loads(capacity_raw)==w.capacity_report(full,inherited),'whole new bounded-space report preserved')
 need(w.data.canonical(state['pending_runs'])==w.data.canonical([dict(run_id=RUN,tested_head=SOURCE,status='in_progress')]),'only exact original measurement pending');state['pending_runs']=[]
 tests=(ROOT/'.local/pr16-registered-state-batch-closeout-tests.txt').read_bytes();need(tests.count(b' ... ok\n')==CLOSEOUT_TESTS and b'\nOK\n'in tests,'new complete-publication guards')
 result=dict(terminal_constants(),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),export_guard_test_log=identity(tests))
 need(w.data.canonical(result['failed_attempt'])==w.data.canonical(failed),'terminal failure receipt uses actual retained original')
 validate_terminal_record(result)
 # 未完の次根は受入済み最小型と分離し、実終端の時だけ次工程へ載せる。
 goal=next_goal(state['next_action']['goal_ja']);state['bp']['next_step']=goal;state['next_action']['goal_ja']=goal
 for path in ('scripts/pr16_dex_hof_runtime_party.py','scripts/pr16_dex_hof_callback_party.py','scripts/pr16_dex_hof_callback_party_task.py','content/modernization/pr16_dex_hof_runtime_party_review.json','content/modernization/pr16_dex_hof_callback_party_review.json'):
  if path not in state['next_action']['read_paths']:state['next_action']['read_paths'].append(path)
 state['story_dex_owner']['runtime_integration']['hof_registered_state_batch']['recording']=result;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all14_steps_success=True,measurement_checkpoint_fields_verified=True,failed_measurement_run=failed['run'],failed_measurement_job=failed['job'],failed_attempt_accepted=False,total_current_rom_reconstructions=2,closeout_additional_rom_reconstructions=0)
 state['source_bindings'].update(bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261006-DEX-HOF-REGISTERED-STATE-BATCH / 登録state consumer最小型batchの終端\n- Version: hof-registered-state-batch-closeout\n- Status: STOPPED（新登録state consumer必要最小型を受入、既event/fieldguard未知保持、残root/donor/本番controller未完）\n- Summary: run{RUN}/job{JOB}全14step成功。artifact{ARCHIVE[0]}全11text原本と固定MDJSON/CP/両ログ全byte/LF/Git blobを照合しpending解除。完了measurement起動条件のみmanual-onlyへ。初回run{failed["run"]}/job{failed["job"]}のfixture拒否failureは不受入・記録なし・Artifacts0の診断として保持し、testだけを修正した受入runと混同しない。初回closeout source={FAILED_CLOSEOUT["source_head"]}/run{FAILED_CLOSEOUT["run"]}/job{FAILED_CLOSEOUT["job"]}はsource guard拒否で停止し、ROM/ARM/native/新終端tests/記録/push0・Artifacts0の未受入診断として別保持。2回目closeout source={FAILED_CLOSEOUT_BOOTSTRAP["source_head"]}/run{FAILED_CLOSEOUT_BOOTSTRAP["run"]}/job{FAILED_CLOSEOUT_BOOTSTRAP["job"]}のAPI観測はsource/private guard通過→新test command failure・後段skip・Artifacts0。module-load原因と予定31tests本体未実行は同source/同workflow command/PYTHONPATHなしのローカル再現由来であり、API error本文は未取得。ROM/ARM/native/記録/push0。失敗2件を成功へ読み替えず保持。\n- Files changed: closeout source/workflow/tests、measurement起動条件、固定MDJSON、両append-onlyログ。\n- Verify: 原本{EXPECTED["unit_tests"]}tests、新分類{EXPECTED["newly_classified"]}、{EXPECTED["classified"]}分類/{EXPECTED["unclassified"]}未知（owner内0）を再利用。全774親行・全二十四段155changes/145witnessと残unknown全field、133曲/50assetを保持。新scope後は25namespace157changes147witness。新公開guard{CLOSEOUT_TESTS}tests PASS。新登録state consumerの独立source symbol・実hook/state/caller・完全prologueとopaque ABI/future-live条件の必要最小型、既event/field guardは原本保持をsource-only確認。自然play到達/普遍IRQ/全allocation lifetimeは受入に含めない。初回失敗の現ROM再構成1＋受入1＝計2、closeout追加ROM/ARM/native/旧164suite0。旧独立最終sourceレビュー拒否・未実施を保持し再試行0。\n- Capacity: 未知の最大アクセス範囲が未証明なら全15118byte保護。間接参照/退役/owner移管も未完でsafe0byte。global511＋save804の上限1315は単一controller6528に不足5213。点targetの仮想空隙は安全容量ではなく、今後の追加分類で変わり得る。実配線時の追加容量も未確定。\n- Publication: 全親は参照保持、新delta{cp["delta_identity"]["size"]}byteとpartial-space独立envelope。閉じた非空success set・whole size/SHA/LF・hidden/symlink/未知file拒否。\n- Boundary: 現0641/115owner/52saveowner/804byte/正式ROM/Save101不変。heap13352の保存退避53300跨ぎ禁止。一般CI既知QOL不一致/action_required job0/Stage79cacheは別扱い。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/text原本のみ。ROM断片/rawhex/ROM/save/runtime/runner/credentials追加公開0。\n'


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
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261006-DEX-HOF-REGISTERED-STATE-BATCH VERIFY=PASS COMMIT='+receipt['final_head'])
def validate_export(files,head):
 expected={'closeout.json',*(name for name,_ in w.SNAPSHOTS)}
 need(set(files)==expected,'complete six-file terminal artifact, never a partial success')
 w.bounded_files(files);receipt=json.loads(files['closeout.json'])
 need(type(head)is str and re.fullmatch('[0-9a-f]{40}',head)is not None and receipt.get('final_head')==head and receipt.get('status')=='PASS_TERMINAL_EXACT_REGISTERED_STATE_BATCH_RECORD','completed snapshot receipt and current commit')
 proofs=receipt.get('final_blobs',{});need(type(proofs)is dict and set(proofs)=={path for _,path in w.SNAPSHOTS},'all final snapshot receipts')
 for name,path in w.SNAPSHOTS:
  raw=files[name];binding=proofs[path]
  need(type(binding)is dict and set(binding)=={'size','sha256','git_blob_sha','trailing_newline'}and w.delta.valid_identity({k:binding[k]for k in('size','sha256')})and binding['size']>0,'closed strict terminal snapshot binding')
  need(binding.get('trailing_newline')is True and raw.endswith(b'\n')and identity(raw)=={k:binding[k]for k in('size','sha256')},'complete committed final snapshot identity')
  need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha'],'exact final Git blob content')
 state=json.loads(files['fixed-state.json'])
 need(type(state)is dict and type(state.get('pending_runs'))is list and state['pending_runs']==[],'terminal fixed state has exact empty pending list')
 recording=state
 for key in ('story_dex_owner','runtime_integration','hof_registered_state_batch','recording'):
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
