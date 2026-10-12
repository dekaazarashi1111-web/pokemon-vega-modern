"""新区間の観測欠落/型誤りを拒否。ゲームと旧nativeは起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_story_journey_boundaries as m

class JourneySequenceTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(observe=i, frame=i*100, callback2=c, battle_flags=f,
                          battle_outcome=o, lock=k) for i,c,f,o,k in
                     [(0,m.FIELD_CALLBACK,0,0,0),(1,m.BATTLE_CALLBACK,4,0,1),
                      (2,m.BATTLE_CALLBACK,4,1,1),(3,m.FIELD_CALLBACK,4,1,0)]]
    def reject(self, key, value):
        self.rows[2][key]=value
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_boolean_observe(self): self.reject('observe',True)
    def test_negative_observe(self): self.reject('observe',-1)
    def test_negative_frame(self): self.reject('frame',-1)
    def test_duplicate_observe(self): self.reject('observe',1)
    def test_missing_observe(self): self.reject('observe',3)
    def test_reverse_observe(self): self.reject('observe',0)
    def test_boolean_callback(self): self.reject('callback2',True)
    def test_float_callback(self): self.reject('callback2',float(m.BATTLE_CALLBACK))
    def test_negative_callback(self): self.reject('callback2',-1)
    def test_out_of_range_callback(self): self.reject('callback2',2**32)
    def test_invalid_lock(self): self.reject('lock',2)
    def test_negative_flags(self): self.reject('battle_flags',-1)
    def test_negative_outcome(self): self.reject('battle_outcome',-1)
    def test_same_frame_is_observation_not_new_battle(self):
        self.rows[2]['frame']=self.rows[1]['frame']
        self.assertEqual(m.counts(self.rows)['wild_victories'],1)
    def test_lingering_field_alone_is_not_victory(self):
        self.assertEqual(sum(m.counts([self.rows[-1]]).values()),0)
    def test_no_mutation(self):
        original=copy.deepcopy(self.rows)
        self.assertEqual(m.episodes(self.rows),[dict(start=1,end=3,kind='wild',outcome=1)])
        self.assertEqual(self.rows,original)

if __name__=='__main__': unittest.main()
