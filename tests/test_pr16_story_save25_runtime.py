"""保持済みruntime入力の限定path検査。旧16controller試験を再走しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from pr16_story_save25_measure import runtime_member
class RuntimePath(unittest.TestCase):
    def test_loader(self):self.assertEqual(runtime_member('runtime/ld.so'),'ld.so')
    def test_library(self):self.assertEqual(runtime_member('runtime/lib/libmgba.so'),'lib/libmgba.so')
    def test_missing_prefix(self):
        with self.assertRaises(ValueError):runtime_member('lib/libmgba.so')
    def test_parent(self):
        with self.assertRaises(ValueError):runtime_member('runtime/lib/../x')
    def test_absolute(self):
        with self.assertRaises(ValueError):runtime_member('runtime//tmp/x')
    def test_non_runtime(self):
        with self.assertRaises(ValueError):runtime_member('runtime/candidate.gba')
    def test_type(self):
        with self.assertRaises(ValueError):runtime_member(None)
if __name__=='__main__':unittest.main()
