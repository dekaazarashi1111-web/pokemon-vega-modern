from __future__ import annotations

import hashlib
import json
import unittest

from scripts.build_stage61_display_npc_event_audit import (
    CREATE_BOX_MON_ENTRY,
    CREATE_BOX_MON_FRIENDSHIP_CLEAN_CONTEXT,
    CREATE_BOX_MON_FRIENDSHIP_CONTEXT_START,
    CREATE_BOX_MON_FRIENDSHIP_REPLACEMENT,
    CREATE_BOX_MON_FRIENDSHIP_SITE,
    CREATE_BOX_MON_FRIENDSHIP_STAGE60_CONTEXT,
    CREATE_BOX_MON_FRIENDSHIP_STAGE61_CONTEXT,
    CREATE_BOX_MON_SIZE,
    CREATE_BOX_MON_STAGE60_SHA256,
    CREATE_BOX_MON_STAGE61_SHA256,
    DEFAULT_CONFIG,
    GBA_BASE,
    GET_SPECIES_NAME_EARLY_EXIT_REPLACEMENT,
    GET_SPECIES_NAME_EARLY_EXIT_SITE,
    GET_SPECIES_NAME_IMPLEMENTATION,
    GET_SPECIES_NAME_IMPLEMENTATION_SIZE,
    GET_SPECIES_NAME_STAGE61_SHA256,
    GET_SPECIES_NAME_TABLE,
    GET_SPECIES_NAME_TABLE_COUNT,
    GET_SPECIES_NAME_TABLE_STRIDE,
    ROOT,
    Stage61BuildError,
    _apply_create_box_mon_friendship_repair,
    _apply_species_name_padding_repair,
)


class Stage61CreateBoxMonFriendshipRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = json.loads((ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8"))
        cls.stage60 = (
            ROOT / config["inputs"]["stage60_rom"]["path"]
        ).read_bytes()
        cls.clean = (
            ROOT / config["inputs"]["clean_rom"]["path"]
        ).read_bytes()

    def test_pinned_clean_and_stage60_dataflow_expose_the_register_bug(
        self,
    ) -> None:
        context = CREATE_BOX_MON_FRIENDSHIP_CONTEXT_START - GBA_BASE
        self.assertEqual(
            self.clean[context:context + 16],
            CREATE_BOX_MON_FRIENDSHIP_CLEAN_CONTEXT,
        )
        self.assertEqual(
            self.stage60[context:context + 16],
            CREATE_BOX_MON_FRIENDSHIP_STAGE60_CONTEXT,
        )

        clean_halfwords = tuple(
            int.from_bytes(CREATE_BOX_MON_FRIENDSHIP_CLEAN_CONTEXT[index:index + 2],
                           "little")
            for index in range(0, 16, 2)
        )
        stage60_halfwords = tuple(
            int.from_bytes(CREATE_BOX_MON_FRIENDSHIP_STAGE60_CONTEXT[index:index + 2],
                           "little")
            for index in range(0, 16, 2)
        )
        self.assertEqual(clean_halfwords[2:5], (0x00C2, 0x1A12, 0x0092))
        self.assertEqual(stage60_halfwords[2:5], (0x0148, 0x46C0, 0x46C0))
        # The malformed instruction writes r0 from r1 (SP); the consumer uses
        # r2.  The clean sequence instead writes r2 from species in r0.
        self.assertEqual((stage60_halfwords[2] >> 3) & 0x7, 1)
        self.assertEqual(stage60_halfwords[2] & 0x7, 0)

    def test_repair_is_one_changed_byte_and_exact_complete_function(self) -> None:
        output = bytearray(self.stage60)
        declared: list[dict[str, object]] = []
        report = _apply_create_box_mon_friendship_repair(
            self.stage60, self.clean, output, declared,
        )

        changed = [
            index for index, (before, after) in
            enumerate(zip(self.stage60, output)) if before != after
        ]
        self.assertEqual(
            changed, [CREATE_BOX_MON_FRIENDSHIP_SITE - GBA_BASE]
        )
        self.assertEqual(len(declared), 1)
        self.assertEqual(declared[0]["size"], 2)
        context = CREATE_BOX_MON_FRIENDSHIP_CONTEXT_START - GBA_BASE
        self.assertEqual(
            bytes(output[context:context + 16]),
            CREATE_BOX_MON_FRIENDSHIP_STAGE61_CONTEXT,
        )
        function = CREATE_BOX_MON_ENTRY - GBA_BASE
        self.assertEqual(
            hashlib.sha256(
                self.stage60[function:function + CREATE_BOX_MON_SIZE]
            ).hexdigest(),
            CREATE_BOX_MON_STAGE60_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(
                output[function:function + CREATE_BOX_MON_SIZE]
            ).hexdigest(),
            CREATE_BOX_MON_STAGE61_SHA256,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["assertions"].values()))

    def test_replacement_encodes_lsl_r2_r0_5_and_preserves_pointer_adds(
        self,
    ) -> None:
        instruction = int.from_bytes(
            CREATE_BOX_MON_FRIENDSHIP_REPLACEMENT, "little"
        )
        self.assertEqual(instruction >> 11, 0)
        self.assertEqual((instruction >> 6) & 0x1F, 5)
        self.assertEqual((instruction >> 3) & 0x7, 0)
        self.assertEqual(instruction & 0x7, 2)
        fixed_halfwords = tuple(
            int.from_bytes(CREATE_BOX_MON_FRIENDSHIP_STAGE61_CONTEXT[index:index + 2],
                           "little")
            for index in range(0, 16, 2)
        )
        self.assertEqual(fixed_halfwords[2:5], (0x0142, 0x46C0, 0x46C0))
        self.assertEqual(fixed_halfwords[5:7], (0x3412, 0x1912))

    def test_preimage_drift_fails_closed(self) -> None:
        broken = bytearray(self.stage60)
        broken[CREATE_BOX_MON_FRIENDSHIP_SITE - GBA_BASE] ^= 0x01
        with self.assertRaisesRegex(
            Stage61BuildError,
            "Stage60 stride preimage",
        ):
            _apply_create_box_mon_friendship_repair(
                bytes(broken), self.clean, bytearray(broken), [],
            )

    def test_species_name_padding_repair_copies_full_canonical_rows(self) -> None:
        output = bytearray(self.stage60)
        declared: list[dict[str, object]] = []
        report = _apply_species_name_padding_repair(
            self.stage60, output, declared,
        )
        instruction = int.from_bytes(
            GET_SPECIES_NAME_EARLY_EXIT_REPLACEMENT, "little"
        )
        self.assertEqual(instruction, 0x46C0)
        self.assertEqual(
            [
                index for index, (before, after) in
                enumerate(zip(self.stage60, output)) if before != after
            ],
            [
                GET_SPECIES_NAME_EARLY_EXIT_SITE - GBA_BASE,
                GET_SPECIES_NAME_EARLY_EXIT_SITE - GBA_BASE + 1,
            ],
        )
        implementation = GET_SPECIES_NAME_IMPLEMENTATION - GBA_BASE
        self.assertEqual(
            hashlib.sha256(output[
                implementation:
                implementation + GET_SPECIES_NAME_IMPLEMENTATION_SIZE
            ]).hexdigest(),
            GET_SPECIES_NAME_STAGE61_SHA256,
        )
        self.assertEqual(len(declared), 1)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["assertions"].values()))

        table = GET_SPECIES_NAME_TABLE - GBA_BASE
        species18 = self.stage60[
            table + 18 * GET_SPECIES_NAME_TABLE_STRIDE:
            table + 19 * GET_SPECIES_NAME_TABLE_STRIDE
        ]
        self.assertEqual(species18, bytes.fromhex("648A9CAEFFFFFFFFFFFFFF"))
        stale_destination = bytearray(b"\x0E\x1C" * 6)
        stale_destination[:GET_SPECIES_NAME_TABLE_STRIDE] = species18
        self.assertEqual(
            stale_destination[:7], bytes.fromhex("648A9CAEFFFFFF")
        )

    def test_species_name_table_is_a_complete_eos_padded_partition(self) -> None:
        table = GET_SPECIES_NAME_TABLE - GBA_BASE
        raw = self.stage60[
            table:table
            + GET_SPECIES_NAME_TABLE_COUNT * GET_SPECIES_NAME_TABLE_STRIDE
        ]
        self.assertEqual(
            len(raw), GET_SPECIES_NAME_TABLE_COUNT * GET_SPECIES_NAME_TABLE_STRIDE
        )
        for species in range(GET_SPECIES_NAME_TABLE_COUNT):
            with self.subTest(species=species):
                row = raw[
                    species * GET_SPECIES_NAME_TABLE_STRIDE:
                    (species + 1) * GET_SPECIES_NAME_TABLE_STRIDE
                ]
                eos = row.index(0xFF)
                self.assertEqual(row[eos:], b"\xFF" * (len(row) - eos))


if __name__ == "__main__":
    unittest.main()
