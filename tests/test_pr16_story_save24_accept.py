"""新しい東通路の全原本と拒否境界。旧native/51controller試験は再実行しない。"""
import copy
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save24_accept as a


class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(os.environ['PR16_SAVE24_ORIGINAL'])
        cls.pa=a.d.m.shared.trace(p/'progress',a.d.m.prior.OUTPUT)
        cls.pb=a.d.m.shared.trace(p/'continue',a.OUTPUT)
    def reject(self,lane,index,key,value):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb)
        (pa if lane=='progress' else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    def test_positive(self):
        v=a.semantics(self.pa,self.pb)
        self.assertFalse(v['teleport_accepted']);self.assertFalse(v['save_success_wording_observed'])
    def test_map(self):self.reject('progress',13,'map',[1,36])
    def test_xy(self):self.reject('progress',13,'xy',[19,14])
    def test_lag(self):self.reject('progress',13,'live_xy',[31,4])
    def test_facing(self):self.reject('progress',13,'facing',4)
    def test_party_count(self):self.reject('progress',13,'party_count',3)
    def test_party_bytes(self):self.reject('progress',13,'party_sha256','0'*64)
    def test_ledger(self):self.reject('progress',13,'ledger_sha256','0'*64)
    def test_rp(self):self.reject('progress',13,'rp',1)
    def test_trainer(self):self.reject('progress',13,'battle_flags',12)
    def test_victory(self):self.reject('progress',13,'battle_outcome',1)
    def test_callback(self):self.reject('progress',13,'callback2',a.d.m.prior.parent.BATTLE)
    def test_early_save(self):self.reject('progress',16,'save_counter',24)
    def test_partial_field(self):self.reject('progress',17,'field',True)
    def test_partial_flash(self):self.reject('progress',18,'flash_sha256',a.FLASH)
    def test_unfinished_save(self):self.reject('progress',19,'save_counter',23)
    def test_unfinished_lock(self):self.reject('progress',19,'lock',1)
    def test_wrong_flash(self):self.reject('progress',19,'flash_sha256',a.d.m.prior.FLASH)
    def test_cold_move(self):self.reject('continue',0,'xy',[31,5])
    def test_cold_flash(self):self.reject('continue',1,'flash_sha256','0'*64)
    def test_cold_battle(self):self.reject('continue',1,'battle_outcome',4)
    def test_input_count(self):
        p=copy.deepcopy(self.pa);p['end']['inputs']+=1
        with self.assertRaises(ValueError):a.semantics(p,self.pb)
    def test_frame_count(self):
        p=copy.deepcopy(self.pb);p['end']['frames']+=1
        with self.assertRaises(ValueError):a.semantics(self.pa,p)
    def test_missing_observation(self):
        p=copy.deepcopy(self.pa);p['observations'].pop()
        with self.assertRaises(ValueError):a.semantics(p,self.pb)


if __name__=='__main__':unittest.main()
