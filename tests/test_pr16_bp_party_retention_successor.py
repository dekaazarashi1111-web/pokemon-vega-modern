"""Scoped successor wiring tests for the verified player-party predicate callsite."""
from pathlib import Path
import struct
import sys
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts")]
import pr16_bp_party_retention_successor as p


class RetentionSuccessorTests(unittest.TestCase):
    def test_verified_original_call_and_new_trampoline_round_trip(self):
        self.assertEqual(p.decode_thumb_bl(p.CALLSITE, p.CALLSITE_BEFORE), p.ORIGINAL_PREDICATE)
        encoded = p.encode_thumb_bl(p.CALLSITE, p.TRAMPOLINE_ADDRESS)
        self.assertEqual(p.decode_thumb_bl(p.CALLSITE, encoded), p.TRAMPOLINE_ADDRESS)
        self.assertNotEqual(encoded, p.CALLSITE_BEFORE)

    def test_trampoline_is_absolute_thumb_tail_jump(self):
        entry = 0x09FF4735
        raw = p.make_trampoline(entry)
        self.assertEqual(len(raw), 8)
        self.assertEqual(struct.unpack("<HHI", raw), (0x4B00, 0x4718, entry))
        with self.assertRaises(ValueError):
            p.make_trampoline(entry - 1)

    def test_bl_range_and_alignment_fail_closed(self):
        for target in (p.CALLSITE + (1 << 22) + 4, p.CALLSITE - (1 << 22) - 2):
            with self.assertRaises(ValueError):
                p.encode_thumb_bl(p.CALLSITE, target)
        with self.assertRaises(ValueError):
            p.encode_thumb_bl(p.CALLSITE + 1, p.TRAMPOLINE_ADDRESS)

    def test_fixed_size_patch_rejects_wrong_preimage_and_reapply(self):
        raw = b"abcde"
        out = p.patch_bytes(raw, 1, b"bc", b"XY")
        self.assertEqual(out, b"aXYde")
        with self.assertRaises(ValueError):
            p.patch_bytes(out, 1, b"bc", b"XY")
        with self.assertRaises(ValueError):
            p.patch_bytes(raw, 1, b"b", b"XY")

    def test_source_is_read_only_and_entry_bound(self):
        text = (p.ROOT / p.SOURCE).read_text()
        self.assertIn('section(".text.entry")', text)
        self.assertIn("VegaFacilityRandomPlayerParty", text)
        self.assertIn("VEGA_ORIGINAL_RANDOM_PREDICATE", text)
        for token in ("write8(", "write16(", "write32(", "memcpy(", "busWrite", "rawWrite"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
