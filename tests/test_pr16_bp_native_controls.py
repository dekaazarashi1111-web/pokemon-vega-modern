"""Source-only strict-result tests; synthetic rows are never native evidence."""
import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_native_controls as bp


class NativeBPControlTests(unittest.TestCase):
    def sample(self,name):
        row=bp.expected(name);active=bp.TRACE if name==bp.CASES[1] else ('interaction','tier','cancel','field')
        w={k:(active.index(k)+1)*100 if k in active else 0 for k in bp.TRACE}
        row.update(save_counter_before=2,save_counter_before_manual=2,save_counter_after=2+row['manual_saves'],total_frames=max(w.values()),witness=w)
        return row
    def check(self,row,code=0,stderr=b'BP_CTRL label=fixture x\nBP_CTRL label=returned x\n'):
        return bp.validate(bp.stable(row),stderr,row['case'],code)
    def test_two_scoped_synthetic_shapes(self):
        for name in bp.CASES:
            with self.subTest(name=name):self.assertEqual(self.check(self.sample(name)),self.sample(name))
    def test_explicit_unique_known_requests(self):
        self.assertEqual(bp.selected(list(bp.CASES)),list(bp.CASES))
        for names in (None,[],[bp.CASES[0]]*2,['unknown'],'reception-cancel-unchanged'):
            with self.subTest(names=names),self.assertRaises(ValueError):bp.selected(names)
    def test_positive_reward_or_gap_promotion_rejected(self):
        for key,value in (('bp_earned',9),('bp_after',9),('physical_bp_earning_accepted',True),('p05_native_bp_gap_closed',True),('release_ready',True),('input_only_after_guard',False)):
            row=self.sample(bp.CASES[1]);row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(row)
    def test_exit_skip_signal_bool_rejected(self):
        for code in (False,True,1,77,-9,None):
            with self.subTest(code=code),self.assertRaises(ValueError):self.check(self.sample(bp.CASES[0]),code)
    def test_save_lifecycle_and_fresh_core_rejected(self):
        for key,value in (('save_counter_before_manual',3),('save_counter_after',2),('fresh_cores',1),('automatic_full_saves',1),('party_bytes_verified',100)):
            row=self.sample(bp.CASES[1]);row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(row)
    def test_missing_or_reordered_observation_rejected(self):
        for key in bp.TRACE:
            row=self.sample(bp.CASES[1]);row['witness'][key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(row)
    def test_reception_only_cannot_claim_rentals(self):
        row=self.sample(bp.CASES[0]);row['witness']['rentals']=150
        with self.assertRaises(ValueError):self.check(row)
    def test_warning_or_missing_trace_rejected(self):
        for text in (b'',b'mGBA[error]\nBP_CTRL label=fixture x\nBP_CTRL label=returned x\n'):
            with self.assertRaises(ValueError):self.check(self.sample(bp.CASES[0]),stderr=text)
    def test_schema_typed_values_duplicate_keys(self):
        row=self.sample(bp.CASES[1]);row['manual_saves']=True
        with self.assertRaises(ValueError):self.check(row)
        with self.assertRaises(ValueError):bp.validate(b'{"x":1,"x":2}',b'',bp.CASES[0],0)
    def test_candidate_must_be_exact_before_inspection(self):
        with self.assertRaises(ValueError):bp.oracle(b'not a ROM')


if __name__=='__main__':unittest.main()
