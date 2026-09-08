"""P01 ROM参照監査の境界回帰。ROM原本は使わない。"""
from pathlib import Path
import struct
import unittest
from scripts.audit_p01_rom import BASE, collection_image, compatibility, occurrences, pointer
from tools.modernization_ids import CanonicalIndex, IdentityError


class RomAuditTests(unittest.TestCase):
    def test_pointer_requires_bounds_and_alignment(self):
        raw = bytearray(32)
        struct.pack_into("<I", raw, 0, BASE + 16)
        self.assertEqual(pointer(raw, 0, 16), 16)
        for address, size in ((BASE - 1, 1), (BASE + 17, 4), (BASE + 28, 8)):
            struct.pack_into("<I", raw, 0, address)
            with self.assertRaises(IdentityError):
                pointer(raw, 0, size)

    def test_collection_literal_full_identity(self):
        source = "const A gVegaAcqCollectionDefs[2] = {{0u,65535u,0u,0u,0u,0u}, {1u,386u,1u,1u,1u,0u}};"
        data, rows = collection_image(source, 2)
        self.assertEqual(len(data), 16)
        self.assertEqual(rows[1][1], 386)
        with self.assertRaisesRegex(IdentityError, "ID_SET"):
            collection_image(source.replace("{1u,", "{0u,"), 2)
        with self.assertRaisesRegex(IdentityError, "ID_SET"):
            collection_image(source, 3)

    def test_table_occurrences_do_not_claim_unique_or_live(self):
        self.assertEqual(occurrences(b"old.table.old.table", b"table"), [4, 14])
        self.assertEqual(occurrences(b"none", b"table"), [])
        with self.assertRaises(IdentityError):
            occurrences(b"anything", b"")

    def test_compatibility_table_preserves_inactive_bits(self):
        index = CanonicalIndex([{"move_key": "MOVE_KEY_NONE", "id": 0}, {"move_key": "MOVE_KEY_TEST", "id": 1}], "move", count=2)
        raw = bytearray(256)
        struct.pack_into("<II", raw, 0, BASE + 32, BASE + 64)
        struct.pack_into("<H", raw, 64, 1)
        raw[32] = 1
        raw[40] = 1
        result = compatibility(raw, 1, index, 0, 4, 1)
        self.assertEqual(result["compatibilities"], 1)
        self.assertEqual(result["inactive_bits_set"], 1)
        self.assertFalse(result["additional_slots_automatically_available"])
        struct.pack_into("<H", raw, 64, 2)
        with self.assertRaisesRegex(IdentityError, "OUT_OF_RANGE"):
            compatibility(raw, 1, index, 0, 4, 1)

    def test_actual_collection_source_parses_all_fixed_ids(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "vendor/vega_acquisition/generated/acquisition_collection_defs.c").read_text()
        image, rows = collection_image(source, 1621)
        self.assertEqual(len(image), 12968)
        self.assertEqual([row[0] for row in rows], list(range(1621)))


if __name__ == "__main__":
    unittest.main()
