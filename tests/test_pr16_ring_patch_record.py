"""記録の改変拒否と冪等投影。受入済みnative/旧監査を再実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_patch_record as record


class PatchRecordTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads((record.ROOT / record.owner.REPORT).read_bytes())

    def fixtures(self):
        s = {'candidate': dict(self.value['candidate'], final_product_sha_fixed=False, full_candidate_regression_complete=False),
             'bp': {'spending_accepted': True}, 'latest_native_run': 34946969126,
             'remaining_physical_gap_ids': [record.GAP], 'next_action': {},
             'observed_head_checks': {}, 'do_not_repeat': []}
        b = {'remaining_conditions': [{'id': 'NATURAL_CAPTURE_GEAR', 'remaining_supply_gap_ids': [record.GAP],
              'selected_supply_entrypoints': {record.GAP: None}}]}
        return s, b

    def test_exact_success_receipt(self):
        self.assertIs(record.validate_metadata(self.value), self.value)

    def test_mutated_audit_rejected(self):
        self.value['ring_acquisition_accepted'] = True
        with self.assertRaises(ValueError): record.validate_metadata(self.value)

    def test_failed_run_rejected(self):
        self.value['verification']['run']['conclusion'] = 'failure'
        with self.assertRaises(ValueError): record.validate_metadata(self.value)

    def test_wrong_job_run_rejected(self):
        self.value['verification']['job']['run_id'] += 1
        with self.assertRaises(ValueError): record.validate_metadata(self.value)

    def test_wrong_artifact_rejected(self):
        self.value['verification']['artifact']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): record.validate_metadata(self.value)

    def test_skipped_tests_rejected(self):
        self.value['verification']['focused_tests']['skips'] = 1
        with self.assertRaises(ValueError): record.validate_metadata(self.value)

    def test_projection_idempotent_preserves_acceptance(self):
        s, b = self.fixtures(); original = copy.deepcopy((s, b))
        x, y = record.project(s, b, self.value)
        self.assertEqual((s, b), original)
        self.assertEqual(record.project(x, y, self.value), (x, y))
        self.assertEqual(x['latest_native_run'], 34946969126)
        self.assertIs(x['bp']['spending_accepted'], True)
        self.assertEqual(x['remaining_physical_gap_ids'], [record.GAP])
        self.assertIs(x['ring_patch_owner']['ring_acquisition_accepted'], False)

    def test_candidate_change_rejected(self):
        s, b = self.fixtures(); s['candidate']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): record.project(s, b, self.value)

    def test_bp_change_rejected(self):
        s, b = self.fixtures(); s['bp']['spending_accepted'] = False
        with self.assertRaises(ValueError): record.project(s, b, self.value)

    def test_already_closed_ring_rejected(self):
        s, b = self.fixtures(); s['remaining_physical_gap_ids'] = []
        with self.assertRaises(ValueError): record.project(s, b, self.value)

    def test_selected_owner_change_rejected(self):
        s, b = self.fixtures(); b['remaining_conditions'][0]['selected_supply_entrypoints'][record.GAP] = {'owner': 'new'}
        with self.assertRaises(ValueError): record.project(s, b, self.value)

    def test_release_promotion_rejected(self):
        s, b = self.fixtures(); s['candidate']['final_product_sha_fixed'] = True
        with self.assertRaises(ValueError): record.project(s, b, self.value)


if __name__ == '__main__': unittest.main()
