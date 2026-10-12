"""今回の保存継続のみ。先行prefixやnativeの再実行なし。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external1_cont_abi as m

def fixture():
    return {'candidate':copy.deepcopy(m.s.CANDIDATE),'target':m.START|1,
        'inherited_prefix_boundary':{'target':m.START|1,'frame_bytes_live':16,'r0':0x0300202C,'r4':m.COUNTER},
        'graph':{'entry':m.START|1,'window':64,'window_identity':{'size':64,'sha256':'4b644247477cc75b70ee272a1685ce71d62d5853951b7b4f53c9496193fb719d'},
        'nodes':m.expected_nodes(),'memory_write_sites':[0x081138E4],
        'external_edges':[dict(site=0x081138EE,kind='window_fallthrough',target=m.EXIT|1,resolved_to_code_address_only=True,stop_reason='SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED')],
        'saved_instruction_bytes_redecoded':0,'deferred_roots_decoded':0},
        'sampled_ranges':[dict(address=p,hex=h,**m.s.identity(bytes.fromhex(h))) for p,h in m.CODE.items()],
        'sampled_instruction_bytes':36,'old_unread_targets':list(range(1,36,2)),'remaining_unread_targets':[m.EXIT|1],
        **{k:False for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven','return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready')}}

class ContinuationABI(unittest.TestCase):
    def test_program(self):self.assertEqual(len(m.program(fixture())),18)
    def test_instruction_mutations(self):
        for i in range(18):
            a=fixture();a['graph']['nodes'][i]['hex']='0000'
            with self.assertRaises(ValueError):m.program(a)
    def test_sample_hash_mutation(self):
        a=fixture();a['sampled_ranges'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):m.program(a)
    def test_store_annotation_mutation(self):
        a=fixture();a['graph']['memory_write_sites']=[]
        with self.assertRaises(ValueError):m.program(a)
    def test_unread_edge_mutation(self):
        a=fixture();a['graph']['external_edges']=[]
        with self.assertRaises(ValueError):m.program(a)
    def test_frame_mutation(self):
        a=fixture();a['inherited_prefix_boundary']['frame_bytes_live']=0
        with self.assertRaises(ValueError):m.program(a)
    def test_acceptance_promotion(self):
        a=fixture();a['callee_return_proven']=True
        with self.assertRaises(ValueError):m.program(a)
    def test_match_pointer(self):self.assertEqual(m.execute(1,0x1234,7,0x02010000,0xabcd9234)['r0'],0x0201001e)
    def test_key_mismatch_no_store(self):
        r=m.execute(1,2,7,0x02010000,0xabcd9234);self.assertEqual(r['r0'],0);self.assertEqual(r['writes'],[])
    def test_mode_mismatch_no_store(self):self.assertEqual(m.execute(0,0x1234,7,0x02010000,0xabcd9234)['writes'],[])
    def test_key_upper_bit_cannot_match(self):self.assertEqual(m.execute(0,0x8000,0,0x02010000,0)['r0'],0)
    def test_mode_outside_one_bit_cannot_match(self):
        for mode in (2,255):self.assertEqual(m.execute(mode,0,0,0x02010000,0x8000)['r0'],0)
    def test_counter_wrap(self):self.assertEqual(m.execute(0,0,65535,0x02000000,0)['writes'],[dict(site=0x081138E4,address=m.COUNTER,size=2,value=0)])
    def test_record_high16_not_key(self):
        for high in (0,1,0x7fff,0xffff):self.assertEqual(m.execute(1,0x1234,0,0x02010000,(high<<16)|0x9234)['r0'],0x02010002)
    def test_exact_word_read_addresses(self):
        r=m.execute(0,0,9,0x02010000,0);self.assertEqual([x['address'] for x in r['loads']],[0x0300202c,0x02010024])
    def test_no_stack_or_prior_execution(self):
        r=m.execute(0,0,0,0x02010000,0);self.assertEqual(r['local_sp_delta'],0);self.assertFalse(r['unread_code_executed']);self.assertEqual((r['r4'],r['r5'],r['r6']),(m.COUNTER,0,0))
    def test_all_instructions_covered(self):
        seen=set()
        for key in (0,1):seen.update(m.execute(0,key,0,0x02010000,0)['visited'])
        self.assertEqual(seen,set(m.CODE))
    def test_pointer_wrap_arithmetic_only(self):self.assertEqual(m.execute(0,0,1,0xfffffffc,0)['r0'],2)
    def test_counter_can_overlap_saved_lr_halfword(self):
        r=m.execute(0,0,0,0x02010000,0);saved_lr=0x0203AF98-4
        self.assertTrue(saved_lr<=r['writes'][0]['address']<saved_lr+4)
    def test_invalid_inputs(self):
        for args in ((256,0,0,0,0),(0,65536,0,0,0),(0,0,-1,0,0),(0,0,0,1<<32,0)):
            with self.assertRaises(ValueError):m.execute(*args)

if __name__=='__main__':unittest.main()
