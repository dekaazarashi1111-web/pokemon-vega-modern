"""Diagnostic contract is deliberately distinct from BP earning acceptance."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_bp_selection_native as p
class ContractTests(unittest.TestCase):
    def sample(self):
        return dict(schema_version=1,status=p.STATUS,scope='PR16_P05_THREE_SELECTION_DIAGNOSTIC',case=p.CASE,candidate_sha256=p.SHA,
          selected_count=3,party_count=3,original_snapshot_bytes_verified=600,bp_earned=0,battle_started=False,save_counter=2,
          manual_saves=0,fresh_cores=1,host_write_barriers=7,input_only_after_guard=True,fixture_same_as_accepted_cancel=True,
          native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,warnings_errors=0,
          selected_frame=1000,second_chooser_frame=2000,total_frames=2000)
    def validate(self,row):return p.validate(json.dumps(row).encode(),b'BP_CTRL label=fixture \nBP_READ name=cfru_selected_order ',0)
    def test_declared_diagnostic(self):self.assertFalse(self.validate(self.sample())['native_bp_earning_accepted'])
    def test_not_earning(self):
        row=self.sample();row['bp_earned']=9
        with self.assertRaises(ValueError):self.validate(row)
    def test_not_closed(self):
        row=self.sample();row['p05_native_bp_gap_closed']=True
        with self.assertRaises(ValueError):self.validate(row)
    def test_not_previous_candidate(self):
        row=self.sample();row['candidate_sha256']=p.previous.layer.PARENT_SHA
        with self.assertRaises(ValueError):self.validate(row)
    def test_no_frame_boolean(self):
        row=self.sample();row['selected_frame']=True
        with self.assertRaises(ValueError):self.validate(row)
    def test_no_missing_read(self):
        with self.assertRaises(ValueError):p.validate(json.dumps(self.sample()).encode(),b'',0)
    def test_no_nonzero_exit(self):
        with self.assertRaises(ValueError):p.validate(json.dumps(self.sample()).encode(),b'',1)
    def test_guard_before_observation(self):
        text=(p.ROOT/p.SOURCE).read_text();after=text.split('a_guard(c);bp_open(c);',1)[1]
        for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving('):self.assertNotIn(forbidden,after)
if __name__=='__main__':unittest.main()
