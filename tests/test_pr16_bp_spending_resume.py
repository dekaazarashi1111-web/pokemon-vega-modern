"""通常BP購入の正式受入を、原stdout・保存再開・台帳の三方で固定する。"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('resume_spending_tests', ROOT/'scripts/pr16_resume.py')
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


class SpendingResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        raw = {
            'scope': 'PR16_P05_NATIVE_BP_SPENDING_PHYSICAL',
            'status': 'PASS_NATIVE_BP_SPENDING_SAVE_CONTINUE',
            'base_reward_bp': 9, 'active_repeat_reward_bp': 3, 'reward_wrapper_saves': 3,
            'bp_before_purchase': 12, 'bp_after_purchase': 8, 'bp_after_continue': 8,
            'item_id': 195, 'catalog_index': 0, 'price_bp': 4, 'purchase_result': 0,
            'item_count_before': 0, 'item_count_after_purchase': 1, 'item_count_after_continue': 1,
            'save_counter_before_purchase': 5, 'save_counter_after_purchase': 6,
            'save_counter_after_manual': 7, 'save_counter_after_continue': 7,
            'physical_shop_local_id': 3, 'automatic_saves': 1, 'manual_saves': 1,
            'fresh_cores': 2, 'p05_native_bp_spending_closed': True,
            'reward_complete_frame': 45322, 'reward_settled_frame': 46889,
            'reward_field_frame': 46950, 'shop_interaction_frame': 47139,
            'shop_menu_frame': 47320, 'purchase_frame': 47857,
            'manual_save_frame': 49410, 'continue_frame': 51832, 'total_frames': 51832,
            'battle_outcome': 1, 'second_battle_outcome': 1, 'third_battle_outcome': 1,
        }
        body = (json.dumps(raw)+'\n').encode()
        (self.root/'original.json').write_bytes(body)
        row = dict(raw, first_battle_outcome=1, native_battle_wins_observed=3)
        self.d = {'native_result': row,
                  'process': {'raw_native_fresh_cores': 2},
                  'verification': {'native_validator_passed': True,
                    'visual_review': {'completed': True},
                    'raw_result': {'path': 'original.json', 'size': len(body),
                                   'sha256': hashlib.sha256(body).hexdigest()}}}
        self.s = {'latest_native_evidence': 'accepted.json', 'bp': copy.deepcopy(row)}
        self.control = {'physical_bp_spending_accepted': True,
                        'spending_success_evidence': 'accepted.json'}

    def check(self):
        resume.validate_spending(self.root, self.d, self.s, self.control)

    def test_exact_purchase_and_continue_read_only(self):
        before = (self.root/'original.json').read_bytes()
        self.check()
        self.assertEqual(before, (self.root/'original.json').read_bytes())

    def test_debit_item_save_core_and_index_mutations_rejected(self):
        row = copy.deepcopy(self.d['native_result'])
        for key in ('bp_before_purchase', 'bp_after_purchase', 'bp_after_continue',
                    'item_id', 'catalog_index', 'price_bp', 'purchase_result',
                    'item_count_before', 'item_count_after_purchase', 'item_count_after_continue',
                    'save_counter_before_purchase', 'save_counter_after_purchase',
                    'save_counter_after_manual', 'save_counter_after_continue', 'fresh_cores'):
            with self.subTest(key=key):
                self.d['native_result'] = dict(row, **{key: row[key]+1})
                with self.assertRaisesRegex(ValueError, key): self.check()
        self.d['native_result'] = row

    def test_boolean_cannot_substitute_numeric_quantity(self):
        self.d['native_result']['item_count_after_continue'] = True
        with self.assertRaisesRegex(ValueError, 'item_count_after_continue'): self.check()

    def test_frame_order_must_extend_reward(self):
        self.d['native_result']['purchase_frame'] = 45322
        with self.assertRaisesRegex(ValueError, 'frame chain'): self.check()

    def test_original_hash_and_projection_are_required(self):
        self.d['verification']['raw_result']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'raw identity'): self.check()
        body = (self.root/'original.json').read_bytes()
        self.d['verification']['raw_result']['sha256'] = hashlib.sha256(body).hexdigest()
        self.d['native_result']['invented'] = True
        with self.assertRaisesRegex(ValueError, 'raw projection'): self.check()

    def test_p08_and_resume_must_mirror_acceptance(self):
        self.control['physical_bp_spending_accepted'] = False
        with self.assertRaisesRegex(ValueError, 'P08 spending'): self.check()
        self.control['physical_bp_spending_accepted'] = True
        self.s['bp']['bp_after_continue'] = 12
        with self.assertRaisesRegex(ValueError, 'spending state'): self.check()

    def test_old_reward_scope_cannot_be_relabelled(self):
        self.d['native_result']['scope'] = 'PR16_P05_NATIVE_THREE_WIN_REWARD'
        with self.assertRaisesRegex(ValueError, 'scope/status'): self.check()

    def test_visual_review_and_two_actual_cores_required(self):
        self.d['verification']['visual_review']['completed'] = False
        with self.assertRaisesRegex(ValueError, 'verification incomplete'): self.check()
        self.d['verification']['visual_review']['completed'] = True
        self.d['process']['raw_native_fresh_cores'] = 1
        with self.assertRaisesRegex(ValueError, 'core accounting'): self.check()


if __name__ == '__main__':
    unittest.main()
