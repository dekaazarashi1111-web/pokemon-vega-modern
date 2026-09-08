"""P01タマゴ技consumerのSpecies/Move意味と終端境界。"""
import struct
import unittest
from scripts.audit_p01_references import egg_stream
from tools.modernization_ids import CanonicalIndex, IdentityError


class EggReferenceTests(unittest.TestCase):
    def setUp(self):
        self.species = CanonicalIndex([{"species_key": "SPECIES_KEY_NONE", "id": 0}, {"species_key": "SPECIES_KEY_CATERPIE", "id": 649}], "species")
        self.moves = CanonicalIndex([{"move_key": "MOVE_KEY_NONE", "id": 0}, {"move_key": "MOVE_KEY_TACKLE", "id": 33}], "move")

    def blob(self, values):
        raw = bytearray(0x45220 + len(values) * 2)
        struct.pack_into("<I", raw, 0x45214, 0x08045220)
        struct.pack_into("<" + "H" * len(values), raw, 0x45220, *values)
        return bytes(raw)

    def test_species_and_move_keys_resolve(self):
        result = egg_stream(self.blob([20649, 33, 65535]), self.species, self.moves)
        self.assertEqual(result["rows"], [{"species_key": "SPECIES_KEY_CATERPIE", "id": 649, "moves": [["MOVE_KEY_TACKLE", 33]]}])
        self.assertEqual(result["missing_species_keys"], ["SPECIES_KEY_NONE"])

    def test_unknown_species_rejected(self):
        with self.assertRaisesRegex(IdentityError, "MARKER_UNKNOWN"):
            egg_stream(self.blob([20412, 33, 65535]), self.species, self.moves)

    def test_duplicate_species_not_overwritten(self):
        with self.assertRaisesRegex(IdentityError, "DUPLICATE"):
            egg_stream(self.blob([20649, 33, 20649, 33, 65535]), self.species, self.moves)

    def test_unknown_move_rejected(self):
        with self.assertRaisesRegex(IdentityError, "MOVE_WITHOUT"):
            egg_stream(self.blob([20649, 1063, 65535]), self.species, self.moves)

    def test_move_before_species_rejected(self):
        with self.assertRaisesRegex(IdentityError, "MOVE_WITHOUT"):
            egg_stream(self.blob([33, 65535]), self.species, self.moves)

    def test_missing_terminator_rejected(self):
        with self.assertRaisesRegex(IdentityError, "WITHOUT_TERMINATOR"):
            egg_stream(self.blob([20649, 33]), self.species, self.moves)


if __name__ == "__main__":
    unittest.main()
