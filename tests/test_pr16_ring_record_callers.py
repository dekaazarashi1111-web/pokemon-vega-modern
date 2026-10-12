"""新規call参照採取の境界。先行ABI/nativeを再実行しない。"""
import copy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_record_callers as m
B = m.ROM_BASE

def encode(at, target):
    offset = target-at-4
    assert not offset & 1 and -(1<<22) <= offset < (1<<22)
    offset &= (1<<23)-1
    return struct.pack('<HH', 0xf000 | (offset>>12), 0xf800 | ((offset>>1)&2047))

class Callers(unittest.TestCase):
    def test_forward(self):
        h,l=struct.unpack('<HH',encode(B,B+40));self.assertEqual(m.bl_target(B,h,l),B+40)
    def test_backward(self):
        h,l=struct.unpack('<HH',encode(B+40,B));self.assertEqual(m.bl_target(B+40,h,l),B)
    def test_extreme_negative(self):
        h,l=struct.unpack('<HH',encode(B+0x500000,B+0x100004));self.assertEqual(m.bl_target(B+0x500000,h,l),B+0x100004)
    def test_extreme_positive(self):
        h,l=struct.unpack('<HH',encode(B,B+0x400002));self.assertEqual(m.bl_target(B,h,l),B+0x400002)
    def test_blx_rejected(self): self.assertIsNone(m.bl_target(B,0xf000,0xe800))
    def test_thumb2_branch_rejected(self): self.assertIsNone(m.bl_target(B,0xf000,0xb800))
    def test_single_halfword(self): self.assertEqual(m.references(b'\x00\xf0',(B,)),[])
    def test_direct_reference(self):
        r=m.references(encode(B,B+8)+b'\x00'*6,(B+8,));self.assertEqual([(x['site'],x['target']) for x in r],[(B,B+8)])
    def test_aligned_pointer_variants(self):
        r=m.references(struct.pack('<II',B+20,B+21),(B+20,));self.assertEqual(len(r),2);self.assertTrue(all(not x['runtime_reachable'] for x in r))
    def test_unaligned_pointer_ignored(self): self.assertEqual(m.references(b'\x00\x00'+struct.pack('<I',B+20),(B+20,)),[])
    def test_invalid_input(self):
        for raw in (b'\x00',bytearray(4),'abcd'):
            with self.assertRaises(ValueError):m.references(raw,(B,))
    def test_invalid_targets(self):
        for targets in ((),(B,B),(B+1,),(True,),(-2,),(0x0a000000,)):
            with self.assertRaises(ValueError):m.references(b'\x00'*8,targets)
    def test_budget(self):
        with self.assertRaises(ValueError):m.references(struct.pack('<II',B,B),(B,),1)
    def test_merge_conflict(self):
        d={};m.merge_bytes(d,B,b'\x12\x34');m.merge_bytes(d,B,b'\x12')
        with self.assertRaises(ValueError):m.merge_bytes(d,B,b'\x13')
    def test_ranges(self):self.assertEqual(m.ranges([4,1,2,2,5]),[[1,3],[4,6]])
    def test_clipped_windows(self):
        self.assertEqual(m.requested_points([{'site':B}],b'\x00'*8,()),set(range(B,B+8)))
    def test_literal_one_level(self):
        raw=struct.pack('<H',0x4807)+b'\x00'*62
        points=m.requested_points([],raw,((B,B+2),))
        self.assertEqual(points,{B,B+1,B+32,B+33,B+34,B+35})
    def test_inputs_unchanged(self):
        r=[{'site':B}];before=copy.deepcopy(r);m.requested_points(r,b'\0'*8,());self.assertEqual(r,before)
    def test_window_bound(self):
        with self.assertRaises(ValueError):m.requested_points([],b'\0'*(m.MAX_BYTES+2),((B,B+m.MAX_BYTES+2),))
    def test_outside_literal(self):
        self.assertEqual(m.requested_points([],b'\xff\x48',((B,B+2),)),{B,B+1})

if __name__=='__main__':unittest.main()
