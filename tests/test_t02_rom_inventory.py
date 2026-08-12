#!/usr/bin/env python3
"""Focused acceptance and negative tests for the T02 ROM-rooted scanner."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.t02.rom_inventory import (
    InventoryError,
    MAP_DYNAMIC,
    ROM_BASE,
    RomImage,
    ScriptRoot,
    ScriptWalker,
    build_rom_inventory,
    validate_early_unlock,
    validate_map_id,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "config/t02_audit_policy.json"


class RomPrimitiveNegativeTests(unittest.TestCase):
    def test_bad_pointer_is_rejected_before_read(self) -> None:
        rom = RomImage("tiny", b"\0" * 16)
        with self.assertRaisesRegex(InventoryError, "invalid bad pointer"):
            rom.require_pointer(ROM_BASE + 16, what="bad pointer")
        with self.assertRaisesRegex(InventoryError, "invalid u32"):
            rom.u32(ROM_BASE + 14)

    def test_signed_map_id_limit_and_sentinels(self) -> None:
        self.assertEqual(validate_map_id(42, 125), "PHYSICAL")
        for group, map_num in ((127, 126), (126, 127), (128, 0), (255, 255)):
            with self.subTest(group=group, map_num=map_num):
                with self.assertRaises(InventoryError):
                    validate_map_id(group, map_num)
        with self.assertRaisesRegex(InventoryError, "MAP_DYNAMIC"):
            validate_map_id(*MAP_DYNAMIC)
        self.assertEqual(validate_map_id(*MAP_DYNAMIC, allow_dynamic=True), "MAP_DYNAMIC")

    def test_rooted_loop_terminates_with_one_visited_node(self) -> None:
        # goto ROM_BASE; a self-loop is traversed once by the visited graph.
        data = bytes([0x05]) + ROM_BASE.to_bytes(4, "little") + b"\xFF" * 8
        walker = ScriptWalker(RomImage("loop", data))
        walker.add_root(ScriptRoot(ROM_BASE, "fixture:loop", "test"))
        result = walker.walk()
        self.assertEqual(result["visited_script_count"], 1)
        self.assertEqual(result["nodes"][0]["edges"], [ROM_BASE])
        self.assertEqual(result["nodes"][0]["end_reason"], "goto")

    def test_unknown_data_is_not_resynchronised_as_bytecode(self) -> None:
        # The embedded 29 24 08 would be `setflag 0x0824` if a scanner tried
        # every byte.  A rooted decoder stops at the leading unknown opcode.
        data = bytes([0xFF, 0x29, 0x24, 0x08, 0x02])
        walker = ScriptWalker(RomImage("data", data))
        walker.add_root(ScriptRoot(ROM_BASE, "fixture:data", "test"))
        result = walker.walk()
        self.assertEqual(result["visited_script_count"], 1)
        self.assertEqual(result["references"], [])
        self.assertEqual(result["diagnostics"], [{"address": ROM_BASE, "kind": "unknown_opcode", "opcode": 0xFF}])

    def test_bad_script_root_and_edge_do_not_escape_rom(self) -> None:
        walker = ScriptWalker(RomImage("tiny", b"\x02"))
        with self.assertRaisesRegex(InventoryError, "script root"):
            walker.add_root(ScriptRoot(ROM_BASE + 1, "fixture:bad", "test"))

    def test_var_get_operand_is_not_misclassified_as_semantic_id(self) -> None:
        # additem VAR_0x8000, 1; showmonpic VAR_0x4001, 0, 0; end
        data = bytes([0x44, 0x00, 0x80, 0x01, 0x00, 0x75, 0x01, 0x40, 0, 0, 0x02])
        walker = ScriptWalker(RomImage("var-get", data))
        walker.add_root(ScriptRoot(ROM_BASE, "fixture:var-get", "test"))
        refs = walker.walk()["references"]
        self.assertEqual({row["category"] for row in refs}, {"var"})
        self.assertEqual({row["value"] for row in refs}, {0x4001, 0x8000})
        self.assertEqual({row["semantic_category"] for row in refs}, {"item", "species"})


class EarlyUnlockNegativeTests(unittest.TestCase):
    def _policy(self) -> dict[str, object]:
        return {
            "early_unlock": {
                "required_flags": [0x824, 0x114B],
                "forbidden_inferred_flags": [0x822],
                "latch_policy": "NEW_DEDICATED_FLAG",
                "shiou": {"battle_script_address": ROM_BASE, "completion_flag": 0x824},
                "dh_building": {"final_script_address": ROM_BASE + 0x20, "completion_flag": 0x114B},
            }
        }

    def test_0822_cannot_be_substituted_for_0824(self) -> None:
        policy = self._policy()
        policy["early_unlock"]["required_flags"] = [0x822, 0x114B]  # type: ignore[index]
        with self.assertRaisesRegex(InventoryError, "exact 0x0824"):
            validate_early_unlock(policy, [])

    def test_completion_must_be_reachable_from_each_fixed_root(self) -> None:
        refs = [
            {"category": "flag", "value": 0x824, "access": "set", "script_address": ROM_BASE + 0x10, "instruction_address": ROM_BASE + 0x12, "roots": ["shiou"]},
            {"category": "flag", "value": 0x114B, "access": "set", "script_address": ROM_BASE + 0x20, "instruction_address": ROM_BASE + 0x22, "roots": ["dh"]},
        ]
        graph = [
            {"address": ROM_BASE, "edges": [ROM_BASE + 0x10]},
            {"address": ROM_BASE + 0x10, "edges": []},
            {"address": ROM_BASE + 0x20, "edges": []},
        ]
        result = validate_early_unlock(self._policy(), refs, graph)
        self.assertTrue(result["validated"])
        self.assertEqual(result["required_flags"], [0x824, 0x114B])
        refs[0]["script_address"] = ROM_BASE + 0x18
        with self.assertRaisesRegex(InventoryError, "completion flag"):
            validate_early_unlock(self._policy(), refs, graph)


@unittest.skipUnless(POLICY_PATH.is_file(), "T02 policy is not present")
class FixedVegaIntegrationTests(unittest.TestCase):
    inventory: dict[str, object]
    policy: dict[str, object]

    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        required_roms = [REPO_ROOT / value["path"] for value in cls.policy["inputs"].values()]  # type: ignore[index,union-attr]
        if not all(path.is_file() for path in required_roms):
            raise unittest.SkipTest("fixed clean/Vega/Factory ROMs are unavailable")
        cls.inventory = build_rom_inventory(REPO_ROOT, cls.policy)

    def test_exact_top_level_schema(self) -> None:
        self.assertEqual(
            set(self.inventory),
            {"schema_version", "provenance", "maps", "encounters", "script_references", "early_unlock", "trainers", "qol_hooks", "summaries"},
        )
        self.assertEqual(self.inventory["schema_version"], 1)

    def test_wrong_fixed_rom_hash_is_rejected(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["inputs"]["vega"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(InventoryError, "vega ROM sha256 mismatch"):
            build_rom_inventory(REPO_ROOT, policy)

    def test_map_inventory_is_43_groups_and_425_rooted_headers(self) -> None:
        maps = self.inventory["maps"]  # type: ignore[assignment]
        self.assertEqual(maps["group_count"], 43)
        self.assertEqual(maps["physical_map_count"], 425)
        self.assertEqual(sum(maps["group_sizes"]), 425)
        self.assertEqual(max(maps["group_sizes"]), 123)
        self.assertEqual(len(maps["rows"]), 425)
        required = {"group", "map", "header_address", "layout_id", "map_section", "music", "events_address", "object_count", "warp_count", "coord_count", "bg_count", "map_scripts_address", "classification", "evidence"}
        self.assertTrue(all(required <= set(row) for row in maps["rows"]))

    def test_aeshia_port_has_no_object_slot_and_preserves_dummy_warps(self) -> None:
        port = self.inventory["maps"]["early_port"]  # type: ignore[index]
        self.assertEqual((port["group"], port["map"]), (3, 4))
        self.assertEqual(port["object_local_ids"], list(range(1, 16)))
        self.assertEqual(port["runtime_object_count_including_player"], 16)
        self.assertEqual(port["free_runtime_object_slots"], 0)
        self.assertFalse(port["new_static_object_allowed"])
        self.assertEqual((port["dh_entry_warp"]["destination_group"], port["dh_entry_warp"]["destination_map"]), (1, 47))
        self.assertEqual([row["index"] for row in port["reserved_dummy_warps"]], [9, 10, 11, 12])
        self.assertTrue(all((row["destination_group"], row["destination_map"]) == (0, 0) for row in port["reserved_dummy_warps"]))

    def test_wild_headers_have_132_rows_and_exact_ffff_terminator(self) -> None:
        encounters = self.inventory["encounters"]  # type: ignore[assignment]
        self.assertEqual(encounters["header_count"], 132)
        self.assertEqual(encounters["terminator"], [0xFF, 0xFF])
        self.assertEqual(encounters["terminator_address"], encounters["headers_address"] + 132 * 0x14)
        required = {"group", "map", "header_address", "land_address", "water_address", "rock_address", "fishing_address", "classification", "evidence"}
        self.assertTrue(all(required <= set(row) for row in encounters["rows"]))

    def test_travel_save_abi_escape_fly_and_hidden_item_width_are_explicit(self) -> None:
        travel = self.inventory["maps"]["travel_state"]  # type: ignore[index]
        self.assertEqual(travel["map_id_abi"]["physical_max"], 126)
        self.assertEqual(travel["map_id_abi"]["dynamic_sentinel"], [0x7F, 0x7F])
        self.assertEqual(travel["save_warp_abi"]["record_size"], 8)
        self.assertEqual(travel["save_warp_abi"]["records"]["last_heal_location"]["saveblock1_offset"], 0x1C)
        self.assertEqual(travel["save_warp_abi"]["records"]["escape_warp"]["saveblock1_offset"], 0x24)
        self.assertGreater(travel["escape"]["allowed_map_count"], 0)
        self.assertGreater(travel["fly_and_heal"]["fly_allowed_map_count"], 0)
        self.assertGreater(len(travel["fly_and_heal"]["respawn_references"]), 0)
        self.assertGreater(len(travel["fly_and_heal"]["fly_unlock_references"]), 0)
        hidden = travel["hidden_items"]
        self.assertEqual((hidden["raw_width_bits"], hidden["item_id_bits"], hidden["flag_index_bits"], hidden["quantity_bits"], hidden["underfoot_bits"]), (32, 16, 8, 7, 1))
        self.assertEqual(hidden["flag_base"], 0x3E8)
        self.assertEqual(hidden["row_count"], len(hidden["rows"]))
        self.assertGreater(hidden["row_count"], 0)

    def test_unlock_is_exact_and_has_script_provenance(self) -> None:
        unlock = self.inventory["early_unlock"]  # type: ignore[assignment]
        self.assertEqual(unlock["required_flags"], [0x824, 0x114B])
        self.assertEqual(unlock["forbidden_inferred_flags"], [0x822])
        self.assertEqual(unlock["operator"], "AND")
        self.assertTrue(unlock["validated"])
        self.assertEqual({row["flag"] for row in unlock["evidence"]}, {0x824, 0x114B})
        self.assertTrue(all(row["roots"] for row in unlock["evidence"]))

    def test_all_trainers_and_required_roles_have_rooted_baselines(self) -> None:
        trainers = self.inventory["trainers"]  # type: ignore[assignment]
        self.assertEqual(trainers["count"], 743)
        self.assertEqual(len(trainers["rows"]), 743)
        self.assertTrue(trainers["required_roles_validated"])
        self.assertEqual(trainers["role_counts"]["gym_leader"], 8)
        for role in trainers["required_roles"]:
            self.assertGreater(trainers["role_counts"].get(role, 0), 0, role)
        required = {"trainer_id", "role", "party_size", "levels", "moves", "items", "ai_flags", "reward", "rematch_branch", "evidence"}
        self.assertTrue(all(required <= set(row) for row in trainers["rows"]))
        self.assertTrue(all(row["role"] for row in trainers["rows"]))
        self.assertTrue(all(row["reward"] != "" for row in trainers["rows"]))
        self.assertTrue(all(row["rematch_branch"] != "" for row in trainers["rows"]))

    def test_trainer_money_and_known_boss_records_are_exact(self) -> None:
        trainers = self.inventory["trainers"]  # type: ignore[assignment]
        self.assertEqual(trainers["money_table"]["address"], 0x0820C0D0)
        self.assertEqual(trainers["money_table"]["row_count"], 104)
        dh = trainers["rows"][0x123]
        shiou = trainers["rows"][0x1A2]
        self.assertEqual((dh["role"], dh["levels"], dh["ai_flags"]), ("dh_executive", [33, 36, 35, 36], 7))
        self.assertEqual((shiou["role"], shiou["levels"], shiou["ai_flags"]), ("gym_leader", [30, 29, 28, 30], 7))
        self.assertEqual(dh["reward"], 9 * 4 * 36)
        self.assertEqual(shiou["reward"], 25 * 4 * 30)

    def test_script_walker_contract_and_reference_domains(self) -> None:
        script_refs = self.inventory["script_references"]  # type: ignore[assignment]
        graph = script_refs["graph"]
        self.assertGreater(graph["root_count"], 3000)
        self.assertGreater(graph["visited_script_count"], 4000)
        categories = {row["category"] for row in script_refs["rows"]}
        self.assertTrue({"flag", "var", "special", "trainer", "item", "species", "move", "map"} <= categories)
        contract = self.inventory["provenance"]["scan_contract"]  # type: ignore[index]
        self.assertFalse(contract["rom_byte_pattern_scan"])
        self.assertTrue(contract["pointer_bounds_checked"])
        self.assertTrue(contract["visited_graph"])

    def test_qol_rows_cover_every_policy_domain(self) -> None:
        rows = self.inventory["qol_hooks"]  # type: ignore[assignment]
        self.assertEqual([row["domain"] for row in rows], sorted(self.policy["qol_required_domains"]))
        required = {"domain", "address_or_symbol", "status", "vega_expected_sha256", "classification", "evidence", "followup_task"}
        self.assertTrue(all(required == set(row) for row in rows))
        self.assertTrue(all(row["evidence"] and row["followup_task"] for row in rows))

    def test_api_is_deterministic_and_contains_no_timestamp(self) -> None:
        second = build_rom_inventory(REPO_ROOT, copy.deepcopy(self.policy))
        first_json = json.dumps(self.inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        second_json = json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(first_json, second_json)
        self.assertNotIn('"timestamp"', first_json.lower())
        self.assertNotIn(str(REPO_ROOT / "inputs/private"), first_json)


if __name__ == "__main__":
    unittest.main()
