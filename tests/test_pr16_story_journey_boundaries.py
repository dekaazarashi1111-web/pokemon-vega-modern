"""境界集約だけの検査。旧native/旧受入検査は起動しない。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_story_journey_boundaries as m


def obs(n, callback, flags, outcome, lock=1):
    return dict(observe=n, frame=n*100, callback2=callback, battle_flags=flags,
                battle_outcome=outcome, lock=lock)


class JourneyBoundariesTests(unittest.TestCase):
    def setUp(self):
        self.rows = [obs(0,m.FIELD_CALLBACK,0,0,0), obs(1,m.BATTLE_CALLBACK,12,0),
                     obs(2,m.BATTLE_CALLBACK,12,2), obs(3,m.FIELD_CALLBACK,12,2),
                     obs(4,m.FIELD_CALLBACK,12,2,0), obs(5,m.BATTLE_CALLBACK,4,0),
                     obs(6,m.BATTLE_CALLBACK,4,4), obs(7,m.FIELD_CALLBACK,4,4,0)]
    def test_separate_loss_escape_and_lingering_state(self):
        self.assertEqual(m.episodes(self.rows), [dict(start=1,end=3,kind='trainer',outcome=2),
                                               dict(start=5,end=7,kind='wild',outcome=4)])
        self.assertEqual(m.counts(self.rows), dict(wild_victories=0,wild_escapes=1,wild_losses=0,
                                                 trainer_victories=0,trainer_losses=1))
    def test_wild_victory_at_field_return(self):
        self.assertEqual(m.counts([obs(0,m.BATTLE_CALLBACK,4,0),obs(1,m.FIELD_CALLBACK,4,1,0)])['wild_victories'],1)
    def test_reject_unfinished(self):
        with self.assertRaises(ValueError): m.episodes(self.rows[:-1])
    def test_reject_missing_start(self):
        with self.assertRaises(ValueError): m.episodes(self.rows[2:])
    def test_reject_outcome_relabel(self):
        self.rows[3]['battle_outcome']=1
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_reject_flags_relabel(self):
        self.rows[2]['battle_flags']=4
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_reject_trainer_escape(self):
        self.rows[2]['battle_outcome']=self.rows[3]['battle_outcome']=4
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_reject_time_rewind(self):
        self.rows[4]['frame']=0
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_reject_boolean_state(self):
        self.rows[2]['battle_outcome']=True
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_reject_unknown_state(self):
        self.rows[2]['battle_outcome']=8
        with self.assertRaises(ValueError): m.episodes(self.rows)
    def test_reject_empty(self):
        with self.assertRaises(ValueError): m.episodes([])
    def test_no_mutation(self):
        original=copy.deepcopy(self.rows);m.episodes(self.rows);self.assertEqual(original,self.rows)

if __name__ == '__main__': unittest.main()
