"""新state終端receipt全本文・実committed recordingへの結合だけを検査。"""
import copy,inspect,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import guard_private_files
import pr16_dex_hof_registered_state_batch_closeout as m
from test_pr16_dex_hof_registered_state_batch_actions import raw,git_blob,measurement_fixture,committed_git
class StateCloseoutTests(unittest.TestCase):
 def setUp(self):
  self.head='a'*40;self.payload=dict(m.terminal_constants(),closeout_source='d'*40,closeout_run=1234,export_guard_test_log={'size':17,'sha256':'e'*64})
  self.files={n:b'{}\n'if n.endswith('.json')else b'synthetic-only\n'for n,_ in m.w.SNAPSHOTS}
  self.files['fixed-checkpoint.json']=(m.ROOT/m.w.CP).read_bytes()
  self.files['fixed-state.json']=raw(dict(pending_runs=[],story_dex_owner=dict(runtime_integration=dict(hof_registered_state_batch=dict(recording=self.payload)))))
  self.receipt=dict(self.payload,final_head=self.head,final_blobs={p:dict(**m.identity(self.files[n]),git_blob_sha=git_blob(self.files[n]),trailing_newline=True)for n,p in m.w.SNAPSHOTS});self.files['closeout.json']=raw(self.receipt)
 def test_producer_guard_uploadpath_agree(self):self.assertEqual(m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF)['directory'],'public-dex-hof-registered-state-batch-closeout')
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
  for state in({},dict(pending_runs=[{'run':1}],story_dex_owner=dict(runtime_integration=dict(hof_registered_state_batch=dict(recording=self.payload)))),dict(pending_runs=[],story_dex_owner=dict(runtime_integration=dict(hof_registered_state_batch={})))):
   files=dict(self.files);files['fixed-state.json']=raw(state);receipt=copy.deepcopy(self.receipt);b=files['fixed-state.json'];receipt['final_blobs'][m.w.STATE]=dict(**m.identity(b),git_blob_sha=git_blob(b),trailing_newline=True);files['closeout.json']=raw(receipt)
   with self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_terminal_self_reseal_cannot_replace_committed_recording(self):
  files=dict(self.files);receipt=copy.deepcopy(self.receipt);receipt['closeout_run']=999;state=json.loads(files['fixed-state.json']);state['story_dex_owner']['runtime_integration']['hof_registered_state_batch']['recording']['closeout_run']=999;files['fixed-state.json']=raw(state);b=files['fixed-state.json'];receipt['final_blobs'][m.w.STATE]=dict(**m.identity(b),git_blob_sha=git_blob(b),trailing_newline=True);files['closeout.json']=raw(receipt);self.assertTrue(m.validate_export(files,self.head))
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
  good=dict(schema_version=1,status='PASS_NEW_REGISTERED_STATE_CLOSEOUT_SOURCE_REVIEW',review_scope='new_registered_state_closeout_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings={p:{'size':1,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}})
  with patch.object(m,'bindings',return_value=good['source_bindings']):self.assertTrue(m.validate_development(good))
  for key,value in(('schema_version',True),('schema_version',1.0),('extra','private'),('open_findings',None),('open_findings',False),('open_findings',['unresolved']),('source_bindings',{}),('old_independent_final_review_retried',True)):
   changed=copy.deepcopy(good);changed[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_development(changed)

class StateCloseoutStrictSchemaTests(unittest.TestCase):
 setUp=StateCloseoutTests.setUp
 def test_final_snapshot_float_bool_or_extra_binding_rejected(self):
  for mutation in('float','bool','extra'):
   receipt=copy.deepcopy(self.receipt);binding=receipt['final_blobs'][m.w.STATE]
   if mutation=='extra':binding['extra']='injected'
   else:binding['size']=float(binding['size'])if mutation=='float'else True
   files=dict(self.files);files['closeout.json']=raw(receipt)
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):m.validate_export(files,self.head)
 def test_terminal_review_source_identity_has_no_float_alias(self):
  bindings={p:{'size':17,'sha256':'a'*64}for p in m.CODE-{m.DEVELOPMENT}}
  value=dict(schema_version=1,status='PASS_NEW_REGISTERED_STATE_CLOSEOUT_SOURCE_REVIEW',review_scope='new_registered_state_closeout_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings=copy.deepcopy(bindings));value['source_bindings'][next(iter(bindings))]['size']=17.0
  with patch.object(m,'bindings',return_value=bindings),self.assertRaises(ValueError):m.validate_development(value)

class StateCloseoutMeasuredContractTests(unittest.TestCase):
 def payload(self):return dict(m.terminal_constants(),closeout_source='d'*40,closeout_run=1234,export_guard_test_log={'size':17,'sha256':'e'*64})
 def test_actual_bindings_are_complete_and_distinct(self):
  self.assertTrue(m.require_measured_bindings())
  self.assertEqual((m.INITIAL,m.BASE,m.SOURCE),('b9be8c6c231df0aac1c5eb163b154a4ec8ff5787','22a320d1c8234de23f7015f32221c0254efcd0ad','c9c961bfeee686066c625b5d20b928cfb0df5749'))
  self.assertEqual((m.RUN,m.JOB,m.ARCHIVE),(37455026681,112240418353,(11409007060,37455026681,1509183,'95bd086e26c96fd8f0b861b77db50e81aa1ec9e5fd23a4e7c64c7dcda354a463')))
  self.assertEqual(set(m.MEASUREMENT_FILES),m.w.PROOF|{'record.json',*(n for n,_ in m.w.SNAPSHOTS)})
 def test_terminal_counter_fixed_to_only_new_complete_suite(self):
  suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
  self.assertEqual(m.CLOSEOUT_TESTS,suite.countTestCases())
  self.assertEqual(m.EXPECTED['unit_tests'],164)
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
  raw_development=(m.ROOT/m.w.DEVELOPMENT).read_bytes();failed=m.validate_fixture_correction(raw_development)
  self.assertEqual(failed,self.payload()['failed_attempt'])
  self.assertEqual((failed['run'],failed['job'],failed['artifacts']),(37453822147,112236454951,0))
  self.assertFalse(failed['classification_accepted']);self.assertFalse(failed['recorded'])
  with self.assertRaises(ValueError):m.validate_fixture_correction(raw_development+b'\n')
 def test_failed_correction_cannot_be_resealed_as_success(self):
  value=json.loads((m.ROOT/m.w.DEVELOPMENT).read_bytes())
  for key,replacement in(('failed_attempt_accepted',True),('failed_attempt_artifacts',1),('failed_run',m.RUN),('native_processes',0.0),('corrected_test_only',False)):
   changed=copy.deepcopy(value);changed['fixture_correction'][key]=replacement;b=raw(changed)
   with patch.object(m,'MEASUREMENT_DEVELOPMENT',m.identity(b)),self.subTest(key=key),self.assertRaises(ValueError):m.validate_fixture_correction(b)
 def test_failed_and_accepted_rom_counts_are_not_closeout_work(self):
  value=self.payload()
  self.assertEqual(value['failed_current_rom_reconstructions']+value['accepted_current_rom_reconstructions'],value['total_current_rom_reconstructions'])
  self.assertEqual(value['total_current_rom_reconstructions'],2)
  for key in('current_rom_reconstructions','arm_compiles','native_processes','tests_rerun','closeout_additional_rom_reconstructions','closeout_additional_arm_compiles','closeout_additional_native_processes','closeout_old_suite_runs'):self.assertEqual(value[key],0)
  self.assertFalse(value['failed_attempt_promoted_to_success'])
 def test_exact_successful_job_and_all_steps(self):
  run=dict(id=m.RUN,head_sha=m.SOURCE,status='completed',conclusion='success',run_attempt=1)
  job=dict(id=m.JOB,run_id=m.RUN,head_sha=m.SOURCE,run_attempt=1,status='completed',conclusion='success',steps=[dict(status='completed',conclusion='success')for _ in range(14)])
  self.assertTrue(m.validate_successful_job(run,job))
  for scope,key,replacement in(('run','id',1),('run','id',float(m.RUN)),('run','run_attempt',True),('run','head_sha',m.FIXTURE_CORRECTION['initial_source']),('run','conclusion','failure'),('job','id',1),('job','id',float(m.JOB)),('job','run_id',float(m.RUN)),('job','run_attempt',True),('job','run_attempt',2),('job','run_id',m.FIXTURE_CORRECTION['failed_run']),('job','steps',job['steps'][:-1]),('job','steps',[dict(status='completed',conclusion='failure')]+job['steps'][1:])):
   r,j=copy.deepcopy(run),copy.deepcopy(job);(r if scope=='run'else j)[key]=replacement
   with self.subTest(scope=scope,key=key),self.assertRaises(ValueError):m.validate_successful_job(r,j)
 def test_measurement_self_reseal_cannot_replace_pinned_eleven_texts(self):
  head,files,receipt=measurement_fixture();pinned={n:m.identity(b)for n,b in files.items()}
  files['registered-state-batch-tests.txt']=b'different source-only text\n';receipt['precommit_publication_files']['registered-state-batch-tests.txt']=m.identity(files['registered-state-batch-tests.txt']);files['record.json']=raw(receipt)
  self.assertTrue(m.w.validate_export(files,head))
  with patch.object(m,'BASE',head),patch.object(m,'MEASUREMENT_FILES',pinned),self.assertRaises(ValueError):m.validate_received_measurement(files)
 def test_next_three_roots_preserve_every_prior_runtime_boundary(self):
  goal=m.next_goal(m.w.data.NEXT_GOAL)
  self.assertTrue(goal.endswith(m.w.data.NEXT_GOAL))
  for token in(*m.NEXT_ROOTS,'special057','Frontier','CurrentStreak/MaxStreak','ChooseMove','effect dispatch','旧06c5','正式分類追加0','future-live','同epoch','変異/reseal反証は未完','全S61E/MDX','writer/loader/Link','exact-source/no-main/INITIAL/全mode/早期31/species9bit','保存境界','シオウ通常回復/保存/独立coldContinue','雑魚毎Saveなし','heap13352','53300','退避前Free'):
   self.assertIn(token,goal)
  with self.assertRaises(ValueError):m.next_goal('replacement omitting runtime gates')
 def test_new_candidates_cannot_be_counted_as_current_acceptance(self):
  value=self.payload();self.assertEqual(value['next_scope_candidates'],list(m.NEXT_ROOTS));self.assertEqual(value['classified'],776);self.assertEqual(value['unclassified'],98)
  self.assertEqual(value['next_scope_current_classifications_added'],0)
  for key in('next_scope_current_measured','next_scope_finite_consumer_live_epoch_proven','natural_full_play_proven','universal_irq_or_heap_lifetime_proven','indirect_reference_completeness_claimed','retirement_proven','owner_transfer_proven','controller_runtime_wired','independent_final_source_review_completed','old_independent_final_review_retried'):self.assertIs(value[key],False)
 def test_only_closeout_workflow_push_and_exact_measurement_retirement(self):
  closeout=(m.ROOT/m.WF).read_text();measured=(m.ROOT/m.w.WF).read_bytes()
  push=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+m.w.WF+']\n').encode()
  self.assertIn('    paths: ['+m.WF+']\n',closeout);self.assertNotIn('workflow_dispatch:',closeout)
  self.assertEqual(measured.count(b'  workflow_dispatch:\n'),1);self.assertNotIn(b'  push:\n',measured)
  original=measured.replace(b'  workflow_dispatch:\n',push)
  dev=json.loads((m.ROOT/m.w.DEVELOPMENT).read_bytes());self.assertEqual(m.identity(original),dev['source_bindings'][m.w.WF])
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
  value=self.payload();failed=value['failed_closeout_attempts']
  self.assertEqual(failed,[m.FAILED_CLOSEOUT,m.FAILED_CLOSEOUT_BOOTSTRAP]);self.assertEqual(value['failed_closeout_runs'],2)
  row=failed[0];self.assertEqual((row['source_head'],row['run'],row['job']),('e1071ce7bab8a8f111999121f4a396b08b153679',37457248101,112247753034))
  self.assertIs(row['source_guard_failed'],True);self.assertIs(row['classification_accepted'],False);self.assertIs(row['recorded'],False)
  for key in('current_rom_reconstructions','arm_compiles','native_processes','new_closeout_suite_tests_executed','pushes','artifacts'):self.assertEqual(row[key],0)
  self.assertEqual(value['total_current_rom_reconstructions'],2)
  self.assertEqual(value['failed_closeout_current_rom_reconstructions'],0)
  row=failed[1];self.assertEqual((row['source_head'],row['run'],row['job']),('431a16d2cd01938839e5d15b7c08f08159237a8e',37458617710,112252265422))
  self.assertIs(row['source_guard_passed'],True);self.assertIs(row['private_guard_passed'],True);self.assertIs(row['module_load_failed'],True)
  self.assertIs(row['classification_accepted'],False);self.assertIs(row['recorded'],False)
  self.assertEqual(row['new_closeout_suite_tests_planned'],31)
  self.assertEqual(row['module_load_cause_source'],'same_source_workflow_command_local_reproduction_not_API_error_text');self.assertIs(row['api_error_text_retrieved'],False)
  for key in('current_rom_reconstructions','arm_compiles','native_processes','new_closeout_suite_tests_executed','pushes','artifacts'):self.assertEqual(row[key],0)
 def test_export_rejects_hidden_symlink_directory_and_unknown_file(self):
  fixture=StateCloseoutTests();fixture.setUp()
  for kind in('hidden','symlink','directory','extension'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory()as tmp:
    p=Path(tmp)
    for n,b in fixture.files.items():(p/n).write_bytes(b)
    if kind=='hidden':(p/'.hidden').write_bytes(b'x\n')
    elif kind=='symlink':(p/'linked.json').symlink_to(p/'closeout.json')
    elif kind=='directory':(p/'nested').mkdir()
    else:(p/'unknown.bin').write_bytes(b'x\n')
    with patch.object(m,'PUBLIC',p),patch.object(m,'git',side_effect=committed_git(fixture.head,fixture.files,proof=False)),self.assertRaises(ValueError):m.export()
