#!/usr/bin/env python3
"""工程5の新Ability 6件host runtime checkpoint focused test。"""

from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p05_ability_runtime import (  # noqa: E402
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT,
    EXPECTED_ABILITIES,
    P05AbilityRuntimeError,
    REQUIRED_CATEGORIES,
    STATUS,
    audit_p05_ability_runtime_checkpoint,
    build_p05_ability_runtime_checkpoint,
    canonical_json_bytes,
    validate_checkpoint_document,
    write_p05_ability_runtime_checkpoint,
)


class ModernizationP05AbilityRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = build_p05_ability_runtime_checkpoint(ROOT)

    def _case(self, case_key: str) -> dict[str, object]:
        rows = [
            row for row in self.document["fixture"]["cases"]
            if row["case_key"] == case_key
        ]
        self.assertEqual(1, len(rows), case_key)
        return rows[0]

    def test_stable_key_allocation_uses_u16_and_not_upstream_order(self) -> None:
        rows = self.document["ability_allocation"]["rows"]
        self.assertEqual(sorted(EXPECTED_ABILITIES), [row["ability_key"] for row in rows])
        self.assertEqual(list(range(312, 318)), [row["canonical_id"] for row in rows])
        self.assertTrue(all(row["canonical_id"] > 255 for row in rows))
        self.assertEqual(314, next(
            row["canonical_id"] for row in rows
            if row["ability_key"] == "ABILITY_KEY_FIREMANE"
        ))
        self.assertEqual(316, next(
            row["source_numeric_id_not_canonical"] for row in rows
            if row["ability_key"] == "ABILITY_KEY_FIREMANE"
        ))
        self.assertTrue(self.document["ability_allocation"]["source_numeric_ids_are_noncanonical"])

    def test_every_ability_executes_all_required_behavior_categories(self) -> None:
        cases = self.document["fixture"]["cases"]
        coverage = {
            key: {row["category"] for row in cases if row["ability_key"] == key}
            for key in EXPECTED_ABILITIES
        }
        self.assertEqual({key: REQUIRED_CATEGORIES for key in EXPECTED_ABILITIES}, coverage)
        self.assertEqual(2, self.document["fixture"]["independent_process_runs"])
        self.assertEqual(0, self.document["fixture"]["summary"]["failure_count"])
        self.assertGreaterEqual(self.document["fixture"]["summary"]["case_count"], 44)

    def test_damage_type_weather_and_protection_semantics_are_executed(self) -> None:
        self.assertEqual(25, self._case(
            "contact_pierces_single_protect_at_quarter_damage"
        )["observed"])
        self.assertEqual(16120, self._case(
            "normal_becomes_dragon_and_gains_twenty_percent"
        )["observed"])
        self.assertEqual(150, self._case(
            "physical_fire_move_gains_fifty_percent"
        )["observed"])
        self.assertEqual(50, self._case("personal_sun_halves_water")["observed"])
        self.assertEqual(200, self._case(
            "weather_ball_and_healing_use_personal_sun"
        )["observed"])
        self.assertEqual(23, self._case(
            "project_fairy_id_23_passes_through"
        )["observed"])
        self.assertEqual(24, self._case(
            "project_stellar_id_24_passes_through"
        )["observed"])

    def test_extended_type_ids_match_the_canonical_manifest(self) -> None:
        with (ROOT / "manifests/type_ids.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            ids = {row["type_key"]: int(row["id"]) for row in csv.DictReader(stream)}
        self.assertEqual(23, ids["TYPE_KEY_FAIRY"])
        self.assertEqual(24, ids["TYPE_KEY_STELLAR"])
        self.assertEqual(23, self._case("project_fairy_id_23_passes_through")["observed"])
        self.assertEqual(24, self._case("project_stellar_id_24_passes_through")["observed"])

    def test_eelevate_and_spicy_spray_event_semantics_are_executed(self) -> None:
        self.assertEqual(1, self._case("damaging_ground_move_is_immune")["observed"])
        self.assertEqual(202, self._case(
            "two_knockouts_raise_highest_stat_twice_with_tie_order"
        )["observed"])
        self.assertEqual(1, self._case(
            "damaging_noncontact_attack_burns_present_attacker"
        )["observed"])
        self.assertEqual(0, self._case(
            "substitute_only_damage_does_not_trigger"
        )["observed"])
        self.assertEqual(1, self._case(
            "two_holders_queue_only_one_idempotent_burn"
        )["observed"])

    def test_ai_and_save_paths_execute_without_u8_truncation(self) -> None:
        ai_rows = [
            row for row in self.document["fixture"]["cases"]
            if row["category"] == "ai"
        ]
        self.assertGreaterEqual(len(ai_rows), 7)
        self.assertTrue(all(row["status"] == "PASS" for row in ai_rows))
        save_rows = [
            row for row in self.document["fixture"]["cases"]
            if row["category"] == "save"
        ]
        self.assertEqual(list(range(312, 318)), [row["observed"] for row in save_rows])

    def test_pinned_source_and_capacity_reservation_are_bound(self) -> None:
        source = self.document["inputs"]["technical_reference"]
        self.assertEqual(
            "cafe0221cefb2a991cc0ece429174ade877d037d", source["commit"]
        )
        self.assertTrue(source["clean_checkout"])
        self.assertGreaterEqual(len(source["files"]), 13)
        self.assertTrue(all(len(row["sha256"]) == 64 for row in source["files"]))
        capacity = self.document["inputs"]["capacity_checkpoint"]
        self.assertEqual([312, 317], capacity["ability_range"])

    def test_rom_link_boundary_and_hook_contract_remain_explicit(self) -> None:
        self.assertEqual(STATUS, self.document["status"])
        self.assertTrue(self.document["host_runtime_verified"])
        self.assertFalse(self.document["rom_linked"])
        self.assertFalse(self.document["rom_mutated"])
        self.assertFalse(self.document["save_mutated"])
        self.assertFalse(self.document["shared_manifests_mutated"])
        self.assertEqual(
            "UNRESOLVED_STAGE_ROM_DISASSEMBLY_REQUIRED",
            self.document["implementation"]["hook_address_status"],
        )
        self.assertFalse(self.document["completion_boundary"]["release_ready"])
        self.assertIn(
            "run_exact_rom_mgba_battle_ai_ui_and_save_acceptance",
            self.document["completion_boundary"]["remaining"],
        )
        config_text = (ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8")
        self.assertNotIn("ALLYSWITCH", config_text)
        self.assertNotIn("SIDE_CHANGE", config_text)

    def test_validator_rejects_false_rom_completion(self) -> None:
        broken = copy.deepcopy(self.document)
        broken["rom_linked"] = True
        with self.assertRaisesRegex(P05AbilityRuntimeError, "rom_linked"):
            validate_checkpoint_document(broken)

    def test_tracked_checkpoint_is_exact_and_cli_check_is_side_effect_free(self) -> None:
        output = ROOT / DEFAULT_OUTPUT
        actual = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(canonical_json_bytes(self.document), canonical_json_bytes(actual))
        before = (output.stat().st_size, output.stat().st_mtime_ns)
        report = audit_p05_ability_runtime_checkpoint(ROOT)
        self.assertEqual("PASS", report["status"])
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_modernization_p05_ability_runtime.py"),
                "--check",
                "--compact",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual("PASS", json.loads(completed.stdout)["status"])
        self.assertEqual(before, (output.stat().st_size, output.stat().st_mtime_ns))

    def test_writer_rejects_non_task_output_before_overwrite(self) -> None:
        readme = ROOT / "README.md"
        before = (readme.stat().st_size, readme.stat().st_mtime_ns)
        with self.assertRaisesRegex(P05AbilityRuntimeError, "task固有path"):
            write_p05_ability_runtime_checkpoint(ROOT, output_path="README.md")
        self.assertEqual(before, (readme.stat().st_size, readme.stat().st_mtime_ns))


if __name__ == "__main__":
    unittest.main()
