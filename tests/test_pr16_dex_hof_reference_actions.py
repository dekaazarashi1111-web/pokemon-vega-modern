"""公開path・全量guard・独立測定envelopeの新規統合契約。"""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_dex_hof_reference_actions as m

class ActionTests(unittest.TestCase):
 def test_publication_contract(self):
  r=m.publication.contract(m.ROOT,m.WF,m.PUBLIC,m.ARTIFACT,m.SELF);self.assertEqual(r['directory'],'public-dex-hof-references')
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
   with self.assertRaises(ValueError):m.bounded_files({'reference-delta.json':b'{}\n'})
 def test_private_failure_never_enters_public_exception_or_report(self):
  private_marker='PRIVATE_RUNTIME_FRAGMENT_AND_PATH'
  with tempfile.TemporaryDirectory()as directory,patch.object(m.prior,'current'),patch.object(m.unittest,'TextTestRunner')as runner,patch.object(m.song_actions,'public_sources',side_effect=RuntimeError(private_marker)),patch.object(m.song_actions,'OUT'),patch.object(m.song_actions,'SOURCES'),patch.object(m,'OUT',Path(directory)/'private'),patch.object(m,'PUBLIC',Path(directory)/'public'):
   runner.return_value.run.return_value.wasSuccessful.return_value=True
   runner.return_value.run.return_value.testsRun=1
   with self.assertRaisesRegex(RuntimeError,'REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')as error:m.run()
   self.assertTrue(error.exception.__suppress_context__)
   self.assertNotIn(private_marker,str(error.exception))
   self.assertNotIn(private_marker,(m.PUBLIC/'failure.json').read_text())
   self.assertIn(private_marker,(m.OUT/'private-failure.txt').read_text())
 def test_record_requires_independent_envelope(self):
  with patch.object(m.delta,'read_measured',side_effect=ValueError('tampered'))as bound:
   with self.assertRaisesRegex(ValueError,'tampered'):m.validate_record({'delta_identity':{'size':3,'sha256':'fixed'}},b'{}\n',{})
   bound.assert_called_once_with(b'{}\n',{'size':3,'sha256':'fixed'},{})
if __name__=='__main__':unittest.main()
