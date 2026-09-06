from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import stage61_state_namespace_collision_audit as audit
from tests.fixtures.private_unit_fixtures import ensure_stage60_test_ready_save
from scripts.regenerate_stage61_unit_state import ensure_stage61_state_fixture


ROOT = Path(__file__).resolve().parents[1]


class Stage61StateNamespaceCollisionAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_stage60_test_ready_save()
        cls.root = ensure_stage61_state_fixture()
        cls.raw = (cls.root / audit.STAGE60_ROM_RELATIVE).read_bytes()
        cls.report = audit.build_stage61_state_namespace_collision_audit(cls.root)
        cls.installed_report = audit._build_stage61_installed_state_namespace_audit(
            cls.root, cls.report
        )

    def test_exact_stage60_and_all_top_level_assertions(self) -> None:
        self.assertEqual(audit._sha(self.raw), audit.STAGE60_ROM_SHA256)
        self.assertEqual(self.report["audit_status"], "PASS")
        self.assertTrue(all(self.report["assertions"].values()))
        self.assertIn("LEGACY_MIGRATION_REQUIRED", self.report["status"])
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit.require_ready(self.report)

    def test_global_pointer_hooks_are_linked_but_unconnected(self) -> None:
        contract = self.report["global_expanded_hooks"]
        self.assertEqual(contract["status"], "CRITICAL_UNCONNECTED")
        self.assertEqual(
            [row["address"] for row in contract["repair_patches"]],
            [audit.GET_VAR_POINTER, audit.GET_FLAG_POINTER],
        )
        patched = audit.apply_exact_patches(self.raw, audit.hook_patch_plan())
        self.assertEqual(
            patched[
                audit.GET_FLAG_POINTER - audit.ROM_BASE:
                audit.GET_FLAG_POINTER - audit.ROM_BASE + 8
            ].hex(),
            "0049084705710909",
        )
        special = contract["global_entries"]["GetFlagPointer"][
            "stock_special_flag_fallback"
        ]
        self.assertEqual(
            special,
            {
                "id_range": [0x4000, 0x407F],
                "literal_address": 0x0806DE70,
                "owner_address": 0x02037014,
                "owner_address_hex": "0x02037014",
                "size": 16,
            },
        )
        offset = audit.SPECIAL_FLAG_POINTER_LITERAL - audit.ROM_BASE
        self.assertEqual(
            int.from_bytes(self.raw[offset:offset + 4], "little"),
            audit.SPECIAL_FLAG_RAM,
        )

    @unittest.skipUnless(shutil.which("cc"), "C compiler unavailable")
    def test_mgba_global_fallback_preserves_engine_special_flag_owner(self) -> None:
        probe = audit.run_mgba_flag_probe(self.root)
        self.assertEqual(probe["status"], "PASS")
        for label in ("stage60_unconnected", "candidate_hooks_connected"):
            row = next(
                item for item in probe["observations"][label]["flags"]
                if item["id"] == 0x4001
            )
            self.assertEqual(
                (row["linked_pointer"], row["global_pointer"],
                 row["special_pointer"]),
                (0, audit.SPECIAL_FLAG_RAM, audit.SPECIAL_FLAG_RAM),
            )
            self.assertEqual(
                (row["get_after_set"], row["special_after_set"],
                 row["get_after_clear"], row["special_after_clear"]),
                (1, 2, 0, 0),
            )

    def test_all_six_cfru_save_entries_and_exact_patch_bytes(self) -> None:
        contract = self.report["save_storage"]["binary_expansion"]
        rows = contract["stage60_core_entries"]
        self.assertEqual(len(rows), 6)
        by_symbol = {row["target_symbol"]: row for row in rows}
        self.assertEqual(
            set(by_symbol),
            {
                "SaveWriteToFlash",
                "HandleWriteSector",
                "HandleLoadSector",
                "GetSaveValidStatus",
                "TryLoadSaveSector",
                "HandleSavingData",
            },
        )
        expected_replacements = {
            "SaveWriteToFlash": "004a1047417f1209",
            "HandleWriteSector": "004a1047357e1209",
            "HandleLoadSector": "004a1047857a1209",
            "GetSaveValidStatus": "004908474d7c1209",
            "TryLoadSaveSector": "004b1847e97b1209",
            "HandleSavingData": "0049084751801209",
        }
        self.assertEqual(
            {name: row["replacement_hex"] for name, row in by_symbol.items()},
            expected_replacements,
        )
        self.assertEqual(
            {
                name for name, row in by_symbol.items()
                if row["project_policy"].startswith("REJECT_")
            },
            {"SaveWriteToFlash", "HandleSavingData"},
        )
        self.assertEqual(contract["all_candidate_patch_count"], 10)

    def test_direct_cfru_table_plan_is_exact_but_requires_migration(self) -> None:
        contract = self.report["save_storage"]["binary_expansion"]
        pointer = contract["table_pointer_patch"]
        self.assertEqual(pointer["address"], 0x080DB224)
        self.assertEqual(pointer["expected_hex"], "284b3c08")
        self.assertEqual(pointer["replacement_hex"], "60951609")
        self.assertEqual(
            [(row["offset"], row["size"]) for row in contract["stock_table"]],
            list(audit.STOCK_SAVE_SECTION_ROWS),
        )
        self.assertEqual(
            [(row["offset"], row["size"]) for row in contract["linked_table"]],
            list(audit.LINKED_SAVE_SECTION_ROWS),
        )
        legacy = self.report["save_storage"]["legacy_stage60_compatibility"]
        self.assertTrue(legacy["stock_layout_valid"])
        self.assertFalse(legacy["linked_layout_valid"])
        self.assertEqual(legacy["linked_invalid_section_ids_each_slot"], [4, 13])
        self.assertEqual(
            [row["linked_invalid_section_ids"] for row in legacy["slots"]],
            [[4, 13], [4, 13]],
        )

    def test_parasite_slots_and_existing_sector31_owner_geometry(self) -> None:
        owners = self.report["save_storage"]["parasite_and_sector_owners"]
        self.assertEqual(
            [
                (
                    row["main_save_sector_id"],
                    row["image_offset_start"],
                    row["image_offset_end_exclusive"],
                    row["size"],
                )
                for row in owners["parasite_fragments"]
            ],
            [
                (0, 0x0000, 0x00CC, 0x00CC),
                (4, 0x00CC, 0x0324, 0x0258),
                (13, 0x0324, 0x0EC4, 0x0BA0),
            ],
        )
        self.assertEqual(
            [(row["ram_start"], row["ram_end_exclusive"]) for row in owners["regions"]],
            [
                (0x0203B0E8, 0x0203BFAC),
                (0x0203BFAC, 0x0203CF9C),
                (0x0203CF9C, 0x0203DF8C),
            ],
        )
        required = owners["required_owner_geometry"]
        self.assertEqual(required["expanded_flags"]["ram_start"], 0x0203B0E8)
        self.assertEqual(required["expanded_vars"]["ram_start"], 0x0203B2E8)
        self.assertEqual(
            required["magic_version_size_checksum_generation"]["ram_start"],
            0x0203D000,
        )
        self.assertEqual(required["codex_battle_reward_owner"]["ram_start"], 0x0203D800)
        self.assertEqual(required["collection_supply_owner"]["ram_start"], 0x0203D900)

    def test_sector31_transaction_conflict_is_explicit(self) -> None:
        owner = self.report["save_storage"]["sector31_transaction_owner"]
        self.assertFalse(owner["full_upstream_save_write_compatible"])
        self.assertEqual(owner["sector31_image"], 0x0203CF9C)
        self.assertEqual(
            owner["transaction_bypass"], "VegaQolProduction_OriginalTrySavingData"
        )
        self.assertIn("double-write", owner["reason"])

    def test_stage61_custom_record_preserves_legacy_table_and_exact_hooks(self) -> None:
        custom = self.report["save_storage"]["stage61_custom_compatibility"]
        self.assertEqual(
            custom["status"], "PREFERRED_STOCK_LAYOUT_COMPATIBILITY_PLAN_INSTALLED"
        )
        self.assertTrue(custom["stock_layout_retained"])
        self.assertTrue(custom["stock_orchestration_retained"])
        self.assertTrue(custom["delayed_signature_replace_retained"])
        self.assertTrue(custom["unsafe_cfru_direct_plan_rejected"])
        self.assertEqual(custom["active_patch_count"], 12)
        by_name = {row["name"]: row for row in custom["active_exact_patches"]}
        custom_hooks = {
            "stage61_save_compatibility::handle_write_sector": (
                0x080DA858, "Stage61State_HandleWriteSector"
            ),
            "stage61_save_compatibility::handle_replace_sector": (
                0x080DAB38, "Stage61State_HandleReplaceSector"
            ),
            "stage61_save_compatibility::handle_load_sector": (
                0x080DAE3C, "Stage61State_HandleLoadSector"
            ),
            "stage61_save_compatibility::get_save_valid_status": (
                0x080DAEF4, "Stage61State_GetSaveValidStatus"
            ),
        }
        for name, (address, symbol) in custom_hooks.items():
            self.assertEqual(by_name[name]["address"], address)
            self.assertEqual(
                by_name[name]["replacement_hex"],
                audit._register_jump_stub(
                    address, custom["symbols"][symbol]["address"],
                    1 if symbol == "Stage61State_GetSaveValidStatus" else 2,
                ).hex(),
            )
        self.assertEqual(
            by_name["stage61_save_link_record_near_veneer"]["address"],
            0x080C6480,
        )
        for address in (0x080DB35C, 0x080F64C4):
            row = by_name[
                f"stage61_save_link_record_caller::{address:#010x}"
            ]
            self.assertEqual(
                audit._thumb_bl_target(
                    address, bytes.fromhex(row["replacement_hex"])
                ),
                0x080C6480,
            )
        self.assertTrue(custom["stock_bounded_read_trampolines_absent"])
        bounded = custom["bounded_read_contract"]
        self.assertTrue(
            bounded["footer_id_must_be_below_row_count_before_index"]
        )
        self.assertEqual(
            bounded["generation_order"]["algorithm"],
            "HALF_RANGE_MODULAR_U32",
        )
        self.assertEqual(
            bounded["slot_sector_rotation_policy"],
            {
                "first_sector_definition": "PHYSICAL_INDEX_OF_LOGICAL_ID_0",
                "expected_physical_index_by_logical_id": (
                    "(first + logical_id) % 14"
                ),
                "all_14_logical_ids_require_exact_relative_rotation": True,
                "permuted_full_bank_status": "ERROR",
                "newest_permuted_full_bank_selection": (
                    "FALL_BACK_TO_OLDER_EXACT_ROTATION"
                ),
                "both_banks_permuted_status": "INVALID_NO_RAM_COPY",
                "mgba_required": True,
            },
        )
        self.assertEqual(
            [row["name"] for row in custom["bounded_read_entry_hooks"]],
            ["GetSaveValidStatus", "HandleLoadSector"],
        )
        link = custom["link_save_record_commit"]
        self.assertFalse(link["stock_entry_modified"])
        self.assertEqual(
            link["transaction_sequence"],
            [
                "PREFLIGHT_ENSURE_TWO_COMPLETE_GENERATIONS",
                "STOCK_SAVE_LINK_IDS_0_TO_4_IN_PLACE",
                (
                    "POST_STOCK_ATOMIC_SOURCE_RECORD_COMMIT_WITH_"
                    "OLD_BACKUP_VALID"
                ),
                (
                    "POST_STOCK_COPY_ON_WRITE_FULL_GENERATION_FROM_"
                    "EXACT_NEW_SOURCE"
                ),
            ],
        )
        transaction = link["record_only_transaction"]
        self.assertEqual(
            (
                transaction["preflight_callback_boundaries"],
                transaction["stock_callback_boundaries"],
                transaction["post_callback_boundaries"],
            ),
            (57358, 20485, 61456),
        )
        self.assertTrue(
            transaction[
                "at_least_one_exact_generation_remains_valid_at_every_"
                "fault_offset"
            ]
        )
        self.assertEqual(
            transaction["post_source_record_callback_boundaries"], 4097,
        )
        self.assertEqual(
            transaction["fault_injection_granularity"],
            (
                "MGBA_STOCK_FLASH_CALLBACK_BEFORE_AND_AFTER_EACH_"
                "ERASE_OR_PROGRAM_BYTE"
            ),
        )
        self.assertFalse(
            transaction["analog_flash_cell_threshold_during_callback_modelled"]
        )
        self.assertFalse(link["outer_post_failure_additional_mark"])
        self.assertTrue(
            link[
                "target_invalidation_early_guard_non_ok_caller_marks_"
                "target_id13"
            ]
        )
        self.assertTrue(link["save_failed_screen_wipe_and_retry_mgba_required"])
        record = custom["record"]
        self.assertEqual(
            (
                record["magic"], record["version"], record["header_size"],
                record["payload_size"], record["record_size"],
            ),
            (0x45313653, 1, 0x10, 0x606, 0x616),
        )
        self.assertEqual(
            [(row["owner"], row["size"]) for row in record["payload"]],
            [
                ("expanded_flags", 0x200),
                ("expanded_vars", 0x400),
                ("gLastUsedBall", 2),
                ("cfru_player_coins_u32", 4),
            ],
        )
        self.assertEqual(
            [
                (row["section_id"], row["chunk_size"], row["record_start"], row["length"])
                for row in record["segments"]
            ],
            [
                (13, 0x7D0, 0x000, 0x616),
            ],
        )
        self.assertLessEqual(0x7D0 + 0x616, audit.SAVE_SECTOR_DATA_SIZE)
        literals = custom["runtime_code"]["persistent_literal_evidence"]
        self.assertEqual(
            set(literals),
            {"gExpandedFlags", "gExpandedVars", "gLastUsedBall", "gPlayerCoins"},
        )
        self.assertTrue(all(row["count"] >= 1 for row in literals.values()))
        self.assertFalse(custom["legacy_exact_save"]["record_magic_present"])

    def test_parasite_live_consumers_are_rooted_not_inferred_from_ram(self) -> None:
        contract = self.report["save_storage"]["parasite_live_consumers"]
        self.assertEqual(
            contract["status"],
            "LAST_USED_BALL_ONLY_ADDITIONAL_DURABLE_OWNER",
        )
        features = contract["feature_hook_evidence"]
        self.assertEqual(
            {name: row["hook_count"] for name, row in features.items()},
            {
                "keypad": 6,
                "dynamic_overworld_palettes": 40,
                "followers": 20,
                "updated_repel": 2,
                "expanded_bag": 36,
                "expanded_coins": 6,
                "wild_encounter_roamer_paths": 13,
                "roamers": 12,
                "pedometers": 1,
                "last_used_ball": 1,
            },
        )
        self.assertEqual(features["last_used_ball"]["canonical_connected_count"], 1)
        for name in set(features) - {"last_used_ball"}:
            self.assertEqual(features[name]["canonical_connected_count"], 0)
            self.assertEqual(features[name]["external_inbound_count"], 0)
        self.assertTrue(contract["last_used_ball"]["required_in_custom_record"])
        self.assertEqual(contract["minimum_custom_payload"]["total"], 0x606)
        bag = contract["expanded_bag"]
        self.assertEqual(bag["size"], 0xC28)
        self.assertEqual(bag["parasite_prefix_size"], 0x514)
        self.assertEqual(bag["sector30_suffix_size"], 0x714)
        self.assertFalse(bag["fits_stock_main_save_tails"])
        roamer = next(
            row for row in contract["regions"] if row["symbol"] == "gRoamers"
        )
        self.assertEqual((roamer["size"], roamer["stage60_status"]), (0xF0, "UNCONNECTED"))
        adapter = contract["stage61_roamer_context_adapter"]
        self.assertEqual(
            adapter["status"],
            "INNER_ADAPTER_INSTALLED_BUT_ALL_CALLER_ROOTS_UNCONNECTED",
        )
        self.assertFalse(adapter["persistent_owner_live"])
        self.assertEqual(adapter["inner_entry"], 0x09125ECC)
        self.assertEqual(adapter["inner_call_sites"], [0x09097774, 0x0909777C])
        self.assertTrue(
            all(not row["canonical_connected"] for row in adapter["caller_roots"])
        )
        noncanonical = contract["noncanonical_state_paths"]
        follower = noncanonical["gFollowerState"]
        self.assertEqual(
            follower["status"],
            "LIVE_READ_INACTIVE_SENTINEL_NO_CONNECTED_WRITER",
        )
        self.assertEqual(follower["read_root_count"], 5)
        self.assertEqual(follower["connected_writer_count"], 0)
        self.assertFalse(follower["persistent_owner_live"])
        roamer_path = noncanonical["gRoamers"]
        self.assertEqual(
            roamer_path["status"],
            "DORMANT_ROUTINE_POINTER_READ_NOT_IN_EVENT_UNIVERSE",
        )
        self.assertEqual(roamer_path["absent_special_ids"], [0x97, 0x98, 0x129])
        self.assertEqual(roamer_path["connected_writer_count"], 0)
        self.assertFalse(roamer_path["persistent_owner_live"])

    def test_process_restart_gate_requires_real_save_and_fresh_continue(self) -> None:
        gate = self.report["save_storage"]["mgba_process_restart_gate"]
        self.assertEqual(
            gate["status"], "DEFINED_FAIL_CLOSED_PENDING_RUNTIME_PASS"
        )
        self.assertEqual(gate["writer_save_route"], "two ordinary Start-menu saves")
        self.assertIn("fresh OS process", gate["reader_load_route"])
        self.assertEqual(len(gate["sources"]), 3)

    def test_raid_consumers_collision_and_free_aligned_window(self) -> None:
        raid = self.report["raid_binary"]
        self.assertEqual(raid["binary_consumer_count"], 6)
        self.assertEqual(raid["patch_site_count"], 9)
        self.assertEqual(
            raid["operation_counts"],
            {"FlagClear": 3, "FlagGet": 2, "FlagSet": 1},
        )
        findings = self.report["collision_findings"]
        requested = findings["requested_0x1500_candidate"]
        self.assertEqual(requested["status"], "REJECTED_FULL_COLLISION")
        event = next(
            row for row in requested["collisions"]
            if row["source"] == "stage60_event_operands"
        )
        bindings = next(
            row for row in requested["collisions"]
            if row["source"] == "stage60_trainer_bindings"
        )
        self.assertEqual((event["count"], bindings["count"]), (109, 109))
        recommended = findings["recommended_0x15c0_candidate"]
        self.assertEqual(
            (recommended["start"], recommended["end_exclusive"], recommended["count"]),
            (0x15C0, 0x162D, 109),
        )
        self.assertEqual(recommended["collisions"], [])
        installed = raid["stage61_installation"]
        self.assertEqual(installed["patch_count"], 9)
        self.assertEqual(installed["api_guard_patch_count"], 5)
        self.assertEqual(installed["total_binary_patch_count"], 14)
        self.assertEqual(
            [row["address"] for row in installed["patches"]],
            [
                0x090F3AD0,
                0x090F3AF8,
                0x090F3B1A,
                0x090F3B38,
                0x090F3B4A,
                0x090F3B6A,
                0x090F3B8C,
                0x090F3BA2,
                0x090F3BE4,
            ],
        )
        self.assertEqual(
            [row["address"] for row in installed["api_guard_patches"]],
            [0x090F3AEC, 0x090F3B14, 0x090F3B34, 0x090F3B88, 0x090F3BEC],
        )

    def test_registry_keeps_topology_flags_in_collision_math_and_audits_vars(self) -> None:
        registry = audit._namespace_registry_inventory(self.root)
        project_ids = set(registry["project_ids_excluding_raid_owner"])
        topology_ids = set(range(0x162D, 0x163F))
        self.assertEqual(set(registry["topology_owner_ids"]), topology_ids)
        self.assertLessEqual(topology_ids, project_ids)
        self.assertEqual(
            project_ids,
            topology_ids | set(range(0x1800, 0x1900)),
        )
        self.assertEqual(set(registry["var_ids"]), set(range(0x5167, 0x5200)))
        self.assertEqual(
            {
                row["owner"]: (
                    row["start"], row["end_inclusive"], row["count"]
                )
                for row in registry["var_ranges"]
            },
            {
                "KANTO_MAP_TOPOLOGY_PERSISTENT_VARS": (0x5167, 0x516B, 5),
                "KANTO_LEAGUE_PROJECT_SCENE_VAR": (0x516C, 0x516C, 1),
                "KANTO_FULL_CFG_PERSISTENT_VARS": (0x516D, 0x517F, 19),
                "T19_QOL_VOLATILE_AND_COUNTERS": (0x5180, 0x51FF, 128),
            },
        )

    def test_patch_application_is_fail_closed_and_non_mutating(self) -> None:
        original = bytes(self.raw)
        corrupt = bytearray(self.raw)
        corrupt[audit.SAVE_SECTION_OFFSETS_POINTER_SITE - audit.ROM_BASE] ^= 1
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit.apply_exact_patches(bytes(corrupt), audit.save_expansion_patch_plan())
        self.assertEqual(self.raw, original)

        overlap = copy.deepcopy(audit.hook_patch_plan())
        duplicate = copy.deepcopy(overlap[0])
        duplicate["name"] = "deliberate_overlap"
        overlap.append(duplicate)
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit.apply_exact_patches(self.raw, overlap)

    def test_installed_candidate_public_api_is_ready(self) -> None:
        with mock.patch.object(
            audit,
            "build_stage61_state_namespace_collision_audit",
            return_value=self.report,
        ):
            report = audit.build_stage61_installed_state_namespace_audit(self.root)
        self.assertEqual(report["mode"], "STAGE61_INSTALLED_CANDIDATE")
        self.assertEqual((report["audit_status"], report["status"]), ("PASS", "READY"))
        self.assertTrue(all(report["assertions"].values()))
        audit.require_ready(report)

    def test_installed_layout_crosswalk_is_exact_and_non_overlapping(self) -> None:
        layout = self.installed_report["layout_ownership"]
        self.assertEqual(layout["status"], "EXACT_NON_OVERLAPPING")
        self.assertTrue(layout["ram_layout"]["all_live_ranges_non_overlapping"])
        self.assertTrue(layout["save_layout"]["all_live_ranges_non_overlapping"])
        self.assertEqual(
            [
                (
                    row["ram_symbol"], row["save_symbol"],
                    row["ram_start"], row["save_image_offset_start"], row["size"],
                )
                for row in layout["ram_save_affine_crosswalk"]
            ],
            [
                ("gExpandedFlags", "expanded_flags", 0x0203B0E8, 0x0000, 0x200),
                ("gExpandedVars", "expanded_vars", 0x0203B2E8, 0x0200, 0x400),
                ("gLastUsedBall", "last_used_ball_u16", 0x0203B6EC, 0x0604, 2),
                ("gPlayerCoins", "cfru_player_coins_u32", 0x0203B78C, 0x06A4, 4),
            ],
        )
        self.assertEqual(
            layout["first_parasite_live_owner_set"],
            [
                "cfru_player_coins_u32",
                "expanded_flags",
                "expanded_vars",
                "last_used_ball_u16",
            ],
        )

    def test_installed_s61e_compacts_all_four_layout_owners_once(self) -> None:
        record = self.installed_report["s61e_record"]
        self.assertEqual(record["status"], "EXACT_COMPLETE_COMPACT_SERIALIZATION")
        self.assertEqual(
            [
                (
                    row["owner"], row["payload_offset_start"],
                    row["payload_offset_end_exclusive"], row["size"],
                )
                for row in record["compact_payload"]
            ],
            [
                ("expanded_flags", 0x000, 0x200, 0x200),
                ("expanded_vars", 0x200, 0x600, 0x400),
                ("gLastUsedBall", 0x600, 0x602, 2),
                ("cfru_player_coins_u32", 0x602, 0x606, 4),
            ],
        )
        self.assertEqual(
            (
                record["header_size"], record["payload_size"],
                record["record_size"], record["record_bearing_logical_chunk"],
                record["stock_chunk_size"],
                record["remaining_checksum_excluded_tail"],
            ),
            (0x10, 0x606, 0x616, 13, 0x7D0, 0x20A),
        )

    def test_installed_all_26_declarations_and_postimages_are_exact(self) -> None:
        declarations = self.installed_report["installed_declarations"]
        self.assertEqual(
            declarations["status"], "ALL_26_POSTIMAGES_EXACT_NON_OVERLAPPING"
        )
        self.assertEqual(declarations["declaration_count"], 26)
        self.assertEqual(
            declarations["category_counts"],
            {
                "PERSISTENT_STATE_NAMESPACE_HOOK": 2,
                "PERSISTENT_STATE_RAID_FLAG_API_GUARD": 5,
                "PERSISTENT_STATE_RAID_FLAG_NAMESPACE": 9,
                "PERSISTENT_STATE_SAVE_COMPATIBILITY": 7,
                "PERSISTENT_STATE_SAVE_LIFECYCLE": 3,
            },
        )
        self.assertTrue(all(row["postimage_exact"] for row in declarations["declarations"]))
        self.assertEqual(
            declarations["global_hook_names"],
            ["expanded_var_pointer_global_hook", "expanded_flag_pointer_global_hook"],
        )

    def test_installed_raid_window_has_no_competing_owner(self) -> None:
        raid = self.installed_report["raid_namespace"]
        self.assertEqual(raid["status"], "INSTALLED_EXACT_NON_COLLIDING")
        self.assertEqual(
            (raid["start"], raid["end_inclusive"], raid["count"]),
            (0x15C0, 0x162C, 109),
        )
        self.assertEqual(raid["collisions"], [])
        self.assertEqual(
            (raid["binary_base_end_patch_count"], raid["bounded_api_guard_count"]),
            (9, 5),
        )

    def test_layout_config_hash_and_exact_range_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage61-layout-audit-") as temp_raw:
            root = Path(temp_raw)
            (root / "config").mkdir()
            for relative in (
                audit.STAGE61_BUILD_CONFIG_RELATIVE,
                audit.RAM_LAYOUT_RELATIVE,
                audit.SAVE_LAYOUT_RELATIVE,
            ):
                shutil.copy2(self.root / relative, root / relative)

            ram_path = root / audit.RAM_LAYOUT_RELATIVE
            ram_path.write_bytes(ram_path.read_bytes() + b"\n")
            with self.assertRaises(audit.StateNamespaceCollisionAuditError):
                audit._stage61_layout_ownership_contract(root)

            shutil.copy2(self.root / audit.RAM_LAYOUT_RELATIVE, ram_path)
            text = ram_path.read_text(encoding="utf-8")
            old = "0x0203B6EC,0x0203B6EE,2,CFRU_SAVE_EXPANSION,gLastUsedBall"
            new = "0x0203B6ED,0x0203B6EF,2,CFRU_SAVE_EXPANSION,gLastUsedBall"
            self.assertEqual(text.count(old), 1)
            ram_path.write_text(text.replace(old, new), encoding="utf-8", newline="")
            config_path = root / audit.STAGE61_BUILD_CONFIG_RELATIVE
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["inputs"]["ram_layout"]["sha256"] = audit._sha(
                ram_path.read_bytes()
            )
            config_path.write_text(
                json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="",
            )
            with self.assertRaises(audit.StateNamespaceCollisionAuditError):
                audit._stage61_layout_ownership_contract(root)

    def test_require_ready_rejects_forged_ready_or_false_assertion(self) -> None:
        forged = copy.deepcopy(self.installed_report)
        forged["assertions"]["raid_15c0_162c_installed_and_noncolliding"] = False
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit.require_ready(forged)
        forged["assertions"]["raid_15c0_162c_installed_and_noncolliding"] = True
        forged["audit_status"] = "FAIL"
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit.require_ready(forged)

    def test_cli_has_separate_installed_candidate_mode(self) -> None:
        args = audit._parser().parse_args(
            ["--installed-candidate", "--require-ready"]
        )
        self.assertTrue(args.installed_candidate)
        self.assertTrue(args.require_ready)


if __name__ == "__main__":
    unittest.main()
