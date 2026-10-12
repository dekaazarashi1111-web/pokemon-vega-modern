"""新規v2表/fixture生成の境界。旧contract/native再実行なし。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_dependency_contracts as m


def fixture():
    rules=bytearray(368)
    for i in range(23):rules[i*16+10]=255
    for i,limit in enumerate((2,1,2,1)):rules[i*16+7:i*16+10]=bytes([1,i,limit])
    counters=bytearray(48)
    for i,limit in enumerate((24,50,18,8,10,6)):counters[i*8+2:i*8+4]=limit.to_bytes(2,'little')
    return bytes(rules),bytes(counters)


class RuleTests(unittest.TestCase):
    def test_exact_limits(self):
        self.assertEqual(m.parse_limits(*fixture()),{'allowed_mask':0,'slot_limits':[2,1,2,1],'counter_limits':[24,50,18,8,10,6]})
    def test_bit0(self):
        r,c=fixture();r=bytearray(r);r[10]=0;self.assertEqual(m.parse_limits(bytes(r),c)['allowed_mask'],1)
    def test_bit31(self):
        r,c=fixture();r=bytearray(r);r[10]=31;self.assertEqual(m.parse_limits(bytes(r),c)['allowed_mask'],1<<31)
    def test_bit32_ignored(self):
        r,c=fixture();r=bytearray(r);r[10]=32;self.assertEqual(m.parse_limits(bytes(r),c)['allowed_mask'],0)
    def test_duplicate_bits_folded(self):
        r,c=fixture();r=bytearray(r);r[10]=r[26]=3;self.assertEqual(m.parse_limits(bytes(r),c)['allowed_mask'],8)
    def test_rule_length(self):
        r,c=fixture()
        with self.assertRaises(ValueError):m.parse_limits(r[:-1],c)
    def test_counter_length(self):
        r,c=fixture()
        with self.assertRaises(ValueError):m.parse_limits(r,c[:-1])
    def test_slot_duplicate(self):
        r,c=fixture();r=bytearray(r);r[24]=0
        with self.assertRaises(ValueError):m.parse_limits(bytes(r),c)
    def test_slot_outside(self):
        r,c=fixture();r=bytearray(r);r[8]=4
        with self.assertRaises(ValueError):m.parse_limits(bytes(r),c)
    def test_slot_zero_limit(self):
        r,c=fixture();r=bytearray(r);r[9]=0
        with self.assertRaises(ValueError):m.parse_limits(bytes(r),c)
    def test_slot_missing(self):
        r,c=fixture();r=bytearray(r);r[7]=0
        with self.assertRaises(ValueError):m.parse_limits(bytes(r),c)
    def test_little_endian_limit(self):
        r,c=fixture();c=bytearray(c);c[2:4]=b'\x34\x12';self.assertEqual(m.parse_limits(r,bytes(c))['counter_limits'][0],0x1234)


class FixtureTests(unittest.TestCase):
    def setUp(self):self.base=m.c.initialized_data(0)
    def test_patch_byte(self):self.assertEqual(m.patched(self.base,0x75b,2,1)[0x75b],2)
    def test_patch_halfword(self):self.assertEqual(m.patched(self.base,0x74d,50,2)[0x74d:0x74f],b'2\0')
    def test_patch_word(self):self.assertEqual(m.patched(self.base,0x75f,0x80000000,4)[0x75f:0x763],b'\0\0\0\x80')
    def test_input_unchanged(self):
        before=self.base;m.patched(self.base,0x75b,2,1);self.assertEqual(self.base,before)
    def test_checksum_updated(self):
        v=m.patched(self.base,0x75b,2,1);self.assertEqual(int.from_bytes(v[8:12],'little'),m.vm.checksum(v))
    def test_value_overflow(self):
        with self.assertRaises(ValueError):m.patched(self.base,0x75b,256,1)
    def test_negative_value(self):
        with self.assertRaises(ValueError):m.patched(self.base,0x75b,-1,1)
    def test_offset_outside(self):
        with self.assertRaises(ValueError):m.patched(self.base,2047,1,2)
    def test_checksum_direct_write(self):
        with self.assertRaises(ValueError):m.patched(self.base,8,1,4)
    def test_width_three(self):
        with self.assertRaises(ValueError):m.patched(self.base,0x75b,1,3)
    def test_bool_value(self):
        with self.assertRaises(ValueError):m.patched(self.base,0x75b,True,1)
    def test_pending_subtype_range(self):
        self.assertEqual(m.PENDING_TABLE['length'],21*4);self.assertEqual(m.PENDING_TABLE['start']+20*4,0x08008c04)

if __name__=='__main__':unittest.main()
