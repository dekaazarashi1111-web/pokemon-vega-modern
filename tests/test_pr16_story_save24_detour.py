"""新東通路controllerだけを検証。旧32試験/nativeを再走しない。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save24_detour as d
from test_pr16_story_save24_measure import obs,Fake


class DetourTests(unittest.TestCase):
    def test_route(self):
        self.assertEqual(d.ROUTE,[[x,3] for x in range(20,32)]+[[31,4]])
    def test_no_rejected_edge(self):
        self.assertNotIn([27,5],d.ROUTE)
    def test_walk(self):
        f=Fake(d.ROUTE[1:]);o,steps=d.walk(f)
        self.assertEqual(o['xy'],[31,4]);self.assertEqual(len(steps),12)
    def test_turn(self):
        f=Fake(d.ROUTE[1:-1]+[[31,3],[31,4]])
        self.assertEqual(len(d.walk(f)[1]),12)
    def test_block_bounded(self):
        f=Fake([d.ROUTE[0]]*3)
        with self.assertRaises(ValueError):d.walk(f)
        self.assertEqual(len(f.inputs),3)
    def test_other_tile(self):
        f=Fake([[20,4]])
        with self.assertRaises(ValueError):d.walk(f)
    def test_wrong_map(self):
        f=Fake([dict(obs([21,3]),map=[1,36])])
        with self.assertRaises(ValueError):d.walk(f)
    def test_wrong_save(self):
        f=Fake([dict(obs([21,3]),save_counter=24)])
        with self.assertRaises(ValueError):d.walk(f)
    def test_hidden_flash(self):
        f=Fake([dict(obs([21,3]),flash_sha256='0'*64)])
        with self.assertRaises(ValueError):d.walk(f)
    def test_wild_is_next_scope(self):
        f=Fake([dict(obs([21,3]),battle_outcome=4)])
        with self.assertRaises(ValueError):d.walk(f)
    def test_trainer_is_next_scope(self):
        f=Fake([dict(obs([21,3]),battle_flags=12)])
        with self.assertRaises(ValueError):d.walk(f)
    def test_wrong_parent(self):
        f=Fake([]);f.last=obs([27,4])
        with self.assertRaises(ValueError):d.walk(f)


if __name__=='__main__':unittest.main()
