"""新規探索形式の境界・誤命令拒否・非受入ラベルを検証する。"""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_branch_frontier as m

B = m.ROM_BASE

def raw16(*words):
    return struct.pack('<'+'H'*len(words), *words)

def raw32(*words):
    return struct.pack('<'+'I'*len(words), *words)

class Frontier(unittest.TestCase):
    def test_thumb_forward(self):
        self.assertEqual(m.thumb_branch(B, 0xE001), (B+6, 'thumb_b', 14))
    def test_thumb_backward(self):
        self.assertEqual(m.thumb_branch(B, 0xE7FD)[0], B-2)
    def test_thumb_signed_limits(self):
        self.assertEqual(m.thumb_branch(B, 0xE400)[0], B+4-2048)
        self.assertEqual(m.thumb_branch(B, 0xE3FF)[0], B+4+2046)
    def test_thumb_conditions(self):
        for condition in range(14):
            self.assertEqual(m.thumb_branch(B, 0xD000+(condition<<8)+127), (B+258, 'thumb_b_cond', condition))
            self.assertEqual(m.thumb_branch(B, 0xD080+(condition<<8))[0], B-252)
    def test_swi_undefined_rejected(self):
        for h in (0xDE00, 0xDF00):
            self.assertIsNone(m.thumb_branch(B, h))
    def test_thumb_bl_blx_bx_rejected(self):
        for h in (0xF000, 0xF800, 0xE800, 0x4700, 0x4780):
            self.assertIsNone(m.thumb_branch(B, h))
    def test_arm_forward_backward(self):
        self.assertEqual(m.arm_branch(B, 0xEA000001), (B+12, 'arm_b', 14))
        self.assertEqual(m.arm_branch(B, 0xEBFFFFFD), (B-4, 'arm_bl', 14))
    def test_arm_conditions(self):
        for c in range(15):
            self.assertEqual(m.arm_branch(B, (c<<28)|0x0A000000)[2], c)
    def test_arm_signed_limits(self):
        self.assertEqual(m.arm_branch(B, 0xEA800000)[0], B+8-0x2000000)
        self.assertEqual(m.arm_branch(B, 0xEA7FFFFF)[0], B+8+0x1FFFFFC)
    def test_arm_blx_rejected(self):
        self.assertIsNone(m.arm_branch(B, 0xFA000000))
        self.assertIsNone(m.arm_branch(B, 0xE12FFF30))
    def test_arm_adr_add_sub(self):
        self.assertEqual(m.arm_adr(B, 0xE28F1020), (B+40, 1))
        self.assertEqual(m.arm_adr(B, 0xE24F2020), (B-24, 2))
    def test_arm_adr_rotation(self):
        self.assertEqual(m.arm_adr(B, 0xE28F1C01), (B+8+256, 1))
        self.assertEqual(m.arm_adr(B, 0xE28F1102), ((B+8+0x80000000)&0xFFFFFFFF, 1))
    def test_arm_adr_not_adr(self):
        for w in (0xE29F1020, 0xE2801020, 0xE08F1002, 0xF28F1020, 0xE28FF020, 0xE38F1020):
            self.assertIsNone(m.arm_adr(B, w))
    def test_arm_literal_sign_pc(self):
        self.assertEqual(m.arm_literal(B, 0xE59F1004), (B+12, 1))
        self.assertEqual(m.arm_literal(B, 0xE51FF004), (B+4, 15))
    def test_arm_literal_reject_other_modes(self):
        for w in (0xE79F1004, 0xE49F1004, 0xE5DF1004, 0xE5BF1004, 0xE58F1004, 0xE5901004, 0xF59F1004):
            self.assertIsNone(m.arm_literal(B, w))
    def test_canonical_aliases(self):
        for alias in (B, 0x0A000000, 0x0C000000):
            self.assertEqual(m.canonical(alias+0x113984), m.INITIALIZER)
    def test_canonical_outside(self):
        for v in (0x02000000, 0x07000000, 0x0E000000, 0xFFFFFFFF):
            self.assertIsNone(m.canonical(v))
    def test_reference_short(self):
        self.assertEqual(m.references(raw16(0xE000, 0), B+4)[0]['kind'], 'thumb_b')
    def test_reference_conditional(self):
        self.assertEqual(m.references(raw16(0xD000, 0), B+4)[0]['condition'], 0)
    def test_reference_arm(self):
        rows = m.references(raw32(0xEB000000), B+8)
        self.assertTrue(any(r['kind']=='arm_bl' for r in rows))
    def test_thumb_adr_alignment(self):
        rows = m.references(raw16(0, 0xA100), B+4)
        self.assertTrue(any(r['site']==B+2 and r['register']==1 for r in rows))
    def test_thumb_sp_not_adr(self):
        self.assertEqual(m.references(raw16(0xA800, 0), B+4), [])
    def test_literal_thumb_odd_mirrored(self):
        raw = raw16(0x4800, 0)+raw32(0x0A000101)
        rows = m.references(raw, B+256)
        self.assertEqual(rows[0]['kind'], 'thumb_literal_pointer')
        self.assertEqual(rows[0]['value'], 0x0A000101)
    def test_literal_arm_pc(self):
        rows = m.references(raw32(0xE51FF004, B+257), B+256)
        self.assertEqual(rows[0]['kind'], 'arm_literal_pc')
    def test_literal_outside_not_read(self):
        self.assertEqual(m.references(raw16(0x48FF, 0), B+256), [])
    def test_trailing_halfword(self):
        self.assertEqual(m.references(raw16(0), B+256), [])
    def test_invalid_inputs(self):
        for raw in (b'', b'\0', bytearray(4), None):
            with self.assertRaises(ValueError): m.references(raw)
        for target in (B+1, B+2, B-4, B+m.ROM_SIZE, True):
            with self.assertRaises(ValueError): m.references(raw32(0), target)
        for budget in (0, 129, True):
            with self.assertRaises(ValueError): m.references(raw32(0), max_refs=budget)
    def test_reference_budget(self):
        with self.assertRaisesRegex(ValueError, '上限超過'):
            m.references(raw16(0xE002, 0xE001), B+8, max_refs=1)
    def test_input_unchanged_and_claims(self):
        raw = raw16(0xE000, 0)
        before = bytes(raw)
        rows = m.references(raw, B+4)
        self.assertEqual(raw, before)
        self.assertTrue(rows)
        self.assertTrue(all(r['runtime_reachable'] is False and r['code_data_boundary_proven'] is False for r in rows))
    def test_no_full_caller_claim(self):
        source = Path(m.__file__).read_text()
        self.assertIn("'all_callers_resolved': False", source)
        self.assertIn("'candidate_reconstructions': 1", source)
        self.assertIn("'new_emulator_processes': 0", source)

if __name__ == '__main__':
    unittest.main()
