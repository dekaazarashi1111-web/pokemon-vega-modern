import csv
import hashlib
import json
import struct
import unittest
from collections import Counter
from pathlib import Path

from scripts import build_trainer_changekit_final as final


ROOT = Path(__file__).resolve().parents[1]


class TrainerChangeKitFinalBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.outputs = final.build_runtime_outputs(ROOT)
        cls.rom = cls.outputs[final.OUTPUT_ROM.as_posix()]
        cls.metadata = json.loads(cls.outputs[final.OUTPUT_META.as_posix()])
        cls.serialized = json.loads(cls.outputs[final.OUTPUT_SERIALIZED.as_posix()])

    def test_generated_outputs_are_current_and_byte_deterministic(self) -> None:
        for relative, expected in self.outputs.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(path.read_bytes(), expected, relative)
        repeated = final.build_runtime_outputs(ROOT)
        self.assertEqual(self.outputs, repeated)

    def test_complete_catalog_party_and_mechanic_coverage(self) -> None:
        coverage = self.metadata["coverage"]
        self.assertEqual(coverage["encounter_count"], 1302)
        self.assertEqual(coverage["party_count"], 1302)
        self.assertEqual(coverage["member_count"], 6490)
        self.assertEqual(
            coverage["battle_format_counts"], {"SINGLE": 1228, "DOUBLE": 74}
        )
        self.assertEqual(
            coverage["gimmick_type_counts"],
            {"NONE": 1034, "MEGA": 86, "Z_MOVE": 111,
             "DYNAMAX": 4, "TERASTAL": 67},
        )
        self.assertEqual(coverage["authored_ability_direct_override_count"], 924)
        sidecars = self.serialized["tables"]["sidecars"]
        self.assertEqual(len(sidecars), 6490)
        self.assertTrue(all(0 <= row["ability_id"] <= 0xFFFF for row in sidecars))
        self.assertEqual(sum(not row["ability_native"] for row in sidecars), 924)

    def test_all_1302_physical_commands_are_unique_and_exact(self) -> None:
        rows = self.serialized["battle_rows"]
        self.assertEqual(len(rows), 1302)
        self.assertEqual(len({row["encounter_key"] for row in rows}), 1302)
        self.assertEqual(len({row["command_address"] for row in rows}), 1302)
        self.assertEqual(
            Counter(row["binding_mode"] for row in rows),
            {"CANONICAL": 1030, "ARCHIVE": 71, "KANTO_NEW": 201},
        )
        for row in rows:
            offset = row["command_address"] - final.GBA_ROM_BASE
            self.assertEqual(self.rom[offset], 0x5C, row["encounter_key"])
            self.assertEqual(self.rom[offset + 1], row["kind"], row["encounter_key"])
            self.assertEqual(
                struct.unpack_from("<H", self.rom, offset + 2)[0],
                row["target_trainer_id"], row["encounter_key"],
            )
            self.assertEqual(row["data_address"], row["command_address"] + 1)

    def test_expanded_trainer_table_points_to_complete_parties(self) -> None:
        runtime = self.metadata["runtime"]["payload"]
        table = runtime["trainer_table_address"] - final.GBA_ROM_BASE
        party_start = runtime["party_blob_address"]
        party_end = party_start + runtime["party_blob_size"]
        records = self.serialized["trainer_records"]
        parties = {row["trainer_id"]: row for row in self.serialized["party_rows"]}
        self.assertEqual(len(records), 1302)
        self.assertEqual(len(parties), 1302)
        for audit in records:
            trainer_id = audit["trainer_id"]
            record = self.rom[
                table + trainer_id * 32:table + (trainer_id + 1) * 32
            ]
            party = parties[trainer_id]
            self.assertEqual(record[0], 3)
            self.assertEqual(record[0x12], party["battle_format"] == "DOUBLE")
            self.assertEqual(record[0x18], party["party_size"])
            pointer = struct.unpack_from("<I", record, 0x1C)[0]
            self.assertEqual(pointer, audit["party_pointer"])
            self.assertTrue(party_start <= pointer < party_end)
            raw_size = party["party_size"] * final.PARTY_MEMBER_SIZE
            raw = self.rom[pointer - final.GBA_ROM_BASE:
                           pointer - final.GBA_ROM_BASE + raw_size]
            self.assertEqual(hashlib.sha256(raw).hexdigest(), party["party_sha256"])

    def test_runtime_hooks_and_cleanup_contract_are_physically_patched(self) -> None:
        hooks = self.metadata["hooks"]
        ram = self.metadata["runtime_ram"]
        self.assertEqual(ram["start"], final.TRAINER_CHANGEKIT_STATE_ADDRESS)
        self.assertEqual(ram["end_exclusive"],
                         final.TRAINER_CHANGEKIT_STATE_ADDRESS
                         + final.TRAINER_CHANGEKIT_STATE_SIZE)
        self.assertEqual(ram["live_overlap_count"], 0)
        self.assertEqual(len(hooks["policy_bl"]), 17)
        self.assertEqual(hooks["save_load"]["size"], 8)
        self.assertEqual(hooks["ability_load"]["size"], 4)
        for group in (hooks["trainer_v5"], hooks["policy_bl"]):
            for row in group:
                offset = row["address"] - final.GBA_ROM_BASE
                self.assertEqual(
                    self.rom[offset:offset + row["size"]],
                    bytes.fromhex(row["replacement_hex"]),
                )
        ability = hooks["ability_load"]
        offset = ability["address"] - final.GBA_ROM_BASE
        self.assertEqual(
            self.rom[offset:offset + ability["size"]],
            bytes.fromhex(ability["replacement_hex"]),
        )
        symbols = self.metadata["runtime"]["entrypoints"]
        for name in (
            "TrainerChangeKitFinalRuntime_PolicyBeginAdapter",
            "TrainerChangeKitFinalRuntime_PolicyEndAdapter",
            "TrainerChangeKitFinalRuntime_SaveLoadAdapter",
            "TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter",
        ):
            self.assertIn(name, symbols)

    def test_kanto_archive_maps_and_dialogue_are_fully_serialized(self) -> None:
        plan = json.loads(self.outputs[final.OUTPUT_PLAN.as_posix()])
        self.assertEqual(len(plan["bindings"]), 272)
        self.assertEqual(plan["summary"]["new_object_records"], 269)
        self.assertLessEqual(plan["summary"]["max_objects_per_map"], 10)
        self.assertEqual(len(plan["relocations"]), 3)
        self.assertEqual(len(plan["texts"]), 42)  # 35 authored + 7 safe fallback lines
        self.assertEqual(
            sum(row["text_key"].startswith("text::kanto::")
                and row["text_key"].count("::") == 2
                and len(row["text_key"].rsplit("::", 1)[1]) == 16
                for row in plan["texts"]),
            35,
        )
        self.assertTrue(all(bytes.fromhex(row["data_hex"])[-1] == 0xFF
                            for row in plan["texts"]))
        with (ROOT / "content/trainer_changekit_final/trainer_dialogue.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            dialogue = list(csv.DictReader(stream))
        self.assertEqual(len(dialogue), 4662)
        # Task06's 188 new battles occupy 69 maps; the 71 Archive consumers
        # add ten more safe map event tables.
        self.assertEqual(self.metadata["physical_events"]["map_patch_count"], 79)

    def test_release_patches_round_trip_exactly(self) -> None:
        stage = (ROOT / final.INPUT_ROM).read_bytes()
        base = (ROOT / final.BASE_ROM).read_bytes()
        incremental = self.outputs[final.PATCH_INCREMENTAL.as_posix()]
        cumulative = self.outputs[final.PATCH_CUMULATIVE.as_posix()]
        self.assertEqual(final.apply_bps(stage, incremental), self.rom)
        self.assertEqual(final.apply_bps(base, cumulative), self.rom)
        self.assertTrue(all(self.metadata["invariants"].values()))


if __name__ == "__main__":
    unittest.main()
