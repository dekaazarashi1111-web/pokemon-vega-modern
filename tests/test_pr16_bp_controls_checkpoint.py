"""Retained-original checks only; no simulator is started."""
import copy
import io
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_controls_checkpoint as ck


class BPControlCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={p[0]:(ROOT/ck.BASE/str(p[0])/'original.zip').read_bytes() for p in ck.PINS}

    def test_preflight_failure_stays_zero_native_runs(self):
        row,info=ck.validate(self.raw[ck.PINS[0][0]],ck.PINS[0])
        self.assertIsNone(row)
        self.assertEqual(info['actual_new_processes'],0)
        self.assertEqual(info['accepted_controls'],0)
        self.assertEqual(info['actions_conclusion'],'failure')

    def test_only_the_original_native_reception_control_is_accepted(self):
        row,info=ck.validate(self.raw[ck.PINS[1][0]],ck.PINS[1])
        self.assertEqual(info['actual_new_processes'],1)
        self.assertEqual(row['name'],'reception-cancel-unchanged')
        self.assertFalse(row['result']['physical_bp_earning_accepted'])
        self.assertFalse(row['result']['native_rental_selection_entry'])
        self.assertEqual(row['result']['bp_earned'],0)
        self.assertEqual(row['result']['manual_saves'],0)
        self.assertEqual(len(row['screens']),4)

    def test_changed_outer_archive_rejected(self):
        for p in ck.PINS:
            with self.subTest(run=p[0]),self.assertRaises(ValueError):
                ck.validate(self.raw[p[0]]+b'changed',p)

    def test_source_snapshot_member_not_just_zip_identity(self):
        p=ck.PINS[1]
        with zipfile.ZipFile(io.BytesIO(self.raw[p[0]])) as z:
            report=ck.load(z.read('pr16-bp-native-controls/result.json'))
            bindings=copy.deepcopy(report['sources'])
            bindings['tools/mgba_pr16_bp_native_controls.c']['sha256']='0'*64
            with self.assertRaises(ValueError):
                ck.sources(z.read('pr16-bp-native-controls/sources.zip'),bindings,p[3],None)

    def test_source_tested_head_cannot_be_relabelled(self):
        p=list(ck.PINS[1]);p[3]='0'*40
        with self.assertRaises(ValueError):ck.validate(self.raw[p[0]],tuple(p))

    def test_p08_does_not_close_or_reopen_any_gap(self):
        before=ck.load((ROOT/ck.close.P08).read_bytes())
        after=ck.update_p08(copy.deepcopy(before))
        for key in before:
            if key not in ('remaining_conditions','p05_native_bp_control_checkpoint'):
                self.assertEqual(before[key],after[key])
        for left,right in zip(before['remaining_conditions'],after['remaining_conditions']):
            if left['id']=='NATURAL_CAPTURE_GEAR':
                self.assertEqual({k:v for k,v in left.items() if k not in ('resume','native_bp_negative_controls')},
                                 {k:v for k,v in right.items() if k not in ('resume','native_bp_negative_controls')})
                self.assertEqual(len(right['remaining_supply_gap_ids']),3)
                self.assertFalse(right['supply_physical_acceptance_complete'])
            else:self.assertEqual(left,right)
        self.assertEqual(ck.update_p08(copy.deepcopy(after)),after)

    def test_p08_rejects_changed_supply_scope(self):
        data=ck.load((ROOT/ck.close.P08).read_bytes())
        row=next(r for r in data['remaining_conditions'] if r['id']=='NATURAL_CAPTURE_GEAR')
        row['remaining_supply_gap_ids'].remove('P05_NATIVE_BP_EARNING_PHYSICAL')
        with self.assertRaises(ValueError):ck.update_p08(data)

    def test_p08_never_promotes_release(self):
        data=ck.load((ROOT/ck.close.P08).read_bytes());data['release_ready']=True
        with self.assertRaises(ValueError):ck.update_p08(data)


if __name__=='__main__':unittest.main()
