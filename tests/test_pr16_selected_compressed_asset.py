"""保存音声rootからtype1圧縮read範囲だけの新しい人工境界試験。"""
import copy
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pr16_selected_compressed_asset as m

B = m.BASE


class DpcmTests(unittest.TestCase):
    def setUp(self):
        self.raw = bytearray(b"\xff" * 0x10000)
        self.bank = B + 0x1000
        self.wave = B + 0x3000
        self.raw[0x1000:0x100c] = struct.pack("<BBBBI4B", 0, 60, 0, 0, self.wave, 255, 0, 255, 0)
        self.set_wave(65)

    def set_wave(self, samples, kind=1, flags=0, freq=22050*1024, loop=0):
        struct.pack_into("<HHIII", self.raw, 0x3000, kind, flags, freq, loop, samples)
        self.raw[0x3010:0x3100] = bytes(range(240))

    def parse(self):
        return m.wave_type1(self.raw, self.wave)

    def test_one_block(self):
        self.set_wave(64)
        r = self.parse()
        self.assertEqual((r["blocks"], r["consumed_bytes"]), (1, 33))

    def test_partial_block_requires_full_encoded_block(self):
        self.assertEqual((self.parse()["blocks"], self.parse()["consumed_bytes"]), (2, 66))

    def test_65_samples_not_65_bytes(self):
        self.assertEqual(self.parse()["end_exclusive"], self.wave+16+66)

    def test_entire_four_bytes_at_start(self):
        self.assertEqual(m.blocks_covering(self.parse(), self.wave+16), [0])

    def test_four_bytes_at_last_block_end(self):
        self.assertEqual(m.blocks_covering(self.parse(), self.wave+16+62), [1])

    def test_boundary_straddle_requires_two_blocks(self):
        self.assertEqual(m.blocks_covering(self.parse(), self.wave+16+32), [0, 1])

    def test_partial_outside_refused(self):
        self.assertEqual(m.blocks_covering(self.parse(), self.wave+16+63), [])

    def test_header_not_payload(self):
        self.assertEqual(m.blocks_covering(self.parse(), self.wave+12), [])

    def test_unaligned_wave_refused(self):
        with self.assertRaises(ValueError): m.wave_type1(self.raw, self.wave+1)

    def test_noncompressed_refused(self):
        self.set_wave(1, kind=0)
        with self.assertRaises(ValueError): self.parse()

    def test_bad_flags_refused(self):
        self.set_wave(1, flags=1)
        with self.assertRaises(ValueError): self.parse()

    def test_invalid_frequency_refused(self):
        self.set_wave(1, freq=0)
        with self.assertRaises(ValueError): self.parse()

    def test_invalid_loop_refused(self):
        self.set_wave(1, loop=1)
        with self.assertRaises(ValueError): self.parse()

    def test_zero_samples_refused(self):
        self.set_wave(0)
        with self.assertRaises(ValueError): self.parse()

    def test_oversize_samples_refused(self):
        self.set_wave(0x200001)
        with self.assertRaises(ValueError): self.parse()

    def test_short_payload_refused(self):
        with self.assertRaises(ValueError):
            m.wave_type1(self.raw[:0x3032], self.wave)

    def test_invalid_width_refused(self):
        with self.assertRaises(ValueError):
            m.blocks_covering(self.parse(), self.wave+16, 0)

    def test_static_never_means_actual_reader(self):
        self.assertFalse(self.parse()["actual_reader_proven"])

    def test_no_write_deterministic(self):
        before = bytes(self.raw)
        self.assertEqual(self.parse(), self.parse())
        self.assertEqual(bytes(self.raw), before)

    def test_decoder_source_contract(self):
        text = ("arm_func_start SoundMainRAM_Unk2\n"
                "mov r0, r3, lsr 6\nmov r1, 0x21\nmul r2, r1, r0\n"
                "add r2, r2, 0x10\nmov r7, 0x40\n"
                "ldrb lr, [r2], 1\nldrb r1, [r2], 1\n"
                "ldrb r1, [r2], 1\nsubs r7, r7, 2\n"
                "arm_func_end SoundMainRAM_Unk2")
        m.verify_decoder_source(text)

    def test_decoder_contract_missing_second_byte_read(self):
        with self.assertRaises(ValueError):
            m.verify_decoder_source("arm_func_start SoundMainRAM_Unk2\n"
                                    "arm_func_end SoundMainRAM_Unk2")

    def test_owner_lineage_mismatched_archive_rejected(self):
        row = lambda at, owners: {"address": at, "modernization": {"owners": owners}}
        name = "pr16_supply_pla1"
        a = {"name": name, "gba_start": m.TARGETS[1]-8, "gba_end_exclusive": m.TARGETS[1]+8,
             "size": 16, "content_sha256": "abc", "owner": "fixed"}
        known = dict(name=name, start=a["gba_start"], end_exclusive=a["gba_end_exclusive"],
                     owner_offset=8, current_owner_sha256="abc", full_target_containment=True)
        p = {"rows": [row(m.TARGETS[0], []), row(m.TARGETS[1], [known]), row(m.TARGETS[2], [])]}
        gen = {"placement": {"allocation": {"allocations": [a]}}}
        supply = {"data_files": {"archive-image.bin": {"size": 16, "sha256": "abc"}}}
        align = {"link": {"allocation": {"allocations": [copy.deepcopy(a)]}},
                 "data_files": {"archive-image.bin": {"size": 16, "sha256": "other"}}}
        with self.assertRaises(ValueError): m.owner_lineage(p, gen, supply, align)


if __name__ == "__main__":
    unittest.main()
