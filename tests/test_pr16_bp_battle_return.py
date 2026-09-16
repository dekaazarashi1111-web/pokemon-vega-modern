"""未観測の勝敗/AfterBattleだけを追加し、過去受入・原本は変更しない。"""
import json
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_bp_battle_return as p
from tests.test_pr16_bp_battle_progress import ProgressTests

class ReturnTests(unittest.TestCase):
    def sample(self,outcome=1):
        row=ProgressTests().sample()
        row.update(status=p.STATUS,case=p.CASE,scope=p.SCOPE,total_frames=9000,
            return_start_frame=4200,additional_turns=8,forced_switches=2,additional_pp_events=7,
            battle_outcome=outcome,outcome_frame=8200,facility_return_frame=9000,
            final_party_count=3 if outcome==1 else 1,final_marker=2 if outcome==1 else 0,
            final_snapshot_valid=1 if outcome==1 else 0,final_reward_pending=1 if outcome==1 else 0,
            final_streak=1 if outcome==1 else 0,final_script_pointer=0x092CF690,final_callback2=0x08056789,
            native_afterbattle_observed=True,original_party_or_snapshot_bytes_verified=600)
        return row
    def check(self,row,code=0,extra=b''):
        stderr=(b'BP_CTRL label=fixture \nBP_READ name=cfru_selected_order \nBP_LAUNCH label=before-confirm \n'
            b'BP_LAUNCH label=launch-stop \nBP_READ name=enemy_party_generated \nBP_PROGRESS move=\n'
            b'BP_CTRL label=first-turn-return \nBP_RETURN label=extension-start \nBP_RETURN label=facility-stop ')+extra
        return p.validate(json.dumps(row).encode(),stderr,code)
    def test_win_observations(self):self.assertEqual(self.check(self.sample())['final_reward_pending'],1)
    def test_loss_observations(self):self.assertEqual(self.check(self.sample(2))['final_snapshot_valid'],0)
    def test_no_inflation_or_timing_relaxation(self):
        for key,value in [('battle_outcome',3),('battle_outcome',True),('additional_turns',0),('forced_switches',3),
            ('additional_pp_events',9),('final_streak',3),('final_reward_pending',0),('bp_earned',9),
            ('native_bp_earning_accepted',True),('release_ready',True),('native_afterbattle_observed',1),
            ('facility_return_frame',9001),('outcome_frame',4200),('return_start_frame',4000),
            ('original_party_or_snapshot_bytes_verified',599),('total_frames',True),('final_callback2',0)]:
            with self.subTest(key=key,value=value):
                row=self.sample();row[key]=value
                with self.assertRaises(ValueError):self.check(row)
    def test_loss_must_restore_original(self):
        row=self.sample(2);row['final_party_count']=3
        with self.assertRaises(ValueError):self.check(row)
    def test_extra_missing_and_process_failure(self):
        row=self.sample();row['invented_success']=True
        with self.assertRaises(ValueError):self.check(row)
        row=self.sample();del row['outcome_frame']
        with self.assertRaises(ValueError):self.check(row)
        with self.assertRaises(ValueError):self.check(self.sample(),1)
    def test_old_source_pin_and_append_only_derivation(self):
        text=p.assemble_controller()
        self.assertEqual(text.count('struct BPReturn finish=br_battle_return(c,party,counter);'),1)
        self.assertEqual(text.count('struct BPProgress progress=bp_progress(c);'),1)
        after=text.split('a_guard(c);bp_open(c);',1)[1]
        fragment=(p.ROOT/p.SOURCE).read_text()
        for term in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'busWrite', 'rawWrite'):
            self.assertNotIn(term,after);self.assertNotIn(term,fragment)
        for name,sha in p.PINS.items():self.assertTrue(p.checked_text(p.ROOT/name,sha))
    def test_trace_required(self):
        with self.assertRaises(ValueError):p.validate(json.dumps(self.sample()).encode(),b'',0)

if __name__=='__main__':unittest.main()
