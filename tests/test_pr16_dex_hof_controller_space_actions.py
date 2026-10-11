"""公開path・全量guard・独立測定envelopeの新規統合契約。"""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_dex_hof_controller_space_actions as m

class ActionTests(unittest.TestCase):
 def test_unknown_frontier_dictionary_owners(self):
  full=dict(hits=[dict(address=10,size=4,accepted=False),dict(address=30,size=4,accepted=False),dict(address=50,size=4,accepted=True)])
  result=m.unknown_frontier(full,{'owner':dict(name='owner',address=8,size=8)})
  self.assertEqual((result['total'],result['owner_unknown'],result['unowned_unknown']),(2,1,1));self.assertEqual(result['rows'][0]['owners'],['owner'])
 def test_old_checkpoint_is_distinct_exact_parent(self):
  self.assertNotEqual(m.OLDCP,m.CP);self.assertEqual(json.loads((m.ROOT/m.OLDCP).read_bytes())['delta_identity'],m.delta.PARENT_ID)
 def test_only_new_scope_test_modules(self):
  import inspect
  source=inspect.getsource(m.run)
  self.assertIn('test_pr16_dex_hof_controller_space as data_tests',source)
  self.assertIn('test_pr16_dex_hof_partial_space as space_tests',source)
  self.assertIn('test_pr16_dex_hof_space_chain as delta_tests',source)
  self.assertNotIn('test_pr16_dex_hof_reference_code as',source)
 def test_publication_contract(self):
  r=m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF);self.assertEqual(r['directory'],'public-dex-hof-controller-space')
 def test_small_closed_text(self):self.assertEqual(m.bounded_files({'measurement.json':b'{}\n'})['measurement.json']['size'],3)
 def test_empty(self):
  with self.assertRaises(ValueError):m.bounded_files({})
 def test_empty_member(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.txt':b''})
 def test_missing_lf(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.txt':b'x'})
 def test_null_byte(self):
  with self.assertRaises(ValueError):m.bounded_files({'a.txt':b'x\0\n'})
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
   with self.assertRaisesRegex(RuntimeError,'SPACE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')as error:m.run()
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
  self.files['measurement.json']=(json.dumps(dict(source_head='b'*40,run_id=123,delta_identity=m.identity(self.files['reference-chain.json']),capacity_identity=m.identity(self.files['partial-space.json'])))+'\n').encode()
  proofs={path:dict(**m.identity(self.files[n]),git_blob_sha=hashlib.sha1(b'blob '+str(len(self.files[n])).encode()+b'\0'+self.files[n]).hexdigest(),trailing_newline=True)for n,path in m.SNAPSHOTS}
  self.receipt=dict(final_head=self.head,status='PASS_RECORDED_REFERENCE_CHAIN',source_head='b'*40,record_run=123,final_blobs=proofs,precommit_publication_files={n:m.identity(raw)for n,raw in self.files.items()})
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
  self.files['controller-space-tests.txt']=b'changed\n'
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_wrong_git_blob(self):
  self.receipt['final_blobs'][m.STATE]['git_blob_sha']='wrong';self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_wrong_measurement_envelope(self):
  self.files['measurement.json']=(json.dumps(dict(source_head='b'*40,run_id=123,delta_identity={}))+'\n').encode()
  self.receipt['precommit_publication_files']['measurement.json']=m.identity(self.files['measurement.json']);self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
 def test_wrong_measurement_run(self):
  self.receipt['record_run']=456;self.update()
  with self.assertRaises(ValueError):m.validate_export(self.files,self.head)
class MeasuredBoundaryTests(unittest.TestCase):
 def setUp(self):
  self.m=dict(status='PASS_CURRENT_726_PARENT_ROOTS_AND_PARTIAL_SPACE_REFUSAL',source_head='a'*40,run_id=123,current_owner_count=115,current_rom_reconstructions=1,old_inventory_candidates=874,previous_classified=726,previous_unknown=148,**m.EXPECTED,unit_tests=1,retained_sample_witnesses=50,all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,old_models_reused_for_new_cross_song_role_safety=True)
 def check(self):
  with patch.dict(m.os.environ,{'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123'}):m.validate_measurement(self.m)
 def reject(self,key,value):
  self.m[key]=value
  with self.assertRaises(ValueError):self.check()
 def test_exact_new_scope(self):self.check()
 def test_owner_count_exact(self):self.reject('current_owner_count',114)
 def test_owner_unknown_zero(self):self.reject('owner_unknown',1)
 def test_retained133_models(self):self.reject('combined_song_models',132)
 def test_retained50_assets(self):self.reject('retained_sample_witnesses',49)
 def test_old_frontier_cannot_replace_parent(self):self.reject('previous_classified',723)
 def test_previous_unknown148(self):self.reject('previous_unknown',151)
 def test_one_current_reconstruction(self):self.reject('current_rom_reconstructions',0)
 def test_no_dropped_inventory(self):self.reject('old_inventory_candidates',873)
 def test_no_skipped_tests(self):self.reject('unit_tests',0)
 def test_boolean_not_count(self):self.reject('newly_classified',True)
 def test_no_accepted_proof_replacement(self):self.reject('all_prior_accepted_retained',False)
 def test_no_remaining_unknown_replacement(self):self.reject('remaining_unknown_rows_retained',False)
 def test_new_source_excludes_old_history(self):
  self.assertTrue(all('history'not in p and 'consumer_references'not in p for p in m.CODE))
  self.assertTrue(all((m.ROOT/p).is_file()for p in m.CODE))
 def test_safety_before_old_replay(self):
  import inspect
  source=inspect.getsource(m.run)
  self.assertNotIn('history_terminal',source);self.assertNotIn('d.inventory(',source)
  self.assertIn('space.current_report(full,ROOT,parent_audit=inherited)',source)
if __name__=='__main__':unittest.main()
