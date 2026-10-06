"""公開path・全量guard・独立測定envelopeの新規統合契約。"""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_dex_hof_registered_boundary_batch_actions as m

class ActionTests(unittest.TestCase):
 def test_initial_remote_head_exact(self):self.assertEqual(m.BASE,'001cd8430558fce0a03130898e08d24981bfe33a')
 def test_unknown_frontier_dictionary_owners(self):
  full=dict(hits=[dict(address=10,size=4,accepted=False),dict(address=30,size=4,accepted=False),dict(address=50,size=4,accepted=True)])
  result=m.unknown_frontier(full,{'owner':dict(name='owner',address=8,size=8)})
  self.assertEqual((result['total'],result['owner_unknown'],result['unowned_unknown']),(2,1,1));self.assertEqual(result['rows'][0]['owners'],['owner'])
 def test_old_checkpoint_is_distinct_exact_parent(self):
  self.assertNotEqual(m.OLDCP,m.CP);self.assertEqual(json.loads((m.ROOT/m.OLDCP).read_bytes())['delta_identity'],m.delta.PARENT_ID)
 def test_only_new_scope_test_modules(self):
  import inspect
  source=inspect.getsource(m.run)
  self.assertIn('test_pr16_dex_hof_registered_boundary_batch as data_tests',source)
  self.assertIn('test_pr16_dex_hof_registered_boundary_batch_capacity as space_tests',source)
  self.assertIn('test_pr16_dex_hof_registered_boundary_batch_chain as delta_tests',source)
  self.assertNotIn('test_pr16_dex_hof_reference_code as',source)
 def test_publication_contract(self):
  r=m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF);self.assertEqual(r['directory'],'public-dex-hof-registered-boundary-batch')
 def test_small_closed_text(self):self.assertEqual(m.bounded_files({'measurement.json':b'{}\n'})['measurement.json']['size'],3)
 def test_empty(self):
  with self.assertRaises(ValueError):m.bounded_files({})
 def test_empty_member(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.txt':b''})
 def test_missing_lf(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.txt':b'x'})
 def test_null_byte(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.txt':b'x\0\n'})
 def test_carriage_return_rejected(self):
  for raw in(b'{}\r\n',b'a\rb\n'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):m.bounded_files({'a.txt':raw})
 def test_invalid_utf8(self):
  with self.assertRaises(UnicodeDecodeError):m.bounded_files({'a.txt':b'\xff\n'})
 def test_invalid_json(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.json':b'{\n'})
 def test_file_limit(self):
  with patch.object(m,'MAX_FILE',4):
   with self.assertRaises(ValueError):m.bounded_files({'a.txt':b'xxx\n'})
 def test_total_limit(self):
  with patch.object(m,'MAX_TOTAL',6):
   with self.assertRaises(ValueError):m.bounded_files({'a.txt':b'aa\n','b.txt':b'bb\n'})
 def test_delta_limit(self):
  with patch.object(m.delta,'MAX_DELTA_BYTES',2):
   with self.assertRaises(ValueError):m.bounded_files({'reference-chain.json':b'{}\n'})
 def test_private_failure_never_enters_public_exception_or_report(self):
  private_marker='PRIVATE_RUNTIME_FRAGMENT_AND_PATH'
  with tempfile.TemporaryDirectory()as directory,patch.object(m.prior,'current'),patch.object(m.unittest,'TextTestRunner')as runner,patch.object(m,'public_sources',side_effect=RuntimeError(private_marker)),patch.object(m,'OUT',Path(directory)/'private'),patch.object(m,'PUBLIC',Path(directory)/'public'),patch('sys.stdout',__import__('io').StringIO()):
   runner.return_value.run.return_value.wasSuccessful.return_value=True
   runner.return_value.run.return_value.testsRun=1
   with self.assertRaisesRegex(RuntimeError,'REGISTERED_BOUNDARY_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')as error:m.run()
   self.assertTrue(error.exception.__suppress_context__)
   self.assertNotIn(private_marker,str(error.exception))
   self.assertNotIn(private_marker,(m.OUT/'failure.json').read_text())
   self.assertIn(private_marker,(m.OUT/'private-failure.txt').read_text())
 def test_record_requires_independent_envelope(self):
  with patch.object(m.delta,'read_measured',side_effect=ValueError('tampered'))as bound:
   with self.assertRaisesRegex(ValueError,'tampered'):m.validate_record({'delta_identity':{'size':3,'sha256':'fixed'}},b'{}\n',{})
   bound.assert_called_once_with(b'{}\n',{'size':3,'sha256':'fixed'},{})
class CompleteExportTests(unittest.TestCase):
 def setUp(self):
  self.head='a'*40
  self.files={n:(b'{}\n'if n.endswith('.json')else b'synthetic\n')for n in m.PROOF|{n for n,_ in m.SNAPSHOTS}}
  self.files['measurement.json']=(json.dumps(dict(source_head='b'*40,run_id=121,delta_identity=m.identity(self.files['reference-chain.json']),capacity_identity=m.identity(self.files['partial-space.json'])))+'\n').encode()
  proofs={path:dict(**m.identity(self.files[n]),git_blob_sha=hashlib.sha1(b'blob '+str(len(self.files[n])).encode()+b'\0'+self.files[n]).hexdigest(),trailing_newline=True)for n,path in m.SNAPSHOTS}
  self.receipt=dict(final_head=self.head,status='PASS_RECORDED_REFERENCE_CHAIN',source_head='b'*40,record_run=121,native_processes=0,final_blobs=proofs,precommit_publication_files={n:m.identity(raw)for n,raw in self.files.items()})
  self.update()
 def update(self):self.files['record.json']=(json.dumps(self.receipt)+'\n').encode()
 def test_complete(self):self.assertTrue(m.validate_export(self.files,self.head))
 def test_each_missing_file(self):
  for name in list(self.files):
   with self.subTest(name=name):
    changed=dict(self.files);changed.pop(name)
    with self.assertRaises(ValueError):m.validate_export(changed,self.head)
 def test_extra_file(self):
  self.files['hidden.txt']=b'extra\n'
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_uncommitted(self):
  self.receipt.pop('final_head');self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_no_snapshot_proof(self):
  self.receipt.pop('final_blobs');self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_changed_text(self):
  self.files['registered-boundary-batch-tests.txt']=b'changed\n'
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_crlf_with_resealed_receipt_rejected(self):
  name='registered-boundary-batch-tests.txt';self.files[name]=b'tests\r\n'
  self.receipt['precommit_publication_files'][name]=m.identity(self.files[name]);self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_midline_cr_with_resealed_receipt_rejected(self):
  name='registered-boundary-batch-tests.txt';self.files[name]=b'tes\rts\n'
  self.receipt['precommit_publication_files'][name]=m.identity(self.files[name]);self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_wrong_git_blob(self):
  self.receipt['final_blobs'][m.STATE]['git_blob_sha']='wrong';self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_wrong_measurement_envelope(self):
  self.files['measurement.json']=(json.dumps(dict(source_head='b'*40,run_id=121,delta_identity={}))+'\n').encode()
  self.receipt['precommit_publication_files']['measurement.json']=m.identity(self.files['measurement.json']);self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_directory_is_closed_before_read_or_upload(self):
  for bad in('hidden','unknown','subdirectory','symlink'):
   with self.subTest(case=bad),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp)
    for name,raw in self.files.items():(root/name).write_bytes(raw)
    if bad=='hidden':(root/'.hidden').write_text('private\n')
    elif bad=='unknown':(root/'unexpected.bin').write_bytes(b'data')
    elif bad=='subdirectory':(root/'nested').mkdir()
    else:(root/'linked.json').symlink_to(root/'record.json')
    with patch.object(m,'PUBLIC',root),patch.object(m,'git',return_value=self.head.encode()):
     with self.assertRaises(ValueError):m.export()
 def test_whole_success_directory_export(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for name,raw in self.files.items():(root/name).write_bytes(raw)
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.committed_git(dict(self.files))):m.export()
 def committed_git(self,files):
  objects={self.head+':'+path:files[name]for name,path in m.SNAPSHOTS}
  objects.update({self.head+':'+m.EVIDENCE+'/'+name:files[name]for name in m.PROOF})
  def run(*args):
   if args==('rev-parse','HEAD'):return self.head.encode()
   if args[0]=='show':return objects[args[1]]
   if args[0]=='rev-parse':
    raw=objects[args[1]];return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest().encode()
   raise AssertionError(args)
  return run
 def test_resealed_snapshot_cannot_replace_committed_bytes(self):
  committed=dict(self.files);name='fixed-state.json';raw=b'{"changed":true}\n';self.files[name]=raw
  self.receipt['precommit_publication_files'][name]=m.identity(raw)
  self.receipt['final_blobs'][m.STATE]=dict(**m.identity(raw),git_blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),trailing_newline=True);self.update()
  self.assertTrue(m.validate_export(self.files,self.head))
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for n,b in self.files.items():(root/n).write_bytes(b)
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.committed_git(committed)):
    with self.assertRaisesRegex(ValueError,'independent committed blob'):m.export()
 def test_resealed_proof_cannot_replace_committed_measurement(self):
  committed=dict(self.files);name='registered-boundary-batch-tests.txt';self.files[name]=b'tampered tests\n'
  self.receipt['precommit_publication_files'][name]=m.identity(self.files[name]);self.update()
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for n,b in self.files.items():(root/n).write_bytes(b)
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.committed_git(committed)):
    with self.assertRaisesRegex(ValueError,'immutable committed measurement'):m.export()
 def test_closed_entire_receipt_rejects_extra_field(self):
  self.receipt['unexpected_receipt_field']='forged';self.update()
  with self.assertRaisesRegex(ValueError,'entire closed receipt'):m.validate_export(self.files,self.head)
 def test_receipt_native_process_is_exact_integer_zero(self):
  for value in (99,True,False,None,0.0,'0'):
   self.receipt['native_processes']=value;self.update()
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'entire closed receipt'):m.validate_export(self.files,self.head)
 def test_missing_receipt_native_process_rejected(self):
  self.receipt.pop('native_processes');self.update()
  with self.assertRaisesRegex(ValueError,'entire closed receipt'):m.validate_export(self.files,self.head)
 def test_additional_field_in_identity_rejected(self):
  self.receipt['precommit_publication_files']['measurement.json']['extra']=1;self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_entire_receipt_native_injection_rejected_by_export(self):
  committed=dict(self.files);self.receipt['native_processes']=99;self.receipt['unexpected_receipt_field']='forged';self.update()
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for name,raw in self.files.items():(root/name).write_bytes(raw)
   with patch.object(m,'PUBLIC',root),patch.object(m,'git',side_effect=self.committed_git(committed)):
    with self.assertRaisesRegex(ValueError,'entire closed receipt'):m.export()
 def test_wrong_measurement_run(self):
  self.receipt['record_run']=456;self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
