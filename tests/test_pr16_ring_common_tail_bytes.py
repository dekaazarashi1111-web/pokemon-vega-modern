"""共通末尾だけを許可する採取境界。実ROM/native/旧ABIは実行しない。"""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'scripts/pr16_ring_common_tail_bytes.py'
SPEC = importlib.util.spec_from_file_location('common_tail_bytes', PATH)
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)
AT = a.TARGET & ~1


def graph():
    return {'entry': a.TARGET, 'window': a.MAX_WINDOW, 'side_effects_excluded': False,
            'nodes': [{'address': AT, 'size': 2, 'hex': '7047', 'kind': 'return',
                       'memory_write': False, 'successors': []}],
            'memory_write_sites': [], 'external_edges': []}


def prior():
    value = {'task': 'PR-P08-7-RING-ZERO-ABI', 'analysis': {
        'classification': 'ZERO_CONTINUATION_PREFIX_WITH_CONDITIONAL_STORES_NOT_RETURN_PROOF',
        'candidate': copy.deepcopy(a.CANDIDATE), 'priority_unread_targets': [a.TARGET],
        'instructions_verified': 54, 'instruction_bytes_verified': 114,
        'old_unread_targets': list(range(18)), 'additional_unread_targets': [a.TARGET, *a.OTHER_ROOTS],
        'remaining_unread_targets': list(range(18)) + [a.TARGET, *a.OTHER_ROOTS]}}
    for key in (*a.NO_PROOF, 'old_frontier_removed', 'zero_callee_return_proven',
                'zero_callee_return_observed', 'saved_slot_preservation_proven', 'return_pointer_non_alias_proven'):
        value['analysis'][key] = False
    return value


class CommonTailBoundaryTests(unittest.TestCase):
    def reject_graph(self, mutate, cached=None):
        g = graph()
        mutate(g)
        with self.assertRaises(ValueError):
            a.validate_graph(g, set() if cached is None else cached)

    def test_valid_new_root(self):
        self.assertEqual(a.validate_graph(graph(), set()), {AT, AT + 1})

    def test_window_stops_before_cached_code(self):
        self.assertEqual(a.window_for({AT + 24, AT + 25}), 24)

    def test_window_rejects_sampled_root(self):
        with self.assertRaises(ValueError): a.window_for({AT})

    def test_window_rejects_partial_instruction(self):
        with self.assertRaises(ValueError): a.window_for({AT + 1})

    def test_wrong_root(self):
        self.reject_graph(lambda g: g.update(entry=a.OTHER_ROOTS[0]))

    def test_wrong_window(self):
        self.reject_graph(lambda g: g.update(window=128))

    def test_empty_graph(self):
        self.reject_graph(lambda g: g.update(nodes=[]))

    def test_duplicate_nodes(self):
        self.reject_graph(lambda g: g['nodes'].append(copy.deepcopy(g['nodes'][0])))

    def test_old_instruction_overlap(self):
        with self.assertRaises(ValueError): a.validate_graph(graph(), {AT + 1})

    def test_instruction_width(self):
        self.reject_graph(lambda g: g['nodes'][0].update(size=3))

    def test_wrong_hex_width(self):
        self.reject_graph(lambda g: g['nodes'][0].update(hex='00'))

    def test_unknown_kind(self):
        self.reject_graph(lambda g: g['nodes'][0].update(kind='invented'))

    def test_overclaim(self):
        self.reject_graph(lambda g: g.update(side_effects_excluded=True))

    def test_another_unread_root(self):
        self.reject_graph(lambda g: g['nodes'].append(dict(g['nodes'][0], address=a.OTHER_ROOTS[0] & ~1)))

    def test_missing_successor(self):
        self.reject_graph(lambda g: g['nodes'][0].update(successors=[AT + 2]))

    def test_unaligned_successor(self):
        self.reject_graph(lambda g: g['nodes'][0].update(successors=[AT + 1]))

    def test_orphan_edge(self):
        self.reject_graph(lambda g: g['external_edges'].append({'site': AT + 2, 'target': None}))

    def test_invalid_thumb_edge(self):
        self.reject_graph(lambda g: g['external_edges'].append({'site': AT, 'target': a.TARGET - 1}))

    def test_write_annotation(self):
        self.reject_graph(lambda g: g['nodes'][0].update(memory_write=1))

    def test_write_sites(self):
        self.reject_graph(lambda g: g.update(memory_write_sites=[AT]))

    def test_literal_opcode(self):
        self.reject_graph(lambda g: g['nodes'][0].update(literal_address=AT + 4, literal_value=0))

    def test_prior_unchanged(self):
        p = prior(); original = copy.deepcopy(p)
        a.validate_prior(p)
        result = a.analysis(p, graph(), [])
        self.assertEqual(p, original)
        self.assertFalse(result['ring_acquisition_accepted'])
        self.assertFalse(result['callee_return_proven'])
        self.assertEqual(result['accepted_native_cases_replayed'], 0)
        self.assertEqual(result['old_unread_targets'], list(range(18)))
        self.assertEqual(result['other_unread_roots_preserved'], list(a.OTHER_ROOTS))

    def test_prior_target_drift(self):
        p = prior(); p['analysis']['priority_unread_targets'] = [a.OTHER_ROOTS[0]]
        with self.assertRaises(ValueError): a.validate_prior(p)

    def test_prior_candidate_drift(self):
        p = prior(); p['analysis']['candidate']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): a.validate_prior(p)

    def test_prior_removed_frontier(self):
        p = prior(); p['analysis']['remaining_unread_targets'].pop()
        with self.assertRaises(ValueError): a.validate_prior(p)

    def test_each_prior_overclaim_rejected(self):
        for key in (*a.NO_PROOF, 'old_frontier_removed', 'saved_slot_preservation_proven', 'zero_callee_return_proven'):
            with self.subTest(key=key):
                p = prior(); p['analysis'][key] = True
                with self.assertRaises(ValueError): a.validate_prior(p)

    def test_exact_sample_binding(self):
        raw = bytes(AT - a.ROM_BASE) + bytes.fromhex('7047')
        r = a.sample_ranges(raw, graph())
        self.assertEqual(r, [dict(address=AT, hex='7047', **a.identity(bytes.fromhex('7047')))])

    def test_instruction_mismatch(self):
        raw = bytes(AT - a.ROM_BASE) + bytes.fromhex('0047')
        with self.assertRaises(ValueError): a.sample_ranges(raw, graph())

    def test_truncated_sample(self):
        with self.assertRaises(ValueError): a.sample_ranges(b'', graph())

    def test_literal_value_binding(self):
        g = graph(); g['nodes'][0].update(hex='0048', literal_address=AT + 4, literal_value=123)
        raw = bytes(AT - a.ROM_BASE) + bytes.fromhex('00480000') + (123).to_bytes(4, 'little')
        self.assertEqual(len(a.sample_ranges(raw, g)), 2)
        with self.assertRaises(ValueError): a.sample_ranges(raw[:-1] + b'\1', g)

    def test_unresolved_new_edge_retained(self):
        g = graph(); edge = 0x08070001
        g['external_edges'] = [{'site': AT, 'target': edge}]
        r = a.analysis(prior(), g, [])
        self.assertIn(edge, r['remaining_unread_targets'])
        self.assertFalse(r['old_frontier_removed'])


if __name__ == '__main__':
    unittest.main()
