"""公開path・全量guard・独立測定envelopeの新規統合契約。"""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_dex_hof_remaining_references_actions as m

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
  self.assertIn('test_pr16_dex_hof_remaining_references as data_tests',source)
  self.assertIn('test_pr16_dex_hof_remaining_song as song_tests',source)
  self.assertIn('test_pr16_dex_hof_remaining_chain as delta_tests',source)
  self.assertNotIn('test_pr16_dex_hof_reference_code as',source)
 def test_publication_contract(self):
  r=m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF);self.assertEqual(r['directory'],'public-dex-hof-remaining-references')
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
  with tempfile.TemporaryDirectory()as directory,patch.object(m.prior,'current'),patch.object(m.unittest,'TextTestRunner')as runner,patch.object(m.song_actions,'public_sources',side_effect=RuntimeError(private_marker)),patch.object(m.song_actions,'OUT'),patch.object(m.song_actions,'SOURCES'),patch.object(m,'OUT',Path(directory)/'private'),patch.object(m,'PUBLIC',Path(directory)/'public'),patch('sys.stdout',__import__('io').StringIO()):
   runner.return_value.run.return_value.wasSuccessful.return_value=True
   runner.return_value.run.return_value.testsRun=1
   with self.assertRaisesRegex(RuntimeError,'REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')as error:m.run()
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
  self.files['measurement.json']=(json.dumps(dict(source_head='b'*40,run_id=123,delta_identity=m.identity(self.files['reference-chain.json'])))+'\n').encode()
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
  self.files['remaining-references-tests.txt']=b'changed\n'
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
if __name__=='__main__':unittest.main()
