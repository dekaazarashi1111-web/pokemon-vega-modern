"""保存prefixの正負境界と改変拒否。native/既読ABIは起動しない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external1_abi as m


def fixture():
    return {'candidate':copy.deepcopy(m.s.CANDIDATE),'target':m.START|1,
        'graph':{'entry':m.START|1,'window':64,'window_identity':{'size':64,'sha256':'e100b51b7f2c73e835baefbe2aa45c0f57ef07031e8fb4f025a856ef7eaa67d4'},
        'nodes':m.expected_nodes(),'memory_write_sites':[m.START],
        'external_edges':[dict(site=0x081138B0,kind='jump',target=m.EXIT|1,resolved_to_code_address_only=True,stop_reason=m.STOP),
                          dict(site=0x081138C6,kind='window_fallthrough',target=m.CONT|1,resolved_to_code_address_only=True,stop_reason=m.STOP)],
        'saved_instruction_bytes_redecoded':0,'deferred_roots_decoded':0},
        'sampled_ranges':m.expected_ranges(),'sampled_instruction_bytes':46,
        'old_unread_targets':list(range(1,36,2)), 'remaining_unread_targets':[m.CONT|1,m.EXIT|1,*range(1,36,2)],
        **{k:False for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven','return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready')}}

class PrefixABI(unittest.TestCase):
    def test_program(self):self.assertEqual(len(m.program(fixture())),23)
    def test_all_instruction_mutations_rejected(self):
        for i in range(23):
            with self.subTest(i=i):
                a=fixture();a['graph']['nodes'][i]['hex']='0000'
                with self.assertRaises(ValueError):m.program(a)
    def test_literal_mutations_rejected(self):
        for i,n in enumerate(m.expected_nodes()):
            if 'literal_value' in n:
                a=fixture();a['graph']['nodes'][i]['literal_value']^=1
                with self.assertRaises(ValueError):m.program(a)
    def test_sample_hash_mutation(self):
        a=fixture();a['sampled_ranges'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):m.program(a)
    def test_external_edge_mutation(self):
        a=fixture();a['graph']['external_edges'][0]['target']+=2
        with self.assertRaises(ValueError):m.program(a)
    def test_frontier_loss_rejected(self):
        a=fixture();a['remaining_unread_targets'].remove(m.CONT|1)
        with self.assertRaises(ValueError):m.program(a)
    def test_no_acceptance_promotion(self):
        a=fixture();a['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.program(a)
    def test_zero_short_circuit(self):
        r=m.execute(0,0,[0]);self.assertEqual(r['boundary'],m.EXIT|1);self.assertEqual(r['registers'][0],0);self.assertEqual(len(r['loads']),1)
    def test_unsigned_second_compare(self):
        self.assertEqual(m.execute(0,0,[0xffff,0x8000])['boundary'],m.EXIT|1)
        self.assertEqual(m.execute(0,0,[0x8000,0xffff,0,1,2])['boundary'],m.CONT|1)
    def test_equality_early_exit(self):
        for values in ([1,1],[1,2,3,3]):self.assertEqual(m.execute(0,0,values)['boundary'],m.EXIT|1)
    def test_unsigned_third_compare(self):
        self.assertEqual(m.execute(0,0,[1,2,0xffff,1])['boundary'],m.EXIT|1)
    def test_arguments_truncate(self):
        r=m.execute(0xffffffab,0x1234fedc,[0]);self.assertEqual(r['registers'][6],0xab);self.assertEqual(r['registers'][5],0xfedc)
    def test_stack_words_order(self):
        initial={4:1,5:2,6:3,13:0x3007000,14:0x9000001};r=m.execute(0,0,[0],initial)
        self.assertEqual(r['local_sp_delta'],-16);self.assertEqual([x['register'] for x in r['stack_writes']],[4,5,6,14]);self.assertEqual([x['value'] for x in r['stack_writes']],[1,2,3,0x9000001]);self.assertEqual([x['address'] for x in r['stack_writes']],[0x3006ff0,0x3006ff4,0x3006ff8,0x3006ffc])
    def test_continuation_registers(self):
        r=m.execute(0x101,0x10002,[1,2,0,9,7]);self.assertEqual(r['registers'][:7],[0x300202c,9,0,7,0x203af96,2,1])
    def test_independent_ram_reread(self):
        r=m.execute(0,0,[1,2,0,1,0xffff]);self.assertEqual(r['registers'][3],0xffff);self.assertEqual([x['address'] for x in r['loads']],[0x203af10,0x3005edc,0x203af96,0x3002030,0x203af96])
    def test_all_saved_instructions_covered(self):
        seen=set()
        for values in ([0],[1,2,0,1,3]):seen.update(m.execute(0,0,values)['visited'])
        self.assertEqual(seen,set(m.CODE))
    def test_invalid_input_rejected(self):
        for x,y,reads in ((-1,0,[0]),(0,1<<32,[0]),(0,0,[65536]),(0,0,[]),(0,0,[0,1])):
            with self.assertRaises(ValueError):m.execute(x,y,reads)
    def test_no_unread_execution(self):
        r=m.execute(0,0,[1,2,0,1,0]);self.assertFalse(r['unread_code_executed']);self.assertEqual(r['nonstack_store_count'],0);self.assertNotIn(m.CONT,r['visited'])

if __name__=='__main__':unittest.main()
