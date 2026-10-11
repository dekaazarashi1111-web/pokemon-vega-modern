"""旧guideへの誤書込み防止。受入済み20試験を再実行しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save29_record as r
class Targets(unittest.TestCase):
 def test_new_guide_only(self):self.assertIsNone(r.targets({'docs/PR16_STORY_SAVE27_JA.md','docs/PR16_STORY_SAVE28_JA.md'}))
 def test_previous_guide_rejected(self):
  with self.assertRaises(ValueError):r.targets({'docs/PR16_STORY_SAVE27_JA.md'},guide='docs/PR16_STORY_SAVE27_JA.md')
if __name__=='__main__':unittest.main()
