"""次の2slotだけを対象にする計画・重複排除・境界検査。先行ABIは再実行しない。"""
import copy
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_bios_selector_continuation as n


class SelectorContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=n.b.context();cls.previous=n.s.load(n.PRIOR)
        cls.rows=n.plan(cls.previous,cls.c)
        raw=bytearray(n.s.CANDIDATE['size'])
        for node in cls.c['nodes']:
            at=node['address']-0x08000000;data=bytes.fromhex(node['hex']);raw[at:at+len(data)]=data
            if 'literal_address'in node:
                at=node['literal_address']-0x08000000;raw[at:at+4]=node['literal_value'].to_bytes(4,'little')
        raw[0x1534f8:0x1534fa]=bytes.fromhex('7047')
        raw[0x1534e4:0x1534e8]=(0x08153508).to_bytes(4,'little')
        raw[0x1aec:0x1af0]=(0x08001af0).to_bytes(4,'little')
        cls.raw=bytes(raw)

    def mutated_plan(self,mutate):
        previous=copy.deepcopy(self.previous);mutate(previous['analysis'])
        with self.assertRaises(ValueError):n.plan(previous,self.c)

    def test_exact_two_slots(self):
        self.assertEqual([(r['address'],r['size'])for r in self.rows],[(0x081534e4,4),(0x08001aec,4)])

    def test_original_candidate_required(self):
        self.mutated_plan(lambda a:a['candidate'].update(sha256='0'*64))

    def test_previous_case_count_required(self):
        self.mutated_plan(lambda a:a.update(new_contract_cases=25))

    def test_native_claim_rejected(self):
        self.mutated_plan(lambda a:a.update(bios_execution_observed=True))

    def test_ring_claim_rejected(self):
        self.mutated_plan(lambda a:a.update(ring_acquisition_accepted=True))

    def test_missing_effect_rejected(self):
        self.mutated_plan(lambda a:a.update(window_fill_effects_conditional_proven=False))

    def test_previous_slot_mutation_rejected(self):
        self.mutated_plan(lambda a:a['next_unmapped_reads'][0]['read_fault'].update(address=0x081534e8))

    def test_previous_width_mutation_rejected(self):
        self.mutated_plan(lambda a:a['next_unmapped_reads'][0]['read_fault'].update(size=2))

    def test_palette_identity_required(self):
        self.mutated_plan(lambda a:a['source_palette'].update(hex='00'*20))

    def test_read_slots_exact_bytes(self):
        slots=n.read_slots(self.raw,self.rows)
        self.assertEqual([r['pointer']for r in slots],[0x08153508,0x08001af0])
        self.assertEqual([r['identity']['size']for r in slots],[4,4])

    def test_candidate_size_rejected(self):
        with self.assertRaises(ValueError):n.read_slots(self.raw[:-1],self.rows)

    def test_expanded_plan_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]['size']=8
        with self.assertRaises(ValueError):n.read_slots(self.raw,rows)

    def test_wrong_owner_target_rejected(self):
        raw=bytearray(self.raw);raw[0x1534e4:0x1534e8]=(0x08000101).to_bytes(4,'little')
        with self.assertRaisesRegex(ValueError,'所有範囲'):n.read_slots(bytes(raw),self.rows)

    def test_saved_targets_never_redecoded(self):
        decode=Mock(side_effect=AssertionError('旧node再解読'))
        result=n.extend(self.raw,self.c,n.read_slots(self.raw,self.rows),decode)
        decode.assert_not_called();self.assertFalse(result['new_nodes']);self.assertFalse(result['points'])
        self.assertTrue(all(r['saved_target_reused']for r in result['roots']))

    def test_only_unknown_target_is_decoded(self):
        raw=bytearray(self.raw);raw[0x1534e4:0x1534e8]=(0x081534f8).to_bytes(4,'little');raw=bytes(raw)
        decode=Mock(return_value={'address':0x081534f8,'size':2,'hex':'7047','kind':'return','memory_write':False})
        result=n.extend(raw,self.c,n.read_slots(raw,self.rows),decode)
        self.assertEqual(decode.call_count,1);self.assertEqual(len(result['new_nodes']),1)
        self.assertEqual(result['points'],[0x081534f8,0x081534f9])

    def test_foreign_literal_rejected(self):
        raw=bytearray(self.raw);raw[0x1534e4:0x1534e8]=(0x081534f8).to_bytes(4,'little');raw=bytes(raw)
        decode=lambda data,at:{'address':at,'size':2,'hex':'7047','kind':'return','memory_write':False,
            'literal_address':0x09000000,'literal_value':0}
        # frontierはdecoder拒否を境界として保存し、偽nodeを採用しない。
        result=n.extend(raw,self.c,n.read_slots(raw,self.rows),decode)
        self.assertFalse(result['new_nodes'])
        self.assertEqual(result['roots'][0]['boundaries'][0]['kind'],'decoder_rejection')

    def test_new_node_collision_rejected(self):
        with self.assertRaisesRegex(ValueError,'重複'):n.Machine(self.c,[],(),[self.c['nodes'][0]])

    def test_new_node_duplicate_rejected(self):
        node={'address':0x081534f8,'size':2,'hex':'7047','kind':'return','memory_write':False}
        with self.assertRaisesRegex(ValueError,'重複'):n.Machine(self.c,[],(),[node,node])

    def test_new_node_length_rejected(self):
        node={'address':0x081534f8,'size':4,'hex':'7047','kind':'return','memory_write':False}
        with self.assertRaisesRegex(ValueError,'形式'):n.Machine(self.c,[],(),[node])

    def test_synthetic_new_leaf_runs_without_bios(self):
        nodes=[{'address':0x081534f8,'size':2,'hex':'2a20','kind':'ordinary','memory_write':False},
            {'address':0x081534fa,'size':2,'hex':'7047','kind':'return','memory_write':False}]
        m=n.Machine(self.c,[],(),nodes);m.run(0x081534f9)
        self.assertEqual(m.r[0],42);self.assertFalse(m.bios_events);self.assertFalse(m.writes)

    def test_previous_model_source_not_replaced(self):
        self.assertIs(n.Machine.__mro__[1],n.b.Machine)
        self.assertEqual(n.EXTRA_CODE,())
        self.assertEqual(n.BASE,'9406fcab6be820c9979069b9e73771eee0c7e674')


if __name__=='__main__':unittest.main()
