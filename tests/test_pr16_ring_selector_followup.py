"""selector参照抽出の誤検知境界と既読byte除外。旧ABI/nativeは呼ばない。"""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest

PATH = Path(__file__).resolve().parents[1]/'scripts/pr16_ring_selector_followup.py'
SPEC = importlib.util.spec_from_file_location('selector_followup', PATH)
a = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(a)

class SelectorReferences(unittest.TestCase):
    def rom(self, site=0, literal=16, register=3, value=0x03005ed8):
        raw=bytearray(2048)
        half=0x4800 | register << 8 | ((literal-((site+4)&~3))//4)
        struct.pack_into('<H',raw,site,half);struct.pack_into('<I',raw,literal,value)
        return bytes(raw)
    def test_exact_literal(self):
        r=a.literal_references(self.rom(),{'selector':0x03005ed8})
        self.assertEqual(len(r),1);self.assertEqual(r[0]['site'],a.ROM_BASE)
        self.assertEqual(r[0]['register'],3);self.assertFalse(r[0]['runtime_reachable'])
    def test_pc_alignment(self):
        r=a.literal_references(self.rom(site=2),{'s':0x03005ed8})
        self.assertEqual(r[0]['site'],a.ROM_BASE+2)
    def test_largest_immediate(self):
        self.assertEqual(len(a.literal_references(self.rom(literal=1024),{'s':0x03005ed8})),1)
    def test_not_ldr(self):
        raw=bytearray(self.rom());struct.pack_into('<H',raw,0,0x4904)
        self.assertEqual(a.literal_references(bytes(raw),{'s':0x03005ed8}),[])
    def test_unaligned_literal(self):
        raw=bytearray(2048);struct.pack_into('<I',raw,17,0x03005ed8)
        self.assertEqual(a.literal_references(bytes(raw),{'s':0x03005ed8}),[])
    def test_other_global(self):
        self.assertEqual(a.literal_references(self.rom(),{'s':0x0300202c}),[])
    def test_all_registers(self):
        for reg in range(8):
            with self.subTest(reg=reg):
                self.assertEqual(a.literal_references(self.rom(register=reg),{'s':0x03005ed8})[0]['register'],reg)
    def test_invalid_input(self):
        for raw in (b'\0',bytearray(2),None):
            with self.subTest(raw=type(raw)),self.assertRaises(ValueError):a.literal_references(raw,{'s':1})
    def test_invalid_targets(self):
        for targets in ({},{'x':1,'y':1},{'x':-1},{'x':True}):
            with self.subTest(targets=targets),self.assertRaises(ValueError):a.literal_references(b'\0'*8,targets)
    def test_saved_node_conflict(self):
        n={'address':a.ROM_BASE,'size':2,'hex':'1048','kind':'ordinary'}
        self.assertEqual(len(a.node_bytes({'graph':{'nodes':[n,n]}})),2)
        m=dict(n,hex='0048')
        with self.assertRaises(ValueError):a.node_bytes([n,m])
    def test_saved_node_size(self):
        with self.assertRaises(ValueError):
            a.node_bytes({'address':a.ROM_BASE,'size':4,'hex':'1048','kind':'ordinary'})
    def test_known_site_not_redecoded(self):
        refs=[{'site':a.ROM_BASE+64}]
        self.assertEqual(a.fresh_windows(refs,{a.ROM_BASE+64:0},2048),[])
    def test_cut_known_bytes(self):
        base=a.ROM_BASE; known={base+at:0 for at in range(70,80)}
        windows=a.fresh_windows([{'site':base+64}],known,2048)
        points={at for lo,hi in windows for at in range(lo,hi)}
        self.assertTrue(points);self.assertFalse(points & known.keys())
    def test_merge_and_rom_edges(self):
        refs=[{'site':a.ROM_BASE},{'site':a.ROM_BASE+2}]
        self.assertEqual(a.fresh_windows(refs,{},64),[[a.ROM_BASE,a.ROM_BASE+64]])
    def test_no_input_mutation(self):
        refs=[{'site':a.ROM_BASE}];before=copy.deepcopy(refs)
        a.fresh_windows(refs,{},64);self.assertEqual(refs,before)

if __name__=='__main__':unittest.main()
