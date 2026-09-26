"""旧51unitの再実行なしで、固定tracked Cのコンパイル経路だけを検査。"""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_share_saved as s


class SavedSourceTests(unittest.TestCase):
    def test_bound_originals_are_preserved(self):
        files,v=s.bound_saved();self.assertEqual(v['native_processes'],0)
        self.assertEqual(files['shared-route.c'],(s.e.ROOT/s.C).read_bytes())
    def test_relative_tracked_source_is_passed_unchanged(self):
        command=['cc','-MMD',s.C,'-lmgba','-o','runner']
        self.assertIs(s.compile_command(command),command)
    def test_missing_duplicate_or_accepted_source_is_rejected(self):
        for command in (['cc','-MMD'],['cc','-MMD',s.C,s.C],['cc','-MMD',str(s.e.ROOT/s.C)],['cc','-MMD',s.C,s.r.o.s.C]):
            with self.subTest(command=command),self.assertRaises(ValueError):s.compile_command(command)
    def test_driver_uses_saved_source_and_unchanged_shared_validator(self):
        source=(s.e.ROOT/s.SELF).read_text()
        self.assertIn('e.SELF,e.TEST,e.C=SELF,TEST,C',source)
        self.assertIn('e.x.validate=r.validate',source)
        self.assertNotIn('derived_source(',source)
        self.assertNotIn('write_text(',source)


if __name__=='__main__':unittest.main()
