"""観測前の1マス移動差分だけを受け入れる新規検査。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_collection_gift_step as step
class StepTests(unittest.TestCase):
    def test_pre_barrier_only_and_mutation_rejected(self):
        raw=(step.ROOT/step.C).read_bytes();old=step.normalized_controller(raw)
        self.assertEqual(raw.split(b'cf_t.boundary=b_frames;',1)[1],old.split(b'cf_t.boundary=b_frames;',1)[1])
        self.assertIn(b'b_step(c,QOL_KEY_UP);b_state(c,"fixture-approach")',raw)
        with self.assertRaises(ValueError):step.normalized_controller(raw.replace(b'cf_watching=true',b'cf_watching=false'))
        with self.assertRaises(ValueError):step.normalized_controller(old)
if __name__=='__main__':unittest.main()
