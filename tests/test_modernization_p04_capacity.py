#!/usr/bin/env python3
"""工程4/5のID容量予約・consumer監査checkpointのfocused test。"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_capacity import (
    CHECKPOINT_STATUS,
    DEFAULT_OUTPUT,
    P04CapacityError,
    allocate_append_ids,
    audit_p04_capacity_checkpoint,
    build_p04_capacity_checkpoint,
    canonical_json_bytes,
    materialize_reserved_id_rows,
    validate_checkpoint_document,
    write_p04_capacity_checkpoint,
)


class ModernizationP04CapacityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = build_p04_capacity_checkpoint(ROOT)

    def test_reserved_ranges_are_exact_contiguous_and_stable(self) -> None:
        expected = {
            "species_form": (1621, 1672, 52),
            "item": (999, 1043, 45),
            "ability": (312, 317, 6),
            "move": (None, None, 0),
        }
        self.assertEqual(CHECKPOINT_STATUS, self.document["status"])
        self.assertFalse(self.document["runtime_ready"])
        for domain, (start, end, count) in expected.items():
            group = self.document["id_reservations"][domain]
            self.assertEqual(count, group["append_count"])
            self.assertEqual((start, end), (group["reserved_start_id"], group["reserved_end_id"]))
            expected_ids = list(range(start, end + 1)) if start is not None else []
            self.assertEqual(expected_ids, [row["id"] for row in group["rows"]])
            key_field = group["key_field"]
            self.assertEqual(
                sorted(row[key_field] for row in group["rows"]),
                [row[key_field] for row in group["rows"]],
            )
            self.assertTrue(all(row["materialization_ready"] is False for row in group["rows"]))

    def test_temporary_ability_and_asset_gaps_stay_separate(self) -> None:
        temporary = self.document["temporary_ability_replacement_contract"]
        self.assertEqual(16, len(temporary["rows"]))
        self.assertEqual(14, temporary["adopted_binding_count"])
        self.assertEqual(2, temporary["classification_hold_binding_count"])
        replacements = [row["ability_replacement_key"] for row in temporary["rows"]]
        self.assertEqual(len(replacements), len(set(replacements)))
        assets = self.document["asset_readiness_separate_gate"]
        self.assertTrue(assets["id_reservation_is_independent_from_asset_readiness"])
        self.assertEqual((0, 3), (
            assets["winds_waves"]["source_assets_ready"],
            assets["winds_waves"]["reserved_ids"],
        ))
        self.assertEqual((49, 49), (
            assets["mega_species"]["gba_palette_ready"],
            assets["mega_species"]["reserved_ids"],
        ))
        self.assertFalse(assets["winds_waves"]["fake_or_placeholder_generated"])

    def test_fixed_geometry_evolution_slots_and_allocator_are_measured(self) -> None:
        tables = self.document["table_capacity"]
        self.assertEqual(34, tables["known_fixed_table_count"])
        self.assertEqual((616521, 637389, 20868), (
            tables["known_fixed_old_bytes"],
            tables["known_fixed_new_bytes"],
            tables["known_fixed_delta_bytes"],
        ))
        self.assertTrue(all(row["stage65_old_slice_measured"] for row in tables["fixed_tables"]))
        mold = next(
            row for row in tables["fixed_tables"]
            if row["table_key"] == "ability_mold_breaker_ignored"
        )
        self.assertEqual((0x0915F77C, 312, 318, 6), (
            mold["current_address"], mold["old_count"], mold["new_count"], mold["delta_bytes"],
        ))
        self.assertEqual(
            "4296ce4fb1a4107a4c137de646a94740169013be4c2c2b3f742b73e2f2ec02de",
            mold["stage65_old_slice_sha256"],
        )
        self.assertEqual(
            4,
            self.document["consumer_audit"]["stage65_exact_literal_candidates"]
            ["ability_mold_breaker_ignored"]["occurrence_count"],
        )
        evolution = tables["mega_evolution_slot_capacity"]
        self.assertEqual((48, 49, 15), (
            evolution["source_base_count"],
            evolution["required_mega_row_count"],
            evolution["minimum_current_free_slots"],
        ))
        raichu = next(row for row in evolution["rows"] if row["source_species_key"] == "SPECIES_KEY_RAICHU")
        self.assertEqual((2, 16), (raichu["required_mega_rows"], raichu["current_free_slots"]))
        spans = {
            row["region"]: row for row in self.document["allocator_audit"]["candidate_span_assessments"]
        }
        self.assertTrue(spans["integration_modules"]["fits_known_fixed_bundle"])
        self.assertFalse(spans["future_tail"]["fits_known_fixed_bundle"])

    def test_generated_and_collection_overlay_consumers_are_not_hidden(self) -> None:
        tables = self.document["table_capacity"]
        generated = tables["generated_relink_item_index_tables"]
        self.assertEqual((1249, 1306, 57), (
            generated["logical_old_bytes"], generated["logical_new_bytes"], generated["logical_delta_bytes"],
        ))
        self.assertEqual((3497, 3656, 159), (
            generated["stage65_physical_old_bytes"],
            generated["stage65_physical_new_bytes_if_all_instances_relinked"],
            generated["stage65_physical_delta_bytes_if_all_instances_relinked"],
        ))
        instances = {row["table_key"]: row["stage65_instance_count"] for row in generated["tables"]}
        self.assertEqual({
            "codex_runtime_held_item_safe_bitmap": 1,
            "codex_reward_ball_item_bitmap": 3,
            "codex_reward_ball_type_by_item": 3,
        }, instances)
        owners = {
            row["table_key"]: {
                site["allocation_name"] for site in row["stage65_instance_allocations"]
            }
            for row in generated["tables"]
        }
        self.assertEqual(
            {"codex_battle_runtime_stage44_payload"},
            owners["codex_runtime_held_item_safe_bitmap"],
        )
        self.assertEqual({
            "codex_battle_rewards_stage45_payload",
            "windows_battle_catalog_stage46_payload",
            "windows_box14_vault_stage47_payload",
        }, owners["codex_reward_ball_type_by_item"])
        collection = tables["collection_supply_derived_overlay"]
        self.assertEqual(540, collection["required_item_fixed_delta_bytes_excluding_names"])
        self.assertEqual(588, collection["conditional_mega_fixed_delta_bytes_excluding_names"])
        self.assertEqual(1128, collection["maximum_fixed_delta_bytes_excluding_names"])
        self.assertTrue(collection["not_in_known_fixed_relocation_bundle"])
        self.assertTrue(collection["item_obtained_accessor"]["sidecar_aware_accessor_patch_required"])
        variable = {
            row["component_key"]: row
            for row in tables["variable_or_policy_blocked_components"]
        }
        stone = variable["mega_stone_icon_palette_payload"]
        self.assertEqual((45, 12960, 1440, 14400), (
            stone["source_record_count"], stone["source_icon_bytes"],
            stone["source_palette_bytes"], stone["minimum_raw_payload_bytes"],
        ))
        self.assertIsNone(stone["linked_size_bytes"])

    def test_pinned_consumers_and_move_effect_semantics_are_explicit(self) -> None:
        consumer = self.document["consumer_audit"]
        counts = consumer["pinned_cfru_count_macro_consumers"]
        self.assertEqual(37, counts["match_count"])
        self.assertEqual({
            "ABILITIES_COUNT": 8,
            "ITEMS_COUNT": 9,
            "MOVES_COUNT": 9,
            "NUM_SPECIES": 11,
        }, counts["counts_by_macro"])
        dispatch = consumer["pinned_move_effect_dispatch"]
        self.assertEqual(256, dispatch["entry_count"])
        self.assertEqual([251, 252, 255], dispatch["blank_candidate_ids"])
        self.assertEqual(254, dispatch["excluded_blank_id"])
        self.assertIsNone(dispatch["ally_switch_effect_id"])
        self.assertFalse(dispatch["in_place_table_growth_possible"])
        self.assertEqual("NO_NEW_MOVE_EFFECT_REQUESTED", dispatch["status"])
        self.assertFalse(dispatch["semantic_reuse_requires_review"])
        self.assertEqual("NONE_PRESERVE_CURRENT_DISPATCH", dispatch["required_action"])
        self.assertEqual({"251": 0, "252": 0, "255": 0}, dispatch["blank_candidate_active_move_use_count"])
        event = consumer["codex_public_event_abi"]
        self.assertEqual((88, 89, 11, 12, 44, 48), (
            event["current_bits_per_event"], event["minimum_required_bits_per_event"],
            event["current_bytes_per_event"], event["minimum_required_bytes_per_event"],
            event["current_event_ring_bytes"], event["minimum_required_event_ring_bytes"],
        ))
        self.assertEqual(
            "tools/vega_codex_battle.py",
            event["inputs"]["windows_reader"]["path"],
        )
        self.assertEqual(
            64,
            len(event["inputs"]["windows_reader"]["sha256"]),
        )

    def test_numeric_width_and_save_abi_blockers_are_exact(self) -> None:
        blockers = {
            row["field"] for row in self.document["numeric_width_audit"]
            if row.get("known_limit_exceeded") is True
        }
        self.assertEqual({
            "BattlePokemon.oldAbility",
            "BattleStruct.abilityPreventingSwitchout",
            "CodexBattlePublicEventV2.last_item_id",
            "MirageProduction_Probe.virtual_items_packed",
        }, blockers)
        item_bitmap = self.document["save_abi"]["item_obtained_bitmap"]
        self.assertEqual((125, 131, 6), (
            item_bitmap["current_bytes"], item_bitmap["new_bytes"], item_bitmap["delta_bytes"],
        ))
        sidecar = item_bitmap["non_binding_sidecar_candidate"]
        self.assertEqual((0x2697, 0x269D, 6), (
            sidecar["candidate_start"], sidecar["candidate_end_exclusive"], sidecar["candidate_bytes"],
        ))
        self.assertFalse(sidecar["binding_allocation"])

    def test_pure_allocation_and_materialization_fail_closed(self) -> None:
        existing = [{"id": "0", "unit_key": "UNIT_KEY_ZERO"}]
        requested = [{"unit_key": "UNIT_KEY_ONE", "materialization_ready": False}]
        original_existing = copy.deepcopy(existing)
        reserved = allocate_append_ids(
            existing, requested, key_field="unit_key", expected_current_count=1
        )
        self.assertEqual(1, reserved[0]["id"])
        projected = materialize_reserved_id_rows(existing, reserved, key_field="unit_key")
        self.assertEqual(["0", "1"], [row["id"] for row in projected])
        self.assertEqual(original_existing, existing)
        with self.assertRaisesRegex(P04CapacityError, "key衝突"):
            allocate_append_ids(
                existing,
                [{"unit_key": "UNIT_KEY_ZERO"}],
                key_field="unit_key",
                expected_current_count=1,
            )
        with self.assertRaisesRegex(P04CapacityError, "上限"):
            allocate_append_ids(
                existing,
                requested,
                key_field="unit_key",
                expected_current_count=1,
                maximum_id=0,
            )

    def test_validator_rejects_runtime_ready_tamper(self) -> None:
        broken = copy.deepcopy(self.document)
        broken["runtime_ready"] = True
        with self.assertRaisesRegex(P04CapacityError, "runtime反映済み"):
            validate_checkpoint_document(broken)

    def test_writer_rejects_non_task_output_before_overwrite(self) -> None:
        readme = ROOT / "README.md"
        before = (readme.stat().st_size, readme.stat().st_mtime_ns)
        with self.assertRaisesRegex(P04CapacityError, "task固有path"):
            write_p04_capacity_checkpoint(ROOT, output_path="README.md")
        self.assertEqual(before, (readme.stat().st_size, readme.stat().st_mtime_ns))

    def test_tracked_checkpoint_is_exact_and_cli_check_has_no_side_effect(self) -> None:
        output = ROOT / DEFAULT_OUTPUT
        actual = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(canonical_json_bytes(self.document), canonical_json_bytes(actual))
        before = (output.stat().st_size, output.stat().st_mtime_ns)
        report = audit_p04_capacity_checkpoint(ROOT)
        self.assertEqual("PASS", report["status"])
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_modernization_p04_capacity.py"),
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


if __name__ == "__main__":
    unittest.main()
