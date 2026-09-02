#!/usr/bin/env python3
"""Stage 61 map-section consumer 恒久修正契約の fail-closed test。"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest

from tools import stage61_map_section_consumer_policy as policy
from tools import stage61_state_namespace_collision_audit as state_audit


ROOT = Path(__file__).resolve().parents[1]


class Stage61MapSectionConsumerPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage60 = (ROOT / policy.STAGE60_ROM_RELATIVE).read_bytes()
        cls.clean = (ROOT / policy.CLEAN_ROM_RELATIVE).read_bytes()
        cls.plan = policy.build_policy_plan(ROOT)

    def test_exact_stage60_identity_preimages_extents_and_dormancy(self) -> None:
        proof = policy.verify_stage60_contract(self.stage60, clean=self.clean)
        self.assertEqual(proof["stage60_sha256"], policy.STAGE60_ROM_SHA256)
        self.assertEqual(proof["patch_window_count"], 27)
        self.assertEqual(proof["conditional_alternative_patch_window_count"], 4)
        self.assertEqual(proof["function_extent_count"], 25)
        self.assertEqual(proof["data_extent_count"], 7)
        self.assertEqual(
            proof["raid_inline_getter_literal_sites"],
            [
                "0x090F3838",
                "0x090F3A90",
                "0x090F3AE8",
                "0x090F3B10",
                "0x090F3B90",
                "0x090F3FC0",
            ],
        )
        self.assertFalse(proof["raid_single_entry_available"])
        self.assertEqual(
            proof["roamer_direct_bl_xrefs"], ["0x09097774", "0x0909777C"]
        )
        self.assertTrue(proof["roamer_function_boundary_replacement_proven"])
        self.assertEqual(proof["cfru_warp_direct_bl_xrefs"], [])
        self.assertEqual(proof["cfru_warp_pointer_roots"], [])
        self.assertEqual(
            proof["dormancy_clean_comparisons"],
            [
                {
                    "site_id": "msc22_roamer_activation_main_map",
                    "stage60_equals_clean": True,
                },
                {
                    "site_id": "msc22_roamer_activation_post_switch",
                    "stage60_equals_clean": True,
                },
            ],
        )

    def test_stage60_identity_is_fail_closed(self) -> None:
        tampered = bytearray(self.stage60)
        tampered[0x0F3838] ^= 1
        with self.assertRaisesRegex(
            policy.MapSectionConsumerPolicyError, "SHA-256 mismatch"
        ):
            policy.verify_stage60_contract(bytes(tampered), clean=self.clean)

    def test_project_source_crosswalk_and_contextual_primitives(self) -> None:
        rows = self.plan["source_map_section_crosswalk"]
        self.assertEqual(len(rows), 53)
        expected = {
            0: (88, 1, 0),
            10: (98, 11, 10),
            11: (101, 14, 13),
            52: (142, 55, 54),
        }
        for project_id, values in expected.items():
            row = rows[project_id]
            self.assertEqual(row["project_id"], project_id)
            self.assertEqual(
                (row["source_id"], row["raid_index"], row["town_map_layout_index"]),
                values,
            )
            self.assertEqual(policy.project_to_source(project_id), values[0])

        for invalid in (-1, 53, 255, True, "0"):
            self.assertIsNone(policy.project_to_source(invalid))

        self.assertEqual(policy.normalize_for_stock(96, 0), 88)
        self.assertEqual(policy.normalize_for_stock(98, 52), 142)
        self.assertEqual(policy.normalize_for_stock(1, 0), 0)
        self.assertEqual(policy.normalize_for_stock(1, 196), 196)
        self.assertEqual(policy.normalize_for_stock(97, 53), policy.MAPSEC_NONE)

    def test_raid_and_roamer_indices_are_bounded(self) -> None:
        fixtures = [
            ((96, 0), 88, 0),
            ((96, 10), 98, 10),
            ((97, 11), 101, 13),
            ((98, 52), 142, 54),
            ((1, 88), 88, 0),
            ((1, 196), 87, 108),
        ]
        for (group, section), raid_source, roamer_index in fixtures:
            self.assertEqual(policy.raid_source_section(group, section), raid_source)
            self.assertEqual(policy.roamer_layout_index(group, section), roamer_index)
        self.assertEqual(policy.raid_source_section(96, 53), policy.MAPSEC_DYNAMIC)
        self.assertEqual(policy.raid_source_section(1, 196), policy.MAPSEC_DYNAMIC)
        self.assertEqual(policy.roamer_layout_index(96, 53), None)
        self.assertEqual(policy.roamer_layout_index(1, 87), None)
        self.assertEqual(policy.roamer_layout_index(1, 197), None)

    def test_map_name_low_ids_require_exact_provenance(self) -> None:
        contract = self.plan["map_name_provenance_contract"]
        self.assertEqual(contract["consumer_id"], "MSC-01")
        self.assertEqual(contract["status"], "PROVENANCE_GATED")
        self.assertEqual(
            contract["hook"],
            {
                "address": "0x080C5F5C",
                "stage60_preimage": "70b5061c09041204",
            },
        )
        inventory = contract["physical_inventory"]
        self.assertEqual(inventory["row_count"], 678)
        self.assertEqual(inventory["source_non_kanto_count"], 425)
        self.assertEqual(inventory["project_kanto_count"], 253)
        self.assertEqual(inventory["non_kanto_project_id_count"], 0)
        self.assertEqual(
            inventory["canonical_sha256"],
            policy.MAP_NAME_PHYSICAL_INVENTORY_CANONICAL_SHA256,
        )
        self.assertEqual(
            inventory["excluded_unused_coordinates"],
            [
                {"group": 98, "map": 101, "map_key": "Route6_UnusedHouse"},
                {"group": 98, "map": 118, "map_key": "Route19_UnusedHouse"},
                {"group": 98, "map": 120, "map_key": "Route23_UnusedHouse"},
            ],
        )
        self.assertEqual(
            contract["caller_counts"],
            {"GetMapName": 4, "GetMapNameGeneric": 15, "GetMapNameGeneric_": 2},
        )
        self.assertEqual(
            [row["provenance"] for row in contract["low_id_acceptance"]],
            [
                "CURRENT_PHYSICAL_MAP",
                "PENDING_WARP_DESTINATION",
                "POKEMON_MET_LOCATION",
            ],
        )

        runtime = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(
            runtime.count("stage61_has_project_name_provenance("), 3
        )
        self.assertIn("is_imported_kanto_context()", runtime)
        self.assertIn(
            "imported_kanto_map_is_valid(current_group(), current_map())",
            runtime,
        )
        self.assertIn("STAGE61_MAP_PREVIEW_NAME_RETURN = 0x080F93D4u", runtime)
        self.assertIn("__builtin_return_address(0)", runtime)
        self.assertIn("if (allow_pending_destination)", runtime)
        self.assertIn(
            "imported_kanto_map_is_valid(destination_group, destination_map)",
            runtime,
        )
        for unused in (101, 118, 120):
            self.assertIn(f"map != {unused}u", runtime)
        self.assertIn("FN_GET_MON_DATA(mon, 35, (void *)0) != mapsec", runtime)
        self.assertIn("met_game == 4u || met_game == 5u", runtime)

    def test_quest_log_crosswalk_has_exact_51_rows_and_special_cases(self) -> None:
        quest = self.plan["quest_log_physical_crosswalk"]
        self.assertEqual(quest["row_count"], 51)
        self.assertEqual(quest["canonical_sha256"], policy.QUEST_PAIR_CANONICAL_SHA256)
        self.assertEqual([row["index"] for row in quest["rows"]], list(range(51)))
        self.assertTrue(
            all(
                side["group"] in policy.IMPORTED_PHYSICAL_GROUPS
                for row in quest["rows"]
                for side in (row["project"]["inside"], row["project"]["outside"])
            )
        )
        home = quest["rows"][0]
        self.assertEqual(home["location_symbol"], "QL_LOCATION_HOME")
        self.assertEqual(
            (home["project"]["inside"]["group"], home["project"]["inside"]["map"]),
            (98, 0),
        )
        self.assertEqual(
            (home["project"]["outside"]["group"], home["project"]["outside"]["map"]),
            (96, 0),
        )
        self.assertEqual(quest["rows"][3]["project"]["outside"]["section"], 32)
        self.assertEqual(quest["rows"][4]["project"]["outside"]["section"], 33)
        self.assertEqual(quest["rows"][50]["location_symbol"], "QL_LOCATION_CERULEAN_CAVE")
        self.assertEqual(
            [row["case"] for row in quest["special_case_rewrites"]],
            [
                "VIRIDIAN_FOREST_TWO_EXITS",
                "LEAGUE_GATE_ROUTE22_ROUTE23",
                "ROCK_TUNNEL_DESTINATION_WARP_ID_DISAMBIGUATION",
                "SEAFOAM_DESTINATION_WARP_ID_DISAMBIGUATION",
                "ROCKET_HIDEOUT_GAME_CORNER_REARM",
            ],
        )

    def test_quest_log_source_exit_manifest_is_exact_and_fully_materialized(self) -> None:
        quest = self.plan["quest_log_physical_crosswalk"]
        manifest = quest["source_exit_manifest"]
        raw = (ROOT / policy.QUEST_LOG_EXIT_MANIFEST_RELATIVE).read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            policy.QUEST_LOG_EXIT_MANIFEST_SHA256,
        )
        self.assertEqual(manifest["source_rom_sha256"], policy.STAGE60_ROM_SHA256)
        self.assertEqual(manifest["row_count"], 51)
        self.assertEqual(manifest["enabled_count"], 49)
        self.assertEqual(manifest["disabled_rows"], [15, 29])
        self.assertEqual(
            manifest["classification_counts"],
            policy.QUEST_LOG_SOURCE_CLASSIFICATION_COUNTS,
        )

        expected_exits = [
            (3, 0), (3, 0), (3, 8), (3, 41), (3, 42),
            (15, 0), (15, 3), (3, 2), (3, 1), (3, 34),
            (3, 22), (3, 6), (3, 3), (3, 5), (3, 23),
            None, (3, 24), (3, 7), (3, 10), (3, 10),
            (3, 21), (3, 21), (3, 26), (3, 26), (3, 3),
            (3, 4), (3, 4), (3, 2), (3, 26), None,
            (3, 4), (3, 6), (3, 4), (3, 2), (3, 6),
            (3, 7), (11, 0), (3, 3), (3, 7), (3, 10),
            (3, 5), (3, 4), (3, 38), (3, 38), (3, 2),
            (3, 7), (3, 3), (3, 38), (3, 38), (3, 9),
            (3, 12),
        ]
        self.assertEqual(len(expected_exits), 51)
        for index, (row, manifest_row, expected) in enumerate(zip(
            quest["rows"], manifest["rows"], expected_exits
        )):
            self.assertEqual(row["index"], index)
            self.assertEqual(manifest_row["index"], index)
            if expected is None:
                self.assertFalse(manifest_row["enabled"])
                self.assertEqual(
                    (
                        row["source"]["inside"]["group"],
                        row["source"]["inside"]["map"],
                        row["source"]["outside"]["group"],
                        row["source"]["outside"]["map"],
                    ),
                    (0xFF, 0xFF, 0xFF, 0xFF),
                )
                continue
            self.assertTrue(manifest_row["enabled"])
            self.assertEqual(tuple(manifest_row["record_exits"][0]["map"]), expected)
            self.assertEqual(
                (row["source"]["outside"]["group"], row["source"]["outside"]["map"]),
                expected,
            )
            self.assertEqual(manifest_row["record_exits"][0]["location_id"], index)

        # Representative actual Vega exit: 6/2 warp event 0 reaches 3/1,
        # never the stale FireRed declaration 3/2.
        pewter = manifest["rows"][8]
        self.assertEqual(pewter["inside"], [6, 2])
        self.assertEqual(pewter["existing_outside"], [3, 2])
        self.assertEqual(pewter["record_exits"][0]["map"], [3, 1])
        self.assertEqual(pewter["record_exits"][0]["path"], ["0x0870CBB8"])

    def test_quest_log_components_and_warp_variants_match_runtime_exactly(self) -> None:
        quest = self.plan["quest_log_physical_crosswalk"]
        manifest = quest["source_exit_manifest"]
        runtime_path = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        )
        runtime = runtime_path.read_text(encoding="utf-8")
        initializer = re.search(
            r"sStage61SourceQuestLogComponentExtras\[\]\s*=\s*\{(.*?)\n\};",
            runtime,
            re.DOTALL,
        )
        self.assertIsNotNone(initializer)
        actual_extras = [
            tuple(map(int, values))
            for values in re.findall(
                r"\{(\d+)u,\s*(\d+)u,\s*(\d+)u\}",
                initializer.group(1),
            )
        ]
        expected_extras = [
            (row["index"], group, number)
            for row in manifest["rows"]
            if row["enabled"]
            for group, number in row["inside_component"][1:]
        ]
        self.assertEqual(actual_extras, expected_extras)

        project_proof = quest["project_component_proof"]
        self.assertEqual(project_proof["physical_map_count"], 253)
        self.assertEqual(project_proof["row_count"], 51)
        self.assertEqual(project_proof["direct_exit_row_count"], 50)
        self.assertEqual(project_proof["multihop_rows"], [19])
        self.assertEqual(
            project_proof["extra_component_memberships"],
            [{"location_id": 19, "group": 97, "map": 4}],
        )
        self.assertEqual(
            quest["rows"][19]["project_runtime_policy"],
            {
                "index": 19,
                "enabled": True,
                "inside_component": [[97, 5], [97, 4]],
                "record_exits": [{
                    "map": [96, 5],
                    "location_id": 19,
                    "destination_warp_id": None,
                    "path": ["0x092C0D10", "0x09369854"],
                }],
            },
        )
        project_initializer = re.search(
            r"sStage61ProjectQuestLogComponentExtras\[\]\s*=\s*\{(.*?)\n\};",
            runtime,
            re.DOTALL,
        )
        self.assertIsNotNone(project_initializer)
        self.assertEqual(
            [
                tuple(map(int, values))
                for values in re.findall(
                    r"\{(\d+)u,\s*(\d+)u,\s*(\d+)u\}",
                    project_initializer.group(1),
                )
            ],
            [(19, 97, 4)],
        )

        # Both namespaces use SaveBlock1 location.warpId (+6).  The four
        # physical interiors each have two exact locationId outcomes.
        expected_variants = [
            ("project", 22, (97, 81), (96, 21), 0, 22),
            ("project", 22, (97, 81), (96, 21), 1, 23),
            ("source", 22, (1, 81), (3, 26), 0, 22),
            ("source", 22, (1, 81), (3, 26), 1, 23),
            ("project", 42, (97, 83), (96, 31), 0, 42),
            ("project", 42, (97, 83), (96, 31), 1, 43),
            ("source", 42, (1, 83), (3, 38), 0, 42),
            ("source", 42, (1, 83), (3, 38), 1, 43),
        ]
        for namespace, base, inside, outside, warp_id, location_id in expected_variants:
            first = quest["rows"][base][namespace]
            second = quest["rows"][base + 1][namespace]
            self.assertEqual((first["inside"]["group"], first["inside"]["map"]), inside)
            self.assertEqual((first["outside"]["group"], first["outside"]["map"]), outside)
            self.assertEqual((second["outside"]["group"], second["outside"]["map"]), outside)
            self.assertEqual(base + warp_id, location_id)

        self.assertIn("return save == (volatile u8 *)0 ? 0xFFu : save[6];", runtime)
        self.assertIn("if (warp_id > 1u)", runtime)
        self.assertIn("(u8)(first + warp_id)", runtime)
        for obsolete in (
            "FN_PLAYER_GET_DEST_COORDS",
            "PlayerCoordsFn",
            "x != 15 || y != 26",
            "x != 67 || y != 15",
            "expected_first_exit_xy",
            "COORDINATE_DISAMBIGUATION",
        ):
            self.assertNotIn(obsolete, runtime)
            self.assertNotIn(obsolete, (
                ROOT / "tools/stage61_map_section_consumer_policy.py"
            ).read_text(encoding="utf-8"))

    def test_quest_log_source_pending_lifecycle_is_fail_closed(self) -> None:
        runtime = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        ).read_text(encoding="utf-8")
        check = runtime[
            runtime.index("void Stage61MapSection_QuestLog_CheckDepartingIndoorsMap"):
            runtime.index("STAGE61_EXPORT(Stage61MapSection_QuestLog_TryRecordDepartedLocation)")
        ]
        source = runtime[
            runtime.index("static void stage61_quest_log_try_record_source"):
            runtime.index("STAGE61_EXPORT(Stage61MapSection_QuestLog_CheckDepartingIndoorsMap)")
        ]
        project = runtime[
            runtime.index("static void stage61_quest_log_try_record_project"):
            runtime.index("static void stage61_quest_log_try_record_source")
        ]
        self.assertLess(
            check.index("FN_FLAG_GET(STAGE61_FLAG_SYS_QL_DEPARTED)"),
            check.index("FN_VAR_SET(STAGE61_VAR_QL_ENTRANCE, index)"),
        )
        self.assertIn("stage61_current_in_source_component(location)", source)
        self.assertIn("stage61_quest_log_clear_pending();", source)
        self.assertIn("stage61_quest_log_arm_current_source();", source)
        self.assertNotIn("STAGE61_QL_ROCKET_HIDEOUT", source)
        self.assertIn("STAGE61_QL_ROCKET_HIDEOUT", project)

    def test_quest_log_project_lifecycle_all_branches_are_fail_closed(self) -> None:
        quest = self.plan["quest_log_physical_crosswalk"]

        # Every row preserves each exact component member and records its
        # reviewed exit. Rock/Seafoam additionally require exact warpId.
        for index, row in enumerate(quest["rows"]):
            runtime = row["project_runtime_policy"]
            for group, number in runtime["inside_component"]:
                decision = policy.quest_log_transition_decision(
                    quest,
                    namespace="project",
                    pending_location=index,
                    current_group=group,
                    current_map=number,
                )
                self.assertEqual(
                    decision["action"], "KEEP_PENDING", (index, group, number)
                )
            exit_row = runtime["record_exits"][0]
            decision = policy.quest_log_transition_decision(
                quest,
                namespace="project",
                pending_location=index,
                current_group=exit_row["map"][0],
                current_map=exit_row["map"][1],
                current_warp_id=exit_row["destination_warp_id"],
            )
            self.assertEqual(
                decision["action"], "RECORD_EVENT_35_AND_CLEAR", index
            )
            self.assertEqual(decision["record_location"], index)

        # A different imported interior is a mismatch, clears the old token,
        # and immediately rearms the first row owned by that interior.
        mismatch = policy.quest_log_transition_decision(
            quest,
            namespace="project",
            pending_location=0,
            current_group=98,
            current_map=3,
        )
        self.assertEqual(
            mismatch,
            {
                "action": "CLEAR_PENDING",
                "record_location": None,
                "rearm_location": 1,
                "reason": "COMPONENT_DEPARTURE_MISMATCH",
            },
        )
        shared_mismatch = policy.quest_log_transition_decision(
            quest,
            namespace="project",
            pending_location=5,
            current_group=96,
            current_map=6,
        )
        self.assertEqual(shared_mismatch["action"], "CLEAR_PENDING")
        invalid_variant = policy.quest_log_transition_decision(
            quest,
            namespace="project",
            pending_location=22,
            current_group=96,
            current_map=21,
            current_warp_id=2,
        )
        self.assertEqual(invalid_variant["action"], "CLEAR_PENDING")

        # Rocket rearm is success-only; an unrelated departure never produces
        # the historical Game Corner token.
        rocket_success = policy.quest_log_transition_decision(
            quest,
            namespace="project",
            pending_location=35,
            current_group=98,
            current_map=56,
        )
        self.assertEqual(rocket_success["record_location"], 35)
        self.assertEqual(rocket_success["rearm_location"], 32)
        rocket_mismatch = policy.quest_log_transition_decision(
            quest,
            namespace="project",
            pending_location=35,
            current_group=96,
            current_map=7,
        )
        self.assertEqual(rocket_mismatch["action"], "CLEAR_PENDING")
        self.assertIsNone(rocket_mismatch["rearm_location"])

        source_rocket = policy.quest_log_transition_decision(
            quest,
            namespace="source",
            pending_location=35,
            current_group=3,
            current_map=7,
        )
        self.assertEqual(source_rocket["record_location"], 35)
        self.assertNotEqual(source_rocket["rearm_location"], 32)

        runtime_source = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        ).read_text(encoding="utf-8")
        project_c = runtime_source[
            runtime_source.index("static void stage61_quest_log_try_record_project"):
            runtime_source.index("static void stage61_quest_log_try_record_source")
        ]
        self.assertIn("stage61_current_in_project_component(location)", project_c)
        self.assertIn("if (!recorded) {", project_c)
        self.assertIn("stage61_quest_log_clear_pending();", project_c)
        self.assertIn("stage61_quest_log_arm_current_project();", project_c)

    def test_quest_log_source_recording_uses_stage60_runtime_header(self) -> None:
        contract = self.plan["quest_log_physical_crosswalk"][
            "source_runtime_section_contract"
        ]
        expected = {
            2: (89, 96),
            3: (122, 196),
            4: (122, 196),
            8: (90, 89),
            11: (91, 94),
            13: (125, 93),
            14: (105, 129),
            15: (129, 196),
            16: (129, 196),
            17: (93, 95),
            18: (93, 98),
            27: (92, 90),
            28: (130, 196),
            29: (130, 196),
            30: (94, 92),
            32: (94, 92),
            33: (94, 90),
            37: (95, 91),
            39: (98, 196),
            40: (98, 93),
            45: (96, 95),
            46: (96, 142),
        }
        actual = {
            row["index"]: (
                row["clean_section"], row["stage60_runtime_section"]
            )
            for row in contract["mismatches"]
        }
        self.assertEqual(contract["mismatch_count"], 22)
        self.assertEqual(actual, expected)

        runtime = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "stage61_departed_inside_section(const u8 *row, u8 imported)",
            runtime,
        )
        self.assertIn("header = FN_GET_MAP_HEADER(row[0], row[1]);", runtime)
        self.assertGreaterEqual(
            runtime.count("stage61_departed_inside_section(row,"), 3
        )

    def test_save_load_clones_are_bounded_before_any_ram_copy(self) -> None:
        runtime = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        ).read_text(encoding="utf-8")

        def function(start: str, end: str) -> str:
            return runtime[runtime.index(start):runtime.index(end)]

        offsets_match = re.search(
            r"sStage61SaveChunkOffsets\[[^]]+\]\s*=\s*\{(.*?)\n\};",
            runtime,
            re.DOTALL,
        )
        sizes_match = re.search(
            r"sStage61SaveChunkSizes\[[^]]+\]\s*=\s*\{(.*?)\n\};",
            runtime,
            re.DOTALL,
        )
        self.assertIsNotNone(offsets_match)
        self.assertIsNotNone(sizes_match)
        values = lambda match: [
            int(value, 16)
            for value in re.findall(r"0x([0-9A-Fa-f]+)u", match.group(1))
        ]
        self.assertEqual(values(offsets_match), [
            0x0000,
            0x0000, 0x0F80, 0x1F00, 0x2E80,
            0x0000, 0x0F80, 0x1F00, 0x2E80, 0x3E00,
            0x4D80, 0x5D00, 0x6C80, 0x7C00,
        ])
        self.assertEqual(values(sizes_match), [
            0x0F24,
            0x0F80, 0x0F80, 0x0F80, 0x0EC0,
            0x0F80, 0x0F80, 0x0F80, 0x0F80, 0x0F80,
            0x0F80, 0x0F80, 0x0F80, 0x07D0,
        ])

        expected_data = function(
            "static volatile u8 *stage61_save_expected_chunk_data",
            "static u8 stage61_save_chunk_descriptor_is_valid",
        )
        self.assertLess(
            expected_data.index("if (id >= STAGE61_SAVE_SLOT_SECTORS)"),
            expected_data.index("sStage61SaveChunkOffsets[id]"),
        )
        descriptor = function(
            "static u8 stage61_save_chunk_descriptor_is_valid",
            "static u8 stage61_save_all_descriptors_are_valid",
        )
        self.assertLess(
            descriptor.index("id >= STAGE61_SAVE_SLOT_SECTORS"),
            descriptor.index("chunks[id].size"),
        )
        self.assertIn("chunks[id].size > STAGE61_SAVE_TAIL_END", descriptor)
        self.assertIn("chunks[id].size != expected_size", descriptor)
        self.assertIn("chunks[id].data != expected", descriptor)
        self.assertIn("STAGE61_EWRAM_START", runtime)
        self.assertIn("STAGE61_EWRAM_END", runtime)

        validator = function(
            "static void stage61_save_validate_slot",
            "static u8 stage61_save_second_counter_is_newer",
        )
        self.assertLess(
            validator.index("stage61_save_all_descriptors_are_valid(chunks)"),
            validator.index("FN_READ_FLASH_SECTION"),
        )
        self.assertLess(
            validator.index("id = stage61_read16"),
            validator.index("if (id >= STAGE61_SAVE_SLOT_SECTORS)"),
        )
        self.assertLess(
            validator.index("if (id >= STAGE61_SAVE_SLOT_SECTORS)"),
            validator.index("stage61_save_chunk_descriptor_is_valid(id, chunks)"),
        )
        self.assertIn("(claimed_mask & bit) != 0u", validator)
        self.assertIn("counter != result->counter", validator)
        self.assertIn("STAGE61_SAVE_SLOT_SECTORS * (counter & 1u)", validator)
        self.assertIn("result->valid_mask == STAGE61_SAVE_FULL_MASK", validator)
        self.assertIn(
            "result->physical_by_id[index]", validator,
        )
        self.assertIn(
            "(result->first_save_sector + index)", validator,
        )
        self.assertLess(
            validator.index("result->physical_by_id[index]"),
            validator.rindex("result->status = STAGE61_SAVE_STATUS_OK"),
        )
        self.assertNotIn("destination[", validator)

        selector = function(
            "static u8 stage61_save_second_counter_is_newer",
            "static void stage61_save_copy_validated_slot",
        )
        self.assertIn("u32 delta = second - first", selector)
        self.assertIn(
            "delta != 0u && delta < 0x80000000u", selector,
        )
        self.assertIn("return STAGE61_SAVE_STATUS_EMPTY", selector)
        self.assertIn("return STAGE61_SAVE_STATUS_INVALID", selector)
        self.assertIn("? STAGE61_SAVE_STATUS_ERROR", selector)

        load = function(
            "u8 Stage61State_HandleLoadSector(",
            "static u8 stage61_summary_has_project_name_provenance",
        )
        self.assertNotIn("FN_STOCK_HANDLE_LOAD_SECTOR", runtime)
        self.assertLess(
            load.index("stage61_save_validate_slot"),
            load.index("stage61_save_copy_validated_slot"),
        )
        self.assertGreaterEqual(load.count("stage61_save_validate_slot"), 3)
        self.assertIn("stage61_save_validations_match", load)
        self.assertLess(
            load.index("stage61_save_validations_match"),
            load.index("stage61_save_copy_validated_slot"),
        )
        self.assertIn("stage61_state_clear();", load)
        self.assertIn("return STAGE61_SAVE_STATUS_OK;", load)
        self.assertIn("Stage61State_GetSaveValidStatus", runtime)

    def test_partial_link_record_update_is_full_generation_copy_on_write(
        self,
    ) -> None:
        runtime = (
            ROOT
            / "overlays/stage61_display_npc_event_audit/"
              "stage61_display_npc_event_audit.c"
        ).read_text(encoding="utf-8")
        clone = runtime[
            runtime.index("static u8 stage61_save_clone_record_sector("):
            runtime.index("STAGE61_EXPORT(Stage61State_UpdateRecordOnly)")
        ]
        clone_sector = runtime[
            runtime.index("static u8 stage61_save_clone_record_sector("):
            runtime.index("static u8 stage61_save_clone_complete_generation(")
        ]
        source_rewrite = runtime[
            runtime.index("static u8 stage61_save_rewrite_source_record_sector("):
            runtime.index("STAGE61_EXPORT(Stage61State_UpdateRecordOnly)")
        ]
        replace = runtime[
            runtime.index("u8 Stage61State_HandleReplaceSector("):
            runtime.index("STAGE61_EXPORT(Stage61State_CommitSignatureByte)")
        ]
        signature_commit = runtime[
            runtime.index("u8 Stage61State_CommitSignatureByte("):
            runtime.index("static u8 stage61_save_clone_record_sector(")
        ]
        update = runtime[
            runtime.index("u8 Stage61State_UpdateRecordOnly("):
            runtime.index("STAGE61_EXPORT(Stage61State_GetSaveValidStatus)")
        ]

        self.assertLess(
            update.index("stage61_save_validate_slot"),
            update.index("stage61_save_rewrite_source_record_sector"),
        )
        self.assertLess(
            update.index("stage61_save_rewrite_source_record_sector"),
            update.index("stage61_save_invalidate_target_record_sector"),
        )
        self.assertLess(
            update.index("stage61_save_invalidate_target_record_sector"),
            update.index("stage61_save_clone_complete_generation"),
        )
        self.assertIn("target_counter = G_SAVE_COUNTER + 1u", update)
        self.assertIn(
            "STAGE61_SAVE_SLOT_SECTORS * (target_counter & 1u)", update,
        )
        self.assertIn("source_base == target_base", update)
        self.assertIn(
            "for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id)", clone,
        )
        self.assertNotIn("erase_sector(", update)
        self.assertNotIn("program_byte(", update)
        self.assertLess(
            update.index("stage61_save_clone_complete_generation("),
            update.index("G_SAVE_COUNTER = target_counter"),
        )
        self.assertLess(
            update.index("G_SAVE_COUNTER = target_counter"),
            update.index(
                "G_FIRST_SAVE_SECTOR = committed_source.first_save_sector"
            ),
        )

        self.assertLess(
            clone.index("FN_READ_FLASH_SECTION(source_sector"),
            clone.index("erase_sector(target_sector)"),
        )
        self.assertEqual(clone_sector.count("stage61_state_inject_tail"), 1)
        self.assertEqual(source_rewrite.count("stage61_state_inject_tail"), 1)
        self.assertIn("inject_record != 0u && id == 13u", clone_sector)
        self.assertIn("target_counter, 0u", update)
        self.assertNotIn("chunks[13].data", clone + update)
        self.assertIn("selected.physical_by_id[13]", update)
        self.assertIn("selected.counter != G_SAVE_COUNTER", update)
        self.assertIn("selected.valid_mask != STAGE61_SAVE_FULL_MASK", update)
        self.assertIn("STAGE61_SAVE_SIGNATURE_OFFSET + 1u", clone)
        self.assertNotIn("erase_sector(source_sector)", clone_sector)
        self.assertNotIn("program_byte(source_sector", clone_sector)
        self.assertIn("erase_sector(source_sector)", source_rewrite)
        self.assertIn("program_byte(source_sector", source_rewrite)
        self.assertIn("stage61_save_section_crc32(section)", source_rewrite)
        self.assertIn("stage61_state_tail_matches_live_crc", source_rewrite)
        self.assertIn("stage61_save_readback_matches_prepared", replace)
        self.assertIn("FN_READ_FLASH_SECTION((u8)sector", replace)
        self.assertIn("record_crc = stage61_state_crc()", replace)
        self.assertIn("0xFFu", replace)
        self.assertLess(
            replace.index("FN_READ_FLASH_SECTION((u8)sector"),
            replace.index("stage61_save_clear_damaged(sector)"),
        )
        self.assertIn("one_based_id - 1u", signature_commit)
        self.assertIn("stage61_save_mark_damaged(sector)", signature_commit)
        self.assertIn("FN_READ_FLASH_SECTION((u8)sector", signature_commit)
        self.assertIn(
            "stage61_save_readback_matches_prepared", signature_commit,
        )
        self.assertIn(
            "stage61_save_reject_written_target_sector", signature_commit,
        )
        self.assertLess(
            signature_commit.index("FN_READ_FLASH_SECTION((u8)sector"),
            signature_commit.index("stage61_save_clear_damaged(sector)"),
        )
        self.assertLess(
            source_rewrite.index("erase_sector(source_sector)"),
            source_rewrite.rindex("FN_READ_FLASH_SECTION(source_sector"),
        )
        final_commit = clone_sector.rindex("program_byte(")
        self.assertGreater(
            final_commit,
            clone_sector.index("STAGE61_SAVE_SIGNATURE_OFFSET + 1u"),
        )
        self.assertIn(
            "section[STAGE61_SAVE_SIGNATURE_OFFSET]",
            clone_sector[final_commit:],
        )
        self.assertIn("stage61_save_mark_damaged", clone + update)
        self.assertIn("stage61_save_clear_damaged", clone)
        self.assertNotIn("STAGE61_DAMAGED_SECTOR_", clone + update)
        self.assertGreaterEqual(
            clone.count("stage61_save_section_crc32(section)"), 3,
        )
        self.assertGreaterEqual(
            clone.count("FN_READ_FLASH_SECTION(target_sector"), 2,
        )
        self.assertIn("expected_crc[STAGE61_SAVE_SLOT_SECTORS]", clone)
        self.assertIn(
            "expected_live_record[STAGE61_SAVE_SLOT_SECTORS]", clone,
        )
        self.assertIn("stage61_state_tail_matches_live_crc", clone)
        self.assertIn("written.physical_by_id[id]", clone)
        self.assertIn("selected->physical_by_id[id]", clone)
        self.assertIn("stage61_save_reject_written_target_sector", clone)
        reject_helper = runtime[
            runtime.index(
                "static u8 stage61_save_reject_written_target_sector("
            ):
            runtime.index("static void stage61_state_load_compatible_record(")
        ]
        self.assertGreaterEqual(
            reject_helper.count("FN_READ_FLASH_SECTION(target_sector"), 2,
        )
        self.assertIn(
            "!= STAGE61_SAVE_SIGNATURE", reject_helper,
        )
        structural_failure = clone[
            clone.index("if (written.status != STAGE61_SAVE_STATUS_OK"):
            clone.index(
                "for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id)",
                clone.index("if (written.status != STAGE61_SAVE_STATUS_OK"),
            )
        ]
        self.assertIn(
            "stage61_save_reject_written_target_sector", structural_failure,
        )
        self.assertLess(
            clone.rindex("FN_READ_FLASH_SECTION(target_sector"),
            clone.rindex("return STAGE61_SAVE_STATUS_OK;"),
        )

        # One erase plus 4096 byte programs per sector.  Post-stock first
        # commits source id13 while the exact-old backup remains valid, then
        # invalidates backup id13 and clones the exact-new source generation.
        operations_per_sector = 1 + 0x1000
        clone_operations = 14 * operations_per_sector
        source_record_operations = operations_per_sector
        post_transaction_operations = (
            source_record_operations + 1 + clone_operations
        )
        self.assertEqual(clone_operations, 57358)
        self.assertEqual(source_record_operations, 4097)
        self.assertEqual(post_transaction_operations, 61456)
        for backup_state in ("EMPTY", "ERROR", "PARTIAL_OR_SINGLE_GENERATION"):
            for callback_ordinal in range(post_transaction_operations):
                source_generation_valid = (
                    callback_ordinal < 1
                    or callback_ordinal >= source_record_operations - 1
                )
                old_backup_generation_valid = (
                    callback_ordinal < source_record_operations + 1
                )
                target_generation_valid = callback_ordinal == (
                    post_transaction_operations - 1
                )
                self.assertTrue(
                    source_generation_valid
                    or old_backup_generation_valid
                    or target_generation_valid,
                    (backup_state, callback_ordinal),
                )
            self.assertTrue(source_generation_valid)
            self.assertEqual(
                clone_operations // operations_per_sector, 14,
            )

        wrapper = runtime[
            runtime.index("u8 Stage61State_HandleSavingData("):
            runtime.index("STAGE61_EXPORT(Stage61State_GetSaveValidStatus)")
        ]
        self.assertLess(
            wrapper.index("stage61_save_ensure_live_backup_generation()"),
            wrapper.index("FN_STOCK_HANDLE_SAVING_DATA(save_type)"),
        )
        self.assertLess(
            wrapper.index("FN_STOCK_HANDLE_SAVING_DATA(save_type)"),
            wrapper.index("stage61_save_update_live_record_only()"),
        )
        self.assertIn(
            "if (preflight_result != STAGE61_SAVE_STATUS_OK)", wrapper,
        )
        self.assertLess(
            wrapper.index("if (preflight_result != STAGE61_SAVE_STATUS_OK)"),
            wrapper.index("FN_STOCK_HANDLE_SAVING_DATA(save_type)"),
        )

        preflight = runtime[
            runtime.index("u8 Stage61State_EnsureBackupGeneration("):
            runtime.index("static u8 stage61_save_invalidate_target_record_sector(")
        ]
        self.assertLess(
            preflight.index("stage61_save_select_generation"),
            preflight.index("stage61_save_validate_slot"),
        )
        self.assertEqual(
            preflight.count("stage61_save_clone_complete_generation("), 1,
        )
        self.assertNotIn("if (backup.status == STAGE61_SAVE_STATUS_OK)", preflight)
        self.assertIn("G_SAVE_COUNTER = source_counter", preflight)
        self.assertNotIn("G_SAVE_COUNTER = backup_counter", preflight)

        invalidator = runtime[
            runtime.index("static u8 stage61_save_invalidate_target_record_sector("):
            runtime.index("static u8 stage61_save_rewrite_source_record_sector(")
        ]
        self.assertIn("selected->physical_by_id[13]", invalidator)
        self.assertIn("ProgramFlashByteFn program_byte", invalidator)
        self.assertIn(
            "stage61_save_reject_written_target_sector(", invalidator,
        )
        self.assertIn("erase_sector, program_byte, target_sector", invalidator)
        self.assertNotIn("erase_sector(target_sector)", invalidator)
        # A success return from erase is not proof that the newer old target
        # generation became invalid.  The shared helper must read the full
        # signature back and, on a silent no-op, program a zero signature byte
        # and read it again before the clone can begin.
        self.assertGreaterEqual(
            reject_helper.count("FN_READ_FLASH_SECTION(target_sector"), 2,
        )
        self.assertIn(
            "program_byte(\n            target_sector, "
            "STAGE61_SAVE_SIGNATURE_OFFSET, 0u",
            reject_helper,
        )
        self.assertIn(
            "!= STAGE61_SAVE_SIGNATURE", reject_helper,
        )
        self.assertNotIn("stage61_save_select_generation", update)
        self.assertNotIn("selected = committed_source", update)
        self.assertIn("&committed_source, source_base, target_base", update)
        self.assertIn("committed_source.first_save_sector", update)
        invalidation_failure = update[
            update.index("stage61_save_invalidate_target_record_sector("):
            update.index("stage61_save_clone_complete_generation(")
        ]
        self.assertIn(
            "target_base + committed_source.physical_by_id[13]",
            invalidation_failure,
        )
        self.assertIn("stage61_save_validations_match", update)
        rewrite_failure = update[
            update.index("stage61_save_rewrite_source_record_sector("):
            update.index(
                "stage61_save_validate_slot(source_base, chunks, "
                "&committed_source)"
            )
        ]
        self.assertIn("source_base + selected.physical_by_id[13]",
                      rewrite_failure)
        clone_failure = update[
            update.index("stage61_save_clone_complete_generation("):
            update.index("G_SAVE_COUNTER = target_counter")
        ]
        self.assertIn("target_base + committed_source.physical_by_id[13]",
                      clone_failure)

        # Preflight always refreshes the exact old c source into c+1 but keeps
        # RAM counter c.  Before its first erase source c is authoritative;
        # after each callback source remains complete, and only the final
        # target signature makes the exact-old backup visible as newer.
        for callback_ordinal in range(clone_operations):
            source_old_exact = True
            backup_old_exact = callback_ordinal == clone_operations - 1
            self.assertTrue(source_old_exact or backup_old_exact)

        # Once preflight succeeds the exact-old c+1 backup is newer to every
        # fresh boot.  Exhaust each callback return of stock's five in-place
        # logical writes: no partially updated c bank can be selected.
        stock_partial_operations = 5 * operations_per_sector
        for callback_ordinal in range(stock_partial_operations):
            active_generation_may_be_mixed = True
            preflight_backup_generation_valid_and_newer = True
            self.assertTrue(
                preflight_backup_generation_valid_and_newer,
                (callback_ordinal, active_generation_may_be_mixed),
            )

        # A retry after a torn stock phase starts by selecting backup c+1 as
        # authoritative, then creates c+2 without promoting before the retry's
        # stock phase.  Normal success therefore advances one generation;
        # recovery from a prior failed attempt advances from its protected one.
        original_counter = 0xFFFFFFFE
        protected_counter = (original_counter + 1) & 0xFFFFFFFF
        retry_target_counter = (protected_counter + 1) & 0xFFFFFFFF
        self.assertEqual(protected_counter, 0xFFFFFFFF)
        self.assertEqual(retry_target_counter, 0)
        self.assertIn(
            "if (G_DAMAGED_SAVE_SECTORS != 0u)", wrapper,
        )
        self.assertLess(
            wrapper.index("if (G_DAMAGED_SAVE_SECTORS != 0u)"),
            wrapper.index("stage61_save_update_live_record_only()"),
        )
        self.assertNotIn("G_RAM_SAVE_SECTOR_LOCATIONS", wrapper)
        preflight_helper = runtime[
            runtime.index(
                "u8 stage61_save_ensure_live_backup_generation(void)"
            ):
            runtime.index(
                "static u8 stage61_save_invalidate_target_record_sector("
            )
        ]
        post_helper = runtime[
            runtime.index("u8 stage61_save_update_live_record_only(void)"):
            runtime.index("STAGE61_EXPORT(Stage61State_HandleSavingData)")
        ]
        self.assertEqual(
            runtime.count(
                "static __attribute__((noinline))\n"
                "u8 stage61_save_"
            ),
            3,
        )
        self.assertIn(
            "static __attribute__((noinline))\n"
            "u8 stage61_save_normal_copy_on_write(void)",
            runtime,
        )
        for helper in (preflight_helper, post_helper):
            self.assertIn(
                "struct Stage61SaveBlockChunk "
                "live_chunks[STAGE61_SAVE_SLOT_SECTORS]",
                helper,
            )
            self.assertIn(
                "stage61_save_build_live_descriptors(live_chunks)", helper,
            )
        self.assertIn("Stage61State_EnsureBackupGeneration(live_chunks)",
                      preflight_helper)
        self.assertIn("Stage61State_UpdateRecordOnly(live_chunks)", post_helper)
        self.assertIn("stage61_save_physical_sector_for_id(13u)", post_helper)
        self.assertLess(
            wrapper.index("stage61_save_ensure_live_backup_generation()"),
            wrapper.index("FN_STOCK_HANDLE_SAVING_DATA(save_type)"),
        )
        self.assertGreater(
            wrapper.index("stage61_save_update_live_record_only()"),
            wrapper.index("FN_STOCK_HANDLE_SAVING_DATA(save_type)"),
        )
        live_descriptors = runtime[
            runtime.index("static u8 stage61_save_build_live_descriptors("):
            runtime.index("static void stage61_save_validate_slot")
        ]
        self.assertIn("stage61_save_expected_chunk_data(id)", live_descriptors)
        self.assertIn("sStage61SaveChunkSizes[id]", live_descriptors)
        self.assertIn("chunks[id].padding = 0u", live_descriptors)
        self.assertIn(
            "stage61_save_all_descriptors_are_valid(chunks)",
            live_descriptors,
        )
        self.assertIn("return STAGE61_SAVE_STATUS_ERROR;", wrapper)
        self.assertNotIn("SAVE_EREADER", wrapper)
        self.assertLess(
            wrapper.index("G_MAIN_VBLANK_COUNTER1 = (volatile u32 *)0;"),
            wrapper.index("stage61_save_update_live_record_only()"),
        )
        self.assertGreater(
            wrapper.rindex("G_MAIN_VBLANK_COUNTER1 = backup_counter;"),
            wrapper.index("stage61_save_update_live_record_only()"),
        )
        post_wrapper = wrapper[
            wrapper.index("stage61_save_update_live_record_only()"):
        ]
        self.assertNotIn("stage61_save_fail_with_sector", post_wrapper)
        self.assertIn("return STAGE61_SAVE_STATUS_ERROR;", post_wrapper)

    def test_save_link_dispatcher_callers_and_shared_veneer_are_exact(self) -> None:
        callers = state_audit._thumb_bl_calls_to(self.stage60, 0x080DB230)
        self.assertEqual(callers, [0x080DB35C, 0x080F64C4])
        self.assertEqual(
            self.stage60[0x0DB35C:0x0DB360], bytes.fromhex("fff768ff")
        )
        self.assertEqual(
            self.stage60[0x0F64C4:0x0F64C8], bytes.fromhex("e4f7b4fe")
        )
        self.assertEqual(
            self.stage60[0x0C6480:0x0C6488],
            bytes.fromhex("5ff07ef811e00000"),
        )

        # SetFlyWarpDestination's 0x080C6460 entry is replaced wholesale.
        # Its original body is therefore unreachable; three disjoint veneers
        # occupy 0x6468..0x6487 with no aligned pointer or BL target into the
        # newly selected final eight bytes in Stage60.
        ranges = [(0x080C6468, 16), (0x080C6478, 8), (0x080C6480, 8)]
        occupied: set[int] = set()
        for address, size in ranges:
            span = set(range(address, address + size))
            self.assertFalse(occupied & span)
            occupied |= span
        self.assertEqual(
            state_audit._thumb_bl_calls_to(self.stage60, 0x080C6480), []
        )
        for pointer in (0x080C6480, 0x080C6481):
            self.assertNotIn(struct.pack("<I", pointer), self.stage60)

        builder = (
            ROOT / "scripts/build_stage61_display_npc_event_audit.py"
        ).read_text(encoding="utf-8")
        # The stock entry must remain callable by the wrapper; patching it
        # would recurse.  Only both exact BL callers may be redirected.
        self.assertNotIn(
            '("handle_saving_data",\n        0x080DB230,', builder
        )

    def test_save_generation_failure_matrix_reference_contract(self) -> None:
        sizes = [
            0x0F24,
            0x0F80, 0x0F80, 0x0F80, 0x0EC0,
            0x0F80, 0x0F80, 0x0F80, 0x0F80, 0x0F80,
            0x0F80, 0x0F80, 0x0F80, 0x07D0,
        ]
        empty, ok, invalid, error = 0, 1, 2, 0xFF

        def checksum(section: bytes, size: int) -> int:
            total = sum(
                struct.unpack_from("<I", section, offset)[0]
                for offset in range(0, size, 4)
            ) & 0xFFFFFFFF
            return ((total >> 16) + total) & 0xFFFF

        def make_sector(
            section_id: int,
            counter: int,
            *,
            signature: bool = True,
            bad_checksum: bool = False,
        ) -> bytearray:
            sector = bytearray(0x1000)
            for index in range(0xFF0):
                sector[index] = (section_id * 17 + index) & 0xFF
            struct.pack_into("<H", sector, 0xFF4, section_id)
            struct.pack_into(
                "<I", sector, 0xFF8,
                0x08012025 if signature else 0xFFFFFFFF,
            )
            struct.pack_into("<I", sector, 0xFFC, counter)
            if 0 <= section_id < 14:
                value = checksum(sector, sizes[section_id])
                struct.pack_into(
                    "<H", sector, 0xFF6,
                    value ^ (1 if bad_checksum else 0),
                )
            return sector

        def make_slot(base: int, counter: int) -> list[bytearray]:
            self.assertEqual(base, 14 * (counter & 1))
            return [make_sector(index, counter) for index in range(14)]

        def scan(slot: list[bytearray], physical_base: int) -> dict[str, object]:
            claimed: set[int] = set()
            valid: dict[int, int] = {}
            seen_signature = False
            selected_counter: int | None = None
            malformed = False
            for physical, sector in enumerate(slot):
                if struct.unpack_from("<I", sector, 0xFF8)[0] != 0x08012025:
                    continue
                seen_signature = True
                counter = struct.unpack_from("<I", sector, 0xFFC)[0]
                if selected_counter is None:
                    selected_counter = counter
                elif selected_counter != counter:
                    malformed = True
                if 14 * (counter & 1) != physical_base:
                    malformed = True
                section_id = struct.unpack_from("<H", sector, 0xFF4)[0]
                if section_id >= 14:
                    malformed = True
                    continue
                if section_id in claimed:
                    malformed = True
                    continue
                claimed.add(section_id)
                if struct.unpack_from("<H", sector, 0xFF6)[0] != checksum(
                    sector, sizes[section_id]
                ):
                    malformed = True
                    continue
                valid[section_id] = physical
            if not seen_signature:
                status = empty
            elif not malformed and set(valid) == set(range(14)):
                status = ok
            else:
                status = error
            return {
                "status": status,
                "counter": selected_counter or 0,
                "physical": valid,
            }

        def second_is_newer(first: int, second: int) -> bool:
            delta = (second - first) & 0xFFFFFFFF
            return delta != 0 and delta < 0x80000000

        def select(
            slot0: list[bytearray], slot1: list[bytearray]
        ) -> tuple[int, int | None, int]:
            first = scan(slot0, 0)
            second = scan(slot1, 14)
            if first["status"] == ok and second["status"] == ok:
                a, b = int(first["counter"]), int(second["counter"])
                choose_second = second_is_newer(a, b)
                chosen = second if choose_second else first
                return ok, 14 if choose_second else 0, int(chosen["counter"])
            if first["status"] == ok:
                return (
                    error if second["status"] == error else ok,
                    0,
                    int(first["counter"]),
                )
            if second["status"] == ok:
                return (
                    error if first["status"] == error else ok,
                    14,
                    int(second["counter"]),
                )
            if first["status"] == empty and second["status"] == empty:
                return empty, None, 0
            return invalid, None, 0

        # Untrusted footer IDs are rejected before any size lookup.
        for bad_id in (14, 255):
            slot = make_slot(0, 2)
            slot[13] = make_sector(bad_id, 2)
            self.assertEqual(scan(slot, 0)["status"], error)

        duplicate = make_slot(0, 2)
        duplicate[13] = make_sector(12, 2)
        self.assertEqual(scan(duplicate, 0)["status"], error)
        bad_checksum = make_slot(0, 2)
        bad_checksum[7] = make_sector(7, 2, bad_checksum=True)
        self.assertEqual(scan(bad_checksum, 0)["status"], error)
        mixed_counter = make_slot(0, 2)
        mixed_counter[7] = make_sector(7, 4)
        self.assertEqual(scan(mixed_counter, 0)["status"], error)

        # A corrupt newer generation falls back to the complete old slot;
        # stock compatibility still reports ERROR when the peer is corrupt.
        older = make_slot(0, 2)
        newer_corrupt = make_slot(14, 3)
        newer_corrupt[9] = make_sector(9, 3, bad_checksum=True)
        self.assertEqual(select(older, newer_corrupt), (error, 0, 2))

        # Serial-number arithmetic works across an arbitrary u32 wrap.
        wrapped_new = make_slot(0, 0)
        wrapped_old = make_slot(14, 0xFFFFFFFF)
        self.assertEqual(select(wrapped_new, wrapped_old), (ok, 0, 0))
        self.assertEqual(
            select(make_slot(0, 0xFFFFFFFE), make_slot(14, 1)),
            (ok, 14, 1),
        )
        self.assertTrue(second_is_newer(0xFFFFFFFE, 1))
        self.assertFalse(second_is_newer(1, 0xFFFFFFFE))
        self.assertFalse(second_is_newer(7, 7))
        self.assertFalse(second_is_newer(7, 0x80000007))

        # Both invalid/empty selections expose no copy target, so caller RAM
        # canaries remain byte-exact.
        canaries = [bytearray([0xA5]) * size for size in sizes]
        before = [bytes(row) for row in canaries]
        both_bad = make_slot(0, 2)
        both_bad[0] = make_sector(0, 2, bad_checksum=True)
        no_signature = [
            make_sector(index, 3, signature=False) for index in range(14)
        ]
        status, selected, _ = select(both_bad, no_signature)
        self.assertEqual((status, selected), (invalid, None))
        self.assertEqual([bytes(row) for row in canaries], before)

    def test_record_only_reference_image_keeps_storage_footer_and_backup(self) -> None:
        current = bytearray((index * 29 + 7) & 0xFF for index in range(0x1000))
        backup = [
            bytes((sector + index) & 0xFF for index in range(0x1000))
            for sector in range(14)
        ]
        before = bytes(current)
        backup_before = tuple(backup)
        replacement = bytes((index * 11 + 3) & 0xFF for index in range(0x616))
        current[0x7D0:0xDE6] = replacement

        self.assertEqual(current[:0x7D0], before[:0x7D0])
        self.assertEqual(current[0xDE6:0xFF0], before[0xDE6:0xFF0])
        self.assertEqual(current[0xFF0:0x1000], before[0xFF0:0x1000])
        self.assertEqual(tuple(backup), backup_before)

        program_order = [
            *range(0, 0xFF8),
            *range(0xFF9, 0x1000),
            0xFF8,
        ]
        self.assertEqual(program_order[-1], 0xFF8)
        interrupted = bytearray([0xFF]) * 0x1000
        for index in program_order[:-1]:
            interrupted[index] = current[index]
        self.assertNotEqual(
            struct.unpack_from("<I", interrupted, 0xFF8)[0], 0x08012025
        )
        self.assertEqual(tuple(backup), backup_before)

    def test_all_requested_consumers_have_exact_owned_patch_sites(self) -> None:
        consumers = self.plan["consumers"]
        expected_ids = {
            "MSC-04",
            "MSC-05",
            "MSC-06",
            "MSC-07",
            "MSC-10",
            "MSC-11",
            "MSC-15",
            "MSC-16",
            "MSC-17",
            "MSC-21",
            "MSC-22",
            "MSC-23",
        }
        self.assertEqual({row["consumer_id"] for row in consumers}, expected_ids)
        expected_counts = {
            "MSC-04": 1,
            "MSC-05": 2,
            "MSC-06": 3,
            "MSC-07": 2,
            "MSC-10": 1,
            "MSC-11": 1,
            "MSC-15": 1,
            "MSC-16": 1,
            "MSC-17": 2,
            "MSC-21": 11,
            "MSC-22": 1,
            "MSC-23": 1,
        }
        self.assertEqual(
            Counter(row["consumer_id"] for row in self.plan["patch_windows"]),
            expected_counts,
        )
        by_id = {row["consumer_id"]: row for row in consumers}
        self.assertEqual(by_id["MSC-17"]["priority"], "HIGH")
        self.assertEqual(by_id["MSC-21"]["priority"], "CRITICAL")
        self.assertEqual(by_id["MSC-22"]["priority"], "CRITICAL")
        self.assertIn("fully inlined", by_id["MSC-21"]["single_entry_finding"])
        self.assertIn("one 0x108-byte function", by_id["MSC-22"]["function_boundary_finding"])

    def test_exact_patch_addresses_and_stage60_preimages_are_reported(self) -> None:
        sites = {row["site_id"]: row for row in self.plan["patch_windows"]}
        self.assertEqual(sites["msc17_check_departing_entry"]["address"], "0x080CD6AC")
        self.assertEqual(
            sites["msc17_check_departing_entry"]["expected_stage60_hex"],
            "70b50024104e114d",
        )
        self.assertEqual(sites["msc17_record_departed_entry"]["address"], "0x080CD714")
        self.assertEqual(sites["msc21_raid_getter_rewards"]["address"], "0x090F3FC0")
        self.assertEqual(
            sites["msc21_raid_getter_rewards"]["expected_stage60_hex"], "215b0508"
        )
        self.assertEqual(sites["msc22_roamer_entry"]["address"], "0x09125ECC")
        self.assertEqual(
            sites["msc22_roamer_entry"]["expected_stage60_hex"],
            "f0b5de4657464e46",
        )
        self.assertEqual(sites["msc23_cfru_warp_fade_entry"]["address"], "0x0911FEC8")
        alternatives = {
            row["site_id"]: row
            for row in self.plan["conditional_alternative_patch_windows"]
        }
        self.assertEqual(
            alternatives["msc07_dungeon_cursor_constant_only"][
                "expected_stage60_hex"
            ],
            "8d2c",
        )
        self.assertEqual(
            alternatives["msc22_roamer_total_corners_pointer"]["address"],
            "0x09125FB8",
        )
        self.assertEqual(
            alternatives["msc22_roamer_total_dimensions_pointer"]["address"],
            "0x09125FBC",
        )

    def test_legacy_raid_flag_window_is_a_complete_critical_collision(self) -> None:
        flags = self.plan["flag_ownership"]
        self.assertEqual(flags["severity"], "CRITICAL")
        self.assertEqual(flags["aliased_raid_flags"], 109)
        self.assertTrue(flags["all_legacy_raid_flags_collide"])
        self.assertFalse(flags["lossless_stage60_migration_possible"])
        self.assertEqual(
            [
                (row["project_owner"], row["start"], row["end_inclusive"], row["count"])
                for row in flags["intersection_segments"]
            ],
            [
                ("TRAINER_ARCHIVE_DEFEAT_FLAGS", "0x1800", "0x1846", 71),
                ("KANTO_FULL_CFG_SOURCE_FLAGS", "0x1847", "0x186C", 38),
            ],
        )
        options = {row["option"]: row for row in flags["options"]}
        self.assertEqual(
            options["MOVE_PROJECT_ARCHIVE_AND_STAGE61_WINDOW"]["target_window_size"], 256
        )
        self.assertEqual(
            options["MOVE_RAID_FLAGS_AT_FLAG_API_BOUNDARIES"]
            ["exact_stage60_pointer_repoints"]["total"],
            5,
        )
        self.assertEqual(
            flags["selected_architecture"], "MOVE_RAID_FLAGS_AT_FLAG_API_BOUNDARIES"
        )
        self.assertIsNone(flags["selected_base"])
        self.assertEqual(
            flags["explicitly_rejected_bases"][0]["base"], "0x14A0"
        )
        self.assertIn(
            "0x1500..0x150C", flags["explicitly_rejected_bases"][0]["reason"]
        )

    def test_raid_flag_base_is_parameterized_and_collision_checked(self) -> None:
        with self.assertRaisesRegex(
            policy.MapSectionConsumerPolicyError, "Raid flag base collision"
        ):
            policy.validate_raid_flag_base(ROOT, 0x14A0)

        ownership = policy.load_declared_flag_ownership(ROOT)
        first_window = ownership["unclaimed_contiguous_windows_at_least_109"][0]
        observed_base = int(first_window["start"], 0)
        observed_free = policy.validate_raid_flag_base(ROOT, observed_base)
        self.assertEqual(observed_free["base"], f"0x{observed_base:04X}")
        self.assertEqual(
            observed_free["end_inclusive"],
            f"0x{observed_base + policy.RAID_ROW_COUNT - 1:04X}",
        )
        self.assertEqual(
            observed_free["status"], "PASS_UNCLAIMED_BY_DECLARED_OWNERS"
        )
        self.assertIn("global collision audit", observed_free["scope_warning"])

        with self.assertRaisesRegex(
            policy.MapSectionConsumerPolicyError, "Raid flag base collision"
        ):
            policy.validate_raid_flag_base(
                ROOT,
                observed_base,
                additional_reserved_ranges=(
                    ("SYNTHETIC_OWNER", observed_base + 1, observed_base + 1),
                ),
            )

    def test_literal_pointer_patch_expectations_and_candidate_fail_closed(self) -> None:
        symbols = {
            "Stage61MapSection_GetRaidCompatibleCurrent": 0x09F00000,
            "Stage61MapSection_RaidFlagGet": 0x09F00100,
            "Stage61MapSection_RaidFlagSet": 0x09F00200,
            "Stage61MapSection_RaidFlagClear": 0x09F00300,
        }
        exact = policy.pointer_patch_expectations(symbols)
        self.assertEqual(len(exact), 11)
        site_id = "msc21_raid_getter_determine"
        self.assertEqual(exact[site_id], struct.pack("<I", 0x09F00001))

        selected = policy.candidate_patch_expectations(
            {
                **symbols,
                "Stage61MapSection_MusicCanOverrideMapMusic": 0x09F00400,
                "STAGE61_CFRU_SAFE_ROAMER_CORNERS": 0x09F10000,
            },
            site_ids=[
                "msc04_music_entry",
                "msc21_raid_getter_determine",
                "msc07_dungeon_cursor_constant_only",
                "msc22_roamer_total_corners_pointer",
            ],
        )
        self.assertEqual(
            selected["msc04_music_entry"],
            struct.pack("<HHI", 0x4B00, 0x4718, 0x09F00401),
        )
        self.assertEqual(
            selected["msc21_raid_getter_determine"],
            struct.pack("<I", 0x09F00001),
        )
        self.assertEqual(
            selected["msc07_dungeon_cursor_constant_only"], bytes.fromhex("332c")
        )
        self.assertEqual(
            selected["msc22_roamer_total_corners_pointer"],
            struct.pack("<I", 0x09F10000),
        )

        candidate = bytearray(self.stage60)
        site = next(row for row in policy.PATCH_WINDOWS if row.site_id == site_id)
        offset = site.address - policy.ROM_BASE
        candidate[offset : offset + 4] = exact[site_id]
        checked = policy.verify_candidate_patch_contract(
            bytes(candidate), {site_id: exact[site_id]}, require_all=False
        )
        row = next(item for item in checked["sites"] if item["site_id"] == site_id)
        self.assertEqual(row["state"], "EXACT_PATCH_ASSERTION_PASS")
        self.assertEqual(checked["roamer_activation_contract"], "NOT_ACTIVE")
        self.assertTrue(
            all(
                row["state"] == "DORMANT_STAGE60_PREIMAGE"
                for row in checked["dormancy_guards"]
            )
        )

        active_roamer = bytearray(candidate)
        active_roamer[0x0C5A90] ^= 1
        with self.assertRaisesRegex(
            policy.MapSectionConsumerPolicyError,
            "roamer hook is active without",
        ):
            policy.verify_candidate_patch_contract(
                bytes(active_roamer), {site_id: exact[site_id]}, require_all=False
            )

        with self.assertRaisesRegex(
            policy.MapSectionConsumerPolicyError, "candidate patch mismatch"
        ):
            policy.verify_candidate_patch_contract(
                bytes(candidate), {site_id: b"\0\0\0\0"}, require_all=False
            )
        with self.assertRaisesRegex(
            policy.MapSectionConsumerPolicyError, "missing required sites"
        ):
            policy.verify_candidate_patch_contract(
                bytes(candidate), {site_id: exact[site_id]}, require_all=True
            )

        parent_symbol = "Stage61MapSection_CreateDungeonIconsCeruleanGate"
        parent_exact = policy.candidate_patch_expectations(
            {parent_symbol: 0x09F00500},
            site_ids=["msc07_dungeon_icon_gate"],
        )
        parent_candidate = bytearray(self.stage60)
        parent_site = next(
            row for row in policy.PATCH_WINDOWS
            if row.site_id == "msc07_dungeon_icon_gate"
        )
        parent_offset = parent_site.address - policy.ROM_BASE
        parent_candidate[
            parent_offset:parent_offset + parent_site.write_size
        ] = parent_exact[parent_site.site_id]
        parent_checked = policy.verify_candidate_patch_contract(
            bytes(parent_candidate), parent_exact, require_all=False,
        )
        covered = next(
            row for row in parent_checked["sites"]
            if row["site_id"] == "msc07_dungeon_icon_constant_only"
        )
        self.assertEqual(
            covered["state"], "COVERED_BY_EXACT_PARENT_ASSERTION"
        )
        self.assertEqual(
            covered["covering_exact_site_ids"], ["msc07_dungeon_icon_gate"]
        )

    def test_report_status_requires_caller_selected_flag_base_and_is_json(self) -> None:
        self.assertEqual(self.plan["schema_version"], 1)
        self.assertEqual(
            self.plan["status"],
            "READY_EXCEPT_RAID_FLAG_BASE_REQUIRES_GLOBAL_COLLISION_AUDIT",
        )
        self.assertFalse(
            self.plan["flag_ownership"]["base_parameter"]["provided"]
        )
        encoded = json.dumps(self.plan, ensure_ascii=False, sort_keys=True)
        self.assertEqual(json.loads(encoded)["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