class MeasuredBoundaryTests(unittest.TestCase):
 def setUp(self):
  # 完成前のレビュー成果へ循環依存せず、独立した合成whole-fileを使う。
  self.original_development=m.DEVELOPMENT
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  fixture=Path(temporary.name)/'synthetic-review.json';fixture.write_bytes(b'{"synthetic_unit_only":true}\n')
  binding_patch=patch.object(m,'DEVELOPMENT',str(fixture));binding_patch.start();self.addCleanup(binding_patch.stop)
  self.m=dict(status='PASS_CURRENT_761_PARENT_REGISTERED_BOUNDARY_BATCH_AND_PARTIAL_SPACE_REFUSAL',source_head='a'*40,run_id=121,current_owner_count=115,current_rom_reconstructions=1,old_inventory_candidates=874,previous_classified=761,previous_unknown=113,**m.EXPECTED,unit_tests=1,retained_sample_witnesses=50,independent_final_source_review_completed=False,new_registered_boundary_batch_source_review_completed=True,development_validation=m.identity((m.ROOT/m.DEVELOPMENT).read_bytes()),all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,old_models_reused_for_new_cross_song_role_safety=True)
 def check(self):
  with patch.dict(m.os.environ,{'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'121'}):m.validate_measurement(self.m)
 def reject(self,key,value):
  self.m[key]=value
  with self.assertRaises(ValueError):self.check()
 def test_exact_new_scope(self):self.check()
 def test_old_review_cannot_be_promoted(self):self.reject('independent_final_source_review_completed',True)
 def test_old_review_false_is_not_integer_zero(self):self.reject('independent_final_source_review_completed',0)
 def test_new_scope_review_required(self):self.reject('new_registered_boundary_batch_source_review_completed',False)
 def test_new_scope_review_true_is_not_integer_one(self):self.reject('new_registered_boundary_batch_source_review_completed',1)
 def test_development_envelope_whole_bytes(self):self.reject('development_validation',{'size':1,'sha256':'forged'})
 def test_owner_count_exact(self):self.reject('current_owner_count',114)
 def test_owner_unknown_zero(self):self.reject('owner_unknown',1)
 def test_retained133_models(self):self.reject('combined_song_models',134)
 def test_retained50_assets(self):self.reject('retained_sample_witnesses',49)
 def test_old_frontier_cannot_replace_parent(self):self.reject('previous_classified',723)
 def test_previous_unknown146(self):self.reject('previous_unknown',151)
 def test_one_current_reconstruction(self):self.reject('current_rom_reconstructions',0)
 def test_no_dropped_inventory(self):self.reject('old_inventory_candidates',873)
 def test_no_skipped_tests(self):self.reject('unit_tests',0)
 def test_boolean_not_count(self):self.reject('newly_classified',True)
 def test_no_accepted_proof_replacement(self):self.reject('all_prior_accepted_retained',False)
 def test_no_remaining_unknown_replacement(self):self.reject('remaining_unknown_rows_retained',False)
 def test_new_source_excludes_old_history(self):
  self.assertTrue(all('history'not in p and 'consumer_references'not in p for p in m.CODE))
  self.assertTrue(all((m.ROOT/p).is_file()for p in m.CODE-{self.original_development}))
 def test_safety_before_old_replay(self):
  import inspect
  source=inspect.getsource(m.run)
  self.assertNotIn('history_terminal',source);self.assertNotIn('d.inventory(',source)
  self.assertIn('capacity_report(full,inherited)',source)
if __name__=='__main__':unittest.main()

class DevelopmentReviewTests(unittest.TestCase):
 def setUp(self):
  self.d=dict(status='PASS_NEW_SOURCE_ONLY_REGISTERED_BOUNDARY_BATCH_REVIEW',review_scope='new_registered_boundary_batch_sources_only',old_independent_final_review_retried=False,open_findings=[],source_bindings={p:{'size':1,'sha256':'synthetic'}for p in m.CODE-{m.DEVELOPMENT}})
 def check(self):
  with patch.object(m.prior,'bindings',side_effect=lambda rows:{p:{'size':1,'sha256':'synthetic'}for p in rows}):m.validate_development(self.d)
 def test_all_expected_sources(self):self.check()
 def test_empty_bindings_rejected(self):
  self.d['source_bindings']={}
  with self.assertRaises(ValueError):self.check()
 def test_each_omitted_source_rejected(self):
  for path in list(self.d['source_bindings']):
   old=self.d['source_bindings'].pop(path)
   with self.subTest(path=path),self.assertRaises(ValueError):self.check()
   self.d['source_bindings'][path]=old
 def test_extra_source_rejected(self):
  self.d['source_bindings']['outside-scope.txt']={'size':1,'sha256':'synthetic'}
  with self.assertRaises(ValueError):self.check()
 def test_self_binding_rejected(self):
  self.d['source_bindings'][m.DEVELOPMENT]={'size':1,'sha256':'synthetic'}
  with self.assertRaises(ValueError):self.check()
 def test_changed_source_bytes_rejected(self):
  next(iter(self.d['source_bindings'].values()))['sha256']='changed'
  with self.assertRaises(ValueError):self.check()
 def test_wrong_status_rejected(self):
  self.d['status']='SOURCE_REVIEW_IN_PROGRESS'
  with self.assertRaises(ValueError):self.check()
 def test_old_review_cannot_be_retried(self):
  self.d['old_independent_final_review_retried']=True
  with self.assertRaises(ValueError):self.check()
 def test_wrong_review_scope_rejected(self):
  self.d['review_scope']='old_final_song_battle_surf'
  with self.assertRaises(ValueError):self.check()

 def test_unresolved_finding_rejected(self):
  self.d['open_findings']=[{'id':'live_contract_open'}]
  with self.assertRaises(ValueError):self.check()
 def test_missing_findings_rejected(self):
  self.d.pop('open_findings')
  with self.assertRaises(ValueError):self.check()
 def test_false_empty_findings_rejected(self):
  for value in (False,None,(),{},'',0):
   with self.subTest(value=value):
    self.d['open_findings']=value
    with self.assertRaises(ValueError):self.check()

class ClosedBoundaryTypesTests(unittest.TestCase):
 def setUp(self):
  self.false_fields=('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed')
  self.zero_fields=('native_processes','old_full_rom_scan_runs','accepted_heap_reruns','historical_rom_reconstructions')
  self.value={**{k:False for k in self.false_fields},**{k:0 for k in self.zero_fields}}
 def test_canonical_boolean_and_integer_boundaries(self):self.assertTrue(m.validate_closed_boundaries(self.value))
 def test_each_false_alias_rejected(self):
  for key in self.false_fields:
   for value in (0,None,'',[],True):
    with self.subTest(field=key,value=value),self.assertRaises(ValueError):m.validate_closed_boundaries(dict(self.value,**{key:value}))
 def test_each_zero_alias_rejected(self):
  for key in self.zero_fields:
   for value in (False,0.0,None,'',[],1):
    with self.subTest(field=key,value=value),self.assertRaises(ValueError):m.validate_closed_boundaries(dict(self.value,**{key:value}))
 def test_missing_boundary_rejected(self):
  for key in self.value:
   changed=dict(self.value);changed.pop(key)
   with self.subTest(field=key),self.assertRaises(ValueError):m.validate_closed_boundaries(changed)
