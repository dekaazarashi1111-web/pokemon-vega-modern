"""3連戦境界だけの新規試験。既受入native/旧試験を呼ばない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_story_ayame_chain as m


def fixture():
    seq = [(m.FIELD, 1, 0), (m.BATTLE, 1, 0), (m.PARTY_UI, 1, 0),
           (m.BATTLE, 1, 0), (m.BATTLE, 1, 1), (m.TRANSITION, 1, 1),
           (m.FIELD, 1, 1), (m.FIELD, 1, 1), (m.BATTLE, 1, 0),
           (m.BATTLE, 1, 1), (m.FIELD, 1, 1), (m.BATTLE, 1, 0),
           (m.BATTLE, 1, 1), (m.FIELD, 1, 1), (m.FIELD, 0, 1)]
    return [dict(observe=i, frame=100+i*10, callback2=cb, lock=lock,
                 battle_flags=12, battle_outcome=outcome, party_count=4,
                 save_counter=17, rp=0, map=[22, 1]) for i,(cb,lock,outcome) in enumerate(seq)]


class ChainTests(unittest.TestCase):
    def bad(self, index, key, value):
        rows = fixture(); rows[index][key] = value
        with self.assertRaises(ValueError): m.chain(rows)

    def test_complete_chain(self):
        result=m.chain(fixture())
        self.assertEqual([r['start'] for r in result['episodes']], [1,8,11])
        self.assertEqual(result['final_unlocked_field'],14)
        self.assertFalse(result['save_acceptance_claimed'])

    def test_party_ui_is_not_another_start(self):
        self.assertEqual(m.chain(fixture())['episodes'][0]['party_ui'],[2])

    def test_residual_field_victory_is_not_counted(self):
        self.assertEqual(m.chain(fixture())['trainer_victories'],3)

    def test_missing_battle_victory_rejected(self): self.bad(4,'battle_outcome',0)
    def test_next_battle_without_reset_rejected(self): self.bad(8,'battle_outcome',1)
    def test_early_unlock_rejected(self): self.bad(6,'lock',0)
    def test_missing_final_unlock_rejected(self): self.bad(14,'lock',1)
    def test_false_lock_rejected(self): self.bad(1,'lock',True)
    def test_frame_reordering_rejected(self): self.bad(4,'frame',120)
    def test_missing_observation_rejected(self): self.bad(5,'observe',6)
    def test_wild_flags_rejected(self): self.bad(8,'battle_flags',0)
    def test_loss_rejected(self): self.bad(9,'battle_outcome',2)
    def test_escape_rejected(self): self.bad(9,'battle_outcome',4)
    def test_capture_rejected(self): self.bad(9,'battle_outcome',7)
    def test_unexplained_callback_rejected(self): self.bad(5,'callback2',123)
    def test_unlocked_transition_rejected(self): self.bad(5,'lock',0)
    def test_map_change_rejected(self): self.bad(8,'map',[3,11])
    def test_changed_party_rejected(self): self.bad(8,'party_count',3)
    def test_precompletion_save_rejected(self): self.bad(8,'save_counter',18)
    def test_rp_change_rejected(self): self.bad(8,'rp',1)
    def test_win_reset_in_active_battle_rejected(self):
        rows=fixture(); rows[3]['battle_outcome']=1; rows[4]['battle_outcome']=0
        with self.assertRaises(ValueError): m.chain(rows)
    def test_unlocked_approach_rejected(self): self.bad(0,'lock',0)
    def test_fourth_battle_rejected(self):
        rows=fixture(); extra=copy.deepcopy(rows[11]); extra.update(observe=15,frame=250); rows.append(extra)
        with self.assertRaises(ValueError): m.chain(rows)
    def test_incomplete_chain_rejected(self):
        with self.assertRaises(ValueError): m.chain(fixture()[:12])
    def test_empty_and_boolean_inputs_rejected(self):
        for rows in ([],True,[{}]):
            with self.assertRaises(ValueError): m.chain(rows)


if __name__ == '__main__': unittest.main()
