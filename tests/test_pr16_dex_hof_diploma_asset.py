"""Diplomaの独立疎fixture・LZ reader・条件付き資源境界の新規反証。"""
import copy
import json
import random
import sys
import unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_diploma_asset as v
import pr16_dex_hof_diploma_sources as source

class Sparse:
    def __init__(self):self.cells={}
    def put(self,a,b):
        for j,x in enumerate(b):
            if a+j in self.cells and self.cells[a+j]!=x:raise ValueError('疎fixture重複')
            self.cells[a+j]=x
    def __len__(self):return v.CANDIDATE['size']
    def __getitem__(self,s):
        if not isinstance(s,slice) or s.step not in (None,1):raise ValueError('連続sliceのみ')
        return bytes(self.cells[a] for a in range(0x08000000+s.start,0x08000000+s.stop))

SYNTHETIC_TILES=random.Random(519).randbytes(8192)
SYNTHETIC_LZ=source.encode_lz10(SYNTHETIC_TILES)[0]
def fixture(asset=None):
    raw=Sparse()
    for i in v.INS.values():raw.put(i.address,v.encoded(i))
    for a,x in v.LITERALS.items():raw.put(a,x.to_bytes(4,'little'))
    raw.put(v.BIOS,bytes((17,223,112,71)))
    raw.put(v.ASSET['address'],SYNTHETIC_LZ if asset is None else asset)
    return raw

def stream(b,**kw):
    base=0x08001000
    return v.decode_stream(lambda a,n:b[a-base:a-base+n],base,**kw)

class DiplomaAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=fixture();cls.result=v.compose(cls.raw)
    def test_actual_two_phase_producer(self):
        self.assertEqual(self.result['phase_steps'],[160,120]);self.assertFalse(self.result['state1_host_seeded'])
    def test_actual_root_to_reader_and_bg(self):
        self.assertIn([0x080F6038,0x080F78D0],self.result['calls'])
        self.assertIn([0x080F7B1C,v.BIOS],self.result['calls'])
        self.assertIn([0x080F7B48,v.BG],self.result['calls'])
    def test_all149_semantics_and157_windows(self):
        self.assertEqual(self.result['instruction_count'],149);self.assertEqual(len(self.result['protected_windows']),157)
    def test_synthetic_output_identity(self):
        self.assertEqual(self.result['decoded'],v.identity(SYNTHETIC_TILES))
        self.assertEqual(self.result['encoded'],v.identity(SYNTHETIC_LZ))
    def test_complete_bios_model_and_false_claims(self):
        e=self.result['events'];self.assertEqual([x['kind']for x in e],['conditional_allocation','bios_lz10','conditional_bg_copy'])
        for key,value in v.CLAIMS.items():self.assertIs(self.result[key],value)
    def test_same_buffer_bg_arguments(self):
        self.assertEqual(self.result['events'][2],dict(kind='conditional_bg_copy',site=0x080F7B48,bg=1,buffer=v.BUFFER,size=8192,offset=0))
    def test_nonlive_erasure(self):self.assertTrue(self.result['nonlive_ram_erased_at_each_boundary'])
    def test_no_host_asset_pointer(self):self.assertFalse(self.result['asset_pointer_host_seeded'])
    def test_every_instruction_byte_rejects_drift(self):
        for i in v.INS.values():
            for a in range(i.address,i.address+i.size):
                raw=fixture();raw.cells[a]^=1
                with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_every_literal_byte_rejects_drift(self):
        for a in v.LITERALS:
            for j in range(4):
                raw=fixture();raw.cells[a+j]^=1
                with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_bios_stub_rejects_other_swi(self):
        raw=fixture();raw.cells[v.BIOS]=18
        with self.assertRaises(ValueError):v.bind_semantics(raw)
    def test_minimum_geometry(self):self.assertEqual(v.witness_geometry(v.evidence_template()),(v.HIT,4))
    def test_padded_extent_rejected(self):
        e=v.evidence_template();e['asset']['size']+=2
        with self.assertRaises(ValueError):v.witness_geometry(e)
    def test_partial_hit_rejected(self):
        e=v.evidence_template();e['classified_window']['size']=3
        with self.assertRaises(ValueError):v.witness_geometry(e)
    def test_geometry_alias_rejected(self):
        e=v.evidence_template();e['classified_window']['address']=float(v.HIT)
        with self.assertRaises(ValueError):v.witness_geometry(e)
    def test_epoch_at_each_boundary_rejected(self):
        for s in (0x080F7B0E,0x080F7B48):
            with self.subTest(site=s),self.assertRaises(ValueError):v.compose(self.raw,invalidated=[s])
    def test_live_object_at_alloc_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={0x080F7B0E:[(v.OBJECT+1,1,2)]})
    def test_live_buffer_at_bg_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={0x080F7B48:[(v.BUFFER+8191,1,0)]})
    def test_live_count_at_bg_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={0x080F7B48:[(v.COUNT,2,32)]})
    def test_nonlive_write_is_erased(self):
        r=v.compose(self.raw,writes={0x080F7B0E:[(0x02008000,4,7)]});self.assertEqual(r,self.result)
    def test_unknown_boundary_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={0x08000000:[]})
    def test_noninteger_boundary_rejected(self):
        with self.assertRaises(ValueError):v.compose(self.raw,writes={float(0x080F7B0E):[]})
    def test_effect_rows_reject_types(self):
        for rows in (True,[[v.BUFFER,True,0]],[[v.BUFFER,1,-1]]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):v.compose(self.raw,writes={0x080F7B0E:rows})
    def test_contract_cannot_be_weakened(self):
        c=dict(v.CONTRACT);c['allocation_ja']='universal'
        with self.assertRaises(ValueError):v.compose(self.raw,contract=c)
    def test_literal_stream_roundtrip(self):
        b=bytes((16,3,0,0,0,1,2,3));encoded,decoded,reads=stream(b)
        self.assertEqual(encoded,b);self.assertEqual(decoded,bytes((1,2,3)))
        self.assertEqual(sum(n for _,n in reads),len(b))
    def test_overlap_reference_roundtrip(self):
        b=bytes((16,6,0,0,0x40,65,0x20,0));self.assertEqual(stream(b)[1],b'A'*6)
    def test_terminal_padding_is_not_read(self):
        b=bytes((16,3,0,0,0,1,2,3));self.assertEqual(stream(b+b'padding')[0],b)
    def test_invalid_distance_rejected(self):
        with self.assertRaises(ValueError):stream(bytes((16,3,0,0,0x80,0,0)))
    def test_final_backref_overshoot_rejected(self):
        with self.assertRaises(ValueError):stream(bytes((16,3,0,0,0x40,65,0,0)))
    def test_bad_codec_rejected(self):
        with self.assertRaises(ValueError):stream(bytes((17,1,0,0,0,1)))
    def test_zero_and_large_output_rejected(self):
        for n in (0,8193):
            with self.subTest(n=n),self.assertRaises(ValueError):stream(bytes((16,))+n.to_bytes(3,'little'))
    def test_truncation_rejected(self):
        b=bytes((16,3,0,0,0,1,2,3))
        for n in range(len(b)):
            with self.subTest(n=n),self.assertRaises(ValueError):stream(b[:n])
    def test_encoded_budget_rejected(self):
        with self.assertRaises(ValueError):stream(bytes((16,3,0,0,0,1,2,3)),encoded_limit=5)
    def test_nonint_budget_rejected(self):
        with self.assertRaises(ValueError):stream(bytes((16,3,0,0,0,1,2,3)),maximum=True)
    def test_current_candidate_gate_rejects_sparse(self):
        with self.assertRaises((ValueError,TypeError)):v.regions(self.raw,{'candidate':v.CANDIDATE})

if __name__=='__main__':unittest.main()
