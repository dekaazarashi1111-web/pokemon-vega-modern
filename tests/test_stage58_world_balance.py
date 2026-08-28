from __future__ import annotations

import copy
import csv
import json
import unittest
from pathlib import Path

from tools.stage58_world_balance import (
    DEFAULT_RATES,
    FIRERED_SLOT_GROUPS,
    FIRERED_SLOT_PROBABILITIES,
    WILD_SLOT_COUNTS,
    WorldBalanceError,
    _allocate_group,
    audit_world_balance_plan,
    build_world_balance_plan,
    classify_manifest_row,
)


ROOT = Path(__file__).resolve().parents[1]


def _csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Stage58WorldBalanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = (ROOT / "build/stages/57_comprehensive_debug_repair.gba").read_bytes()
        cls.stage17 = json.loads(
            (ROOT / "build/stages/17_regression.json").read_text(encoding="utf-8")
        )
        cls.encounters = _csv("manifests/kanto_encounters.csv")
        cls.species = {row["species_key"]: int(row["id"])
                       for row in _csv("manifests/species_ids.csv")}
        cls.plan = build_world_balance_plan(
            ROOT, cls.rom, cls.stage17, cls.encounters, cls.species, DEFAULT_RATES
        )

    def test_method_classifier_is_exact_and_fail_closed(self) -> None:
        base = {
            "status": "ACTIVE", "table_profile": "NORMAL", "weight": "8",
            "condition": "ベガ初回殿堂入り後。認定章数でエリアと中間進化枠を段階解禁。",
            "unlock_key": "KANTO_EARLY_ACCESS",
        }
        self.assertEqual(
            classify_manifest_row({**base, "method": "草むらオーバーレイ"}),
            ("land_outdoor", "native"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "洞窟・屋内オーバーレイ"}),
            ("land_dungeon", "native"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "水上オーバーレイ"}),
            ("water", "native"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "釣りオーバーレイ"}),
            ("fishing", "native"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "いわくだき／DexNav"}),
            ("rock", "native"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "いわくだき／DexNav", "weight": "0"}),
            (None, "zero_weight"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "DexNav隠し枠／低確率タマゴ"}),
            (None, "egg_method"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "博物館鑑定後に復元"}),
            (None, "fossil_method"),
        )
        self.assertEqual(
            classify_manifest_row({**base, "method": "SIMPLE_EVENT",
                                     "table_profile": "EVENT"}),
            (None, "event_profile"),
        )

    def test_plan_has_133_unique_physical_headers(self) -> None:
        headers = self.plan["headers"]
        coordinates = [(row["group"], row["map"]) for row in headers]
        self.assertEqual(len(headers), 133)
        self.assertEqual(len(set(coordinates)), 133)
        self.assertEqual({row["logical_code"] for row in headers},
                         {row["logical_location_key"] for row in self.encounters})
        self.assertEqual(self.plan["audit"]["physical_header_count"], 133)
        self.assertEqual(self.plan["audit"]["duplicate_physical_header_count"], 0)

    def test_only_matching_native_channels_are_serialized(self) -> None:
        audit = self.plan["audit"]
        self.assertEqual(audit["enabled_physical_header_count"], 56)
        self.assertEqual(audit["disabled_non_native_physical_header_count"], 77)
        self.assertEqual(audit["mode_table_counts"], {
            "fishing": 13, "land": 52, "rock": 1, "water": 11,
        })
        self.assertEqual(audit["method_misplacement_count"], 0)
        self.assertEqual(audit["zero_weight_native_inclusion_count"], 0)
        self.assertEqual(audit["event_native_inclusion_count"], 0)
        self.assertEqual(audit["egg_native_inclusion_count"], 0)
        self.assertEqual(audit["fossil_native_inclusion_count"], 0)
        self.assertEqual(audit["positive_weight_physical_channel_drop_count"], 0)
        self.assertEqual(audit["positive_weight_physical_channel_drop_keys"], [])
        self.assertEqual(
            audit["positive_weight_physical_channel_candidate_count"],
            audit["positive_weight_serialized_unique_count"],
        )
        self.assertEqual(audit["positive_weight_native_manifest_candidate_count"], 245)
        self.assertEqual(audit["positive_weight_native_manifest_unmapped_count"], 0)
        self.assertEqual(audit["positive_weight_physical_tuple_expected_count"], 384)
        self.assertEqual(audit["positive_weight_physical_tuple_serialized_count"], 384)
        self.assertEqual(audit["positive_weight_physical_tuple_drop_count"], 0)
        self.assertEqual(audit["unexpected_physical_tuple_count"], 0)

    def test_rock_smash_uses_only_matching_physical_channel(self) -> None:
        k28 = [row for row in self.plan["headers"] if row["logical_code"] == "K28"]
        self.assertTrue(k28)
        enabled_k28 = [row for row in k28 if row["enabled"]]
        self.assertEqual([(row["group"], row["map"]) for row in enabled_k28], [(97, 37)])
        self.assertEqual(enabled_k28[0]["modes"]["land"]["candidate_count"], 5)
        self.assertTrue(all(row["modes"]["rock"] is None for row in k28))
        rock = [row for row in self.plan["headers"]
                if row["modes"]["rock"] is not None]
        self.assertEqual([(row["group"], row["map"]) for row in rock], [(97, 82)])
        self.assertEqual(rock[0]["modes"]["rock"]["native_method"], "rock")
        self.assertEqual(rock[0]["modes"]["rock"]["candidate_count"], 5)
        self.assertEqual(rock[0]["modes"]["rock"]["diversity"], 5)

    def test_capacity_rebalance_keeps_every_positive_candidate_naturally_obtainable(self) -> None:
        k30 = [row for row in self.plan["headers"]
               if row["logical_code"] == "K30" and row["enabled"]]
        self.assertEqual(len(k30), 2)
        for row in k30:
            land = row["modes"]["land"]
            self.assertEqual(land["candidate_count"], 6)
            self.assertEqual(land["diversity"], 6)
        k19 = next(row for row in self.plan["headers"]
                   if row["logical_code"] == "K19" and row["enabled"])
        self.assertEqual(k19["modes"]["water"]["candidate_count"], 5)
        self.assertEqual(k19["modes"]["water"]["diversity"], 5)
        fishing = k19["modes"]["fishing"]
        self.assertEqual(fishing["candidate_count"], 5)
        self.assertIn("ENCOUNTER_KEY_KANTO_FAMILY_0504", fishing["source_keys"])
        self.assertEqual(
            fishing["rod_tier_policy"],
            "MANIFEST_AUTHORED_OLD_GOOD_SUPER_ELIGIBILITY_AND_WEIGHT",
        )

    def test_dead_native_rows_and_safari_grass_classification_are_repaired(self) -> None:
        for logical, expected_count in (("K27", 12), ("K28", 5),
                                        ("K37", 5), ("K42", 6)):
            tables = [row["modes"]["land"] for row in self.plan["headers"]
                      if row["logical_code"] == logical
                      and row["modes"]["land"] is not None]
            self.assertTrue(tables, logical)
            self.assertTrue(all(table["candidate_count"] == expected_count
                                for table in tables), logical)
        overrides = self.plan["physical_encounter_classification_overrides"]
        self.assertEqual(overrides, {
            "SafariZone_Center": "OUTDOOR",
            "SafariZone_West": "OUTDOOR",
        })
        for source_map in overrides:
            header = next(row for row in self.plan["headers"]
                          if row["source_map"] == source_map)
            self.assertEqual(header["classification"], "DUNGEON")
            self.assertEqual(header["encounter_classification"], "OUTDOOR")
            self.assertEqual(header["classification_override"], "OUTDOOR")
            self.assertIsNotNone(header["modes"]["land"])

    def test_every_slot_group_has_explicit_positive_weight_fidelity_contract(self) -> None:
        for header in self.plan["headers"]:
            for mode, table in header["modes"].items():
                if table is None:
                    continue
                with self.subTest(group=header["group"], map=header["map"], mode=mode):
                    contracts = table["group_allocation_contracts"]
                    self.assertEqual(len(contracts), len(FIRERED_SLOT_GROUPS[mode]))
                    for contract in contracts:
                        self.assertEqual(contract["zero_probability_candidate_count"], 0)
                        self.assertEqual(
                            sum(contract["serialized_probability_mass"].values()), 100,
                        )
                        self.assertEqual(
                            set(contract["eligible_source_keys"]),
                            set(contract["serialized_probability_mass"]),
                        )
                        self.assertEqual(contract["allocator"],
                                         "EXACT_SUBSET_DP_MINIMAX_THEN_L1")
                        self.assertEqual(contract["optimality_status"], "EXACT")
                        self.assertLessEqual(contract["max_absolute_weight_error"], 15.0001)
                        self.assertLessEqual(
                            contract["max_absolute_weight_error"],
                            contract["optimal_max_absolute_weight_error"] + 0.0001,
                        )
                        self.assertEqual(contract["optimality_tolerance_points"], 0.0001)
                        self.assertIs(contract["within_optimality_tolerance"], True)
                        self.assertEqual(
                            set(contract["eligible_source_keys"]),
                            set(contract["target_weight_by_source_key"]),
                        )

    def test_fishing_has_manifest_authored_rod_specific_eligibility_and_targets(self) -> None:
        expected_tiers = ["OLD_ROD", "GOOD_ROD", "SUPER_ROD"]
        for header in self.plan["headers"]:
            table = header["modes"]["fishing"]
            if table is None:
                continue
            contracts = table["group_allocation_contracts"]
            self.assertEqual([row["rod_tier"] for row in contracts], expected_tiers)
            for contract in contracts:
                self.assertTrue(contract["eligible_source_keys"])
                self.assertTrue(all(
                    int(value) > 0
                    for value in contract["target_weight_by_source_key"].values()
                ))
            self.assertEqual(
                set(table["source_keys"]),
                set().union(*(set(row["eligible_source_keys"]) for row in contracts)),
            )

    def test_fire_red_slot_abi_probability_diversity_and_metadata_requirement(self) -> None:
        for header in self.plan["headers"]:
            for mode, table in header["modes"].items():
                if table is None:
                    continue
                with self.subTest(group=header["group"], map=header["map"], mode=mode):
                    self.assertEqual(len(table["slots"]), WILD_SLOT_COUNTS[mode])
                    self.assertEqual(table["slot_probabilities"],
                                     FIRERED_SLOT_PROBABILITIES[mode])
                    for group in FIRERED_SLOT_GROUPS[mode]:
                        self.assertEqual(sum(table["slot_probabilities"][i] for i in group),
                                         100)
                    self.assertEqual(table["diversity"],
                                     len(set(table["species_keys"])))
                    self.assertGreaterEqual(table["diversity"], 1)
                    self.assertLessEqual(table["diversity"],
                                         min(table["candidate_count"], len(table["slots"])))
                    self.assertNotIn("gate", table)
                    requirement = table["progression_requirement"]
                    self.assertTrue(requirement["unlock_key"])
                    self.assertEqual(
                        requirement["policy"], "progression_requirement_metadata_only"
                    )
                    self.assertIs(requirement["serializer_applied"], False)
                    self.assertIn(table["native_method"], DEFAULT_RATES)
                    self.assertEqual(table["rate"], DEFAULT_RATES[table["native_method"]])
                    for low, high, species in table["slots"]:
                        self.assertLessEqual(1, low)
                        self.assertLessEqual(low, high)
                        self.assertLessEqual(high, 100)
                        self.assertLessEqual(1, species)
                        self.assertLessEqual(species, 1620)

    def test_stage17_four_mode_defect_is_measured_not_inherited(self) -> None:
        audit = self.plan["audit"]
        self.assertEqual(audit["legacy_all_four_mode_header_count"], 133)
        self.assertGreater(audit["legacy_non_native_mode_pointer_count"], 0)
        self.assertGreater(audit["legacy_two_species_all_mode_header_count"], 0)
        self.assertEqual(audit["legacy_zero_coordinate_orphan_header_count"], 17)

    def test_balance_metrics_quantify_before_after_delta_at_all_scopes(self) -> None:
        metrics = self.plan["balance_metrics"]
        self.assertEqual(len(metrics["physical"]), 133)
        self.assertEqual(
            len(metrics["logical"]),
            len({row["logical_code"] for row in self.plan["headers"]}),
        )
        expected = {
            "land": ((133, 2660, 1596, 401), (52, 445, 624, 191)),
            "water": ((133, 2660, 665, 223), (11, 22, 55, 22)),
            "rock": ((133, 2660, 665, 223), (1, 25, 5, 5)),
            "fishing": ((133, 2660, 1330, 374), (13, 260, 130, 27)),
        }
        for mode, (before_expected, after_expected) in expected.items():
            with self.subTest(mode=mode):
                aggregate = metrics["aggregate"]["modes"][mode]
                before, after, delta = (
                    aggregate["before"], aggregate["after"], aggregate["delta"]
                )
                self.assertEqual(
                    (before["enabled_table_count"], before["rate_sum"],
                     before["slot_count"], before["diversity"]),
                    before_expected,
                )
                self.assertEqual(
                    (after["enabled_table_count"], after["rate_sum"],
                     after["slot_count"], after["diversity"]),
                    after_expected,
                )
                self.assertEqual(
                    delta["enabled_table_count"],
                    after["enabled_table_count"] - before["enabled_table_count"],
                )
                for side in (before, after):
                    for group in side["species_probability_mass_by_slot_group"]:
                        self.assertEqual(
                            sum(group["species_probability_mass"].values()),
                            group["probability_total"],
                        )
        for row in metrics["physical"]:
            for mode, sides in row["modes"].items():
                for side in (sides["before"], sides["after"]):
                    if side is None:
                        continue
                    for group in side["slot_groups"]:
                        self.assertEqual(group["probability_total"], 100)
                        self.assertEqual(
                            sum(group["species_probability_mass"].values()), 100
                        )

    def test_progression_requirement_is_metadata_only_and_owner_mismatch_is_explicit(self) -> None:
        contract = self.plan["progression_contract"]
        self.assertEqual(contract["policy"], "progression_requirement_metadata_only")
        self.assertIs(contract["runtime_gate_claimed_by_world_plan"], False)
        self.assertIs(contract["serializer_applies_progression_requirement"], False)
        self.assertEqual(contract["serializer_non_application_status"], "PASS")
        self.assertEqual(contract["runtime_map_access_owner_coverage_status"], "PASS")
        self.assertEqual(contract["runtime_map_access_owner_physical_count"], 133)
        self.assertEqual(
            contract["metadata_runtime_owner_alignment_status"],
            "SAFE_LATE_ACCESS",
        )
        self.assertEqual(contract["metadata_runtime_owner_mismatch_count"], 46)
        self.assertEqual(contract["metadata_runtime_owner_mismatch_logical_count"], 29)
        self.assertEqual(contract["premature_exposure_count"], 0)
        self.assertEqual(
            contract["serializer_source"]["consumed_table_fields"], ["rate", "slots"]
        )
        self.assertEqual(
            contract["serializer_source"]["ignored_metadata_fields"],
            ["progression_requirement"],
        )
        self.assertEqual(self.plan["audit"]["runtime_gate_claim_count"], 0)

    def test_thin_place_candidates_are_reachable_conflict_free_and_quantified(self) -> None:
        candidates = self.plan["thin_candidates"]
        self.assertEqual(len(candidates), 8)
        self.assertEqual(len({(row["group"], row["map"]) for row in candidates}), 8)
        self.assertEqual(len({row["logical_code"] for row in candidates}), 8)
        for row in candidates:
            self.assertEqual(row["collision"], 0)
            self.assertEqual(row["event_conflicts"], [])
            self.assertGreaterEqual(row["x"], 2)
            self.assertGreaterEqual(row["y"], 2)
            self.assertGreater(row["thin_score"], 0)
            self.assertGreater(row["reachability_seed_count"], 0)
            self.assertEqual(
                row["progression_requirement_policy"],
                "progression_requirement_metadata_only",
            )
            self.assertTrue(row["runtime_map_access_owner_unlock_key"])
            self.assertEqual(
                row["unlock_key"], row["runtime_map_access_owner_unlock_key"]
            )
            self.assertEqual(
                row["reward_tier_owner_policy"], "runtime_map_access_owner"
            )
            self.assertIn("1000 tiles当たり", row["reason"])
            self.assertIn(row["reward_tier"], {
                "EARLY_CONSUMABLE", "MID_EXPLORATION", "LATE_EXPLORATION",
                "POSTGAME_RARE",
            })
        self.assertEqual(
            self.plan["audit"]["thin_candidate_collision_or_event_conflict_count"], 0
        )

    def test_connection_reachability_uses_real_direction_and_offset_spans(self) -> None:
        saffron = next(
            row for row in self.plan["thin_places"]
            if (row["group"], row["map"]) == (96, 11)
        )
        self.assertEqual(saffron["connection_count"], 4)
        self.assertEqual(saffron["warp_seed_count"], 0)
        self.assertEqual(saffron["connection_seed_count"], 19)
        self.assertEqual(
            [(row["direction"], row["offset"], row["source_axis_span"])
             for row in saffron["connections"]],
            [
                ("north", 0, [0, 47]),
                ("south", 12, [12, 35]),
                ("west", 10, [10, 29]),
                ("east", 10, [10, 29]),
            ],
        )

    def test_selected_thin_event_config_still_matches_recomputed_candidates(self) -> None:
        config = json.loads(
            (ROOT / "config/stage58_qol_world_convenience_debug.json")
            .read_text(encoding="utf-8")
        )
        candidates = {
            (row["group"], row["map"], row["x"], row["y"]): row
            for row in self.plan["thin_candidates"]
        }
        for configured in config["thin_events"]:
            key = tuple(configured[field] for field in ("group", "map", "x", "y"))
            with self.subTest(key=configured["key"]):
                self.assertIn(key, candidates)
                self.assertEqual(
                    configured["reward_tier"], candidates[key]["reward_tier"]
                )
        self.assertEqual(len(self.plan["thin_candidates"]), 8)

    def test_plan_is_deterministic_and_independently_auditable(self) -> None:
        again = build_world_balance_plan(
            ROOT, self.rom, self.stage17, self.encounters, self.species, DEFAULT_RATES
        )
        self.assertEqual(again, self.plan)
        result = audit_world_balance_plan(self.plan)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["physical_header_count"], 133)
        self.assertEqual(result["balance_physical_row_count"], 133)
        self.assertEqual(
            result["progression_metadata_runtime_owner_alignment_status"],
            "SAFE_LATE_ACCESS",
        )

    def test_independent_audit_rejects_duplicate_header(self) -> None:
        broken = copy.deepcopy(self.plan)
        broken["headers"][1]["group"] = broken["headers"][0]["group"]
        broken["headers"][1]["map"] = broken["headers"][0]["map"]
        with self.assertRaisesRegex(WorldBalanceError, "重複"):
            audit_world_balance_plan(broken)

    def test_independent_audit_rejects_probability_mass_and_runtime_gate_claim(self) -> None:
        broken = copy.deepcopy(self.plan)
        physical = broken["balance_metrics"]["physical"][0]
        group = physical["modes"]["land"]["before"]["slot_groups"][0]
        first_species = next(iter(group["species_probability_mass"]))
        group["species_probability_mass"][first_species] += 1
        with self.assertRaisesRegex(WorldBalanceError, "mass"):
            audit_world_balance_plan(broken)

        broken = copy.deepcopy(self.plan)
        table = next(
            table for header in broken["headers"] for table in header["modes"].values()
            if table is not None
        )
        table["gate"] = {"unlock_key": "KANTO_EARLY_ACCESS"}
        with self.assertRaisesRegex(WorldBalanceError, "runtime gate"):
            audit_world_balance_plan(broken)

    def test_independent_audit_rejects_slot_source_weight_and_tuple_mutations(self) -> None:
        def first_table(plan: dict) -> dict:
            return next(table for header in plan["headers"]
                        for table in header["modes"].values() if table is not None)

        broken = copy.deepcopy(self.plan)
        first_table(broken)["slots"][0][2] += 1
        with self.assertRaisesRegex(WorldBalanceError, "slot/source"):
            audit_world_balance_plan(broken)

        broken = copy.deepcopy(self.plan)
        first_table(broken)["source_weights"][0] += 1
        with self.assertRaisesRegex(WorldBalanceError, "slot/source"):
            audit_world_balance_plan(broken)

        broken = copy.deepcopy(self.plan)
        contract = first_table(broken)["group_allocation_contracts"][0]
        key = contract["eligible_source_keys"][0]
        contract["target_weight_by_source_key"][key] += 1
        with self.assertRaisesRegex(WorldBalanceError, "exact weight"):
            audit_world_balance_plan(broken)

        broken = copy.deepcopy(self.plan)
        broken["expected_positive_physical_tuples"].pop()
        with self.assertRaisesRegex(WorldBalanceError, "candidate脱落"):
            audit_world_balance_plan(broken)

    def test_rate_key_drift_fails_closed(self) -> None:
        with self.assertRaisesRegex(WorldBalanceError, "rate"):
            build_world_balance_plan(
                ROOT, self.rom, self.stage17, self.encounters, self.species,
                {"land_outdoor": 7},
            )

    def test_unachievable_manifest_weight_over_15_points_fails_closed(self) -> None:
        candidates = [
            {"encounter_key": "A", "slot": 1},
            {"encounter_key": "B", "slot": 2},
        ]
        with self.assertRaisesRegex(WorldBalanceError, "15.0001"):
            _allocate_group(candidates, [70, 30], {"A": 1, "B": 1})


if __name__ == "__main__":
    unittest.main()
