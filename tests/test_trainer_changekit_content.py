#!/usr/bin/env python3
"""Trainer ChangeKit最終正規化のfocused acceptance tests。"""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from scripts.build_trainer_changekit_content import (
    EXPECTED_ARCHIVE_CONSUMERS,
    EXPECTED_ENCOUNTERS,
    EXPECTED_MEMBERS,
    EXPECTED_TABLE_COUNT,
    TASK_DIRS,
    build,
    discover_input_root,
)


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content/trainer_changekit_final"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TrainerChangeKitContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_root = discover_input_root(ROOT)
        cls.coverage = json.loads((CONTENT / "coverage.json").read_text(encoding="utf-8"))
        cls.encounters = read_csv(CONTENT / "trainer_encounters.csv")
        cls.parties = read_csv(CONTENT / "trainer_parties.csv")
        cls.members = read_csv(CONTENT / "trainer_party_members.csv")
        cls.bindings = read_csv(CONTENT / "trainer_physical_bindings.csv")
        cls.archive = read_csv(CONTENT / "archive_rematch_consumers.csv")
        cls.ledger = read_csv(CONTENT / "normalization_ledger.csv")
        cls.allocations = read_csv(CONTENT / "trainer_id_allocations.csv")
        cls.runtime = read_csv(CONTENT / "trainer_runtime_consumers.csv")

    def test_exact_union_and_coverage_contract(self) -> None:
        self.assertEqual(len(self.encounters), EXPECTED_ENCOUNTERS)
        self.assertEqual(len(self.parties), EXPECTED_ENCOUNTERS)
        self.assertEqual(len(self.members), EXPECTED_MEMBERS)
        self.assertEqual(len(self.bindings), EXPECTED_ENCOUNTERS)
        self.assertEqual(len(self.ledger), EXPECTED_ENCOUNTERS)
        self.assertEqual(len(self.runtime), EXPECTED_ENCOUNTERS)
        self.assertEqual(self.coverage["validation"], "PASS")
        self.assertEqual(self.coverage["trainer_table_count"], EXPECTED_TABLE_COUNT)
        self.assertEqual(self.coverage["battle_format_counts"], {"DOUBLE": 74, "SINGLE": 1228})
        self.assertEqual(
            self.coverage["gimmick_type_counts"],
            {"DYNAMAX": 4, "MEGA": 86, "NONE": 1034, "TERASTAL": 67, "Z_MOVE": 111},
        )

    def test_all_parties_are_unique_and_slots_are_contiguous(self) -> None:
        self.assertEqual(len({row["party_key"] for row in self.parties}), EXPECTED_ENCOUNTERS)
        self.assertEqual(len({row["encounter_key"] for row in self.parties}), EXPECTED_ENCOUNTERS)
        by_party: dict[str, list[int]] = defaultdict(list)
        for member in self.members:
            by_party[member["party_key"]].append(int(member["slot"]))
        for party in self.parties:
            size = int(party["party_size"])
            self.assertEqual(sorted(by_party[party["party_key"]]), list(range(1, size + 1)))

    def test_unknown_and_shared_commands_are_non_destructive_archive_consumers(self) -> None:
        self.assertEqual(len(self.archive), EXPECTED_ARCHIVE_CONSUMERS)
        self.assertEqual(
            Counter(row["normalization_reason"] for row in self.archive),
            Counter({"FLAG_REFERENCE_FALSE_POSITIVE": 51, "SHARED_COMMAND_EXTRA_CALLER": 20}),
        )
        self.assertEqual(
            [int(row["consumer_index"]) for row in self.archive],
            list(range(1, EXPECTED_ARCHIVE_CONSUMERS + 1)),
        )
        self.assertEqual(len({row["defeat_state_key"] for row in self.archive}), 71)
        runtime_by_key = {row["encounter_key"]: row for row in self.runtime}
        for row in self.archive:
            runtime = runtime_by_key[row["encounter_key"]]
            self.assertEqual(runtime["binding_mode"], "ARCHIVE")
            self.assertEqual(runtime["command_address"], row["consumer_key"])
            self.assertEqual(runtime["physical_flag"], row["defeat_state_key"])

    def test_ref1012_alias_is_independent_double_archive_battle(self) -> None:
        row = next(row for row in self.archive if row["encounter_key"] == "ENC_TOHOKU_REF_1012")
        self.assertEqual(row["battle_format"], "DOUBLE")
        self.assertEqual(row["battle_type"], "TRAINER_BATTLE_DOUBLE")
        self.assertEqual(row["original_owner"], "ENC_TOHOKU_REF_1013")
        runtime = next(
            candidate
            for candidate in self.runtime
            if candidate["encounter_key"] == "ENC_TOHOKU_REF_1012"
        )
        self.assertEqual(runtime["trainerbattle_kind"], "4")

    def test_kind9_unknown_rows_are_exact_early_rival_single(self) -> None:
        expected = {
            "ENC_TOHOKU_REF_0440": "0x0817C9C7",
            "ENC_TOHOKU_REF_0441": "0x0817CABA",
            "ENC_TOHOKU_REF_0442": "0x0817CA3F",
        }
        by_key = {row["encounter_key"]: row for row in self.runtime}
        for key, address in expected.items():
            row = by_key[key]
            self.assertEqual(row["binding_mode"], "CANONICAL")
            self.assertEqual(row["command_address"], address)
            self.assertEqual(row["trainerbattle_kind"], "9")
            self.assertEqual(row["battle_format"], "SINGLE")

    def test_runtime_trainer_ids_are_unique_and_duplicate_band_is_stable(self) -> None:
        runtime_ids = [int(row["runtime_trainer_id"]) for row in self.allocations]
        self.assertEqual(len(runtime_ids), len(set(runtime_ids)))
        self.assertEqual(max(runtime_ids), 4283)
        reassigned = [
            row for row in self.allocations
            if row["allocation_reason"] == "REALLOCATE_DUPLICATE_TO_UNUSED_BAND"
        ]
        self.assertEqual([int(row["runtime_trainer_id"]) for row in reassigned], list(range(1367, 1383)))
        by_key = {row["encounter_key"]: row for row in self.allocations}
        # 606のflag参照ではなく、最初の実戦闘ownerが既存IDを保持する。
        self.assertEqual(by_key["ENC_TOHOKU_REF_0854"]["runtime_trainer_id"], "606")
        self.assertEqual(by_key["ENC_TOHOKU_REF_0853"]["runtime_trainer_id"], "1367")
        self.assertEqual(by_key["ENC_TOHOKU_REF_0001"]["runtime_trainer_id"], "1383")
        self.assertEqual(
            by_key["ENC_TOHOKU_REF_0001"]["allocation_reason"],
            "REALLOCATE_RESERVED_CFRU_TRAINER_ID",
        )
        self.assertFalse({917, 918, 919, 920, 921, 1024} & set(runtime_ids))
        for row in self.allocations:
            original = int(row["original_trainer_id"])
            if 4096 <= original <= 4283:
                self.assertEqual(row["runtime_trainer_id"], row["original_trainer_id"])

    def test_runtime_consumer_contract_is_complete(self) -> None:
        required = {
            "encounter_key",
            "runtime_trainer_id",
            "source_trainer_id",
            "binding_mode",
            "command_address",
            "trainerbattle_kind",
            "battle_format",
            "party_key",
            "ai_profile_key",
            "gimmick_type",
            "source_template_id",
            "physical_flag",
        }
        self.assertTrue(required.issubset(self.runtime[0]))
        self.assertEqual(Counter(row["binding_mode"] for row in self.runtime)["ARCHIVE"], 71)
        self.assertEqual(Counter(row["binding_mode"] for row in self.runtime)["KANTO_NEW"], 201)
        self.assertTrue(all(row["source_template_id"] for row in self.runtime))
        self.assertTrue(all(row["physical_flag"] for row in self.runtime))

    def test_authored_party_dialogue_reward_and_gimmick_rows_are_preserved(self) -> None:
        for filename in (
            "trainer_parties.csv",
            "trainer_party_members.csv",
            "trainer_dialogue.csv",
            "trainer_rewards.csv",
            "trainer_gimmicks.csv",
        ):
            source: list[dict[str, str]] = []
            for task in TASK_DIRS:
                path = self.input_root / task / "data" / filename
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    source.extend(csv.DictReader(handle))
            generated = read_csv(CONTENT / filename)
            canonical = lambda row: tuple(sorted(row.items()))
            self.assertEqual(sorted(map(canonical, generated)), sorted(map(canonical, source)))

    def test_source_manifest_hashes_match_immutable_inputs(self) -> None:
        manifest = json.loads((CONTENT / "source_manifest.json").read_text(encoding="utf-8"))
        for row in manifest["inputs"]:
            relative = Path(row["path"])
            candidate = self.input_root / relative
            path = candidate if candidate.is_file() else ROOT / relative
            self.assertTrue(path.is_file(), row["path"])
            self.assertEqual(digest(path), row["sha256"])

    def test_generation_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "trainer_changekit_final"
            result = build(ROOT, self.input_root, output)
            self.assertEqual(result, self.coverage)
            expected_files = sorted(path.name for path in CONTENT.iterdir() if path.is_file())
            self.assertEqual(sorted(path.name for path in output.iterdir() if path.is_file()), expected_files)
            for name in expected_files:
                self.assertEqual(digest(output / name), digest(CONTENT / name), name)


if __name__ == "__main__":
    unittest.main()
