from __future__ import annotations

import csv
import os
import struct
import unittest
from pathlib import Path

from tools.trainer_final.kanto_events import (
    KantoPlanError,
    build_event_header,
    build_kanto_event_plan,
    build_object_record,
    build_trainer_scripts,
    encode_dialogue_text,
    normalize_dialogue_text,
)


ROOT = Path(__file__).resolve().parents[1]


def _task06_dir() -> Path | None:
    candidates = []
    if os.environ.get("VEGA_TRAINER_CHANGEKIT_TASK06_DIR"):
        candidates.append(Path(os.environ["VEGA_TRAINER_CHANGEKIT_TASK06_DIR"]))
    candidates += [
        ROOT / "userfile/imports/VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
        ROOT.parents[1] / "integration_inputs/VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
    ]
    return next((path for path in candidates
                 if (path / "data/trainer_encounters.csv").is_file()), None)


class KantoEventPrimitiveTests(unittest.TestCase):
    def test_object_and_event_images_are_relocatable(self) -> None:
        template = bytearray(24)
        template[1] = 7
        template[3] = 8
        struct.pack_into("<HH", template, 12, 1, 4)
        record = build_object_record(bytes(template), local_id=9, x=12, y=13,
                                     elevation=3, sight_range=2)
        raw = bytes.fromhex(record["data_hex"])
        self.assertEqual(len(raw), 24)
        self.assertEqual((raw[0], raw[1], raw[3]), (9, 7, 8))
        self.assertEqual(struct.unpack_from("<HH", raw, 4), (12, 13))
        self.assertEqual(struct.unpack_from("<HH", raw, 12), (1, 2))
        self.assertEqual(record["fixups"], [{"offset": 16, "target": "SCRIPT_KEY"}])

        event = build_event_header(12, {"warps": 2, "coords": 1, "bg": 3})
        self.assertEqual(bytes.fromhex(event["data_hex"])[:4], bytes((12, 2, 1, 3)))
        self.assertEqual({fixup["target"] for fixup in event["fixups"]},
                         {"OBJECT_TABLE", "PRESERVED_WARPS", "PRESERVED_COORDS", "PRESERVED_BG"})

    def test_trainer_script_abi_has_relative_fixups(self) -> None:
        texts = {key: f"text::{key}" for key in
                 ("intro", "defeat", "post", "locked", "not_enough")}
        scripts = build_trainer_scripts("SCRIPT_TEST", 4096, 2, "DOUBLE",
                                        "KANTO_CERT_COUNT>=3", 0x1500, texts)
        battle = next(row for row in scripts if row["role"] == "trainerbattle")
        raw = bytes.fromhex(battle["data_hex"])
        self.assertEqual(raw[:2], b"\x5c\x04")
        self.assertEqual(struct.unpack_from("<HH", raw, 2), (4096, 0))
        self.assertEqual(battle["object_local_id"], 2)
        self.assertEqual(len(battle["fixups"]), 4)
        self.assertTrue(all(isinstance(item["offset"], int) and item["offset"] < len(raw)
                            for item in battle["fixups"]))

    def test_unknown_prose_fails_closed(self) -> None:
        with self.assertRaises(KantoPlanError):
            normalize_dialogue_text("正本にない本文")


