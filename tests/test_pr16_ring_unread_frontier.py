"""未検索PC帯・保存byte差分・月表読取の合成入力回帰。ROM/nativeは起動しない。"""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_unread_frontier as m


def words(*values):
    return struct.pack('<' + 'I' * len(values), *values)


def halves(*values):
    return struct.pack('<' + 'H' * len(values), *values)


class Frontier(unittest.TestCase):
    def refs(self, raw, target=0x08000100):
        return m.mirror_references(raw, target)

    def test_alias_boundaries(self):
        for value, expected in ((0x08000000,0x08000000),(0x09FFFFFF,0x09FFFFFF),
                (0x0A000000,0x08000000),(0x0BFFFFFF,0x09FFFFFF),(0x0C000000,0x08000000),(0x0DFFFFFF,0x09FFFFFF)):
            self.assertEqual(m.canonical(value), expected)

    def test_alias_outside(self):
        for value in (-1,0x07FFFFFF,0x0E000000,0xFFFFFFFF):
            self.assertIsNone(m.canonical(value))

    def test_signed_limits(self):
        self.assertEqual([m.signed(x,24) for x in (0,0x7FFFFF,0x800000,0xFFFFFF)], [0,8388607,-8388608,-1])

    def test_empty_input(self):
        with self.assertRaises(ValueError): self.refs(b'')

    def test_odd_input(self):
        with self.assertRaises(ValueError): self.refs(b'\x00')

    def test_wrong_input_type(self):
        with self.assertRaises(ValueError): self.refs(bytearray(4))

    def test_bad_target(self):
        for t in (True,0x08000101,0x07000000,0x0A000000):
            with self.assertRaises(ValueError): self.refs(bytes(4),t)

    def test_bad_limit(self):
        for limit in (0,-1,129,True):
            with self.assertRaises(ValueError): m.mirror_references(bytes(4),max_refs=limit)

    def test_arm_crosses_canonical_lower_boundary(self):
        delta=(0x08000100-(0x0A000000+8))//4
        r=self.refs(words(0xEA000000|(delta&0xFFFFFF)))
        self.assertEqual([x['execution_address'] for x in r],[0x0A000000,0x0C000000])
        self.assertEqual([x['value'] for x in r],[0x08000100,0x0A000100])
        self.assertTrue(all(x['site']==0x08000000 and x['kind']=='arm_b' for x in r))

    def test_arm_bl_link(self):
        r=self.refs(words(0xEB00003E))
        self.assertEqual([x['kind'] for x in r],['arm_bl','arm_bl'])

    def test_arm_condition_retained(self):
        r=self.refs(words(0x1A00003E))
        self.assertEqual([x['condition'] for x in r],[1,1])

    def test_arm_condition_nv_rejected(self):
        self.assertEqual(self.refs(words(0xFA00003E)),[])

    def test_arm_wrong_opcode(self):
        self.assertEqual(self.refs(words(0xE800003E)),[])

    def test_arm_adr_rotated_cross_boundary(self):
        r=self.refs(words(0xE24F0402),0x08000008)
        self.assertEqual([x['kind'] for x in r],['arm_adr','arm_adr'])
        self.assertEqual([x['value'] for x in r],[0x08000008,0x0A000008])

    def test_arm_adr_add(self):
        r=self.refs(words(0xE28F00F8))
        self.assertEqual(len(r),2)
        self.assertTrue(all(x['register']==0 for x in r))

    def test_arm_adr_s_and_rdpc_rejected(self):
        for word in (0xE29F00F8,0xE28FF0F8):
            self.assertEqual(self.refs(words(word)),[])

    def test_arm_literal_positive(self):
        r=self.refs(words(0xE59F0000,0,0x08000101))
        self.assertEqual([x['literal_address'] for x in r],[0x0A000008,0x0C000008])
        self.assertTrue(all(x['physical_literal_address']==0x08000008 for x in r))

    def test_arm_literal_negative(self):
        self.assertEqual(len(self.refs(words(0xE51F0004,0x08000101))),2)

    def test_arm_literal_pc(self):
        r=self.refs(words(0xE59FF000,0,0x08000101))
        self.assertEqual([x['kind'] for x in r],['arm_literal_pc','arm_literal_pc'])

    def test_arm_literal_bad_modes(self):
        for word in (0xE49F0000,0xE5DF0000,0xE5BF0000,0xE58F0000):
            self.assertEqual(self.refs(words(word,0,0x08000101)),[])

    def test_literal_missing_not_read(self):
        self.assertEqual(self.refs(words(0xE59F0000)),[])

    def test_thumb_b_forward(self):
        self.assertEqual(len(self.refs(halves(0xE07E))),2)

    def test_thumb_b_backward(self):
        r=self.refs(halves(0xE7FE),0x08000000)
        self.assertEqual([x['kind'] for x in r],['thumb_b','thumb_b'])

    def test_thumb_cond(self):
        r=self.refs(halves(0xD17E))
        self.assertEqual([x['condition'] for x in r],[1,1])

    def test_thumb_swi_undefined(self):
        for half in (0xDE7E,0xDF7E): self.assertEqual(self.refs(halves(half)),[])

    def test_thumb_bl_pair(self):
        r=self.refs(halves(0xF000,0xF87E))
        self.assertEqual([x['kind'] for x in r],['thumb_bl','thumb_bl'])

    def test_thumb_bl_backward(self):
        r=self.refs(halves(0xF7FF,0xFFFE),0x08000000)
        self.assertEqual(len(r),2)

    def test_thumb_blx_and_truncated(self):
        for raw in (halves(0xF000,0xE87E),halves(0xF000)):
            self.assertEqual(self.refs(raw),[])

    def test_thumb_adr_alignment(self):
        r=self.refs(halves(0,0xA03F))
        self.assertEqual([x['execution_address'] for x in r],[0x0A000002,0x0C000002])

    def test_thumb_literal_alias_pointer(self):
        r=self.refs(halves(0x4800,0)+words(0x0C000101))
        self.assertEqual([x['value'] for x in r],[0x0C000101,0x0C000101])

    def test_thumb_sp_adr_rejected(self):
        self.assertEqual(self.refs(halves(0xA83F)),[])

    def test_limit_fail_closed(self):
        with self.assertRaises(ValueError): m.mirror_references(halves(0xE07E),0x08000100,1)

    def test_no_canonical_replay_or_reachability_claim(self):
        raw=words(0xEB00003E); before=raw
        r=self.refs(raw)
        self.assertEqual(raw,before)
        for row in r:
            self.assertIn(row['execution_address'],m.MIRRORS)
            self.assertFalse(row['runtime_reachable'])
            self.assertFalse(row['code_data_boundary_proven'])

    def test_unread_split_and_overlap(self):
        b=m.ROM_BASE; raw=bytes(range(16)); memory={b+2:2,b+3:3}
        fresh,reused,count=m.collect_unread(raw,memory,[(b,b+8),(b+4,b+12)])
        self.assertEqual([(w['start'],w['end']) for w in fresh],[(b,b+2),(b+4,b+12)])
        self.assertEqual(reused,[[b+2,b+4]]);self.assertEqual(count,2)
        self.assertEqual(memory,{b+2:2,b+3:3})
        for w in fresh: self.assertEqual(w['identity'],m.identity(bytes.fromhex(w['hex'])))

    def test_unread_all_cached(self):
        b=m.ROM_BASE
        self.assertEqual(m.collect_unread(b'abc',{b:97,b+1:98,b+2:99},[(b,b+3)]),([],[[b,b+3]],3))

    def test_unread_conflict(self):
        b=m.ROM_BASE
        with self.assertRaises(ValueError): m.collect_unread(b'ab',{b:0},[(b,b+2)])

    def test_unread_window_boundaries(self):
        b=m.ROM_BASE
        for focus in ([(b-1,b+1)],[(b,b)],[(b,b+3)],[(True,b+1)]):
            with self.assertRaises(ValueError): m.collect_unread(b'ab',{},focus)

    def test_unread_budgets(self):
        b=m.ROM_BASE;raw=bytes(17*2048)
        with self.assertRaises(ValueError): m.collect_unread(raw,{},[(b,b+2049)])
        with self.assertRaises(ValueError): m.collect_unread(raw,{},[(b+i*2048,b+(i+1)*2048) for i in range(17)])

    def test_month_little_endian_no_calendar_assumption(self):
        values=[0,1,2,30,31,28,29,0x12345678,255,256,65536,0xFFFFFFFF]
        self.assertEqual(m.decode_month_table(words(*values)),values)

    def test_month_length_and_type(self):
        for raw in (bytes(47),bytes(49),bytearray(48)):
            with self.assertRaises(ValueError): m.decode_month_table(raw)

    def test_ranges_empty_and_disjoint(self):
        self.assertEqual(m.ranges(set()),[])
        self.assertEqual(m.ranges({3,1,2,7}),[[1,4],[7,8]])

    def test_scope_constants(self):
        self.assertEqual(m.EXTERNALS,(0x0912C4A9,0x0912C555,0x09099E05))
        self.assertEqual(m.MONTH,(0x09169530,0x09169560))
        self.assertNotIn(m.ROM_BASE,m.MIRRORS)


if __name__=='__main__': unittest.main()
