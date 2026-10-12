"""失敗原本は保ちつつrunner絶対pathをtracked textへ出さない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save29_record as r
class Receipt(unittest.TestCase):
 def test_discard_path_prefix(self):
  got=r.traceback_summary('File <UNPUBLISHED_RUNNER_PATH>, line 95, in record\nValueError: 既存受入正本/入力不変')
  self.assertEqual(got,dict(function='record',line=95,error='ValueError: 既存受入正本/入力不変',absolute_paths_published=False))
 def test_mismatched_failure_rejected(self):
  with self.assertRaises(ValueError):r.traceback_summary('line 96, in record\nValueError: another failure')
if __name__=='__main__':unittest.main()
