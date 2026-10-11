"""新UI終端receipt全本文・実committed recordingへの結合だけを検査。"""
import copy,inspect,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=next(p for p in (ROOT,*ROOT.parents)if (p/'scripts/pr16_dex_hof_donor.py').is_file())
sys.path[:0]=list(dict.fromkeys([str(ROOT/'scripts'),str(SOURCE_ROOT/'scripts'),str(ROOT/'tests'),str(SOURCE_ROOT/'tests')]))
import guard_private_files
import pr16_dex_hof_registered_ui_batch_closeout as m
from test_pr16_dex_hof_registered_ui_batch_actions import raw,git_blob,measurement_fixture,committed_git
from contextlib import contextmanager,ExitStack
from test_pr16_dex_hof_registered_ui_batch import resolved_fixture,SYNTHETIC_EXPECTED

def history_fixture():
 return dict(failed_measurement_attempts=[],failed_closeout_attempts=[],failed_current_rom_reconstructions=0,accepted_current_rom_reconstructions=1,total_current_rom_reconstructions=1,accepted_measurement_runs=1,failed_measurement_runs=0,failed_closeout_runs=0,failed_closeout_current_rom_reconstructions=0,closeout_additional_rom_reconstructions=0,closeout_additional_arm_compiles=0,closeout_additional_native_processes=0,closeout_old_suite_runs=0,failed_attempt_promoted_to_success=False)
@contextmanager
def measured_fixture():
 """closeout schema専用合成値。production定数へ代入しない。"""
 with ExitStack()as stack:
  stack.enter_context(resolved_fixture())
  stack.enter_context(patch.object(m.w,'EXPECTED',SYNTHETIC_EXPECTED))
  values=dict(BASE='a'*40,SOURCE='b'*40,RUN=123,JOB=456,ARCHIVE=(789,123,900,'f'*64),EXPECTED=dict(unit_tests=1,**SYNTHETIC_EXPECTED,retained_sample_witnesses=50),CLOSEOUT_TESTS=38,MEASUREMENT_FILES={n:m.identity(b'{}\n')for n in m.w.PROOF|{'record.json',*(n for n,_ in m.w.SNAPSHOTS)}},MEASUREMENT_DEVELOPMENT=m.identity(b'{}\n'),EXECUTION_HISTORY=history_fixture())
  for key,value in values.items():stack.enter_context(patch.object(m,key,value))
  yield

def enter_measured(test):
 context=measured_fixture();context.__enter__();test.addCleanup(context.__exit__,None,None,None)
