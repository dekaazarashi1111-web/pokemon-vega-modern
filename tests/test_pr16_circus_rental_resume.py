"""受付契約欠落の実原本から、再linkなしで再開する回帰検査。"""
from copy import deepcopy
from pathlib import Path
import inspect
import json
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_circus_rental_resume as t

class RentalResumeTests(unittest.TestCase):
    def setUp(self):
        self.original = json.loads((ROOT / t.PREVIOUS).read_bytes())
        self.saved = self.original['build']

    def test_actual_failure_is_preprocess_not_native_or_link(self):
        n = self.original['native']
        self.assertEqual(n['actual_new_processes'], 0)
        self.assertEqual(n['failures'], [dict(stage='setup-or-execution', error="'reception'")])
        self.assertEqual(self.saved['independent_arm_links'], 2)
        self.assertEqual(n['candidate']['sha256'], t.SHA)

    def test_real_contract_restores_reception_and_three_launches(self):
        fixed = t.restore_contract(self.saved)
        self.assertEqual(fixed['reception'], self.saved['old']['reception'])
        self.assertEqual(fixed['launch_sites'], self.saved['old']['launch_sites'])
        self.assertEqual(len(fixed['launch_sites']), 3)
        # 生成controllerが直後に読む両方のキーを実際に参照する。
        addresses = dict(CF_BRIDGE=fixed['reception']['bridge'], CF_SCRIPT=fixed['reception']['circus'],
                         CF_LAUNCH=fixed['launch_sites'][0]['new'])
        self.assertTrue(all(type(v) is int and 0x08000000 <= v < 0x0A000000 for v in addresses.values()))

    def test_saved_build_and_nested_parent_not_mutated(self):
        before = t.stable(self.saved)
        fixed = t.restore_contract(self.saved)
        for key in self.saved:
            self.assertEqual(fixed[key], self.saved[key], key)
        fixed['reception']['bridge'] = 0
        fixed['patches'][0]['name'] = 'changed only in test copy'
        self.assertEqual(t.stable(self.saved), before)

    def test_wrong_candidate_or_parent_rejected(self):
        for key in ('candidate', 'parent'):
            bad = deepcopy(self.saved)
            bad[key]['sha256'] = '0' * 64
            with self.subTest(key=key), self.assertRaises(ValueError):
                t.restore_contract(bad)

    def test_unproven_build_rejected(self):
        for key, value in [('independent_arm_links', 1), ('whole_rom_rollback_matches_parent', False)]:
            bad = deepcopy(self.saved); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                t.restore_contract(bad)

    def test_partial_or_invalid_native_addresses_rejected(self):
        for kind in ('missing', 'zero', 'bool', 'launch', 'sites'):
            bad = deepcopy(self.saved)
            if kind == 'missing': del bad['old']['reception']['circus']
            elif kind == 'zero': bad['old']['reception']['bridge'] = 0
            elif kind == 'bool': bad['old']['reception']['bridge'] = True
            elif kind == 'launch': bad['old']['launch_sites'][0]['new'] = 0x02000000
            else: bad['old']['launch_sites'].pop()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                t.restore_contract(bad)

    def test_prior_text_evidence_still_exact(self):
        for path, bound in self.original['text_evidence'].items():
            self.assertEqual(t.identity((ROOT / path).read_bytes()), bound, path)

    def test_restore_does_not_compile_or_run_old_native(self):
        source = inspect.getsource(t.reconstruct)
        self.assertIn("checked_patch(raw, saved['old'])", source)
        self.assertIn('checked_patch(parent, saved)', source)
        for call in ('compile_bridge(', 'compile_runtime(', 'inherited.reconstruct(', 'inherited.prepare('):
            self.assertNotIn(call, source)

    def test_native_keeps_original_prefix_and_target_gate(self):
        self.assertIn("need(result['genuine_30_wins_verified']", inspect.getsource(t.native))
        self.assertIn('events[:100]', inspect.getsource(t.inherited.native))
        self.assertIn('same_without_frame', inspect.getsource(t.inherited.native))

    def test_reconstruction_checks_identity_allocation_and_rollback(self):
        raw = b'01234567'; new = b'01AB4567'
        recipe = dict(parent=t.identity(raw), candidate=t.identity(new),
                      patches=[dict(name='test', offset=2, before=b'23'.hex(), after=b'AB'.hex())],
                      allocation=dict(allocations=[dict(name='test', start=2, end_exclusive=4,
                                                       content_sha256=t.identity(b'AB')['sha256'])]))
        self.assertEqual(t.checked_patch(raw, recipe), new)
        bad = deepcopy(recipe); bad['allocation']['allocations'][0]['content_sha256'] = '0' * 64
        with self.assertRaises(ValueError): t.checked_patch(raw, bad)
        with self.assertRaises(ValueError): t.checked_patch(b'badbytes', recipe)

    def test_prepare_preserves_previous_failure_and_refuses_duplicate(self):
        source = inspect.getsource(t.prepare)
        self.assertIn('previous_native_processes=0', source)
        self.assertIn("need(not (ROOT / REPORT).exists()", source)
        self.assertNotIn('inherited.prepare()', source)

    def test_configure_reentrant_and_isolated(self):
        for _ in range(2):
            d, b = t.configure()
            self.assertEqual(d.SELF, t.SELF)
            self.assertEqual(b.SELF, t.SELF)
            self.assertEqual(len(d.FILES), len(set(d.FILES)))
            self.assertTrue(set(t.FILES) <= set(d.FILES))

if __name__ == '__main__': unittest.main()
