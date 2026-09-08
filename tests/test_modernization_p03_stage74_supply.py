from __future__ import annotations

import copy
import json
import struct
import unittest
from pathlib import Path

from tools.modernization_p03_stage74_supply import (
    DEFAULT_CONFIG,
    EXPECTED_CROSS_FAMILY_MOVE_IDS,
    EXPECTED_EXISTING_PROJECTION_SHA256,
    EXPECTED_FULL_PRESERVATION_TARGET_MOVE_SHA256,
    EXPECTED_MACHINE_SET_SHA256,
    EXPECTED_PRESERVATION_CONSUMER_COUNTS,
    EXPECTED_PRESERVATION_METHOD_COUNTS,
    EXPECTED_PRESERVATION_TARGET_MOVE_SHA256,
    EXPECTED_PRESERVATION_TRIPLET_SHA256,
    EXPECTED_SOURCE_COUNTS,
    EXPECTED_TUTOR_SET_SHA256,
    EXPECTED_UNION_SET_SHA256,
    PROVISIONAL_LOAD_ADDRESS,
    ModernizationP03Stage74SupplyError,
    _veneer,
    apply_bps,
    archive_page,
    archive_probe,
    audit_build_learnable_capacity,
    build_outputs,
    build_runtime_tables,
    compile_payload,
    compile_supply_routes,
    read_config,
    require_pinned_parent,
    sha256,
)


ROOT = Path(__file__).resolve().parents[1]