@unittest.skipUnless(_task06_dir() is not None, "Task06 private ChangeKit is not available")
class KantoEventFullPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        task = _task06_dir()
        assert task is not None
        cls.task = task
        cls.stage = (ROOT / "build/stages/34_trainer_v5_tohoku_batch03.gba").read_bytes()
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        cls.archive = [
            {"encounter_key": f"ARCHIVE_{index:03d}", "trainer_id": index + 1,
             "battle_format": "DOUBLE" if index % 7 == 0 else "SINGLE"}
            for index in range(71)
        ]
        cls.archive_dialogue = []
        for row in cls.archive:
            states = ["INTRO", "DEFEAT", "POST_BATTLE", "LOCKED"]
            if row["battle_format"] == "DOUBLE":
                states.append("NOT_ENOUGH_POKEMON")
            for state in states:
                cls.archive_dialogue.append({
                    "encounter_key": row["encounter_key"], "state_key": state,
                    "text_key": f"text::{row['encounter_key']}::{state}",
                    "normalized_text": "きろくの しょうぶだ。",
                })
        cls.plan = build_kanto_event_plan(
            cls.stage, cls.clean, ROOT, task, archive_rows=cls.archive,
            archive_dialogue_rows=cls.archive_dialogue,
        )

    def test_all_814_dialogue_rows_normalize_encode_and_fit(self) -> None:
        with (self.task / "data/trainer_dialogue.csv").open(
                encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 814)
        unique = {row["text"] for row in rows}
        self.assertEqual(len(unique), 35)
        for row in rows:
            normalized = normalize_dialogue_text(row["text"])
            encoded = encode_dialogue_text(ROOT, normalized)
            self.assertEqual(encoded[-1], 0xFF)
            self.assertTrue(all(len(line) <= 18 for line in normalized.splitlines()))

    def test_kanto_and_archive_cardinality(self) -> None:
        summary = self.plan["summary"]
        self.assertEqual(summary["task06_encounters"], 201)
        self.assertEqual(summary["existing_bindings"], 13)
        self.assertEqual(summary["normal_bindings"], 185)
        self.assertEqual(summary["relocated_bindings"], 3)
        self.assertEqual(summary["archive_bindings"], 71)
        self.assertEqual(summary["new_object_records"], 198 + 71)
        self.assertLessEqual(summary["max_objects_per_map"], 15)
        self.assertLessEqual(summary["max_archive_per_map"], 5)
        self.assertEqual(len({row["encounter_key"] for row in self.plan["bindings"]}), 272)
        kanto = [row for row in self.plan["bindings"] if row["owner_kind"] != "ARCHIVE"]
        self.assertEqual(sum(row["battle_format"] == "DOUBLE" for row in kanto), 10)
        self.assertTrue(all(len(row["local_ids"]) == 2 for row in kanto
                            if row["battle_format"] == "DOUBLE"))

    def test_three_ownership_conflicts_relocate_deterministically(self) -> None:
        relocations = {row["encounter_key"]: row for row in self.plan["relocations"]}
        self.assertEqual(set(relocations), {
            "ENC_KANTO_ROUTE_013", "ENC_KANTO_ROUTE_075", "ENC_KANTO_ROUTE_161",
        })
        expected = {
            "ENC_KANTO_ROUTE_013": ("KANTO_DUNGEON_POKEMON_MANSION_B1_F", [34, 13], [34, 12]),
            "ENC_KANTO_ROUTE_075": ("KANTO_DUNGEON_VICTORY_ROAD_3_F", [40, 7], [40, 6]),
            "ENC_KANTO_ROUTE_161": ("KANTO_OUTDOOR_ROUTE25", [11, 4], [11, 3]),
        }
        for key, (map_key, origin, target) in expected.items():
            self.assertEqual((relocations[key]["map_key"], relocations[key]["from"],
                              relocations[key]["to"]), (map_key, origin, target))

    def test_every_new_object_is_safe_unique_and_source_rooted(self) -> None:
        for map_row in self.plan["maps"]:
            all_ids = [row["local_id"] for row in map_row["preserved_objects"]]
            all_ids += [row["local_id"] for row in map_row["new_objects"]]
            self.assertEqual(len(all_ids), len(set(all_ids)), map_row["map_key"])
            self.assertLessEqual(len(all_ids), 15)
            for obj in map_row["new_objects"]:
                self.assertTrue(obj["audit"]["walkable"])
                self.assertTrue(obj["audit"]["avoidable_path"])
                if obj["owner_kind"] == "ARCHIVE":
                    self.assertTrue(obj["audit"]["reachable_from_entry"])
                self.assertGreaterEqual(obj["source_template_trainer_id"], 0)
                self.assertLessEqual(obj["source_template_trainer_id"], 742)
                self.assertEqual(obj["audit"]["source_template"]["candidate_trainer_ids"],
                                 [obj["source_template_trainer_id"]])

    def test_existing_bindings_expose_exact_command_and_locked_proxy(self) -> None:
        rows = [row for row in self.plan["bindings"] if row["owner_kind"] == "EXISTING"]
        self.assertEqual(len(rows), 13)
        for row in rows:
            self.assertGreaterEqual(row["existing_command_address"], 0x08000000)
            self.assertIn(row["existing_command_kind"], range(10))
            self.assertTrue(row["locked_text_key"].startswith("text::kanto::"))
            self.assertTrue(row["proxy_plan"]["preserve_progression_owner"])
            self.assertTrue(row["proxy_plan"]["preserve_reward_owner"])
            self.assertEqual(set(row["proxy_plan"]["task06_text_keys"]),
                             {"intro", "defeat", "post", "locked", "not_enough"})
            self.assertEqual(row["proxy_plan"]["delegate_command_address"],
                             row["existing_command_address"])

    def test_archive_dialogue_states_are_physical_script_consumers(self) -> None:
        archive_scripts = [row for row in self.plan["scripts"]
                           if row["script_key"].startswith("SCRIPT_TRAINER_ARCHIVE_")]
        referenced = {fixup["target"] for row in archive_scripts
                      for fixup in row["fixups"]}
        expected = {row["text_key"] for row in self.archive_dialogue}
        self.assertTrue(expected <= referenced)
        bindings = [row for row in self.plan["bindings"] if row["owner_kind"] == "ARCHIVE"]
        self.assertEqual(len({row["defeat_flag"] for row in bindings}), 71)
        self.assertEqual(len({(row["group_id"], row["map_id"], row["local_ids"][0])
                              for row in bindings}), 71)
        self.assertTrue(all(row["unlock_expression"] == "POSTGAME" for row in bindings))


if __name__ == "__main__":
    unittest.main()
