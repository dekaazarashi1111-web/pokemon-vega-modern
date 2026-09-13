from __future__ import annotations

import unittest
from pathlib import Path

from tools.modernization_identity import stable_json
from tools.modernization_learnsets import (
    EXPECTED_COMPILED_COUNTS,
    ModernizationLearnsetError,
    build_p03_artifacts,
    consumer_for_route,
)


ROOT = Path(__file__).resolve().parents[1]
LEARNSETS = ROOT / (
    "userfile/imports/modernization_p01/"
    "Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905.zip"
)


class ModernizationP03Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 376 MB相当のJSONL走査はtest process内で一度だけ行う。
        cls.artifacts = build_p03_artifacts(ROOT, LEARNSETS)
        cls.contract = cls.artifacts.contract
        cls.index = cls.artifacts.compiled_index
        cls.handoff = cls.artifacts.runtime_handoff

    def test_caterpie_only_correction_matches_p01_identity(self) -> None:
        correction = self.contract["correction"]
        self.assertEqual(1299, correction["source_adopted_records"])
        self.assertEqual(1300, correction["corrected_adopted_records"])
        self.assertEqual(["SPECIES_KEY_CATERPIE"], correction["added_keys"])
        self.assertEqual([], correction["removed_keys"])
        self.assertEqual(
            (649, "swordshield:0010.00", 4),
            (
                correction["caterpie"]["canonical_id"],
                correction["caterpie"]["reference_id"],
                correction["caterpie"]["route_count"],
            ),
        )
        self.assertEqual(
            {"species_key": "SPECIES_KEY_EGG", "canonical_id": 412, "apply": False},
            correction["egg"],
        )

    def test_all_records_and_full_content_are_fingerprinted(self) -> None:
        self.assertEqual((1300, 118528), (self.index["record_count"], self.index["route_count"]))
        self.assertEqual(118369, self.index["selected_route_count"])
        self.assertEqual(159, self.index["excluded_route_count"])
        rows = self.index["records"]
        self.assertEqual(1300, len(rows))
        self.assertEqual(sorted(row["canonical_id"] for row in rows), [row["canonical_id"] for row in rows])
        self.assertEqual(1300, len({row["species_key"] for row in rows}))
        self.assertNotIn("SPECIES_KEY_EGG", {row["species_key"] for row in rows})
        caterpie = next(row for row in rows if row["species_key"] == "SPECIES_KEY_CATERPIE")
        self.assertEqual("ADD_CATERPIE_FROM_REFERENCE", caterpie["origin"])
        self.assertEqual(4, caterpie["route_count"])
        self.assertEqual(
            "5b627a53452f7e004f57701ccd9eec086049b5246dea06eaf66e2bc5a7544fb5",
            self.contract["corrected_adoption"]["record_content_sha256"],
        )
        self.assertEqual(
            "2b2d7cfd1f03b32f4de4a4666e81348f35887e4ab43837451b19387af04820b3",
            self.contract["corrected_adoption"]["target_route_key_set_sha256"],
        )

    def test_nine_consumers_are_an_exact_partition(self) -> None:
        consumers = self.contract["corrected_adoption"]["consumers"]
        self.assertEqual(EXPECTED_COMPILED_COUNTS, {key: row["count"] for key, row in consumers.items()})
        self.assertEqual(118528, sum(row["count"] for row in consumers.values()))
        self.assertEqual(
            "277e80b384e34c238ce151f85ac2ee18e8904b0be65af3c34dd93b54361d1c42",
            self.contract["corrected_adoption"]["compiled_route_content_sha256"],
        )
        selected = self.contract["runtime_selection"]
        self.assertEqual(118369, selected["selected_routes"])
        self.assertEqual(159, selected["excluded_routes"])
        self.assertEqual(
            118369,
            sum(row["count"] for row in selected["consumers"].values()),
        )

    def test_carry_and_form_routes_cannot_become_direct(self) -> None:
        self.assertEqual(
            "pre_evolution_carry",
            consumer_for_route({"route_kind": "pre_evolution", "method": "tm"}),
        )
        self.assertEqual(
            "form_change",
            consumer_for_route({"route_kind": "form_change", "method": "egg"}),
        )
        self.assertEqual(
            "machine", consumer_for_route({"route_kind": "direct", "method": "tr"}),
        )
        carry = self.handoff["fixtures"]["pre_evolution_carry"]
        self.assertEqual("pre_evolution", carry["route_kind"])
        self.assertIsNone(carry["target_learning_level"])
        self.assertEqual("CARRY_ONLY_NO_TARGET_DIRECT_BIT", carry["runtime_supply_status"])
        with self.assertRaises(ModernizationLearnsetError):
            consumer_for_route({"route_kind": "shared_egg", "method": "egg"})

    def test_original_tm_number_is_not_runtime_slot(self) -> None:
        caterpie = self.contract["correction"]["caterpie"]["compiled_routes"]
        machine = next(row for row in caterpie if row["consumer"] == "machine")
        self.assertEqual("TM82", machine["source_machine_item"])
        self.assertEqual(116, machine["runtime_slot_zero_based"])
        supply = self.contract["runtime_supply"]
        self.assertEqual(56493, supply["source_candidate_direct_machine_tutor_pairs"])
        self.assertEqual(56421, supply["direct_machine_tutor_pairs"])
        self.assertEqual(72, supply["excluded_candidate_pairs"])
        self.assertEqual(29773, supply["existing_slot_projection_rows"])
        self.assertEqual(26648, supply["supply_required_rows"])
        self.assertEqual({"machine": 184, "tutor": 31}, supply["supply_required_distinct_moves_by_family"])

    def test_side_change_1063_is_explicitly_not_adopted_without_replacement(self) -> None:
        side = self.handoff["side_change_1063"]
        self.assertEqual("NOT_ADOPTED_BY_USER_DECISION", side["status"])
        self.assertEqual((1063, 502), (side["project_move_id"], side["official_move_id"]))
        self.assertEqual((0, 0), (side["adopted_target_count"], side["adopted_route_count"]))
        self.assertEqual((103, 159), (side["source_target_count"], side["source_route_count"]))
        self.assertEqual(159, side["excluded_route_count"])
        self.assertEqual(
            {
                "egg": 9, "level_up": 15, "machine": 68,
                "pre_evolution_carry": 42, "reminder": 3,
                "shared_egg": 18, "tutor": 4,
            },
            side["routes_by_consumer"],
        )
        self.assertEqual("EXCLUDE_FROM_ALL_LEARNSET_CONSUMERS", side["decision"]["route_action"])
        self.assertEqual("DO_NOT_IMPLEMENT_OR_ALLOCATE", side["decision"]["runtime_action"])
        self.assertIsNone(side["decision"]["replacement_move_key"])

    def test_runtime_connections_preserve_existing_saves_and_explicit_parties(self) -> None:
        connection = self.handoff["connection_points"]
        self.assertEqual(1063, connection["current_abi"]["move_count"])
        self.assertIn("GetMoveRelearnerMoves", connection["current_consumers"]["level_up"])
        self.assertIn("GetAllEggMoves", connection["current_consumers"]["egg"])
        self.assertIn("CanMonLearnTMHM", connection["current_consumers"]["tm_tutor"])
        self.assertIn("既存party/box/saveロード時は変更しない", self.handoff["preservation"]["wild_generation"])
        self.assertIn("自動置換しない", self.handoff["preservation"]["trainer_facility"])

    def test_tracked_documents_match_the_deterministic_build(self) -> None:
        for relative, document in self.artifacts.output_documents().items():
            path = ROOT / relative
            self.assertTrue(path.is_file() and not path.is_symlink())
            self.assertEqual(stable_json(document), path.read_bytes(), relative)


if __name__ == "__main__":
    unittest.main()
