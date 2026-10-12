"""未読1target採取の新規境界テスト。既読ABI/nativeは起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_divmod_frontier as m

class DivmodFrontierTests(unittest.TestCase):
    def setUp(self):
        self.raw = bytes(range(256))*4
        self.base = m.ROM_BASE
    def test_one_window(self):
        rows,n=m.sample(self.raw,{},self.base+4,512)
        self.assertEqual(n,0);self.assertEqual(len(rows),1)
        self.assertEqual(bytes.fromhex(rows[0]['hex']),self.raw[4:516])
    def test_reuse_splits_only_new_bytes(self):
        memory={self.base+4:4,self.base+7:7}
        rows,n=m.sample(self.raw,memory,self.base+4,8)
        self.assertEqual(n,2)
        self.assertEqual([(r['start'],r['end']) for r in rows],[(self.base+5,self.base+7),(self.base+8,self.base+12)])
    def test_all_reused(self):
        memory={self.base+i:i for i in range(8)}
        self.assertEqual(m.sample(self.raw,memory,self.base,8),([],8))
    def test_inputs_unchanged(self):
        memory={self.base:0};before=copy.deepcopy(memory)
        m.sample(self.raw,memory,self.base,8);self.assertEqual(memory,before)
        self.assertEqual(self.raw,bytes(range(256))*4)
    def test_saved_conflict_rejected(self):
        with self.assertRaises(ValueError):m.sample(self.raw,{self.base:7},self.base,8)
    def test_saved_bool_rejected(self):
        with self.assertRaises(ValueError):m.sample(self.raw,{self.base:False},self.base,8)
    def test_size_bounds(self):
        for size in (0,-2,1,513,514,True):
            with self.subTest(size=size),self.assertRaises(ValueError):m.sample(self.raw,{},self.base,size)
    def test_start_alignment(self):
        for start in (self.base+1,True,1.0):
            with self.subTest(start=start),self.assertRaises(ValueError):m.sample(self.raw,{},start,2)
    def test_rom_bounds(self):
        for start in (self.base-2,self.base+1024):
            with self.subTest(start=start),self.assertRaises(ValueError):m.sample(self.raw,{},start,2)
    def test_end_boundary(self):
        rows,_=m.sample(self.raw,{},self.base+1022,2)
        self.assertEqual(rows[0]['end'],self.base+1024)
    def test_raw_type(self):
        for raw in (b'',bytearray(8),None):
            with self.subTest(raw=type(raw)),self.assertRaises(ValueError):m.sample(raw,{},self.base,2)
    def test_memory_type(self):
        with self.assertRaises(ValueError):m.sample(self.raw,[],self.base,2)
    def test_identity(self):
        rows,_=m.sample(self.raw,{},self.base,8)
        self.assertEqual(rows[0]['identity'],m.identity(self.raw[:8]))
    def test_scope(self):
        self.assertEqual(m.TARGET,0x081C85A5);self.assertEqual(m.WINDOW,512)
        self.assertEqual(m.PRIOR,'content/modernization/pr16_ring_clock_contracts.json')

if __name__=='__main__':unittest.main()
