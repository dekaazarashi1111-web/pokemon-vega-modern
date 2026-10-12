"""新Blastoise有限prefixと完全LZ終端の反証。ROM入力/旧suiteは使わない。"""
import copy
import json
import random
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_blastoise_asset as v
import pr16_dex_hof_diploma_sources as codec

class Sparse:
    def __init__(self):self.cells={}
    def put(self,a,b):
        for j,x in enumerate(b):
            if a+j in self.cells and self.cells[a+j]!=x:raise ValueError('疎fixture重複')
            self.cells[a+j]=x
    def __len__(self):return v.CANDIDATE['size']
    def __getitem__(self,s):
        if not isinstance(s,slice) or s.step not in (None,1):raise ValueError('連続sliceだけ')
        return bytes(self.cells[a] for a in range(0x08000000+s.start,0x08000000+s.stop))

TILES=random.Random(601).randbytes(3200)
STREAM=codec.encode_lz10(TILES)[0]
def fixture(asset=STREAM):
    raw=Sparse()
    for ins in v.INS.values():raw.put(ins.address,v.encoded(ins))
    for a,n in v.LITERALS.items():raw.put(a,n.to_bytes(4,'little'))
    raw.put(v.TEMPLATE,v.template_bytes());raw.put(v.BIOS,bytes((17,223,112,71)))
    raw.put(v.ASSET['address'],asset)
    return raw

class BlastoiseAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.raw=fixture();cls.result=v.compose(cls.raw)
    def test58_bound_instructions_and52_steps(self):
        self.assertEqual(self.result['instruction_count'],58);self.assertEqual(self.result['executed_steps'],52)
    def test63_protected_windows(self):self.assertEqual(len(self.result['protected_windows']),63)
    def test_first_asset_return_is_only_endpoint(self):
        self.assertEqual(self.result['stop_pc'],0x080F52D2);self.assertIs(self.result['complete_function_executed'],False)
    def test_real_literal_and_api_calls(self):
        self.assertIn([0x080F52CE,0x080043D0],self.result['calls'])
        self.assertIn([0x08004418,v.BIOS],self.result['calls'])
    def test_real_three_condition_boundaries(self):
        self.assertEqual([x['site'] for x in self.result['conditional_boundaries']],[0x080F52A6,0x080F52AE,0x080F52C2])
    def test_complete_synthetic_decoded_identity(self):self.assertEqual(self.result['decoded'],v.identity(TILES))
    def test_complete_consumed_input_identity(self):
        self.assertEqual(self.result['encoded'],v.identity(STREAM));self.assertEqual(self.result['consumed_input_bytes'],len(STREAM))
    def test_whole_source_mismatch_blocks_even_covered_hit(self):
        a=v.assess(self.result);self.assertTrue(a['hit_fully_consumed']);self.assertFalse(a['minimum_type_eligible'])
    def test_shorter_stream_tail_remains_unknown(self):
        short=codec.encode_lz10(bytes(3200))[0];r=v.compose(fixture(short));a=v.assess(r)
        self.assertFalse(a['hit_fully_consumed']);self.assertFalse(a['minimum_type_eligible']);self.assertEqual(a['classified'],0)
    def test_actual_hit_outside_stream_is_never_read(self):
        raw=fixture(codec.encode_lz10(bytes(3200))[0]);r=v.compose(raw)
        self.assertNotIn(v.HIT,raw.cells);self.assertLess(r['encoded_end_exclusive'],v.HIT)
    def test_buffer_capacity_conditional_not_actual_allocator(self):
        e=self.result['events'][0];self.assertEqual(e['capacity_bytes'],3200);self.assertEqual(e['window'],1)
        self.assertIs(self.result['window_buffer_conditionally_produced'],True)
    def test_nonlive_erasure(self):self.assertTrue(self.result['nonlive_ram_erased_at_each_boundary'])
    def test_no_host_asset_pointer(self):self.assertFalse(self.result['asset_pointer_host_seeded'])
    def test_false_claims(self):
        for k,val in v.CLAIMS.items():self.assertIs(self.result[k],val)
    def test_all_instruction_bytes_reject_drift(self):
        for i in v.INS.values():
            for a in range(i.address,i.address+i.size):
                raw=fixture();raw.cells[a]^=1
                with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_all_literal_bytes_reject_drift(self):
        for a in v.LITERALS:
            for j in range(4):
                raw=fixture();raw.cells[a+j]^=1
                with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_all_template_bytes_reject_drift(self):
        for j in range(32):
            raw=fixture();raw.cells[v.TEMPLATE+j]^=1
            with self.subTest(byte=j),self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_bios_stub_reject_drift(self):
        raw=fixture();raw.cells[v.BIOS]=18
        with self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_epoch_each_boundary_rejected(self):
        for site in (0x080F52A6,0x080F52AE,0x080F52C2):
            with self.subTest(site=site),self.assertRaises(ValueError):v.compose(self.raw,invalidated=[site])
    def test_live_window_pointer_mutation_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={0x080F52AE:[(v.WINDOWS+20,4,0)]})
    def test_nonlive_caller_argument_slot_is_erased(self):
        # このprefixではMON呼出し済みのstack引数を再読しない。
        self.assertEqual(v.compose(self.raw,writes={0x080F52C2:[(0x03006FF0,4,99)]}),self.result)
    def test_nonlive_write_erased(self):
        self.assertEqual(v.compose(self.raw,writes={0x080F52AE:[(0x02008000,4,7)]}),self.result)
    def test_unknown_boundary_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={0:[]})
    def test_alias_boundary_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={float(0x080F52AE):[]})
    def test_write_alias_rejected(self):
        for rows in (True,[[v.BUFFER,True,0]],[[v.BUFFER,1,-1]]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):v.compose(self.raw,writes={0x080F52AE:rows})
    def test_contract_cannot_weaken(self):
        c=dict(v.CONTRACT);c['window_ja']='unconditional'
        with self.assertRaises(ValueError):v.compose(self.raw,contract=c)
    def test_wrong_header_length_rejected(self):
        with self.assertRaises(ValueError):v.compose(fixture(codec.encode_lz10(bytes(3199))[0]))
    def test_terminal_padding_excluded(self):
        self.assertEqual(v.compose(fixture(STREAM+b'not read')),self.result)
    def test_truncated_stream_rejected(self):
        with self.assertRaises((ValueError,KeyError)):v.compose(fixture(STREAM[:-1]))
    def test_minimum_witness_geometry(self):self.assertEqual(v.witness_geometry(v.evidence_template()),(v.HIT,4))
    def test_padding_witness_rejected(self):
        e=v.evidence_template();e['asset']['size']+=2
        with self.assertRaises(ValueError):v.witness_geometry(e)
    def test_partial_hit_rejected(self):
        e=v.evidence_template();e['classified_window']['size']=3
        with self.assertRaises(ValueError):v.witness_geometry(e)
    def test_diagnostic_scope_cannot_classify(self):
        with self.assertRaises(ValueError):v.validate_scope_proof({'newly_classified':1})
    def test_sparse_not_formal_candidate(self):
        with self.assertRaises((ValueError,TypeError)):v.measure(self.raw,{'candidate':v.CANDIDATE})
    def test_endpoint_inconsistent_rejected(self):
        c=copy.deepcopy(self.result);c['encoded_end_exclusive']+=1
        with self.assertRaises(ValueError):v.assess(c)
    def test_endpoint_alias_rejected(self):
        c=copy.deepcopy(self.result);c['encoded_end_exclusive']=float(c['encoded_end_exclusive'])
        with self.assertRaises(ValueError):v.assess(c)

if __name__=='__main__':unittest.main()
