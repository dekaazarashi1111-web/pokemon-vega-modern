"""保存manifestによる限定P05投影テスト。native原本再生成・ABI再実行は行わない。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_tail_ci_closeout as m
import test_modernization_p08_forgetting_evidence as original


class CloseoutTests(unittest.TestCase):
    def case(self):
        case=original.CurrentRemainingWorkOwnershipTests('test_current_snapshot_preserves_later_checkpoint_fields')
        # build/native再検証ではなく、保存済みacceptance manifestだけを渡す。
        case.acceptance=m.s.load(original.record.MANIFEST)
        case.tracked=m.s.load(original.record.OVERVIEW)
        return case

    def rejects(self,change):
        case=self.case(); data=copy.deepcopy(case.tracked); change(data); case.tracked=data
        with patch.object(original.record,'current_remaining_work',return_value=data):
            with self.assertRaises(AssertionError):case.test_current_snapshot_preserves_later_checkpoint_fields()

    @staticmethod
    def p05(data):
        return next(r for r in data['remaining_conditions'] if r['id']=='NATURAL_CAPTURE_GEAR')

    def test_current_projection_with_saved_acceptance(self):
        self.case().test_current_snapshot_preserves_later_checkpoint_fields()

    def test_stale_three_status_rejected(self):
        self.rejects(lambda d:self.p05(d).update(status='PENDING_THREE_BOUND_NATIVE_SUPPLY_ACCEPTANCES'))

    def test_bp_reopening_rejected(self):
        self.rejects(lambda d:self.p05(d)['remaining_supply_gap_ids'].append('P05_NATIVE_BP_EARNING_PHYSICAL'))

    def test_ring_false_completion_rejected(self):
        self.rejects(lambda d:self.p05(d)['remaining_supply_gap_ids'].remove('P05_NATIVE_RING_ACQUISITION_PHYSICAL'))

    def test_policy_false_completion_rejected(self):
        self.rejects(lambda d:self.p05(d)['remaining_supply_gap_ids'].remove('P05_ORDINARY_POLICY_SELECTION_PHYSICAL'))

    def test_bp_case_count_bound(self):
        self.rejects(lambda d:d['bp_chooser_checkpoint'].update(accepted_case_count=2))

    def test_bp_run_bound(self):
        self.rejects(lambda d:d['bp_chooser_checkpoint'].update(latest_native_run=0))

    def test_full_p05_not_promoted(self):
        self.rejects(lambda d:d.update(full_p05_acceptance=True))

    def test_prior_tail_is_only_read(self):
        prior=m.s.load(m.PRIOR); before=copy.deepcopy(prior)
        m.validate_prior(prior); self.assertEqual(before,prior)

    def test_prior_tail_unconditional_return_rejected(self):
        prior=m.s.load(m.PRIOR); prior['analysis']['callee_return_proven']=True
        with self.assertRaises(ValueError):m.validate_prior(prior)

    def test_failure_original_not_success(self):
        run=dict(id=m.FAILURE_RUN,head_sha=m.ABI_HEAD,status='completed',conclusion='failure')
        self.assertEqual(m.validate_failure(run)['conclusion'],'failure')
        run['conclusion']='success'
        with self.assertRaises(ValueError):m.validate_failure(run)

    def test_patch_block_unique_and_bounded(self):
        text='prefix\n'+m.OLD_BLOCK+'suffix\n'
        self.assertEqual(m.expected_source(text),'prefix\n'+m.NEW_BLOCK+'suffix\n')
        for invalid in ('unrelated',m.OLD_BLOCK*2):
            with self.assertRaises(ValueError):m.expected_source(invalid)


if __name__=='__main__':unittest.main()