class UiCloseoutTests(unittest.TestCase):
 def setUp(self):
  enter_measured(self)
  self.head='a'*40;self.payload=dict(m.terminal_constants(),closeout_source='d'*40,closeout_run=1234,export_guard_test_log={'size':17,'sha256':'e'*64})
  self.files={n:b'{}\n'if n.endswith('.json')else b'synthetic-only\n'for n,_ in m.w.SNAPSHOTS}
  self.files['fixed-checkpoint.json']=b'{}\n'
  self.files['fixed-state.json']=raw(dict(pending_runs=[],story_dex_owner=dict(runtime_integration=dict(hof_registered_ui_batch=dict(recording=self.payload)))))
  self.receipt=dict(self.payload,final_head=self.head,final_blobs={p:dict(**m.identity(self.files[n]),git_blob_sha=git_blob(self.files[n]),trailing_newline=True)for n,p in m.w.SNAPSHOTS});self.files['closeout.json']=raw(self.receipt)
 def test_producer_guard_uploadpath_agree(self):self.assertEqual(m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF)['directory'],'public-dex-hof-registered-ui-batch-closeout')
 def test_pending_measured_identity_has_no_old_run_fallback(self):
  for key,value in(('BASE',None),('SOURCE','old'),('RUN',None),('JOB',0),('ARCHIVE',(1,2,3,None)),('CLOSEOUT_TESTS',None)):
   with patch.object(m.w.data,'require_contract'),patch.object(m,key,value),self.subTest(key=key),self.assertRaises(ValueError):m.require_measured_bindings()
 def test_complete_terminal_receipt_matches_recording(self):self.assertTrue(m.validate_export(self.files,self.head))
 def test_missing_every_file_and_unknown_extra_rejected(self):
  for n in self.files:
   files=dict(self.files);files.pop(n)
   with self.subTest(name=n),self.assertRaises(ValueError):m.validate_export(files,self.head)
  files=dict(self.files,**{'extra.json':b'{}\n'})
  with self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_receipt_whole_body_mutation_and_extra_field_rejected(self):
  for key,value in(('run',999),('native_processes',True),('independent_final_source_review_completed',True),('extra','injected')):
   receipt=dict(self.receipt);receipt[key]=value;files=dict(self.files);files['closeout.json']=raw(receipt)
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_fixed_recording_omission_or_pending_is_rejected_even_resealed(self):
  for state in({},dict(pending_runs=[{'run':1}],story_dex_owner=dict(runtime_integration=dict(hof_registered_ui_batch=dict(recording=self.payload)))),dict(pending_runs=[],story_dex_owner=dict(runtime_integration=dict(hof_registered_ui_batch={})))):
   files=dict(self.files);files['fixed-state.json']=raw(state);receipt=copy.deepcopy(self.receipt);b=files['fixed-state.json'];receipt['final_blobs'][m.w.STATE]=dict(**m.identity(b),git_blob_sha=git_blob(b),trailing_newline=True);files['closeout.json']=raw(receipt)
   with self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_terminal_self_reseal_cannot_replace_committed_recording(self):
  files=dict(self.files);receipt=copy.deepcopy(self.receipt);receipt['closeout_run']=999;state=json.loads(files['fixed-state.json']);state['story_dex_owner']['runtime_integration']['hof_registered_ui_batch']['recording']['closeout_run']=999;files['fixed-state.json']=raw(state);b=files['fixed-state.json'];receipt['final_blobs'][m.w.STATE]=dict(**m.identity(b),git_blob_sha=git_blob(b),trailing_newline=True);files['closeout.json']=raw(receipt);self.assertTrue(m.validate_export(files,self.head))
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)
   for n,b in files.items():(p/n).write_bytes(b)
   with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(self.head,self.files,proof=False)),self.assertRaises(ValueError):m.export()
 def test_whole_actual_committed_terminal_export(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)
   for n,b in self.files.items():(p/n).write_bytes(b)
   with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(self.head,self.files,proof=False)):m.export()
 def test_received_measurement_checks_whole_receipt_body(self):
  head,files,receipt=measurement_fixture()
  pinned={n:m.identity(b)for n,b in files.items()}
  with patch.object(m,'BASE',head),patch.object(m,'MEASUREMENT_FILES',pinned):self.assertTrue(m.validate_received_measurement(files))
  receipt['native_processes']=1;files['record.json']=raw(receipt)
  with patch.object(m,'BASE',head),self.assertRaises(ValueError):m.validate_received_measurement(files)
 def test_terminal_source_review_missing_open_finding_never_passes(self):
  good=dict(schema_version=1,status='PASS_NEW_REGISTERED_UI_CLOSEOUT_SOURCE_REVIEW',review_scope='new_registered_ui_closeout_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings={p:{'size':1,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}})
  with patch.object(m,'bindings',return_value=good['source_bindings']):self.assertTrue(m.validate_development(good))
  for key,value in(('schema_version',True),('schema_version',1.0),('extra','private'),('open_findings',None),('open_findings',False),('open_findings',['unresolved']),('source_bindings',{}),('old_independent_final_review_retried',True)):
   changed=copy.deepcopy(good);changed[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_development(changed)

class UiCloseoutStrictSchemaTests(unittest.TestCase):
 setUp=UiCloseoutTests.setUp
 def test_final_snapshot_float_bool_or_extra_binding_rejected(self):
  for mutation in('float','bool','extra'):
   receipt=copy.deepcopy(self.receipt);binding=receipt['final_blobs'][m.w.STATE]
   if mutation=='extra':binding['extra']='injected'
   else:binding['size']=float(binding['size'])if mutation=='float'else True
   files=dict(self.files);files['closeout.json']=raw(receipt)
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_terminal_review_source_identity_has_no_float_alias(self):
  bindings={p:{'size':17,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}}
  value=dict(schema_version=1,status='PASS_NEW_REGISTERED_UI_CLOSEOUT_SOURCE_REVIEW',review_scope='new_registered_ui_closeout_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings=copy.deepcopy(bindings));value['source_bindings'][next(iter(bindings))]['size']=17.0
  with patch.object(m,'bindings',return_value=bindings),self.assertRaises(ValueError):m.validate_development(value)

class UiCloseoutMeasuredContractTests(unittest.TestCase):
 def setUp(self):enter_measured(self)
 def payload(self):return dict(m.terminal_constants(),closeout_source='d'*40,closeout_run=1234,export_guard_test_log={'size':17,'sha256':'e'*64})
 def test_actual_bindings_are_complete_and_distinct(self):
  self.assertTrue(m.require_measured_bindings());self.assertEqual(m.INITIAL,'c2059ee805d978575b319e7a113b3edf0a676f1e')
  self.assertEqual(len({m.INITIAL,m.BASE,m.SOURCE}),3)
  self.assertEqual(set(m.MEASUREMENT_FILES),m.w.PROOF|{'record.json',*(n for n,_ in m.w.SNAPSHOTS)})
  with patch.object(m,'EXECUTION_HISTORY',None),self.assertRaises(ValueError):m.require_measured_bindings()
 def test_terminal_counter_fixed_to_only_new_complete_suite(self):
  suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);self.assertEqual(suite.countTestCases(),38)
  self.assertEqual(m.CLOSEOUT_TESTS,suite.countTestCases());self.assertEqual(m.EXPECTED['unit_tests'],1)
 def test_closed_terminal_record(self):self.assertTrue(m.validate_terminal_record(self.payload()))
 def test_every_missing_or_extra_terminal_field_rejected(self):
  for key in self.payload():
   row=self.payload();row.pop(key)
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_terminal_record(row)
  row=self.payload();row['runner']='private'
  with self.assertRaises(ValueError):m.validate_terminal_record(row)
 def test_all_fixed_fields_reject_mutation_and_numeric_aliases(self):
  for key,value in m.terminal_constants().items():
   row=self.payload();row[key]=not value if type(value)is bool else float(value)if type(value)is int else None
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_terminal_record(row)
 def test_dynamic_run_source_log_are_closed_strict_types(self):
  for key,value in(('closeout_run',True),('closeout_run',1234.0),('closeout_run',0),('closeout_source','short'),('closeout_source','G'*40),('export_guard_test_log',{'size':17.0,'sha256':'e'*64}),('export_guard_test_log',{'size':17,'sha256':'e'*64,'extra':1})):
   row=self.payload();row[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.validate_terminal_record(row)
 def test_failed_history_is_bound_to_entire_original_development(self):
  self.assertEqual(m.validate_history_binding(b'{}\n'),history_fixture())
  with self.assertRaises(ValueError):m.validate_history_binding(b'{}\n\n')
  with patch.object(m,'MEASUREMENT_DEVELOPMENT',None),self.assertRaises(ValueError):m.validate_history_binding(b'{}\n')
 def test_failed_correction_cannot_be_resealed_as_success(self):
  failed=dict(source_head='c'*40,run=222,job=333,status='DIAGNOSTIC_NOT_ACCEPTED',current_rom_reconstructions=1,native_processes=0,recorded=False,classification_accepted=False,artifacts=0)
  history=history_fixture();history.update(failed_measurement_attempts=[failed],failed_measurement_runs=1,failed_current_rom_reconstructions=1,total_current_rom_reconstructions=2)
  self.assertTrue(m.validate_execution_history(history))
  for key,value in(('classification_accepted',True),('recorded',True),('artifacts',1),('run',m.RUN),('source_head',m.SOURCE),('native_processes',0.0),('extra','injected')):
   changed=copy.deepcopy(history);changed['failed_measurement_attempts'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_execution_history(changed)
 def test_failed_and_accepted_rom_counts_are_not_closeout_work(self):
  value=self.payload()
  self.assertEqual(value['failed_current_rom_reconstructions']+value['accepted_current_rom_reconstructions'],value['total_current_rom_reconstructions'])
  self.assertEqual(value['total_current_rom_reconstructions'],1)
  for key in('current_rom_reconstructions','arm_compiles','native_processes','tests_rerun','closeout_additional_rom_reconstructions','closeout_additional_arm_compiles','closeout_additional_native_processes','closeout_old_suite_runs'):self.assertEqual(value[key],0)
  self.assertFalse(value['failed_attempt_promoted_to_success'])
 def test_exact_successful_job_and_all_steps(self):
  run=dict(id=m.RUN,head_sha=m.SOURCE,status='completed',conclusion='success',run_attempt=1)
  job=dict(id=m.JOB,run_id=m.RUN,head_sha=m.SOURCE,run_attempt=1,status='completed',conclusion='success',steps=[dict(status='completed',conclusion='success')for _ in range(14)])
  self.assertTrue(m.validate_successful_job(run,job))
  for scope,key,replacement in(('run','id',1),('run','id',float(m.RUN)),('run','run_attempt',True),('run','head_sha','c'*40),('run','conclusion','failure'),('job','id',1),('job','id',float(m.JOB)),('job','run_id',float(m.RUN)),('job','run_attempt',True),('job','run_attempt',2),('job','run_id',222),('job','steps',job['steps'][:-1]),('job','steps',[dict(status='completed',conclusion='failure')]+job['steps'][1:])):
   r,j=copy.deepcopy(run),copy.deepcopy(job);(r if scope=='run'else j)[key]=replacement
   with self.subTest(scope=scope,key=key),self.assertRaises(ValueError):m.validate_successful_job(r,j)
 def test_measurement_self_reseal_cannot_replace_pinned_eleven_texts(self):
  head,files,receipt=measurement_fixture();pinned={n:m.identity(b)for n,b in files.items()}
  files['registered-ui-batch-tests.txt']=b'different source-only text\n';receipt['precommit_publication_files']['registered-ui-batch-tests.txt']=m.identity(files['registered-ui-batch-tests.txt']);files['record.json']=raw(receipt)
  self.assertTrue(m.w.validate_export(files,head))
  with patch.object(m,'BASE',head),patch.object(m,'MEASUREMENT_FILES',pinned),self.assertRaises(ValueError):m.validate_received_measurement(files)
 def test_zero_next_roots_preserve_every_prior_runtime_boundary(self):
  goal=m.next_goal(m.w.data.NEXT_GOAL);self.assertTrue(goal.endswith(m.w.data.NEXT_GOAL));self.assertEqual(m.NEXT_ROOTS,())
  for token in('独立登録根は0件','083DDEE1/083DE02B/083DE6AB','受入候補へ数えず未知保持','固定JP symbol','生成crosswalk','両側text symbol/EOS込みextent','現配置の実literal/table cell','API','新ROM windowも正式分類も追加しない'):self.assertIn(token,goal)
  for token in('全S61E/MDX','writer/loader/Link','exact-source/no-main/INITIAL/全mode/早期31/species9bit','シオウ通常回復/保存/独立coldContinue','雑魚毎Saveなし','heap13352','53300','退避前Free','全保存入口heap-ready/同期非再入','単一controller6528'):
   self.assertIn(token,goal)
  with self.assertRaises(ValueError):m.next_goal('replacement omitting runtime gates')
 def test_new_candidates_cannot_be_counted_as_current_acceptance(self):
  value=self.payload();self.assertEqual(value['next_scope_candidates'],list(m.NEXT_ROOTS));self.assertEqual(value['classified'],SYNTHETIC_EXPECTED['classified']);self.assertEqual(value['unclassified'],SYNTHETIC_EXPECTED['unclassified'])
  self.assertEqual(value['next_scope_current_classifications_added'],0)
  for key in('next_scope_current_measured','next_scope_finite_consumer_live_epoch_proven','natural_full_play_proven','universal_irq_or_heap_lifetime_proven','indirect_reference_completeness_claimed','retirement_proven','owner_transfer_proven','controller_runtime_wired','independent_final_source_review_completed','old_independent_final_review_retried'):self.assertIs(value[key],False)
 def test_only_closeout_workflow_push_and_exact_measurement_retirement(self):
  closeout=(m.ROOT/m.WF).read_text();measured=(m.ROOT/m.w.WF).read_bytes()
  trigger='  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+m.WF+']\n'
  self.assertTrue(('  workflow_dispatch:\n'in closeout) != (trigger in closeout));self.assertEqual(closeout.count('  push:\n'),int(trigger in closeout))
  self.assertEqual(measured.count(b'  workflow_dispatch:\n'),1);self.assertNotIn(b'  push:\n',measured)
  source=inspect.getsource(m.close);self.assertIn('measurement_retirement_guard()',source)
  self.assertIn(b'run-name: registered-ui-minimum-text-consumers\n',measured)
  self.assertIn("python3 -B -m unittest discover -s tests -p 'test_pr16_dex_hof_registered_ui_batch_closeout.py'",closeout)
 def test_close_has_review_gate_and_no_reconstruction_or_old_suite(self):
  source=inspect.getsource(m.close);self.assertLess(source.index('validate_development('),source.index('t.api('));self.assertLess(source.index('validate_received_measurement(files)'),source.index("state['pending_runs']=[]"))
  self.assertIn("goal=next_goal(state['next_action']['goal_ja'])",source)
  for forbidden in('reconstruct(','subprocess','loadTestsFromModule','m.w.run(','t.restore('):self.assertNotIn(forbidden,source)
 def test_public_payload_excludes_log_body_and_private_paths(self):
  payload=raw(self.payload());self.assertEqual(guard_private_files.document_user_path_lines(payload),[])
  value=payload.decode()
  for forbidden in('runner_name','runner_group','private-failure','job-log','archive_member','userfile/','rawhex','GH_TOKEN','GITHUB_TOKEN'):
   self.assertNotIn(forbidden,value)
 def test_all_new_code_raw_passes_unchanged_private_path_checker(self):
  for path in sorted(m.CODE):
   with self.subTest(path=path):self.assertEqual(guard_private_files.document_user_path_lines((m.ROOT/path).read_bytes()),[])
 def test_failed_closeout_source_guard_has_zero_work(self):
  history=history_fixture();failed=dict(source_head='c'*40,run=222,job=333,status='DIAGNOSTIC_NOT_ACCEPTED',current_rom_reconstructions=0,native_processes=0,recorded=False,classification_accepted=False,artifacts=0)
  history.update(failed_closeout_attempts=[failed],failed_closeout_runs=1);self.assertTrue(m.validate_execution_history(history))
  for key,value in(('current_rom_reconstructions',1),('native_processes',1),('artifacts',1),('recorded',True),('classification_accepted',True)):
   changed=copy.deepcopy(history);changed['failed_closeout_attempts'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_execution_history(changed)
  for key in('failed_closeout_current_rom_reconstructions','closeout_additional_rom_reconstructions','closeout_additional_arm_compiles','closeout_additional_native_processes','closeout_old_suite_runs'):
   changed=copy.deepcopy(history);changed[key]=1
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_execution_history(changed)
 def test_export_rejects_hidden_symlink_directory_and_unknown_file(self):
  fixture=UiCloseoutTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
  for kind in('hidden','symlink','directory','extension'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory()as tmp:
    p=Path(tmp)
    for n,b in fixture.files.items():(p/n).write_bytes(b)
    if kind=='hidden':(p/'.hidden').write_bytes(b'x\n')
    elif kind=='symlink':(p/'linked.json').symlink_to(p/'closeout.json')
    elif kind=='directory':(p/'nested').mkdir()
    else:(p/'unknown.bin').write_bytes(b'x\n')
    with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(fixture.head,fixture.files,proof=False)),self.assertRaises(ValueError):m.export()

class UiCloseoutWorkflowRetirementTests(unittest.TestCase):
 def setUp(self):
  self.new=(m.ROOT/m.w.WF).read_bytes()
  self.trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+m.w.WF+']\n').encode()
  self.old=self.new.replace(b'  workflow_dispatch:\n',self.trigger).replace(b'run-name: registered-ui-minimum-text-consumers\n',b'run-name: registered-ui-unreviewed-draft\n')
  self.binding=m.identity(self.old)
 def test_exact_two_edits_preserve_entire_original_workflow(self):
  self.assertEqual(m.normalized_measurement_workflow(self.old),self.new)
  self.assertTrue(m.validate_measurement_retirement(self.old,self.new,self.binding))
  self.assertEqual(self.new.replace(b'  workflow_dispatch:\n',self.trigger).replace(b'run-name: registered-ui-minimum-text-consumers\n',b'run-name: registered-ui-unreviewed-draft\n'),self.old)
 def test_missing_duplicated_or_alternate_original_header_rejected(self):
  old_name=b'run-name: registered-ui-unreviewed-draft\n'
  for old in(self.old.decode(),self.old.replace(self.trigger,b''),self.old+self.trigger,self.old.replace(old_name,b''),self.old+old_name,self.old+b'run-name: other\n',self.old+b'  workflow_dispatch:\n',self.old.replace(b'on:\n',b'on: \n'),self.old+b'  push:\n'):
   with self.subTest(kind=type(old).__name__),self.assertRaises(ValueError):m.normalized_measurement_workflow(old)
 def test_every_unapproved_byte_change_in_retired_workflow_rejected(self):
  for offset in range(len(self.new)):
   changed=self.new[:offset]+bytes([self.new[offset]^1])+self.new[offset+1:]
   with self.subTest(offset=offset),self.assertRaises(ValueError):m.validate_measurement_retirement(self.old,changed,self.binding)
  for changed in(self.new+b'\n',self.new+b'# harmless-looking change\n',self.new[:-1]):
   with self.assertRaises(ValueError):m.validate_measurement_retirement(self.old,changed,self.binding)
 def test_both_edits_mandatory_no_partial_or_extra_normalization(self):
  for changed in(self.old,self.old.replace(self.trigger,b'  workflow_dispatch:\n'),self.old.replace(b'run-name: registered-ui-unreviewed-draft\n',b'run-name: registered-ui-minimum-text-consumers\n'),self.new.replace(b'\n',b'\r\n'),self.new.decode()):
   with self.assertRaises(ValueError):m.validate_measurement_retirement(self.old,changed,self.binding)
 def test_original_workflow_cannot_be_resealed_with_stale_binding(self):
  changed=self.old.replace(b'timeout-minutes: 30',b'timeout-minutes: 31')
  self.assertNotEqual(changed,self.old)
  with self.assertRaises(ValueError):m.validate_measurement_retirement(changed,m.normalized_measurement_workflow(changed),self.binding)
  for binding in(None,dict(self.binding,size=float(self.binding['size'])),dict(self.binding,extra=1),dict(self.binding,sha256='f'*64)):
   with self.assertRaises(ValueError):m.validate_measurement_retirement(self.old,self.new,binding)
 def test_guard_reads_full_original_git_workflow_and_bound_state(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);path=root/m.w.WF;path.parent.mkdir(parents=True);path.write_bytes(self.new)
   def immutable(*args):
    if args==('show',m.BASE+':'+m.w.STATE):return raw(dict(source_bindings={m.w.WF:self.binding}))
    if args==('show',m.BASE+':'+m.w.WF):return self.old
    raise AssertionError(args)
   with patch.object(m,'BASE','a'*40),patch.object(m,'ROOT',root),patch.object(m,'git',side_effect=immutable)as git:
    self.assertEqual(m.measurement_retirement_guard(),self.old);self.assertEqual(git.call_count,2)
    path.write_bytes(self.new+b'# extra body\n')
    with self.assertRaises(ValueError):m.measurement_retirement_guard()
 def test_source_guard_and_close_enforce_same_retirement_before_actions(self):
  source=inspect.getsource(m.source_guard);close=inspect.getsource(m.close)
  self.assertLess(source.index('measurement_retirement_guard()'),source.index('g.guard()'))
  self.assertLess(close.index('measurement_retirement_guard()'),close.index('t.api('))
  self.assertIn('validate_measurement_retirement(',inspect.getsource(m.measurement_retirement_guard))
