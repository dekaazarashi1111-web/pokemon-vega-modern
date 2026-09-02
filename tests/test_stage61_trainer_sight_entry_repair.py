from __future__ import annotations

import json
import struct
import unittest

from scripts.build_stage61_display_npc_event_audit import (
    DEFAULT_CONFIG,
    GBA_BASE,
    ROOT,
    TRAINER_EMPTY_TEXT_POINTER,
    Stage61BuildError,
    _trainer_intro_entry_patch_specs,
    _trainer_intro_repair_plan,
)


ROUTE501_COMMAND = 0x09376713
ROUTE501_TRAINER_ID = 89


class Stage61TrainerSightEntryRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = json.loads((ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8"))
        cls.stage60 = (
            ROOT / config["inputs"]["stage60_rom"]["path"]
        ).read_bytes()
        cls.plan = _trainer_intro_repair_plan(cls.stage60)

    @staticmethod
    def _materialized_row(source: dict[str, object]) -> dict[str, object]:
        return {
            **source,
            "adapter_address": 0x0942E464,
            "proxy_root_expected_hex": bytes(
                source["proxy_preimage"]
            )[:5].hex(),
            "command_prefix_expected_hex": bytes(
                source["command_raw"]
            )[:6].hex(),
            "intro_pointer_expected_hex": struct.pack(
                "<I", TRAINER_EMPTY_TEXT_POINTER
            ).hex(),
            "intro_pointer_replacement_hex": struct.pack(
                "<I", int(source["normal_text_pointer"])
            ).hex(),
        }

    def test_route501_keeps_direct_parser_prefix_and_repairs_only_intro(self) -> None:
        source = next(
            row for row in self.plan["repairs"]
            if int(row["command_address"]) == ROUTE501_COMMAND
        )
        self.assertEqual(source["kind"], 0)
        self.assertEqual(source["trainer_id"], ROUTE501_TRAINER_ID)
        self.assertNotEqual(
            source["normal_text_pointer"], TRAINER_EMPTY_TEXT_POINTER
        )

        repair = self._materialized_row(source)
        proxy, intro = _trainer_intro_entry_patch_specs(repair)
        output = bytearray(self.stage60)
        for patch in (proxy, intro):
            offset = int(patch["address"]) - GBA_BASE
            expected = bytes(patch["expected"])
            replacement = bytes(patch["replacement"])
            self.assertEqual(output[offset:offset + len(expected)], expected)
            output[offset:offset + len(replacement)] = replacement

        command_offset = ROUTE501_COMMAND - GBA_BASE
        self.assertEqual(
            output[command_offset:command_offset + 6],
            self.stage60[command_offset:command_offset + 6],
        )
        self.assertEqual(output[command_offset], 0x5C)
        self.assertEqual(output[command_offset + 1], 0)
        self.assertEqual(
            struct.unpack_from("<H", output, command_offset + 2)[0],
            ROUTE501_TRAINER_ID,
        )
        self.assertEqual(
            struct.unpack_from("<I", output, command_offset + 6)[0],
            int(source["normal_text_pointer"]),
        )
        self.assertEqual(
            bytes(output[
                command_offset + 10:
                command_offset + len(source["command_raw"])
            ]),
            bytes(source["command_raw"])[10:],
        )

    def test_all_478_commands_retain_a_valid_trainerbattle_header(self) -> None:
        repairs = self.plan["repairs"]
        self.assertEqual(len(repairs), 478)
        for source in repairs:
            with self.subTest(encounter=source["encounter_key"]):
                raw = bytes(source["command_raw"])
                self.assertEqual(raw[0], 0x5C)
                self.assertEqual(raw[1], source["kind"])
                self.assertEqual(
                    struct.unpack_from("<H", raw, 2)[0],
                    source["trainer_id"],
                )
                self.assertEqual(
                    struct.unpack_from("<I", raw, 6)[0],
                    TRAINER_EMPTY_TEXT_POINTER,
                )
                proxy, intro = _trainer_intro_entry_patch_specs(
                    self._materialized_row(source)
                )
                self.assertEqual(proxy["entry_kind"], "proxy_root")
                self.assertEqual(intro["entry_kind"], "battle_intro_pointer")
                self.assertEqual(
                    intro["address"], int(source["command_address"]) + 6
                )

    def test_eos_only_replacement_is_rejected(self) -> None:
        source = dict(self.plan["repairs"][0])
        source["normal_text_pointer"] = TRAINER_EMPTY_TEXT_POINTER
        with self.assertRaisesRegex(Stage61BuildError, "EOS-only"):
            _trainer_intro_entry_patch_specs(self._materialized_row(source))


if __name__ == "__main__":
    unittest.main()
