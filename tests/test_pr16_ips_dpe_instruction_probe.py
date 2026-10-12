"""IPS/DPE新scope命令形とoutput extentの独立人工境界試験（既受入試験を呼ばない）。"""
import hashlib
import struct
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import pr16_ips_dpe_instruction_probe as m

class InstructionExtentTest(unittest.TestCase):
    def setUp(self):
        self.base = 0x08000000
        self.raw = bytearray(0x1000)
        self.site = self.base+0x200
    def shapes(self):
        return m.instruction_shapes(bytes(self.raw), self.site)
    def test_thumb_positive_ldr_word(self):
        struct.pack_into("<H", self.raw, 0x100, 0x483F)
        self.assertEqual([(x["pc"],x["mode"]) for x in self.shapes()],[(self.base+0x100,"THUMB_LDR_LITERAL_SHAPE")])
    def test_arm_negative_ldr_word(self):
        struct.pack_into("<I", self.raw, 0x300, 0xE51F0108)
        self.assertEqual([(x["pc"],x["mode"]) for x in self.shapes()],[(self.base+0x300,"ARM_LDR_LITERAL_SHAPE")])
    def test_arm_positive_ldr_word(self):
        struct.pack_into("<I", self.raw, 0x100, 0xE59F00F8)
        self.assertEqual(self.shapes()[0]["mode"],"ARM_LDR_LITERAL_SHAPE")
    def test_no_shaped_instruction_is_proven_reader(self):
        struct.pack_into("<H", self.raw, 0x100, 0x483F)
        self.assertFalse(self.shapes()[0]["reader_proven"])
    def test_reject_unaligned_literal_word(self):
        self.assertEqual(m.instruction_shapes(bytes(self.raw), self.site+1), [])
    def test_reject_site_past_end(self):
        with self.assertRaises(ValueError):
            m.instruction_shapes(bytes(self.raw), self.base+0x1000)
    def test_random_data_no_literal(self):
        self.assertEqual(self.shapes(),[])
    def test_dpe_chain_fail_closed_wrong_pin(self):
        with self.assertRaises(ValueError):
            m.dpe_extent(bytes(self.raw), [], {"upstream":{"commit":"wrong"},"build_contract":{"insert_address":m.DPE_INSERT,"insert_copies_build_output_bin_contiguously":True}})
    def test_dpe_absent_preserves_not_proven(self):
        chain={"upstream":{"commit":"10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e"},"build_contract":{"insert_address":m.DPE_INSERT,"insert_copies_build_output_bin_contiguously":True}}
        r=m.dpe_extent(bytes(self.raw),[],chain)
        self.assertFalse(r["actual_output_bin_inclusion_proven"])
        self.assertFalse(r["linked_symbol_owner_proven"])
        self.assertEqual(r["observed_candidates"],[])
    def test_serialization_deterministic(self):
        value={"rows":[3,1,2],"私有":"false"}
        self.assertEqual(m.serialize(value),m.serialize(value))
        self.assertTrue(m.serialize(value).endswith(b"\n"))
    def test_identity_is_full_sha(self):
        a=m.identity(b"abc")
        self.assertEqual(a["sha256"],hashlib.sha256(b"abc").hexdigest())
        self.assertEqual(a["size"],3)

if __name__ == "__main__":
    unittest.main()
