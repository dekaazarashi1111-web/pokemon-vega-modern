from __future__ import annotations

import json
import struct
import unittest

from scripts.build_stage61_display_npc_event_audit import (
    DEFAULT_CONFIG,
    GBA_BASE,
    ROOT,
    TRAINERBATTLE_POINTER_ROLES,
    TRAINERBATTLE_SIZES,
    _trainer_original_dialogue_restore_plan,
)


ROUTE501_ORIGINAL_COMMAND = 0x08E03080
ROUTE501_GENERATED_COMMAND = 0x09376713
ROUTE501_TRAINER_ID = 89
NO_INTRO_ORIGINAL_COMMAND = 0x0842A553


class Stage61TrainerDialogueRestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = json.loads((ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8"))

        def read_input(key: str) -> bytes:
            return (ROOT / config["inputs"][key]["path"]).read_bytes()

        cls.stage60 = read_input("stage60_rom")
        cls.vega = read_input("vega_reference_rom")
        cls.plan = _trainer_original_dialogue_restore_plan(
            cls.stage60,
            cls.vega,
            read_input("trainer_runtime_consumers"),
        )

    def test_inventory_restores_only_canonical_vega_trainers(self) -> None:
        report = self.plan["report"]
        self.assertEqual(report["canonical_vega_trainer_count"], 1030)
        self.assertEqual(report["restored_encounter_count"], 855)
        self.assertEqual(report["already_original_encounter_count"], 175)
        self.assertEqual(report["additional_trainer_count_untouched"], 272)
        self.assertEqual(report["generic_intro_proxy_bypass_count"], 499)
        self.assertEqual(
            report["proxy_shape_counts"],
            {
                "35_direct_bypass": 3,
                "35_generated_intro": 478,
                "8_direct_bypass": 150,
                "8_generated_intro": 21,
            },
        )
        self.assertEqual(report["patch_count"], 2209)
        self.assertEqual(report["restored_pointer_count"], 1769)
        self.assertEqual(len(self.plan["text_validations"]), 1366)
        self.assertEqual(len(self.plan["additional_validations"]), 272)
        self.assertEqual(
            report["additional_trainer_mode_counts"],
            {"ARCHIVE": 71, "KANTO_NEW": 201},
        )
        self.assertEqual(
            report["explicit_victory_continuation_count"], 30
        )
        self.assertEqual(
            report[
                "restored_split_victory_and_already_fought_edge_count"
            ],
            20,
        )
        self.assertTrue(all(
            str(row["encounter_key"]).startswith("ENC_TOHOKU_")
            for row in self.plan["patches"]
        ))

    def test_route501_keeps_party_identity_and_uses_vega_text(self) -> None:
        patches = [
            row for row in self.plan["patches"]
            if row["encounter_key"] == "ENC_TOHOKU_REF_1076"
        ]
        self.assertEqual(
            {row["entry_kind"] for row in patches},
            {
                "generic_intro_proxy_bypass",
                "trainerbattle_original_pointer_set",
                "generic_post_bypass",
            },
        )
        output = bytearray(self.stage60)
        for patch in patches:
            offset = int(patch["address"]) - GBA_BASE
            expected = bytes(patch["expected"])
            replacement = bytes(patch["replacement"])
            self.assertEqual(output[offset:offset + len(expected)], expected)
            output[offset:offset + len(replacement)] = replacement

        kind = 0
        size = TRAINERBATTLE_SIZES[kind]
        current_offset = ROUTE501_GENERATED_COMMAND - GBA_BASE
        original_offset = ROUTE501_ORIGINAL_COMMAND - GBA_BASE
        final_command = bytes(output[current_offset:current_offset + size])
        original_command = self.vega[original_offset:original_offset + size]
        self.assertEqual(final_command[:2], b"\x5C\x00")
        self.assertEqual(
            struct.unpack_from("<H", final_command, 2)[0],
            ROUTE501_TRAINER_ID,
        )
        self.assertEqual(
            final_command[4:6],
            self.stage60[current_offset + 4:current_offset + 6],
        )
        self.assertEqual(final_command[6:], original_command[6:])
        post = output[current_offset + size:current_offset + size + 5]
        self.assertEqual(
            post,
            b"\x05" + struct.pack("<I", ROUTE501_ORIGINAL_COMMAND + size),
        )

    def test_kind3_generated_external_intro_is_bypassed(self) -> None:
        key = "ENC_TOHOKU_REF_0000"
        patches = [
            row for row in self.plan["patches"]
            if row["encounter_key"] == key
            and row["entry_kind"] == "generic_intro_proxy_bypass"
        ]
        self.assertEqual(len(patches), 1)
        patch = patches[0]
        self.assertEqual(patch["proxy_size"], 8)
        self.assertEqual(bytes(patch["expected"])[:2], b"\x0F\x00")
        generated_command = struct.unpack_from(
            "<I", bytes(patch["replacement"]), 1
        )[0]
        self.assertEqual(bytes(patch["replacement"])[:1], b"\x05")

        # Vega's kind-3 command has no built-in intro pointer.  Its original
        # script already supplies the visible message immediately beforehand;
        # bypass only the extra ChangeKit msgbox and retain that script.
        original_offset = NO_INTRO_ORIGINAL_COMMAND - GBA_BASE
        original_prelude = self.vega[
            original_offset - 8:original_offset
        ]
        self.assertEqual(original_prelude[:2], b"\x0F\x00")
        self.assertIn(original_prelude[6:8], {b"\x09\x02", b"\x09\x04", b"\x09\x06"})
        self.assertEqual(
            generated_command,
            int(next(
                row["command_address"] for row in self.plan["validations"]
                if row["encounter_key"] == key
            )),
        )

    def test_victory_and_already_fought_continuations_stay_distinct(self) -> None:
        key = "ENC_TOHOKU_REF_0030"
        command_patch = next(
            row for row in self.plan["patches"]
            if row["encounter_key"] == key
            and row["entry_kind"] == "trainerbattle_original_pointer_set"
        )
        post_patch = next(
            row for row in self.plan["patches"]
            if row["encounter_key"] == key
            and row["entry_kind"] == "generic_post_bypass"
        )
        self.assertNotEqual(
            post_patch["victory_next"], post_patch["already_fought_next"]
        )
        kind = int(command_patch["kind"])
        continuation_index = TRAINERBATTLE_POINTER_ROLES[kind].index(
            "continuation"
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", bytes(command_patch["replacement"]),
                6 + 4 * continuation_index,
            )[0],
            post_patch["victory_next"],
        )
        self.assertEqual(
            bytes(post_patch["replacement"]),
            b"\x05" + struct.pack(
                "<I", int(post_patch["already_fought_next"])
            ),
        )

    def test_all_final_commands_keep_generated_headers_and_vega_pointers(self) -> None:
        output = bytearray(self.stage60)
        ranges: list[tuple[int, int]] = []
        for patch in self.plan["patches"]:
            offset = int(patch["address"]) - GBA_BASE
            expected = bytes(patch["expected"])
            replacement = bytes(patch["replacement"])
            ranges.append((offset, offset + len(expected)))
            self.assertEqual(output[offset:offset + len(expected)], expected)
            output[offset:offset + len(replacement)] = replacement
        ranges.sort()
        self.assertTrue(all(
            right_start >= left_end
            for (_left_start, left_end), (right_start, _right_end)
            in zip(ranges, ranges[1:])
        ))

        self.assertEqual(len(self.plan["validations"]), 1030)
        for validation in self.plan["validations"]:
            with self.subTest(encounter=validation["encounter_key"]):
                address = int(validation["command_address"])
                expected = bytes(validation["expected_command"])
                offset = address - GBA_BASE
                self.assertEqual(output[offset:offset + len(expected)], expected)
                kind = expected[1]
                self.assertEqual(expected[0], 0x5C)
                self.assertEqual(len(expected), TRAINERBATTLE_SIZES[kind])
                roles = TRAINERBATTLE_POINTER_ROLES[kind]
                for index, role in enumerate(roles):
                    self.assertEqual(
                        struct.unpack_from("<I", expected, 6 + 4 * index)[0],
                        validation["pointer_roles"][role],
                    )


if __name__ == "__main__":
    unittest.main()