class ModernizationP03Stage74SupplyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_config(ROOT, DEFAULT_CONFIG)
        cls.model = compile_supply_routes(ROOT, cls.config)
        parent_path = ROOT / cls.config["parent_identity"]["rom"]["path"]
        cls.parent = parent_path.read_bytes()
        cls.capacity = audit_build_learnable_capacity(
            ROOT, cls.config, cls.parent, cls.model
        )
        cls.blobs, cls.table_audit = build_runtime_tables(cls.model, cls.capacity)
        cls.compiled = compile_payload(ROOT, PROVISIONAL_LOAD_ADDRESS, cls.blobs)

    def test_parent_identity_and_user_exclusions_are_fail_closed(self) -> None:
        require_pinned_parent(self.config)
        runtime = self.config["runtime"]
        self.assertEqual(runtime["side_change_project_move_id"], 1063)
        self.assertEqual(runtime["side_change_materialized"], 0)
        self.assertEqual(runtime["prohibited_species_materialized"], 0)
        self.assertEqual(
            runtime["prohibited_species_keys"],
            ["SPECIES_KEY_BROWT", "SPECIES_KEY_POMBON", "SPECIES_KEY_GECQUA"],
        )
        self.assertEqual(runtime["unlock"]["required_flag"], "0x082C")
        self.assertFalse(runtime["unlock"]["early_game_archive_available"])
        self.assertEqual(runtime["economy"]["status"], "PROVISIONAL_REPLACEABLE")
        mutated = copy.deepcopy(self.config)
        mutated["parent_identity"]["stage73_commit"] = "PENDING"
        with self.assertRaisesRegex(
            ModernizationP03Stage74SupplyError, "Stage73 identity未確定"
        ):
            require_pinned_parent(mutated)

    def test_exact_route_partition_family_hashes_and_no_coercion(self) -> None:
        audit = self.model.route_audit
        self.assertEqual(audit["source_route_count"], 118528)
        self.assertEqual(audit["source_consumer_counts"], EXPECTED_SOURCE_COUNTS)
        direct = audit["direct_supply"]
        self.assertEqual(direct["route_count"], 26648)
        self.assertEqual(direct["species_family_move_pair_count"], 26648)
        self.assertEqual(direct["duplicate_species_family_move_pairs"], 0)
        self.assertEqual(direct["set_sha256"], EXPECTED_UNION_SET_SHA256)
        self.assertEqual(
            direct["family_set_sha256"],
            {"machine": EXPECTED_MACHINE_SET_SHA256, "tutor": EXPECTED_TUTOR_SET_SHA256},
        )
        self.assertEqual(
            direct["existing_slot_projection_set_sha256"],
            EXPECTED_EXISTING_PROJECTION_SHA256,
        )
        self.assertEqual(
            direct["selected_direct_partition"],
            {"total": 56421, "existing": 29773, "new": 26648},
        )
        self.assertEqual(direct["existing_slot_routes_preserved"], {"machine": 29033, "tutor": 740})
        self.assertEqual(audit["exclusions"]["side_change_source_routes"], 159)
        self.assertEqual(audit["exclusions"]["side_change_materialized"], 0)
        self.assertEqual(audit["exclusions"]["browt_pombon_gecqua_materialized"], 0)
        self.assertEqual(audit["exclusions"]["prohibited_coercions_materialized"], 0)
        self.assertFalse(audit["full_p03_done"])
        self.assertEqual(
            audit["upstream_carry_form_dependency"]["reference_owner_missing_paths"], 38
        )

    def test_machine_and_tutor_tables_remain_distinct_under_adversarial_ids(self) -> None:
        direct = self.model.route_audit["direct_supply"]
        self.assertEqual(
            direct["cross_family_same_move_ids"], list(EXPECTED_CROSS_FAMILY_MOVE_IDS)
        )
        self.assertEqual(direct["same_species_cross_family_pair_count"], 0)
        self.assertIn(173, self.model.machine_rows[18])
        self.assertNotIn(173, self.model.tutor_rows.get(18, ()))
        self.assertIn(173, self.model.tutor_rows[10])
        self.assertNotIn(173, self.model.machine_rows.get(10, ()))
        self.assertEqual(
            direct["family_collapse_risk_counts"],
            {
                "required_machine_rows_using_existing_tutor_move_ids": 2940,
                "required_machine_distinct_moves_using_existing_tutor_move_ids": 24,
                "required_tutor_rows_using_existing_machine_move_ids": 81,
                "required_tutor_distinct_moves_using_existing_machine_move_ids": 9,
            },
        )

    def test_fixed_raw_banks_cover_every_route_without_empty_last_page(self) -> None:
        assigned_machine = 0
        for species, rows in self.model.machine_rows.items():
            pages = (len(rows) + 39) // 40
            rebuilt = tuple(
                move for page in range(pages)
                for move in archive_page(self.model.machine_rows, species, page)
            )
            self.assertEqual(rebuilt, rows)
            self.assertTrue(archive_page(self.model.machine_rows, species, pages - 1))
            self.assertFalse(archive_page(self.model.machine_rows, species, pages))
            assigned_machine += len(rebuilt)
        self.assertEqual(assigned_machine, 26279)
        self.assertEqual(
            [len(archive_page(self.model.machine_rows, 151, page)) for page in range(4)],
            [40, 40, 40, 11],
        )
        self.assertFalse(archive_page(self.model.machine_rows, 151, 4))
        self.assertEqual(
            self.table_audit["machine"]["page_histogram"],
            {"1": 1261, "2": 24, "4": 1},
        )
        self.assertEqual(self.table_audit["machine"]["silent_drop_count"], 0)

        assigned_tutor = sum(len(rows) for rows in self.model.tutor_rows.values())
        self.assertEqual(assigned_tutor, 369)
        self.assertEqual(self.table_audit["tutor"]["page_histogram"], {"1": 138})
        self.assertEqual(self.table_audit["tutor"]["max_rows_per_species"], 12)

    def test_known_first_bank_does_not_hide_later_banks(self) -> None:
        first_bank = self.model.machine_rows[151][:40]
        self.assertEqual(
            archive_page(self.model.machine_rows, 151, 0, first_bank), ()
        )
        self.assertEqual(
            archive_probe(self.model.machine_rows, 151, first_bank),
            (self.model.machine_rows[151][40],),
        )
        scripts = (
            ROOT
            / "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime_scripts.S"
        ).read_text(encoding="utf-8")
        empty_branch = scripts.index("STAGE74_BRANCH 1, Stage74_MachinePageNoMovesScript")
        page_loop = scripts.index("STAGE74_GOTO Stage74_MachineChoosePageScript", empty_branch)
        self.assertLess(empty_branch, page_loop)
        self.assertIn("STAGE74_BRANCH 1, Stage74_FinishScript", scripts)

    def test_machine_probe_zero_exits_before_raw_page_count(self) -> None:
        scripts = (
            ROOT
            / "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime_scripts.S"
        ).read_text(encoding="utf-8")
        start = scripts.index("STAGE74_EXPORT Stage74_MachineSelectScript")
        end = scripts.index(".size Stage74_MachineSelectScript", start)
        machine_select = scripts[start:end]
        probe = machine_select.index("STAGE74_SPECIAL 0x00DB")
        egg_check = machine_select.index("STAGE74_SPECIAL 0x0148", probe)
        zero_check = machine_select.index("STAGE74_COMPARE 0x8005, 0", egg_check)
        zero_exit = machine_select.index(
            "STAGE74_BRANCH 1, Stage74_MachineNoMovesScript", zero_check
        )
        prepare = machine_select.index(
            "STAGE74_CALLNATIVE Stage74_PrepareMachinePages", zero_exit
        )
        self.assertLess(probe, egg_check)
        self.assertLess(egg_check, zero_check)
        self.assertLess(zero_check, zero_exit)
        self.assertLess(zero_exit, prepare)

    def test_machine_page_menu_places_cancel_after_actual_page_count(self) -> None:
        runtime_source = (
            ROOT
            / "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.c"
        ).read_text(encoding="utf-8")
        table_start = runtime_source.index("sStage74PageMenuTexts[]")
        table_end = runtime_source.index("};", table_start)
        page_table = runtime_source[table_start:table_end]
        for page in range(1, 5):
            self.assertIn(f"sStage74TextPage{page}", page_table)
        self.assertNotIn("sStage74TextCancel", page_table)

        function_start = runtime_source.index("void Stage74_OpenMachinePageMenu")
        function_end = runtime_source.index("Stage74U32 Stage74_RuntimeProbe", function_start)
        page_menu = runtime_source[function_start:function_end]
        bounds = page_menu.index("pages > STAGE74_MAX_MACHINE_PAGES")
        copy_pages = page_menu.index(
            "page_texts[index] = sStage74PageMenuTexts[index]", bounds
        )
        append_cancel = page_menu.index(
            "page_texts[pages] = sStage74TextCancel", copy_pages
        )
        open_menu = page_menu.index("Stage74_OpenMenu(", append_cancel)
        self.assertLess(bounds, copy_pages)
        self.assertLess(copy_pages, append_cancel)
        self.assertLess(append_cancel, open_menu)
        self.assertIn("(Stage74U8)(pages + 1u)", page_menu)
        self.assertIn("(Stage74U8)(count - 1u)", runtime_source)

    def test_build_learnable_exact_rom_capacity_and_owner_hook(self) -> None:
        self.assertEqual(self.capacity["status"], "PASS_EXACT_ROM_TABLE_ORACLE")
        self.assertEqual(self.capacity["species_checked"], 1621)
        self.assertEqual(
            self.capacity["maximum_runtime_buffer_entries_after_archive_append"], 238
        )
        self.assertEqual(self.capacity["maximum_unique_entries_after_archive_append"], 234)
        self.assertEqual(self.capacity["maximum_species"], 151)
        self.assertEqual(self.capacity["runtime_buffer_headroom_u16"], 191)
        self.assertEqual(self.capacity["structural_nondeduplicated_upper_bound"], 319)
        self.assertEqual(self.capacity["structural_upper_bound_headroom_u16"], 110)
        self.assertEqual(self.capacity["overflow_species_count"], 0)
        self.assertEqual(
            self.capacity["maximum_species_breakdown"],
            {
                "species": 151,
                "parent_buffer_entries": 110,
                "parent_unique_entries": 106,
                "level_entries": 12,
                "egg_entries_after_family_incense_resolution": 0,
                "legacy_machine_entries": 98,
                "legacy_tutor_entries": 0,
                "archive_machine_entries": 131,
                "archive_tutor_entries": 0,
                "preservation_only_entries": 0,
                "output_buffer_entries": 238,
                "output_unique_entries": 234,
            },
        )
        symbols = self.compiled.symbols
        trampoline = symbols["Stage74_OriginalBuildLearnableMoveset"] - PROVISIONAL_LOAD_ADDRESS
        self.assertEqual(
            self.compiled.code[trampoline:trampoline + 8].hex(),
            "f0b5d6464f464646",
        )
        self.assertIn(bytes.fromhex("c1431109"), self.compiled.code[trampoline:trampoline + 32])

    def test_build_learnable_preservation_covers_all_selected_routes_only(self) -> None:
        preservation = self.capacity["preservation_only"]
        self.assertEqual(preservation["selected_route_count_checked"], 118369)
        self.assertEqual(preservation["missing_path_count"], 4014)
        self.assertEqual(preservation["runtime_target_move_count"], 2223)
        self.assertEqual(preservation["species_count"], 501)
        self.assertEqual(preservation["max_rows_per_species"], 22)
        self.assertEqual(preservation["max_species"], 576)
        self.assertEqual(
            preservation["target_move_set_sha256"],
            EXPECTED_FULL_PRESERVATION_TARGET_MOVE_SHA256,
        )
        self.assertEqual(
            preservation["missing_path_consumer_counts"],
            EXPECTED_PRESERVATION_CONSUMER_COUNTS,
        )
        self.assertEqual(
            preservation["missing_path_method_counts"],
            EXPECTED_PRESERVATION_METHOD_COUNTS,
        )
        self.assertEqual(preservation["ui_supply_routes_added"], 0)
        self.assertEqual(preservation["route_accounting_added"], 0)
        regression = preservation["machine_tutor_carry_form_regression"]
        self.assertEqual(regression["missing_path_count"], 31)
        self.assertEqual(regression["unique_species_family_move_count"], 23)
        self.assertEqual(
            regression["triplet_set_sha256"], EXPECTED_PRESERVATION_TRIPLET_SHA256
        )
        self.assertEqual(
            regression["target_move_set_sha256"],
            EXPECTED_PRESERVATION_TARGET_MOVE_SHA256,
        )
        preservation_rows = {
            row["species"]: tuple(row["moves"])
            for row in preservation["runtime_rows"]
        }
        self.assertNotIn(232, preservation_rows.get(156, ()))
        self.assertNotIn(232, preservation_rows.get(157, ()))
        self.assertIn(206, preservation_rows[157])
        self.assertIn(334, preservation_rows[417])
        self.assertIn(387, preservation_rows[1222])
        self.assertEqual(self.table_audit["preservation"]["move_rows"], 2223)
        self.assertEqual(self.table_audit["preservation"]["species_with_rows"], 501)
        self.assertEqual(self.table_audit["preservation"]["max_rows_per_species"], 22)
        self.assertEqual(self.table_audit["preservation"]["max_species"], 576)
        runtime_source = (
            ROOT
            / "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.c"
        ).read_text(encoding="utf-8")
        provider_start = runtime_source.index("Stage74U8 Stage74_GetMoveRelearnerMoves")
        provider_end = runtime_source.index(
            "static Stage74U16 Stage74_AppendLearnableRange", provider_start
        )
        build_start = runtime_source.index("Stage74U16 Stage74_BuildLearnableMoveset")
        build_end = runtime_source.index(
            "static Stage74U16 Stage74_SelectedMachineRowCount", build_start
        )
        self.assertNotIn("Stage74_Preservation", runtime_source[provider_start:provider_end])
        self.assertIn("Stage74_PreservationIndex", runtime_source[build_start:build_end])
        self.assertIn("Stage74_PreservationMoves", runtime_source[build_start:build_end])

    def test_parent_hook_calls_scripts_and_sync_failure_paths_are_exact(self) -> None:
        abi = self.config["parent_abi"]
        for hook in abi["hooks"]:
            offset = int(hook["address"], 0) - 0x08000000
            self.assertEqual(self.parent[offset:offset + hook["width"]].hex(), hook["parent_hex"])
        for consumer in abi["get_move_relearner_consumers"].values():
            offset = int(consumer["call_address"], 0) - 0x08000000
            self.assertEqual(self.parent[offset:offset + 4].hex(), consumer["call_hex"])
        pointer = int(abi["move_memory"]["item_script_pointer_address"], 0) - 0x08000000
        self.assertEqual(self.parent[pointer:pointer + 4].hex(), "50072d09")

        scripts = (
            ROOT
            / "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime_scripts.S"
        ).read_text(encoding="utf-8")
        main_call = scripts.index("STAGE74_CALLNATIVE Stage74_OpenArchiveModeMenu")
        main_compare = scripts.index("STAGE74_COMPARE 0x800D, 5", main_call)
        main_wait = scripts.index(".byte 0x27", main_call)
        self.assertLess(main_call, main_compare)
        self.assertLess(main_compare, main_wait)
        page_call = scripts.index("STAGE74_CALLNATIVE Stage74_OpenMachinePageMenu")
        page_compare = scripts.index("STAGE74_COMPARE 0x800D, 0xFFFE", page_call)
        page_wait = scripts.index(".byte 0x27", page_call)
        self.assertLess(page_call, page_compare)
        self.assertLess(page_compare, page_wait)
        self.assertIn("STAGE74_CALLNATIVE Stage74_ResetMode", scripts)
        self.assertIn(".hword 0x082C", scripts)

    def test_payload_exports_both_hooks_and_family_tables(self) -> None:
        self.assertEqual(self.compiled.symbols["Stage74_RuntimeProbe"], PROVISIONAL_LOAD_ADDRESS)
        for symbol in (
            "Stage74_GetMoveRelearnerMoves",
            "Stage74_BuildLearnableMoveset",
            "Stage74_OriginalBuildLearnableMoveset",
            "Stage74_MachineIndex",
            "Stage74_MachineMoves",
            "Stage74_TutorIndex",
            "Stage74_TutorMoves",
            "Stage74_PreservationIndex",
            "Stage74_PreservationMoves",
            "Stage74_ItemScript",
        ):
            self.assertIn(symbol, self.compiled.symbols)
        self.assertLess(len(self.compiled.code), 0x20000)
        self.assertEqual(_veneer(8, 0x09501234).hex(), "004b184735125009")

    def test_build_outputs_allocation_bps_and_checkpoint_are_self_consistent(self) -> None:
        outputs = build_outputs(ROOT, DEFAULT_CONFIG)
        self.assertEqual(len(outputs), 9)
        paths = self.config["outputs"]
        metadata = json.loads(outputs[paths["metadata"]])
        allocation = json.loads(outputs[paths["allocation"]])
        checkpoint = json.loads(outputs[paths["checkpoint"]])
        route_audit = json.loads(outputs[paths["route_audit"]])
        rom = outputs[paths["rom"]]
        bps = outputs[paths["incremental_bps"]]

        self.assertEqual(apply_bps(self.parent, bps), rom)
        self.assertEqual(metadata["output"]["sha256"], sha256(rom))
        self.assertFalse(metadata["done"])
        self.assertFalse(metadata["release_candidate"])
        self.assertEqual(metadata["accounting"]["cumulative_runtime_materialized_routes"], 83162)
        self.assertEqual(metadata["accounting"]["cumulative_accounted_routes"], 118369)
        self.assertEqual(metadata["accounting"]["selected_direct_supply_routes_remaining"], 0)

        before = json.loads(
            (ROOT / self.config["parent_identity"]["allocation"]["path"]).read_bytes()
        )["allocations"]
        after = allocation["allocations"]
        self.assertEqual(len(before), 77)
        self.assertEqual(len(after), 78)
        for index, (left, right) in enumerate(zip(before, after, strict=False)):
            for key in (
                "sequence", "name", "region", "alignment", "start", "end_exclusive",
                "gba_start", "gba_end_exclusive", "size", "owner", "purpose", "placement",
            ):
                self.assertEqual(left[key], right[key], f"sequence {index}/{key}")
            if index == 33:
                self.assertNotEqual(left["content_sha256"], right["content_sha256"])
            else:
                self.assertEqual(left["content_sha256"], right["content_sha256"])
        self.assertEqual(after[-1]["sequence"], 77)
        self.assertEqual(after[-1]["content_sha256"], sha256(outputs[paths["payload"]]))

        self.assertEqual(checkpoint["remaining_direct_supply_routes"], 0)
        self.assertFalse(checkpoint["full_p03_done"])
        self.assertEqual(checkpoint["withheld_route_semantics"]["count"], 38)
        self.assertEqual(
            checkpoint["build_learnable_preservation"]["target_move_pairs"], 2223
        )
        self.assertEqual(
            checkpoint["build_learnable_preservation"]["route_accounting_added"], 0
        )
        self.assertEqual(checkpoint["exclusions"]["side_change_materialized"], 0)
        self.assertEqual(checkpoint["exclusions"]["browt_pombon_gecqua_materialized"], 0)
        self.assertEqual(
            checkpoint["route_audit"]["sha256"], sha256(outputs[paths["route_audit"]])
        )
        self.assertEqual(route_audit["serialization"]["silent_drop_count"], 0)


if __name__ == "__main__":
    unittest.main()
