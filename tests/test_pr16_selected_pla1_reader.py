"""新しいPLA1境界検査。過去の全owner試験やnativeを再走しない。"""
import copy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pr16_selected_pla1_reader as m


def fixture():
    b = bytearray(6735)
    b[:4] = b"PLA1"
    for at, value in ((4, 1), (6, 32), (8, 1671)):
        struct.pack_into("<H", b, at, value)
    b[10:12] = bytes((1, 8))
    for at, value in ((12, 32), (16, 6716), (20, 6726), (24, len(b)), (28, 2)):
        struct.pack_into("<I", b, at, value)
    b[32:6716] = b"\xff" * 6684
    struct.pack_into("<HH", b, 6716, 6720, 3)
    struct.pack_into("<HHH", b, 6720, 1, 2, 3)
    b[6726:6730] = b"\xff\xff\x00\x03"
    b[6730:6735] = struct.pack("<H", 6726) + b"\x00\x01\x06"
    struct.pack_into("<H", b, 32 + 530 * 4, 6730)
    struct.pack_into("<H", b, 32, 6726)
    return b


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.b = fixture()

    def reject(self, at, data):
        self.b[at:at + len(data)] = data
        with self.assertRaises(ValueError):
            m.decode(bytes(self.b), 530, 0)

    def test_delta_output(self):
        moves, chain = m.decode(bytes(self.b), 530, 0)
        self.assertEqual(moves, [1, 3])
        self.assertEqual([r["offset"] for r in chain], [6730, 6726])

    def test_base_output(self):
        self.assertEqual(m.decode(bytes(self.b), 0, 0)[0], [1, 2])

    def test_selector_delta_boundary(self):
        rows = m.cover(m.decode(bytes(self.b), 530, 0)[1], 6733, 2)
        self.assertEqual([r["role"] for r in rows], ["selector_u8", "xor_mask_u8"])

    def test_record_header_boundary(self):
        rows = m.cover(m.decode(bytes(self.b), 530, 0)[1], 6731, 3)
        self.assertEqual([r["role"] for r in rows], ["relative_base_u16", "template_id_u8", "selector_u8"])

    def test_unread_target_rejected(self):
        with self.assertRaises(ValueError):
            m.cover(m.decode(bytes(self.b), 530, 0)[1], 6710, 4)

    def test_overlapping_roles_rejected(self):
        chain = m.decode(bytes(self.b), 530, 0)[1]
        with self.assertRaises(ValueError):
            m.cover(chain + copy.deepcopy(chain), 6733, 1)

    def test_empty_target_rejected(self):
        with self.assertRaises(ValueError):
            m.cover([], 0, 0)

    def test_negative_target_rejected(self):
        with self.assertRaises(ValueError):
            m.cover([], -1, 1)

    def test_bad_magic(self): self.reject(0, b"NOPE")
    def test_bad_version(self): self.reject(4, b"\x02")
    def test_bad_header_size(self): self.reject(6, b"\x21")
    def test_bad_owner_count(self): self.reject(8, b"\x00\x00")
    def test_bad_depth_header(self): self.reject(11, b"\x09")
    def test_bad_directory(self): self.reject(12, struct.pack("<I", 33))
    def test_bad_table(self): self.reject(16, struct.pack("<I", 6715))
    def test_bad_size(self): self.reject(24, struct.pack("<I", 6734))
    def test_zero_record_count(self): self.reject(28, b"\x00" * 4)
    def test_bad_template_id(self): self.reject(6732, b"\x01")
    def test_empty_templates(self): self.reject(10, b"\x00")
    def test_future_base(self): self.reject(6730, struct.pack("<H", 6734))
    def test_self_cycle(self): self.reject(6730, struct.pack("<H", 6730))
    def test_base_before_records(self): self.reject(6730, struct.pack("<H", 6725))
    def test_zero_delta(self): self.reject(6734, b"\x00")
    def test_bad_selector_high_bit(self): self.reject(6733, b"\x02")
    def test_bad_unused_mask_bit(self): self.reject(6734, b"\x80")
    def test_zero_move(self): self.reject(6720, b"\x00\x00")
    def test_large_move(self): self.reject(6720, struct.pack("<H", 1063))
    def test_duplicate_selected_move(self): self.reject(6724, struct.pack("<H", 1))
    def test_identity_only_owner(self):
        with self.assertRaises(ValueError): m.decode(bytes(self.b), 1, 0)
    def test_owner_abi(self):
        for owner in (-1, 1671, True):
            with self.subTest(owner=owner), self.assertRaises(ValueError): m.decode(bytes(self.b), owner, 0)
    def test_family_abi(self):
        for family in (-1, 2, True):
            with self.subTest(family=family), self.assertRaises(ValueError): m.decode(bytes(self.b), 530, family)
    def test_take_bounds(self):
        for offset, width in ((-1, 1), (0, 0), (6734, 2), (True, 1)):
            with self.subTest(offset=offset, width=width), self.assertRaises(ValueError): m.take(bytes(self.b), offset, width)
    def test_truncated_selector(self):
        self.b = self.b[:-2]
        struct.pack_into("<I", self.b, 24, len(self.b))
        with self.assertRaises(ValueError): m.decode(bytes(self.b), 530, 0)
    def test_truncated_delta(self):
        self.b = self.b[:-1]
        struct.pack_into("<I", self.b, 24, len(self.b))
        with self.assertRaises(ValueError): m.decode(bytes(self.b), 530, 0)
    def test_deterministic_readonly(self):
        before = bytes(self.b)
        first = m.decode(before, 530, 0)
        self.assertEqual(first, m.decode(before, 530, 0))
        self.assertEqual(before, bytes(self.b))
    def test_proof_rejects_unbound_candidate(self):
        with self.assertRaises(ValueError): m.prove(b"", b"", b"")


if __name__ == "__main__":
    unittest.main()
