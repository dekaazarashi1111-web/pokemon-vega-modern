"""宣言hashからのtext復元を検査。未知の測定結果を期待値へ昇格しない。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save22_measure as t

class TextRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=t.m.load((ROOT/t.SPEC).read_bytes());cls.p=t.m.plan()
        cls.a=t.m.inflate(cls.p['progress']['development_stdout_zlib_b85'])
        cls.b=t.m.inflate(cls.p['continue']['development_stdout_zlib_b85'])
    def reject(self,change):
        s=deepcopy(self.s);change(s)
        with self.assertRaises(ValueError):t.restore_plan(s,self.a,self.b)
    def test_exact_original_text(self):
        b,raw=t.restore_plan(self.s,self.a,self.b)
        self.assertEqual(b,(ROOT/t.m.DEV/'expected.json').read_bytes())
        self.assertEqual(raw['continue'],self.b)
    def test_predetermined_progress_digest(self):
        with self.assertRaises(ValueError):t.restore_plan(self.s,self.a[:-1]+b'!',self.b)
    def test_predetermined_cold_prefix(self):
        with self.assertRaises(ValueError):t.restore_plan(self.s,self.a,b'!'+self.b[1:])
    def test_whole_expected_digest(self):self.reject(lambda s:s['expected_json'].update(sha256='0'*64))
    def test_visual_annotation_cannot_drift(self):self.reject(lambda s:s['template']['visual_review'][0].update(note_ja='別の説明'))
    def test_cold_end_not_predicted_success(self):self.reject(lambda s:s.update(development_cold_end='{}\n'))
    def test_declared_source_parent_cannot_drift(self):self.reject(lambda s:s['template'].update(development_source_parent='0'*40))
    def test_command_round_trip(self):
        self.assertEqual(t.input_commands(self.s),t.m.decode_plan(self.p))
    def test_command_digest_cannot_drift(self):
        s=deepcopy(self.s);s['template']['progress']['commands']['size']+=1
        with self.assertRaises(ValueError):t.input_commands(s)
    def test_cold_prefix_cannot_be_replaced(self):
        s=deepcopy(self.s);s['template']['continue']['commands_zlib_b85']=s['template']['progress']['commands_zlib_b85']
        s['template']['continue']['commands']=s['template']['progress']['commands']
        with self.assertRaises(ValueError):t.input_commands(s)
if __name__=='__main__':unittest.main()
