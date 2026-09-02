from __future__ import annotations

import copy
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tools.stage61_map_script_projection import (
    CATEGORY_NAME,
    GAMEPLAY_TOPOLOGY,
    MATERIALIZED_ALL_OPCODE_ALLOWLIST,
    MATERIALIZED_OPCODE_ALLOWLIST,
    PROJECTABLE_MAPS,
    ROM_BASE,
    SERVICE_GEOMETRY,
    STORY_GATED_GEOMETRY,
    Stage61MapScriptProjectionError,
    _extract_root_projection,
    build_projection_plan,
    build_projection_plan_from_paths,
    load_canonical_maps,
    materialize_projection,
)


ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
STAGE60 = ROOT / "build/stages/60_wild_species_root_repair.gba"
CANONICAL = ROOT / "generated/maps/kanto"
MAP_GROUPS = ROOT / "vendor/upstream/pokefirered/data/maps/map_groups.json"


class Stage61MapScriptProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = CLEAN.read_bytes()
        cls.stage60 = STAGE60.read_bytes()
        cls.canonical = load_canonical_maps(CANONICAL, MAP_GROUPS)
        cls.plan = build_projection_plan(
            cls.clean, cls.stage60, cls.canonical, require_ready=True,
        )
        required_flags = [
            int(row["source_id"], 0)
            for row in cls.plan["state_requirements"]["flags"]
        ]
        required_vars = [
            int(row["source_id"], 0)
            for row in cls.plan["state_requirements"]["vars"]
        ]
        persistent_flags = [source for source in required_flags if source > 0x1F]
        cls.flag_mapping = {
            **{source: source for source in required_flags if 0 < source <= 0x1F},
            **{source: 0x162D + index
               for index, source in enumerate(persistent_flags)},
        }
        cls.var_mapping = {
            source: 0x5151 + index for index, source in enumerate(required_vars)
        }
        cls.materialized = materialize_projection(
            cls.plan,
            payload_base=0x09E00000,
            flag_mapping=cls.flag_mapping,
            var_mapping=cls.var_mapping,
        )
        cls.projection_by_map = {
            row["physical_map"]: row for row in cls.plan["projections"]
        }

    def test_exact_95_table_classification(self) -> None:
        self.assertEqual(self.plan["status"], "READY")
        self.assertTrue(all(self.plan["assertions"].values()))
        self.assertEqual(len(self.plan["classification"]), 95)
        by_category = {
            category: {
                (row["group"], row["map"])
                for row in self.plan["classification"]
                if row["category"] == category
            }
            for category in CATEGORY_NAME
        }
        self.assertEqual(by_category["A"], set(GAMEPLAY_TOPOLOGY))
        self.assertEqual(by_category["B"], set(SERVICE_GEOMETRY))
        self.assertEqual(by_category["C"], set(STORY_GATED_GEOMETRY))
        self.assertEqual(len(by_category["D"]), 54)
        self.assertFalse(by_category["D"] & set(PROJECTABLE_MAPS | STORY_GATED_GEOMETRY))

    def test_every_table_has_root_opcode_and_condition_evidence(self) -> None:
        condition_rows = []
        roots = []
        entries = []
        for row in self.plan["classification"]:
            table = row["table"]
            self.assertTrue(table["table_pointer"].startswith("0x08"))
            self.assertGreater(table["entry_count"], 0)
            entries.extend(table["entries"])
            roots.extend(table["roots"])
            for entry in table["entries"]:
                self.assertIn(entry["tag"], range(1, 8))
                if entry["entry_kind"] == "CONDITION":
                    condition_rows.extend(entry["conditions"])
        self.assertEqual(len(entries), 184)
        self.assertEqual(len(condition_rows), 214)
        self.assertEqual(len({row["variable"] for row in condition_rows}), 16)
        self.assertEqual(len({root["root"] for root in roots}), 139)
        for root in roots:
            self.assertGreater(root["instruction_count"], 0)
            self.assertTrue(root["opcode_counts"])
            self.assertEqual(len(root["cfg_sha256"]), 64)

    def test_source_aggregate_evidence_is_exact(self) -> None:
        summary = self.plan["summary"]
        self.assertEqual(summary["source_table_entry_count"], 184)
        self.assertEqual(summary["source_root_field_count"], 346)
        self.assertEqual(summary["source_unique_root_count"], 139)
        self.assertEqual(summary["source_tag_counts"], {
            "1": 40, "2": 29, "3": 70, "4": 23, "5": 22,
        })
        self.assertEqual(summary["topology_map_count"], 41)
        self.assertEqual(summary["extractable_map_count"], 33)

    def test_A_B_IR_is_only_topology_and_source_tables_are_excluded(self) -> None:
        projectable = [
            row for row in self.plan["projections"] if row["category"] in {"A", "B"}
        ]
        self.assertEqual(len(projectable), 33)
        self.assertTrue(all(row["status"] == "EXTRACTABLE" for row in projectable))
        self.assertEqual(sum(len(row["root_projections"]) for row in projectable), 34)
        self.assertEqual(sum(row["projection_action_count"] for row in projectable), 293)
        for row in projectable:
            self.assertFalse(row["source_full_roots_imported"])
            self.assertFalse(row["source_conditional_tables_imported"])
            self.assertTrue(row["target_map_script_structure_empty"])
            for condition in row["excluded_condition_tables"]:
                self.assertEqual(
                    condition["reason"], "SOURCE_CONDITIONAL_TABLE_IS_NEVER_PROJECTED",
                )
            for root in row["root_projections"]:
                self.assertEqual(root["status"], "EXTRACTED")
                for action in root["actions"]:
                    self.assertIn(action["opcode"], {"0xA2", "0xA7"})
                    self.assertTrue(action["guard_alternatives"])

    def test_guard_extraction_is_exhaustive_not_a_flag_shortcut(self) -> None:
        victory = self.projection_by_map["097/039"]["root_projections"][0]
        self.assertEqual(victory["requirements"], {"flags": [], "vars": ["0x4064"]})
        expected_not_100 = [
            [{"kind": "VAR_LE", "source_var": "0x4064", "value": 99}],
            [{"kind": "VAR_GE", "source_var": "0x4064", "value": 101}],
        ]
        self.assertTrue(all(action["guard_alternatives"] == expected_not_100
                            for action in victory["actions"]))

        seafoam = self.projection_by_map["097/086"]["root_projections"][0]
        # 3 flags x the initialized temp counter's 3 equivalence classes are exhaustively
        # enumerated; minimization proves that the temp counter is not an external requirement.
        self.assertEqual(seafoam["equivalence_assignment_count"], 24)
        self.assertEqual(seafoam["requirements"]["vars"], [])
        self.assertEqual(seafoam["actions"][0]["guard_alternatives"], [
            [{"kind": "FLAG_SET", "source_flag": "0x02D2"}],
            [
                {"kind": "FLAG_CLEAR", "source_flag": "0x0046"},
                {"kind": "FLAG_CLEAR", "source_flag": "0x0047"},
            ],
        ])
        self.assertTrue(any(write["opcode"] == "0x29"
                            for write in seafoam["suppressed_source_writes"]))

        pc2f = self.projection_by_map["098/055"]["root_projections"][0]
        self.assertEqual(pc2f["requirements"], {"flags": [], "vars": ["0x406F"]})
        values = {
            predicate["value"]
            for action in pc2f["actions"]
            for guard in action["guard_alternatives"]
            for predicate in guard
            if predicate["kind"] == "VAR_EQ"
        }
        self.assertEqual(values, {1, 2, 3, 5, 6, 7, 8})

    def test_story_gated_maps_are_enumerated_fail_closed(self) -> None:
        blocked = [row for row in self.plan["projections"] if row["category"] == "C"]
        self.assertEqual(len(blocked), 8)
        self.assertEqual({row["physical_map"] for row in blocked}, {
            "097/042", "097/045", "097/075", "097/076",
            "097/077", "097/078", "098/007", "098/056",
        })
        for row in blocked:
            self.assertEqual(row["status"], "BLOCKED_STORY_BINDING_REQUIRED")
            self.assertFalse(row["root_projections"])
            self.assertIn(
                "SOURCE_STORY_STATE_MUST_NOT_BE_INFERRED_OR_IMPORTED",
                row["block_reasons"],
            )

    def test_seafoam_layouts_are_cloned_against_target_tileset_semantics(self) -> None:
        extension = self.plan["layout_extension"]
        self.assertEqual(extension["status"], "READY")
        self.assertEqual((extension["existing_count"], extension["expanded_count"]),
                         (563, 565))
        self.assertEqual(
            [(row["source_layout_id"], row["new_layout_id"],
              row["used_metatile_count"]) for row in extension["clones"]],
            [(0x116, 564, 93), (0x117, 565, 56)],
        )
        for clone in extension["clones"]:
            self.assertTrue(clone["all_used_metatiles_target_exact"])
            self.assertTrue(all(row["exact"] for row in clone["metatile_bindings"]))
            self.assertFalse(clone["source_pointer_reused"])
        installed = self.materialized["layout_installation"]
        self.assertEqual(installed["expanded_count"], 565)
        self.assertEqual([row["new_layout_id"] for row in installed["clones"]], [564, 565])
        self.assertEqual(installed["pointer_patch"]["address"], "0x08054A54")
        blob = bytes.fromhex(self.materialized["payload_raw_hex"])
        for clone in installed["clones"]:
            entry = struct.unpack_from("<I", blob, (clone["new_layout_id"] - 1) * 4)[0]
            self.assertEqual(entry, int(clone["layout_pointer"], 0))

    def test_materialized_payload_is_project_owned_and_denylisted_commands_absent(self) -> None:
        result = self.materialized
        self.assertEqual(result["status"], "READY")
        self.assertTrue(all(result["assertions"].values()))
        self.assertEqual(len(result["maps"]), 33)
        self.assertEqual(result["condition_table_count"], 0)
        self.assertEqual(result["source_pointer_literals"], [])
        self.assertLessEqual(
            {int(value, 0) for value in result["emitted_opcode_counts"]},
            set(MATERIALIZED_ALL_OPCODE_ALLOWLIST),
        )
        self.assertTrue(all(not row["condition_tables"] for row in result["maps"]))
        by_map = {row["physical_map"]: row for row in result["maps"]}
        self.assertIn("a73402", "".join(
            script["raw_hex"] for script in by_map["097/086"]["scripts"]
        ))
        self.assertIn("a73502", "".join(
            script["raw_hex"] for script in by_map["097/087"]["scripts"]
        ))
        for row in result["maps"]:
            patch = row["map_script_pointer_patch"]
            self.assertTrue(patch["expected_table_structure_empty"])
            self.assertNotEqual(patch["expected_pointer"], patch["replacement_pointer"])

    def test_vermilion_transition_adapter_is_exact_and_project_owned(self) -> None:
        contract = self.plan["vermilion_transition_adapter_contract"]
        self.assertEqual(contract["status"], "READY")
        self.assertTrue(all(contract["assertions"].values()))
        self.assertEqual(
            (contract["physical_map"], contract["source_map"],
             contract["source_wrapper_root"], contract["source_init_root"]),
            ("098/040", "009/006", "0x08182ED3", "0x08182ED9"),
        )
        self.assertEqual(
            contract["source_wrapper_raw_hex"], "04d92e180802",
        )
        self.assertEqual(
            contract["source_init_raw_hex"],
            "2b64020601534d1908255b011900400480190140058003",
        )
        special = contract["selection_special"]
        self.assertEqual(
            (special["id"], special["table_entry_address"],
             special["table_entry_raw_hex"], special["target_pointer"],
             special["span_size"], special["span_sha256"]),
            (
                "0x015B", "0x081635D4", "b9bf0c08", "0x080CBFB9", 616,
                "7c95c370673857591d8547e4078a603e5d89155fbe8fa2290c8b8b5a1c9f5fdc",
            ),
        )
        self.assertEqual(len(contract["allowed_directed_switch_pairs"]), 44)

        by_map = {
            row["physical_map"]: row for row in self.materialized["maps"]
        }
        row = by_map["098/040"]
        self.assertEqual(
            [script["script_type"] for script in row["scripts"]], [1, 3],
        )
        adapter = row["scripts"][1]
        self.assertEqual(
            adapter["materialization_role"],
            "VERMILION_TRANSITION_ADAPTER",
        )
        raw = bytes.fromhex(adapter["raw_hex"])
        self.assertEqual(len(raw), 23)
        self.assertEqual(raw[:1], b"\x2B")
        self.assertEqual(
            struct.unpack_from("<H", raw, 1)[0], self.flag_mapping[0x0264],
        )
        self.assertEqual(raw[3:5], b"\x06\x01")
        self.assertEqual(
            struct.unpack_from("<I", raw, 5)[0],
            int(adapter["pointer"], 0) + 22,
        )
        self.assertEqual(
            raw[9:], bytes.fromhex("255b011900400480190140058002"),
        )
        self.assertNotIn(
            struct.pack("<I", 0x08182ED3),
            bytes.fromhex(self.materialized["payload_raw_hex"]),
        )

    def test_vermilion_transition_adapter_mutation_and_delegation_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            Stage61MapScriptProjectionError, "may not be delegated",
        ):
            materialize_projection(
                self.plan, payload_base=0x09E00000,
                flag_mapping=self.flag_mapping, var_mapping=self.var_mapping,
                delegated_maps={(98, 40)},
            )

        mutated = copy.deepcopy(self.plan)
        contract = mutated["vermilion_transition_adapter_contract"]
        contract["selection_special"]["id"] = "0x015A"
        unsigned = dict(contract)
        unsigned.pop("contract_sha256")
        contract["contract_sha256"] = hashlib.sha256(json.dumps(
            unsigned, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(
            Stage61MapScriptProjectionError, "special identity drift",
        ):
            materialize_projection(
                mutated, payload_base=0x09E00000,
                flag_mapping=self.flag_mapping, var_mapping=self.var_mapping,
            )

    def test_materializer_can_delegate_bounded_maps_to_a_dedicated_producer(self) -> None:
        result = materialize_projection(
            self.plan,
            payload_base=0x09E00000,
            flag_mapping=self.flag_mapping,
            var_mapping=self.var_mapping,
            delegated_maps={(97, 86), (97, 87)},
        )
        self.assertEqual(result["delegated_maps"], ["097/086", "097/087"])
        self.assertEqual(len(result["maps"]), 31)
        self.assertNotIn("097/086", {row["physical_map"] for row in result["maps"]})
        self.assertNotIn("097/087", {row["physical_map"] for row in result["maps"]})
        self.assertTrue(all(result["assertions"].values()))
        with self.assertRaisesRegex(
            Stage61MapScriptProjectionError, "not an extractable projection",
        ):
            materialize_projection(
                self.plan,
                payload_base=0x09E00000,
                flag_mapping=self.flag_mapping,
                var_mapping=self.var_mapping,
                delegated_maps={(97, 75)},
            )

    def test_materializer_rejects_missing_identity_and_alias_state_mapping(self) -> None:
        with self.assertRaisesRegex(
            Stage61MapScriptProjectionError, "state mapping incomplete",
        ):
            materialize_projection(
                self.plan, payload_base=0x09E00000,
                flag_mapping={}, var_mapping={},
            )
        identity_flags = {
            int(row["source_id"], 0): int(row["source_id"], 0)
            for row in self.plan["state_requirements"]["flags"]
        }
        identity_vars = {
            int(row["source_id"], 0): int(row["source_id"], 0)
            for row in self.plan["state_requirements"]["vars"]
        }
        with self.assertRaisesRegex(
            Stage61MapScriptProjectionError, "non-identity mapping",
        ):
            materialize_projection(
                self.plan, payload_base=0x09E00000,
                flag_mapping=identity_flags, var_mapping=identity_vars,
            )
        broken_temp = dict(self.flag_mapping)
        broken_temp[1] = 2
        with self.assertRaisesRegex(
            Stage61MapScriptProjectionError, "temporary flag ABI requires identity",
        ):
            materialize_projection(
                self.plan, payload_base=0x09E00000,
                flag_mapping=broken_temp, var_mapping=self.var_mapping,
            )
        alias_flags = dict(self.flag_mapping)
        first, second = sorted(alias_flags)[:2]
        alias_flags[second] = alias_flags[first]
        with self.assertRaisesRegex(Stage61MapScriptProjectionError, "injective"):
            materialize_projection(
                self.plan, payload_base=0x09E00000,
                flag_mapping=alias_flags, var_mapping=self.var_mapping,
            )

    def test_league_explicit_exception_is_bounded_and_story_roots_stay_out(self) -> None:
        contract = self.plan["league_explicit_adapter_contract"]
        self.assertEqual(contract["status"], "READY")
        self.assertTrue(all(contract["assertions"].values()))
        self.assertEqual(contract["policy"]["scene_sequence"], [0, 1, 2, 3, 4, 5])
        self.assertEqual(
            contract["policy"]["scene_lifecycle"],
            {
                "initial_value": 0,
                "advance": "MONOTONIC_HIGH_WATER_MARK_ON_PHYSICAL_ROOM_ENTRY",
                "mid_room_save_reload": "PRESERVE_TO_AVOID_REPLAYING_ENTRY_MOVEMENT",
                "blackout_retry": "PRESERVE_DEFEATED_ROOM_PROGRESS",
                "completed_revisit": "KEEP_5_AND_LEAVE_COMPLETION_DOORS_OPEN",
                "rematch_geometry": "COMPLETED_OPEN_NO_FORCED_ENTRY_REPLAY",
                "reset_writer": "NONE_BY_DESIGN",
            },
        )
        self.assertEqual(
            [row["table_contract"]["tag_1_on_load"]["completion_flag"]
             for row in contract["elite_rooms"]],
            ["0x1408", "0x1409", "0x140A", "0x140B"],
        )
        self.assertEqual(
            [row["source_cfg_bounds"]["turn_root"] for row in contract["elite_rooms"]],
            ["0x0816949B", "0x08169752", "0x08169A4A", "0x08169D1B"],
        )
        self.assertEqual(
            [row["source_cfg_bounds"]["entry_reference_root"]
             for row in contract["elite_rooms"]],
            ["0x081694AA", "0x08169761", "0x08169A59", "0x08169D2A"],
        )
        champion = contract["champion_room"]
        self.assertEqual(champion["tag_2_entry"]["movement"]["pointer"], "0x0816A327")
        self.assertEqual(champion["tag_2_entry"]["movement_semantics"], "WALK_UP_10")
        self.assertFalse(champion["forbidden_source_story_root_imported"])
        movement_rows = [
            row["entry_movement_payloads"][0]
            for row in contract["elite_rooms"]
        ] + [champion["tag_2_entry"]["movement"]]
        self.assertTrue(all(row["pin_exact"] for row in movement_rows))
        self.assertEqual(
            [(row["pointer"], row["size"], row["sha256"]) for row in movement_rows],
            [
                ("0x08194B9D", 6,
                 "2c8b00240a9731746b37c6cee323b825aa459db38c6d9dcca133ca0979bb4f76"),
                ("0x08194B9D", 6,
                 "2c8b00240a9731746b37c6cee323b825aa459db38c6d9dcca133ca0979bb4f76"),
                ("0x08194B9D", 6,
                 "2c8b00240a9731746b37c6cee323b825aa459db38c6d9dcca133ca0979bb4f76"),
                ("0x08169D94", 35,
                 "a9b09ff9b5dbec3bff689c1edab8444f2f68819411616e670ce3ecb90d92e090"),
                ("0x0816A327", 11,
                 "abfc16cd115ce706e877c4faed8db055afd3249e2836494dace308706176c40a"),
            ],
        )
        self.assertEqual(contract["hall_of_fame"]["policy"],
                         "PRESERVE_EXISTING_PROJECT_TAG_3_ONLY")

    def test_target_tables_are_only_vermilion_and_hall_of_fame(self) -> None:
        self.assertEqual(
            [(row["physical_map"], row["tags"]) for row in
             self.plan["target_nonempty_tables"]],
            [("096/005", [3]), ("097/080", [3])],
        )
        self.assertFalse(
            {row["physical_map"] for row in self.plan["target_nonempty_tables"]}
            & {f"{group:03d}/{number:03d}" for group, number in PROJECTABLE_MAPS}
        )

    def test_unsafe_opcode_in_topology_root_fails_closed(self) -> None:
        mutated = bytearray(self.clean)
        # PokemonMansion_1F DIRECT topology root begins with 3-byte checkflag.
        # Replacing it with same-size special preserves instruction boundaries and proves the
        # denylist, rather than merely exercising a malformed byte stream.
        mutated[0x08168881 - ROM_BASE] = 0x25
        root = _extract_root_projection(bytes(mutated), 0x08168881)
        self.assertEqual(root["status"], "BLOCKED_UNSAFE_TOPOLOGY_ROOT")
        self.assertIn("UNSUPPORTED_OPCODE:0x25:special", root["block_reasons"])
        with self.assertRaisesRegex(Stage61MapScriptProjectionError, "identity mismatch"):
            build_projection_plan(
                bytes(mutated), self.stage60, self.canonical, require_ready=True,
            )

    def test_temp_flag_0001_identity_bridges_full_cfg_producer_and_projection(self) -> None:
        evidence = self.plan["state_requirements"]["temp_flag_0001_abi"]
        self.assertEqual(evidence["mapping_policy"], "EXPLICIT_IDENTITY_REQUIRED")
        self.assertTrue(evidence["producer_consumer_identity_exact"])
        self.assertEqual(
            [(row["address"], row["role"], row["raw_hex"])
             for row in evidence["full_cfg_producer_consumer_instructions"]],
            [
                ("0x08182E0A", "PROJECTION_READ", "2b0100"),
                ("0x08182FC8", "FULL_CFG_READ", "2b0100"),
                ("0x08182FFA", "FULL_CFG_SET", "290100"),
                ("0x08183012", "FULL_CFG_CLEAR", "2a0100"),
            ],
        )
        flag = next(row for row in self.plan["state_requirements"]["flags"]
                    if row["source_id"] == "0x0001")
        self.assertEqual(flag["namespace"], "TEMP_FLAG")
        self.assertEqual(flag["mapping_policy"], "IDENTITY_REQUIRED")
        binding = next(row for row in self.materialized["state_bindings"]["flags"]
                       if row["source_id"] == "0x0001")
        self.assertEqual(binding["target_id"], "0x0001")
        self.assertEqual(binding["mapping"], "IDENTITY")

    def test_blaine_topology_reads_the_real_project_completion_producer(self) -> None:
        binding = self.plan["blaine_project_completion_binding"]
        self.assertEqual(binding["status"], "READY")
        self.assertTrue(all(binding["assertions"].values()))
        self.assertEqual(
            (binding["source_flag"], binding["target_project_flag"]),
            ("0x04B6", "0x1406"),
        )
        # 0x1405 is the Saffron prerequisite checked before battle; 0x1406 is
        # set by Blaine's successful battle continuation.
        self.assertEqual(binding["evidence"][-1]["actual_raw_hex"], "290614")
        materialized_binding = next(
            row for row in self.materialized["state_bindings"]["flags"]
            if row["source_id"] == "0x04B6"
        )
        self.assertEqual(materialized_binding["target_id"], "0x1406")
        self.assertEqual(
            materialized_binding["mapping"], "EXPLICIT_PROJECT_STATE_BINDING"
        )

    def test_canonical_cardinality_is_fail_closed(self) -> None:
        with self.assertRaisesRegex(Stage61MapScriptProjectionError, "exactly 253"):
            build_projection_plan(
                self.clean, self.stage60, self.canonical[:-1], require_ready=False,
            )

    def test_cli_require_ready_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "projection.json"
            process = subprocess.run(
                [sys.executable, str(ROOT / "tools/stage61_map_script_projection.py"),
                 "--root", str(ROOT), "--require-ready", "--output", str(output)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            summary = json.loads(process.stdout)
            self.assertEqual(summary["status"], "READY")
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["plan_sha256"], summary["plan_sha256"])
            self.assertEqual(written["summary"]["classification_counts"],
                             {"A": 21, "B": 12, "C": 8, "D": 54})


if __name__ == "__main__":
    unittest.main()
