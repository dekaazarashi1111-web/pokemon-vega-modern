import unittest
from tools import stage61_interaction_oracle as oracle
from tools.stage61_event_semantic_relocator import SemanticScriptGraph


class GiftStorageRootSeedTests(unittest.TestCase):
    def domains(self, root):
        raw = bytearray(root - 0x08000000 + 32)
        # getpartysize VAR_RESULT; end: give-monより前の受付preflightだけ。
        raw[root - 0x08000000:root - 0x08000000 + 4] = bytes((0x43, 0x0D, 0x80, 0x02))
        graph = SemanticScriptGraph(bytes(raw))
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        return oracle._static_control_domains(graph, root, abi_index={})

    def test_prize_preflight_has_correlated_gift_state_before_givemon(self):
        domains, blockers = self.domains(0x081859FA)
        self.assertEqual(blockers, [])
        gift = [row for row in domains if row['kind'] == oracle.GIFT_STORAGE_TRANSACTION_KIND]
        self.assertEqual(len(gift), 1)
        self.assertEqual(gift[0]['id'], oracle.GIFT_STORAGE_TRANSACTION_CONTROL_ID)
        self.assertEqual(set(gift[0]['candidate_values']), set(oracle.GIFT_STORAGE_EXECUTOR_SCENARIO_IDS))

    def test_ordinary_party_reader_does_not_acquire_gift_owner(self):
        domains, blockers = self.domains(0x08001000)
        self.assertEqual(blockers, [])
        self.assertFalse(any(row['kind'] == oracle.GIFT_STORAGE_TRANSACTION_KIND for row in domains))
        self.assertTrue(any(row['kind'] == 'PARTY_COUNT' for row in domains))
