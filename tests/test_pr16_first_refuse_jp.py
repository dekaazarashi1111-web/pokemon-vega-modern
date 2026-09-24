"""日本語版RAM訂正と、今回変更なし20unitの原本再利用だけを限定検査。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_first_refuse_jp as j


class JapaneseBindingTests(unittest.TestCase):
    def setUp(self):
        self.folder=j.f.ROOT/j.f.EVIDENCE/str(j.PRIOR)
        self.v=j.f.load(self.folder/'verification.json')
        self.read=lambda leaf:(self.folder/leaf).read_bytes()
        self.source=lambda path:(j.f.ROOT/path).read_bytes()
    def test_active_japanese_symbol_not_english_comment(self):
        c=(j.f.ROOT/j.f.C).read_text()
        self.assertIn('#define X_SCRIPT_SLOT 0x02023CD4U',c)
        self.assertNotIn('0x02023D74U',c)
        self.assertIn('read32(c,X_SCRIPT_SLOT)',c)
    def test_reuse_only_unchanged_successful_units(self):
        r=j.reuse(self.v,self.read,self.source)
        self.assertEqual(r['unchanged_unit_tests_reused'],20)
        self.assertEqual(r['changed_native_structure_rechecked'],1)
        self.assertEqual(r['accepted_native_reruns'],0)
    def test_changed_raw_unit_proof_cannot_be_reused(self):
        with self.assertRaises(ValueError):j.reuse(self.v,lambda name:self.read(name)+b' ',self.source)
        v=copy.deepcopy(self.v);v['new_unit_tests']=20
        with self.assertRaises(ValueError):j.reuse(v,self.read,self.source)
    def test_changed_validator_or_oracle_cannot_be_reused(self):
        for changed in (j.f.SELF,j.f.TEST):
            with self.subTest(path=changed),self.assertRaises(ValueError):j.reuse(self.v,self.read,lambda path:self.source(path)+(b'\n' if path==changed else b''))


if __name__=='__main__':unittest.main()
