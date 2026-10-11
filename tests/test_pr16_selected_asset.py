"""新規有限asset探索の人工境界試験。受入済みreaderを再走しない。"""
import copy
import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_asset as m

class SelectedAssetTests(unittest.TestCase):
    def literal(self):
        return b'\x10\x08\x00\x00\x00abcdefgh'
    def test_inside(self): self.assertTrue(m.inside(100, 8, 104))
    def test_end_excluded(self): self.assertFalse(m.inside(100, 8, 108))
    def test_crossing(self): self.assertFalse(m.inside(100, 8, 106))
    def test_negative(self): self.assertRaises(ValueError, m.interval, -1, 1)
    def test_zero(self): self.assertRaises(ValueError, m.interval, 0, 0)
    def test_bool(self): self.assertRaises(ValueError, m.interval, True, 2)
    def test_overflow(self): self.assertRaises(ValueError, m.interval, 2**32-1, 2)
    def test_slice(self): self.assertEqual(m.section(b'abc', 10, 11, 2), b'bc')
    def test_slice_outside(self): self.assertRaises(ValueError, m.section, b'abc', 10, 12, 2)
    def test_literal(self):
        r=m.lz77(self.literal(), 100, 100, 104)
        self.assertEqual(r['expanded'], m.identity(b'abcdefgh'))
        self.assertEqual([x['kind'] for x in r['target_roles']], ['flags','literal','literal','literal'])
        self.assertTrue(r['target_fully_consumed'])
    def test_overlap_reference(self):
        r=m.lz77(b'\x10\x07\x00\x00\x40A\x30\x00', 100,100,104)
        self.assertEqual(r['expanded'], m.identity(b'A'*7))
        self.assertEqual(sorted(i for x in r['target_roles'] for i in x['target_byte_indexes']), [0,1,2,3])
    def test_underflow(self): self.assertRaises(ValueError,m.lz77,b'\x10\x03\x00\x00\x80\x00\x00',0,0,4)
    def test_overshoot(self): self.assertRaises(ValueError,m.lz77,b'\x10\x03\x00\x00\x40A\x30\x00',0,0,4)
    def test_bad_type(self): self.assertRaises(ValueError,m.lz77,b'\x11'+self.literal()[1:],0,0,4)
    def test_zero_output(self): self.assertRaises(ValueError,m.lz77,b'\x10\0\0\0',0,0,4)
    def test_output_limit(self): self.assertRaises(ValueError,m.lz77,self.literal(),0,0,4,4,7)
    def test_truncated(self): self.assertRaises(ValueError,m.lz77,self.literal()[:-1],0,0,4)
    def test_padding_not_consumed(self): self.assertFalse(m.lz77(self.literal()+b'xxxx',0,0,13)['target_fully_consumed'])
    def test_header_not_token(self): self.assertFalse(m.lz77(self.literal(),0,0,0)['target_fully_consumed'])
    def test_candidate(self):
        r=m.candidates(self.literal()+b'0'*32,100,104)
        self.assertEqual([x['start'] for x in r['matches']], [100])
    def test_bad_candidate_is_not_match(self):
        r=m.candidates(b'\x10\x03\x00\x00\x80\x00\x00'+b'0'*16,100,104)
        self.assertEqual(r['matches'],[]); self.assertEqual(r['rejected_headers'],1)
    def test_bounded_radius(self): self.assertRaises(ValueError,m.candidates,self.literal(),0,4,4,65537)
    def test_unaligned_ignored(self): self.assertEqual(m.candidates(b'0'+self.literal()+b'0'*16,100,108)['matches'],[])
    def test_input_unchanged(self):
        raw=bytearray(self.literal()+b'0'*16); before=bytes(raw);m.candidates(raw,100,104)
        self.assertEqual(bytes(raw),before)
    def descriptor(self): return bytes([1,0,0,0])+struct.pack('<5I',*[0x08000100+i*4 for i in range(5)])
    def test_tileset(self): self.assertEqual(m.tileset(self.descriptor(),100,100)['tiles'],0x08000100)
    def test_tileset_flags(self): self.assertRaises(ValueError,m.tileset,b'\x02'+self.descriptor()[1:],100,100)
    def test_tileset_pointer(self):
        raw=bytearray(self.descriptor()); struct.pack_into('<I',raw,4,0)
        self.assertRaises(ValueError,m.tileset,raw,100,100)
    def test_descriptor_binding(self):
        r=m.bind_descriptors(self.descriptor(),{'gTileset_Test':{'address':0x08000000}},[{'start':0x08000100}])
        self.assertEqual(len(r['matching_descriptors']),1); self.assertFalse(r['actual_consumer_proven'])
    def test_descriptor_mismatch(self): self.assertEqual(m.bind_descriptors(self.descriptor(),{'gTileset_Test':{'address':0x08000000}},[])['matching_descriptors'],[])
    def test_deterministic_no_bytes(self):
        raw=self.literal()+b'0'*32; a=m.candidates(raw,100,104); b=m.candidates(raw,100,104)
        self.assertEqual(m.encode(a),m.encode(b)); self.assertNotIn(b'abcdefgh',m.encode(a))
        self.assertFalse(a['actual_consumer_proven'])

if __name__=='__main__': unittest.main()
