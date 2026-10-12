"""FlagSet継続1根採取の範囲・原本維持・拒否条件。ROM実行なし。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_flagset_continuation as m


def fixture():
    edge = {'owner': m.OWNER, 'site': m.OWNER + 9, 'register': 3,
            'classification': 'LITERAL_BRANCH_LIVE_FRAME', 'target': m.TARGET,
            'frame_bytes': 8, 'entry_lr_saved_offsets': [-4], 'all_runtime_owners_excluded': False}
    analysis = {'counts': m.COUNTS.copy(), 'classified_edges': 15, 'edges': [edge],
                'additional_unread_targets': [m.TARGET],
                'old_unread_targets': [0x08001001 + i * 4 for i in range(18)],
                'ring_acquisition_accepted': False, 'all_runtime_owners_excluded': False}
    abi = {'candidate': m.CANDIDATE.copy(), 'analysis': analysis}
    prior = {'candidate': m.CANDIDATE.copy(), 'native_owners': {}}
    previous = {'candidate': m.CANDIDATE.copy(), 'frontier': {'graphs': []}}
    at = m.TARGET & ~1
    node = {'address': at, 'size': 2, 'hex': '7047', 'kind': 'return',
            'register': 14, 'successors': [], 'memory_write': False}
    graph = {'entry': m.TARGET, 'window': m.WINDOW, 'nodes': [node],
             'window_identity': m.identity(bytes(m.WINDOW)), 'external_edges': [],
             'memory_write_sites': [], 'side_effects_excluded': False}
    raw = bytearray(at - m.ROM_BASE + m.WINDOW)
    raw[at - m.ROM_BASE:at - m.ROM_BASE + 2] = b'\x70\x47'
    return bytes(raw), abi, previous, prior, graph


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.abi, self.previous, self.prior, self.graph = fixture()

    def collect(self):
        decoder = Mock(return_value=self.graph)
        with patch.object(m, 'candidate_identity', return_value=m.CANDIDATE):
            result = m.collect(self.raw, self.abi, self.previous, self.prior, decoder)
        decoder.assert_called_once_with(self.raw, m.TARGET, window=m.WINDOW, limit=m.LIMIT)
        return result

    def test_only_one_new_root_and_read_only_inputs(self):
        before = copy.deepcopy((self.raw, self.abi, self.previous, self.prior))
        result = self.collect()
        self.assertEqual(before, (self.raw, self.abi, self.previous, self.prior))
        self.assertEqual(result['new_graph_decodes'], 1)
        self.assertEqual(result['sampled_instruction_bytes'], 2)

    def test_old_eighteen_preserved_target_is_no_longer_unread(self):
        result = self.collect()
        self.assertEqual(result['remaining_unread_targets'], self.abi['analysis']['old_unread_targets'])
        self.assertNotIn(m.TARGET, result['remaining_unread_targets'])

    def test_new_external_target_remains_unread_not_followed(self):
        target = 0x08012345
        self.graph['external_edges'] = [{'site': m.TARGET & ~1, 'kind': 'call', 'target': target}]
        result = self.collect()
        self.assertEqual(result['additional_unread_targets'], [target])
        self.assertEqual(len(result['remaining_unread_targets']), 19)

    def test_saved_callee_reused_without_decode(self):
        target = 0x08012345
        self.previous['frontier']['graphs'] = [{'entry': target, 'nodes': []}]
        self.graph['external_edges'] = [{'site': m.TARGET & ~1, 'kind': 'call', 'target': target}]
        result = self.collect()
        self.assertEqual(result['reused_saved_entries'], [target])
        self.assertEqual(result['additional_unread_targets'], [])

    def test_indirect_edge_and_unproven_live_frame_not_promoted(self):
        self.graph['external_edges'] = [{'site': m.TARGET & ~1, 'kind': 'indirect', 'register': 1, 'target': None}]
        result = self.collect()
        self.assertIsNone(result['graph']['external_edges'][0]['target'])
        for key in ('inherited_frame_return_verified', 'stack_integrity_proven', 'all_callers_resolved',
                    'ring_acquisition_accepted', 'all_runtime_owners_excluded', 'release_ready'):
            self.assertIs(result[key], False)
        for key in ('new_emulator_processes', 'rom_changes', 'accepted_native_cases_replayed', 'prior_abi_classifications_replayed'):
            self.assertEqual(result[key], 0)

    def test_fresh_function_frame_is_rejected(self):
        self.abi['analysis']['edges'][0]['frame_bytes'] = 0
        with self.assertRaisesRegex(ValueError, 'inherited frame'):
            self.collect()

    def test_missing_entry_lr_is_rejected(self):
        self.abi['analysis']['edges'][0]['entry_lr_saved_offsets'] = []
        with self.assertRaisesRegex(ValueError, 'inherited frame'):
            self.collect()

    def test_already_recorded_root_is_rejected(self):
        self.previous['frontier']['graphs'] = [self.graph]
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            self.collect()

    def test_branch_into_recorded_instruction_operand_is_rejected(self):
        node = {'address': (m.TARGET & ~1) - 2, 'size': 4}
        self.previous['frontier']['graphs'] = [{'entry': m.TARGET - 2, 'nodes': [node]}]
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            self.collect()

    def test_wrong_candidate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'candidate identity'):
            m.candidate_identity(b'not a candidate')
        self.abi['candidate']['crc32'] = '00000000'
        with self.assertRaisesRegex(ValueError, 'saved candidate'):
            self.collect()

    def test_wrong_root_or_window_is_rejected(self):
        for key, value in (('entry', m.TARGET + 2), ('window', 1024)):
            graph = copy.deepcopy(self.graph)
            graph[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'collection scope'):
                m.validate_graph(graph, set())

    def test_duplicate_nodes_are_rejected(self):
        self.graph['nodes'].append(self.graph['nodes'][0].copy())
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.collect()

    def test_byte_mismatch_is_rejected(self):
        self.graph['nodes'][0]['hex'] = '0047'
        with self.assertRaisesRegex(ValueError, 'sample differs'):
            self.collect()

    def test_false_no_side_effects_is_rejected(self):
        self.graph['side_effects_excluded'] = True
        with self.assertRaisesRegex(ValueError, 'side-effect'):
            self.collect()

    def test_orphan_or_arm_external_target_is_rejected(self):
        for site, target in ((m.TARGET + 5, 0x08012345), (m.TARGET & ~1, 0x08012344)):
            self.graph['external_edges'] = [{'site': site, 'kind': 'call', 'target': target}]
            with self.subTest(site=site, target=target), self.assertRaises(ValueError):
                self.collect()

    def test_stale_binding_and_path_traversal_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'source.txt').write_bytes(b'original')
            m.bindings_fresh(root, {'source.txt': m.identity(b'original')})
            (root / 'source.txt').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'stale binding'):
                m.bindings_fresh(root, {'source.txt': m.identity(b'original')})
            with self.assertRaisesRegex(ValueError, 'unsafe path'):
                m.safe(root, '../outside')

    def test_instruction_budget_and_literal_contract_are_rejected(self):
        self.graph['nodes'] = []
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.collect()
        self.graph = fixture()[-1]
        self.graph['nodes'][0].update(literal_address=m.TARGET + 7, literal_value=0)
        with self.assertRaisesRegex(ValueError, 'literal address'):
            self.collect()

    def test_saved_artifact_shape_and_source_binding(self):
        path = m.OUT / 'audit.json'
        if path.exists():
            value = json.loads(path.read_bytes())
            result = value['analysis']
            _, _, _, cached = m.saved_metadata(*m.read_inputs())
            m.validate_graph(result['graph'], cached)
            m.bindings_fresh(m.ROOT, value['source_bindings'])
            self.assertEqual(result['candidate'], m.CANDIDATE)
            self.assertEqual(len(result['old_unread_targets']), 18)
            self.assertIs(result['ring_acquisition_accepted'], False)
        else:
            result = self.collect()
        self.assertEqual(json.loads(m.stable(result)), result)


if __name__ == '__main__':
    unittest.main()
