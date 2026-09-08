from __future__ import annotations

import copy
import struct
import unittest

from scripts import build_modernization_p01 as p01


class ModernizationP01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config, cls.inputs = p01._load_config(p01.DEFAULT_CONFIG)

    def test_collection_table_is_resolved_by_stable_species_key(self) -> None:
        table, evidence = p01._derive_collection_table(self.config)

        self.assertEqual(len(table), p01.SPECIES_COUNT * 8)
        self.assertEqual(evidence["mismatch_count"], 2)
        self.assertEqual(
            {row["species_key"] for row in evidence["mismatches"]},
            {"SPECIES_KEY_EGG", "SPECIES_KEY_CATERPIE"},
        )
        self.assertEqual(
            struct.unpack_from("<HHBBBB", table, 412 * 8),
            (412, p01.NO_INDEX, 0, 0, 0, 0),
        )
        self.assertEqual(
            struct.unpack_from("<HHBBBB", table, 649 * 8),
            (649, 386, 1, 1, p01.TARGET_CLASSES["REQUIRED_BASE"], 0),
        )
        self.assertEqual(evidence["ledger_bit_count"], 1216)
        self.assertEqual(evidence["completion_target_count"], 1206)
        self.assertTrue(evidence["save_layout_unchanged"])

    def test_unapproved_identity_mismatch_is_rejected(self) -> None:
        config = copy.deepcopy(self.config)
        config["runtime_table"]["corrections"] = []
        with self.assertRaisesRegex(
            p01.ModernizationP01BuildError,
            "unexpected Species ID mismatch set",
        ):
            p01._derive_collection_table(config)

    def test_changed_spans_are_exact_and_do_not_merge_neighbors(self) -> None:
        self.assertEqual(
            p01._changed_spans(b"0123456789", b"01AA45B789"),
            [
                {"start": 2, "end_exclusive": 4, "size": 2},
                {"start": 6, "end_exclusive": 7, "size": 1},
            ],
        )


if __name__ == "__main__":
    unittest.main()
