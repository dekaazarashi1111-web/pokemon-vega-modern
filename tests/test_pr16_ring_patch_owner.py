"""patch先監査の拒否境界。ROM/private入力/native成功の再実行なし。"""
import copy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_patch_owner as audit


def graph(entry, edges=()):
    return {'entry': entry, 'nodes': [], 'external_edges': list(edges),
            'memory_write_sites': [], 'side_effects_excluded': False}


def veneer(entry=0x08000001, target=0x08000011):
    g = graph(entry, [{'site': (entry & ~1) + 2, 'kind': 'indirect', 'target': None}])
    at = entry & ~1
    g['nodes'] = [{'address': at, 'hex': '004b', 'literal_address': (at + 4) & ~3, 'literal_value': target},
                  {'address': at + 2, 'hex': '1847'}]
    return g


class PatchOwnerTests(unittest.TestCase):
    def test_exact_veneer(self):
        self.assertEqual(audit.veneer(veneer())['target'], 0x08000011)

    def test_different_register_is_not_resolved(self):
        g = veneer(); g['nodes'][1]['hex'] = '0047'
        self.assertIsNone(audit.veneer(g))

    def test_extra_instruction_is_not_resolved(self):
        g = veneer(); g['nodes'].append(dict(g['nodes'][1]))
        self.assertIsNone(audit.veneer(g))

    def test_wrong_literal_address_rejected(self):
        g = veneer(); g['nodes'][0]['literal_address'] += 4
        with self.assertRaises(ValueError): audit.veneer(g)

    def test_non_thumb_or_outside_rejected(self):
        for target in (0x08000010, 0, 0x0A000001, True):
            with self.subTest(target=target), self.assertRaises(ValueError):
                g = veneer(target=target); audit.veneer(g)

    def test_rom_end_halfword_boundary(self):
        self.assertEqual(audit.pointer(0x0800003F, 64), 0x0800003F)
        with self.assertRaises(ValueError): audit.pointer(0x08000041, 64)

    def test_cached_graph_not_replayed(self):
        def fail(*args): self.fail('既存入口を再走査した')
        r = audit.frontier(bytes(64), [(0x08000001, 'old')], {0x08000001: {}}, fail)
        self.assertEqual(r['reused_entries'], [0x08000001]); self.assertFalse(r['graphs'])

    def test_breadth_first_deduplicates_calls_and_cycles(self):
        calls = []
        def decode(raw, p):
            calls.append(p)
            return graph(p, [{'site': p & ~1, 'kind': 'call', 'target': 0x08000011 if p == 0x08000001 else 0x08000001}])
        r = audit.frontier(bytes(64), [(0x08000001, 'a'), (0x08000001, 'b')], {}, decode)
        self.assertEqual(calls, [0x08000001, 0x08000011]); self.assertFalse(r['remaining_boundaries'])

    def test_new_veneer_is_followed_without_guessing(self):
        calls = []
        def decode(raw, p):
            calls.append(p)
            return veneer() if p == 0x08000001 else graph(p)
        r = audit.frontier(bytes(64), [(0x08000001, 'a')], {}, decode)
        self.assertEqual(calls, [0x08000001, 0x08000011]); self.assertFalse(r['remaining_boundaries'])

    def test_indirect_is_not_giver_absence(self):
        r = audit.frontier(bytes(64), [(0x08000001, 'a')], {},
            lambda raw, p: graph(p, [{'site': p & ~1, 'kind': 'indirect', 'target': None}]))
        self.assertEqual(r['remaining_boundaries'][0]['reason'], 'UNRESOLVED_INDIRECT')
        self.assertIs(r['side_effects_excluded'], False)

    def test_decoder_stop_retained(self):
        def stop(*args): raise ValueError('unknown Thumb opcode')
        r = audit.frontier(bytes(64), [(0x08000001, 'a')], {}, stop)
        self.assertEqual(r['decoder_stops'][0]['reason'], 'DECODER_STOP'); self.assertFalse(r['graphs'])

    def test_root_bound(self):
        r = audit.frontier(bytes(64), [(0x08000001, 'a'), (0x08000011, 'b')], {},
                           lambda raw, p: graph(p), max_roots=1)
        self.assertEqual(len(r['graphs']), 1); self.assertEqual(r['remaining_boundaries'][0]['reason'], 'ROOT_BOUND')

    def test_depth_bound(self):
        r = audit.frontier(bytes(64), [(0x08000001, 'a')], {},
            lambda raw, p: graph(p, [{'site': p & ~1, 'kind': 'call', 'target': 0x08000011}]), max_depth=0)
        self.assertEqual(r['remaining_boundaries'][0]['reason'], 'DEPTH_BOUND')

    def test_invalid_budget_rejected(self):
        for kwargs in ({'max_roots': 25}, {'max_roots': True}, {'max_depth': 3}, {'max_depth': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                audit.frontier(bytes(64), [], {}, lambda *a: None, **kwargs)

    def test_scope_promotion_rejected(self):
        def decode(raw, p): return dict(graph(p), side_effects_excluded=True)
        with self.assertRaises(ValueError): audit.frontier(bytes(64), [(0x08000001, 'a')], {}, decode)

    def test_input_graphs_not_mutated(self):
        cached = {0x08000001: veneer()}; before = copy.deepcopy(cached)
        audit.frontier(bytes(64), [(0x08000001, 'a')], cached, lambda *a: None)
        self.assertEqual(cached, before)

    def test_engine_setup_exact_abi(self):
        nodes = [{'address': a, 'hex': h} for a, h in
                 ((0x080693B6, '0949'), (0x080693B8, '094a'), (0x080693BA, '201c'), (0x080693BC, 'fff756fe'))]
        nodes[0]['literal_value'] = 0x08162CC4; nodes[1]['literal_value'] = 0x08163010
        nodes[3]['target'] = 0x0806906C
        r = {'native_owners': {'ScriptContextSetup': {'nodes': nodes}},
             'standard_script': {'nodes': [{'opcode': n} for n in audit.HANDLER_OPS]}}
        self.assertEqual(audit.engine_table(r), (0x08162CC4, 0x08163010))
        nodes[3]['target'] += 2
        with self.assertRaises(ValueError): audit.engine_table(r)

    def test_no_rom_or_native_in_unit_contract(self):
        self.assertEqual(audit.MAX_ROOTS, 24); self.assertEqual(audit.MAX_DEPTH, 2)
        self.assertEqual(set(audit.PATCHES), {'FlagSet', 'SAVE_FINALIZE'})


if __name__ == '__main__': unittest.main()
