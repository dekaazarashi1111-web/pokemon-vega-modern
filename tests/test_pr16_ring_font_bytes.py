"""新しい初期化窓だけの有限採取・型・範囲・過大主張拒否。旧契約は実行しない。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_font_bytes as t


class ProbeTests(unittest.TestCase):
    def fixture(self):
        raw=bytearray(1024);raw[0:2]=bytes.fromhex('0349');raw[4:6]=bytes.fromhex('0348')
        raw[16:20]=t.prior.GFONTS.to_bytes(4,'little');raw[20:24]=(t.ROM+128).to_bytes(4,'little')
        return bytes(raw)
    def probe(self,raw=None):return t.probe(self.fixture()if raw is None else raw,t.ROM,t.ROM+8)
    def test_literal_address_pc_alignment(self):
        a=self.probe();self.assertEqual([r['literal_address']for r in a['literal_candidates']],[t.ROM+16,t.ROM+20])
    def test_gfonts_is_ram_not_rom_table(self):
        a=self.probe();self.assertEqual(a['gfonts_literal_sites'],[t.ROM]);self.assertEqual(len(a['table_candidates']),1)
    def test_sample_size_is_not_extent(self):
        table=self.probe()['table_candidates'][0];self.assertEqual(table['size'],192)
        self.assertIs(table['actual_table_length_proven'],False);self.assertIs(table['is_font_table_proven'],False)
    def test_no_code_boundary_claim(self):self.assertTrue(all(not r['code_boundary_proven']for r in self.probe()['literal_candidates']))
    def test_no_live_initializer_claim(self):self.assertIs(self.probe()['initializer_runtime_observed'],False)
    def test_no_all_writer_claim(self):self.assertIs(self.probe()['all_writers_resolved'],False)
    def test_points_unique_sorted(self):
        p=self.probe()['points'];self.assertEqual(p,sorted(set(p)));self.assertEqual(len(p),208)
    def test_empty_instruction_window(self):self.assertEqual(self.probe(bytes(1024))['table_candidates'],[])
    def test_duplicate_table_pointer_reused(self):
        raw=bytearray(self.fixture());raw[16:20]=raw[20:24]
        self.assertEqual(len(self.probe(bytes(raw))['table_candidates']),1)
    def test_odd_pointer_not_table(self):
        raw=bytearray(self.fixture());raw[20:24]=(t.ROM+129).to_bytes(4,'little')
        self.assertEqual(self.probe(bytes(raw))['table_candidates'],[])
    def test_code_window_not_table(self):
        raw=bytearray(self.fixture());raw[20:24]=t.ROM.to_bytes(4,'little')
        self.assertEqual(self.probe(bytes(raw))['table_candidates'],[])
    def test_truncated_table_not_sampled(self):
        raw=bytearray(self.fixture());raw[20:24]=(t.ROM+900).to_bytes(4,'little')
        self.assertEqual(self.probe(bytes(raw))['table_candidates'],[])
    def test_literal_out_of_rom_rejected(self):
        with self.assertRaisesRegex(ValueError,'読取範囲'):self.probe(bytes.fromhex('ff48')+bytes(1022))
    def test_raw_type_rejected(self):
        for raw in (bytearray(8),'x',None,b''):
            with self.subTest(type=type(raw)),self.assertRaises(ValueError):t.probe(raw,t.ROM,t.ROM+8)
    def test_window_alignment_rejected(self):
        with self.assertRaisesRegex(ValueError,'初期化窓'):t.probe(self.fixture(),t.ROM+1,t.ROM+8)
    def test_window_size_rejected(self):
        for size in (0,-2,98):
            with self.subTest(size=size),self.assertRaisesRegex(ValueError,'初期化窓'):t.probe(self.fixture(),t.ROM,t.ROM+size)
    def test_read_strict_integer(self):
        for size in (True,1.0,0,193):
            with self.subTest(size=size),self.assertRaises(ValueError):t.read(self.fixture(),t.ROM,size)
    def test_read_boundaries(self):
        self.assertEqual(t.read(self.fixture(),t.ROM+1023,1),b'\0')
        with self.assertRaises(ValueError):t.read(self.fixture(),t.ROM+1023,2)
    def test_identity_matches_finite_bytes(self):
        import hashlib
        table=self.probe()['table_candidates'][0];self.assertEqual(table['identity']['sha256'],hashlib.sha256(bytes.fromhex(table['hex'])).hexdigest())
    def test_plan_rejects_incorrect_saved_count(self):
        with self.assertRaisesRegex(ValueError,'保存3955命令'):t.plan({'saved_node_count':3954},[])


if __name__=='__main__':unittest.main()
