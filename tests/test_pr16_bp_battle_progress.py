"""初回native turnと既存launch証拠の境界を検査。emulator不要。"""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_bp_battle_progress as p
from tests import test_pr16_bp_selection_native as historical_tests

class ProgressTests(unittest.TestCase):
    def sample(self):
        row=historical_tests.ContractTests().sample()
        row.update(status=p.STATUS,case=p.CASE,scope=p.SCOPE,total_frames=4200,move_id=52,move_slot=0,pp_before=25,pp_after=24,move_menu_frame=3060,move_selected_frame=3061,pp_spent_frame=3500,action_return_frame=4200,player_hp_before=100,player_hp_after=88,enemy_hp_before=99,enemy_hp_after=65,native_turn_completed=True)
        return row
    def validate(self,row):
        return p.validate(json.dumps(row).encode(),b'BP_CTRL label=fixture \nBP_READ name=cfru_selected_order \nBP_LAUNCH label=before-confirm \nBP_LAUNCH label=launch-stop \nBP_READ name=enemy_party_generated \nBP_PROGRESS move=\nBP_CTRL label=first-turn-return ',0)
    def test_valid(self):self.assertTrue(self.validate(self.sample())['native_turn_completed'])
    def test_not_merely_launch_or_false_reward(self):
        for key,value in [('pp_after',25),('pp_spent_frame',True),('action_return_frame',3500),('native_turn_completed',1),('bp_earned',9),('native_bp_earning_accepted',True),('release_ready',True),('total_frames',4201),('move_slot',4),('move_id',0)]:
            with self.subTest(key=key):
                row=self.sample();row[key]=value
                with self.assertRaises(ValueError):self.validate(row)
    def test_reject_extra_and_absent_fields(self):
        row=self.sample();row['unobserved']=1
        with self.assertRaises(ValueError):self.validate(row)
        row=self.sample();del row['pp_spent_frame']
        with self.assertRaises(ValueError):self.validate(row)
    def test_derivation_rejects_missing_and_duplicate_anchor(self):
        for text in ('none','aa'):
            with self.assertRaises(ValueError):p.replace_once(text,'a','b')
    def test_derivation_and_guard_boundary(self):
        text=p.assemble_controller()
        self.assertEqual(text.count('struct BPProgress progress=bp_progress(c);'),1)
        self.assertIn(p.STATUS,text)
        after=text.split('a_guard(c);bp_open(c);',1)[1]
        extension=(p.ROOT/p.SOURCE).read_text()
        for value in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'busWrite', 'rawWrite'):
            self.assertNotIn(value,after);self.assertNotIn(value,extension)
    def test_historical_source_pin(self):
        self.assertTrue(p.checked_text(p.ROOT/p.OLD_DRIVER,p.DRIVER_SHA))
        with self.assertRaises(ValueError):p.checked_text(p.ROOT/p.OLD_DRIVER,'0'*64)

if __name__=='__main__':unittest.main()
