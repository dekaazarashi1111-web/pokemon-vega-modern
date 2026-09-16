"""候補ROMなしでPC相対計算・境界・過大主張を検証する。"""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('candidate_audit', ROOT/'scripts/pr16_bp_candidate_return_audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class CandidateAuditTests(unittest.TestCase):
    def test_unaligned_references_are_not_dropped(self):
        raw = b'x'+struct.pack('<I', a.WHITEOUT)+b'yy'+struct.pack('<I', a.WHITEOUT)
        self.assertEqual(a.references(raw, a.WHITEOUT), [a.BASE+1, a.BASE+7])

    def test_pc_alignment_and_register(self):
        raw = bytearray(64)
        struct.pack_into('<H', raw, 2, 0x4B03)  # aligned PC=4, literal=16, r3
        struct.pack_into('<I', raw, 16, a.WHITEOUT)
        rows = a.literal_loads(bytes(raw), a.BASE+16)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['address'], rows[0]['register']), (a.BASE+2, 3))
        self.assertEqual(rows[0]['classification'], 'ENCODED_LDR_CANDIDATE_NOT_REACHABILITY_PROOF')

    def test_wrong_literal_immediate_rejected(self):
        raw = struct.pack('<H', 0x4800)+bytes(62)
        self.assertEqual(a.literal_loads(raw, a.BASE+16), [])

    def test_non_ldr_is_not_promoted(self):
        raw = struct.pack('<H', 0xA003)+bytes(62)
        self.assertEqual(a.literal_loads(raw, a.BASE+16), [])

    def test_unaligned_literal_has_no_thumb_ldr(self):
        self.assertEqual(a.literal_loads(bytes(64), a.BASE+17), [])

    def test_excerpt_fail_closed(self):
        for start, size in ((a.BASE-1, 2), (a.BASE+63, 2), (a.BASE, 1025), (a.BASE, 0)):
            with self.subTest(start=start, size=size), self.assertRaises(ValueError):
                a.excerpt(bytes(64), start, size)
        self.assertEqual(a.excerpt(b'abcd', a.BASE, 4)['hex'], '61626364')

    def test_wrong_candidate_rejected_before_decoding(self):
        with self.assertRaisesRegex(ValueError, 'exact bffd'):
            a.audit(b'not the candidate')

    def test_reference_limit(self):
        with self.assertRaisesRegex(ValueError, 'reference bound'):
            a.references(struct.pack('<I', a.WHITEOUT)*129, a.WHITEOUT)

    def test_invalid_literal_bounds(self):
        for address in (a.BASE-4, a.BASE+64):
            with self.assertRaises(ValueError):
                a.literal_loads(bytes(64), address)


if __name__ == '__main__':
    unittest.main()
