"""ABI分類の回帰/異常系。既存native/decoderは起動しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_indirect_abi as a


def node(at, word, kind='ordinary', **extra):
    raw = word.to_bytes(2, 'little').hex()
    return dict(address=at, size=2, hex=raw, kind=kind,
                successors=[] if kind in ('indirect', 'return') else [at + 2], **extra)


def graph(words):
    ns = [node(0x08001000 + 2 * i, w) for i, w in enumerate(words)]
    ns[-1].update(kind='indirect', register=1, successors=[])
    return {'entry': 0x08001001, 'nodes': ns}


class IndirectAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = json.loads((a.ROOT / a.PATCH).read_bytes())
        cls.prior = json.loads((a.ROOT / a.PRIOR).read_bytes())
        cls.result = a.analyze(cls.patch, cls.prior)

    def test_real_fifteen_classifications(self):
        self.assertEqual(self.result['counts'], {'ABI_SAVED_LR_RETURN': 12,
            'CALLSITE_R3_TRAMPOLINE': 2, 'LITERAL_BRANCH_LIVE_FRAME': 1})
        self.assertEqual(len(self.result['edges']), 15)

    def test_qol_uses_already_recorded_flagget(self):
        r = next(r for r in self.result['edges'] if r['owner'] == 0x09376F45)
        self.assertEqual(r['observed_callers'][0]['final_target'], 0x0806DEC5)
        self.assertTrue(r['observed_callers'][0]['final_target_already_decoded'])
        self.assertFalse(r['unseen_callers_excluded'])
        self.assertEqual(r['observed_callers'][0]['return_address'], 0x09376E77)

    def test_flagset_reuses_save_veneer(self):
        r = next(r for r in self.result['edges'] if r['owner'] == 0x09377615)
        c = r['observed_callers'][0]
        self.assertEqual(c['target'], 0x092D28D9)
        self.assertEqual(c['final_target'], 0x093BDD7D)
        self.assertEqual(len(c['reused_veneer_chain']), 1)

    def test_live_frame_not_return_or_tailcall(self):
        r = next(r for r in self.result['edges'] if r['owner'] == 0x093789F3)
        self.assertEqual(r['classification'], 'LITERAL_BRANCH_LIVE_FRAME')
        self.assertEqual(r['frame_bytes'], 8)
        self.assertEqual(r['entry_lr_saved_offsets'], [-4])
        self.assertEqual(r['target'], 0x0806DE7D)

    def test_frontier_preserved_not_eighteen_rescans(self):
        self.assertEqual(len(self.result['old_unread_targets']), 18)
        self.assertEqual(self.result['additional_unread_targets'], [0x0806DE7D])
        self.assertEqual(len(self.result['remaining_unread_targets']), 19)
        for key in ('rom_changes', 'new_graph_decodes', 'new_emulator_processes',
                    'candidate_reconstructions', 'accepted_native_cases_replayed'):
            self.assertEqual(self.result[key], 0)
        for key in ('ring_acquisition_accepted', 'all_runtime_owners_excluded', 'release_ready'):
            self.assertIs(self.result[key], False)

    def test_does_not_mutate_inputs(self):
        before = a.stable([self.patch, self.prior])
        a.analyze(self.patch, self.prior)
        self.assertEqual(a.stable([self.patch, self.prior]), before)

    def test_push_pop_tracks_original_lr(self):
        g = graph([0xb500, 0xbc02, 0x4708])
        st = a.flow(g)[0x08001004]
        self.assertEqual(st[0][1], a.RETURN)
        self.assertEqual(st[0][13], ('sp', 0))

    def test_pop_without_saved_lr_is_not_return(self):
        g = graph([0xbc02, 0x4708])
        self.assertIsNone(a.flow(g)[0x08001002][0][1])

    def test_overwritten_saved_lr_not_return(self):
        g = graph([0xb500, 0x9100, 0xbc02, 0x4708])
        self.assertIsNone(a.flow(g)[0x08001006][0][1])

    def test_call_clobbers_r3_and_lr(self):
        st = list(a.initial()[0]); st[3] = a.const(0x08001235)
        n = dict(address=0x08001000, size=4, hex='00f000f8', kind='call', target=0x08001004, successors=[0x08001004])
        after = a.transfer(n, (tuple(st), ()))
        self.assertIsNone(after[0][3]); self.assertIsNone(after[0][14])

    def test_bad_bl_target_rejected(self):
        n = dict(address=0x08001000, size=4, hex='00f000f8', kind='call', target=0x08002000, successors=[0x08001004])
        with self.assertRaises(ValueError): a.transfer(n, a.initial())

    def test_stack_depth_join_rejected(self):
        left = a.initial(); right = list(left[0]); right[13] = ('sp', -4)
        with self.assertRaises(ValueError): a.merge(left, (tuple(right), ()))

    def test_conflicting_register_join_unknown(self):
        left, right = list(a.initial()[0]), list(a.initial()[0])
        left[3], right[3] = a.const(1), a.const(3)
        self.assertIsNone(a.merge((tuple(left), ()), (tuple(right), ()))[0][3])

    def test_bad_literal_binding_rejected(self):
        n = node(0x08001000, 0x4b00, literal_address=0x08002000, literal_value=0x08002223)
        with self.assertRaises(ValueError): a.transfer(n, a.initial())

    def test_sp_alias_store_rejected(self):
        st = list(a.initial()[0]); st[0] = ('sp', -4)
        with self.assertRaises(ValueError): a.transfer(node(0x08001000, 0x6001), (tuple(st), ()))

    def test_unknown_instruction_fails_closed(self):
        with self.assertRaises(ValueError): a.transfer(node(0x08001000, 0xbe00), a.initial())

    def test_forged_successor_rejected(self):
        g = graph([0xb500, 0xbc02, 0x4708]); g['nodes'][0]['successors'] = [0x08001004]
        with self.assertRaises(ValueError): a.flow(g)

    def test_missing_cfg_node_rejected(self):
        g = graph([0xb500, 0xbc02, 0x4708]); del g['nodes'][1]
        with self.assertRaises(ValueError): a.flow(g)

    def test_non_r3_unresolved_not_guessed(self):
        patch = copy.deepcopy(self.patch)
        g = next(g for g in patch['frontier']['graphs'] if g['entry'] == 0x09377615)
        g['nodes'][0].update(hex='1047', register=2)
        b = next(b for b in patch['frontier']['remaining_boundaries'] if b.get('owner') == g['entry'])
        b['register'] = 2
        result = a.analyze(patch, self.prior)
        r = next(r for r in result['edges'] if r['owner'] == g['entry'])
        self.assertEqual(r['classification'], 'UNRESOLVED')

    def test_projection_preserves_acceptance_and_old_frontier(self):
        state = {'bp': {'spending_accepted': True, 'earning_accepted': True},
            'latest_native_run': 34946969126, 'last_accepted_native_run': 34946969126,
            'candidate': copy.deepcopy(self.patch['candidate']),
            'remaining_physical_gap_ids': ['P05_NATIVE_RING_ACQUISITION_PHYSICAL'],
            'next_action': {}, 'observed_head_checks': {}, 'do_not_repeat': []}
        backlog = {'remaining_conditions': [{'id': 'NATURAL_CAPTURE_GEAR',
            'remaining_supply_gap_ids': ['P05_NATIVE_RING_ACQUISITION_PHYSICAL'],
            'selected_supply_entrypoints': {'P05_NATIVE_RING_ACQUISITION_PHYSICAL': None}}]}
        s, b = a.project(state, backlog, self.result, a.BASE, 123)
        for k in ('candidate', 'remaining_physical_gap_ids', 'latest_native_run', 'last_accepted_native_run'):
            self.assertEqual(s[k], state[k])
        self.assertTrue(s['bp']['spending_accepted']); self.assertTrue(s['bp']['earning_accepted'])
        self.assertEqual((s, b), a.project(s, b, self.result, a.BASE, 123))
        self.assertEqual(len(s['do_not_repeat']), 1)
        self.assertNotIn('ring_indirect_abi', state)

    def test_projection_rejects_changed_classification(self):
        bad = copy.deepcopy(self.result); bad['counts']['ABI_SAVED_LR_RETURN'] = 15
        with self.assertRaises(ValueError): a.project({}, {}, bad, a.BASE, 123)


if __name__ == '__main__': unittest.main()
