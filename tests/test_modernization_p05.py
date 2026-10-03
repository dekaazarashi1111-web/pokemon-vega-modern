#!/usr/bin/env python3
"""工程5 battle content契約のfocused tests。"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_modernization_p05 import render_outputs  # noqa: E402
from tools.modernization_p05_contract import (  # noqa: E402
    ModernizationP05Error,
    P04_ALLOWED_NEW_ABILITY_KEYS,
    P03_RUNTIME_PATH,
    _load_p03_runtime,
    _verify_technical_checkout,
    build_p05_contract,
    validate_p05_contract,
)


class ModernizationP05ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 82.7 MiB ZIPのidentity確認と外部source走査をtestごとに繰り返さない。
        cls.contract = build_p05_contract(ROOT)

    def test_summary_is_the_submitted_delta_only(self) -> None:
        self.assertEqual(
            self.contract["summary"],
            {
                "adopted_performance_adjustment_count": 0,
                "confirmed_data_only_patch_count": 0,
                "existing_official_ability_assignment_count": 29,
                "held_candidate_count": 2,
                "new_ability_requirement_count": 6,
                "new_move_requirement_count": 0,
                "non_adopted_move_candidate_count": 1,
                "non_adopted_p04_record_count": 3,
                "preserved_reference_difference_count": 4,
                "runtime_blocker_count": 1,
                "temporary_ability_assignment_count": 14,
                "temporary_ability_record_count_including_hold": 16,
            },
        )
        self.assertEqual(
            self.contract["policy"]["unsubmitted_move_or_ability"], "DO_NOT_CREATE"
        )
        self.assertEqual(
            self.contract["baseline"]["v3"]["selected_as_new_p05_delta"], 0
        )

    def test_side_change_is_not_adopted_and_has_no_replacement(self) -> None:
        self.assertEqual([], self.contract["move_content"]["new_move_requirements"])
        move = self.contract["move_content"]["non_adopted_move_candidates"][0]
        self.assertEqual(move["move_key"], "MOVE_KEY_ALLYSWITCH")
        self.assertEqual(move["requested_project_id"], 1063)
        self.assertIsNone(move["canonical_id"])
        self.assertEqual(move["selection_status"], "NOT_ADOPTED_BY_USER_DECISION")
        self.assertEqual(move["identity"]["current_last_id"], 1062)
        self.assertEqual(move["identity"]["source_proposed_manifest_count"], 1064)
        self.assertEqual(move["identity"]["adopted_manifest_count"], 1063)
        self.assertEqual(move["source_p03_routes"]["target_count"], 103)
        self.assertEqual(move["source_p03_routes"]["route_count"], 159)
        self.assertEqual(move["source_p03_routes"]["adopted_route_count"], 0)
        self.assertEqual(sum(move["source_p03_routes"]["by_consumer"].values()), 159)
        self.assertFalse(move["exclusion"]["manifest_allocation"])
        self.assertFalse(move["exclusion"]["runtime_implementation"])
        self.assertIsNone(move["exclusion"]["replacement_move_key"])
        self.assertIsNone(move["effect_policy"]["effect_mapping"])
        self.assertFalse(move["effect_policy"]["reuse_existing_effect"])
        self.assertEqual(
            set(move["missing_specification_fields"]),
            {
                "runtime_split", "target", "effect", "secondary_chance", "flags",
                "description_ja", "animation",
            },
        )

    def test_four_reference_differences_are_preserved_not_patched(self) -> None:
        content = self.contract["move_content"]
        self.assertEqual(content["adopted_performance_adjustments"], [])
        self.assertEqual(content["p04_new_move_requests"], [])
        rows = content["preserved_reference_differences"]
        self.assertEqual([row["canonical_id"] for row in rows], [762, 779, 837, 1058])
        expected = {
            762: {"accuracy": [0, 100]},
            779: {"accuracy": [0, 100]},
            837: {"pp": [15, 10]},
            1058: {"power": [1, 0]},
        }
        for row in rows:
            self.assertEqual(row["reference_delta"], expected[row["canonical_id"]])
            self.assertEqual(row["before"], row["after"])
            self.assertEqual(row["decision"], "PRESERVE_CURRENT_NO_PATCH")
            self.assertFalse(row["data_only_patch_eligible"])
        self.assertEqual(
            self.contract["data_only_patch_plan"]["confirmed_patches"], []
        )

    def test_p04_temporary_abilities_are_explicit_and_replaceable(self) -> None:
        abilities = self.contract["ability_content"]
        assignments = abilities["assignments"]
        temporary = [row for row in assignments if row["temporary_replaceable"]]
        held = abilities["held_records"]
        self.assertEqual(len(assignments), 49)
        self.assertEqual(len(temporary), 14)
        self.assertEqual(len(held), 2)
        self.assertEqual(len(temporary) + len(held), 16)
        triggers = []
        for row in temporary + held:
            self.assertIsInstance(row["canonical_id"], int)
            self.assertTrue(row["replacement_trigger_key"].startswith("REPLACEMENT_KEY_ABILITY_"))
            triggers.append(row["replacement_trigger_key"])
        self.assertEqual(len(triggers), len(set(triggers)))
        for row in temporary:
            self.assertFalse(row["official_confirmed"])
            self.assertEqual(row["presentation_guard"], "MUST_LABEL_TEMPORARY_NOT_OFFICIAL")
        non_adopted = abilities["non_adopted_records"]
        self.assertEqual(
            {row["record_key"] for row in non_adopted},
            {"P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA"},
        )
        self.assertTrue(all(not row["manifest_allocation"] for row in non_adopted))
        self.assertTrue(all(not row["runtime_implementation"] for row in non_adopted))

    def test_six_new_abilities_remain_unassigned_and_have_pinned_references(self) -> None:
        rows = self.contract["ability_content"]["new_ability_requirements"]
        self.assertEqual({row["ability_key"] for row in rows}, P04_ALLOWED_NEW_ABILITY_KEYS)
        source_ids = {}
        for row in rows:
            self.assertIsNone(row["canonical_id"])
            self.assertEqual(row["id_status"], "UNASSIGNED_APPEND_ALLOCATION_REQUIRED")
            reference = row["technical_reference"]
            self.assertIsNone(reference["name_ja"])
            self.assertIsNone(reference["description_ja"])
            self.assertTrue(
                any(item["surface"] == "EFFECT_REFERENCE" for item in reference["occurrences"])
            )
            source_ids[row["ability_key"]] = row["do_not_copy_source_numeric_id"]
        self.assertEqual(
            source_ids,
            {
                "ABILITY_KEY_PIERCINGDRILL": 311,
                "ABILITY_KEY_DRAGONIZE": 312,
                "ABILITY_KEY_EELEVATE": 313,
                "ABILITY_KEY_MEGASOL": 315,
                "ABILITY_KEY_FIREMANE": 316,
                "ABILITY_KEY_SPICYSPRAY": 318,
            },
        )
        self.assertEqual(
            self.contract["inputs"]["ability_technical_source"]["commit"],
            "cafe0221cefb2a991cc0ece429174ade877d037d",
        )
        self.assertTrue(
            self.contract["inputs"]["ability_technical_source"][
                "checkout_clean_observed"
            ]
        )

    def test_technical_checkout_rejects_dirty_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=source, check=True)
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.invalid"],
                cwd=source,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "fixture"], cwd=source, check=True,
            )
            subprocess.run(
                ["git", "remote", "add", "origin", "https://example.invalid/source.git"],
                cwd=source,
                check=True,
            )
            tracked = source / "tracked.txt"
            tracked.write_text("fixed\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=source, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=source, check=True)
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=source, check=True,
                stdout=subprocess.PIPE, text=True,
            ).stdout.strip()
            identity = _verify_technical_checkout(
                source,
                expected_commit=commit,
                expected_repository="https://example.invalid/source",
            )
            self.assertTrue(identity["checkout_clean_observed"])
            (source / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ModernizationP05Error, "dirty"):
                _verify_technical_checkout(
                    source,
                    expected_commit=commit,
                    expected_repository="https://example.invalid/source",
                )

    def test_p03_runtime_requires_current_regular_worktree_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ModernizationP05Error, "現行P03 runtime契約"):
                _load_p03_runtime(Path(temporary))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            handoff = root / "content/modernization/p03_runtime_handoff.json"
            handoff.parent.mkdir(parents=True)
            handoff.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                ModernizationP05Error, "Git tracked worktree file"
            ):
                _load_p03_runtime(root)
            subprocess.run(
                ["git", "add", "content/modernization/p03_runtime_handoff.json"],
                cwd=root,
                check=True,
            )
            loaded, identity = _load_p03_runtime(root)
            self.assertEqual({}, loaded)
            self.assertEqual(P03_RUNTIME_PATH, identity["path"])

        self.assertEqual(
            self.contract["inputs"]["p03_runtime"]["resolution"],
            "CURRENT_TRACKED_WORKTREE_REQUIRED_NO_HISTORICAL_FALLBACK",
        )

    def test_existing_evolution_trigger_moves_are_not_redefined(self) -> None:
        rows = self.contract["move_content"]["existing_evolution_trigger_moves"]
        self.assertEqual(
            {row["move_key"]: row["canonical_id"] for row in rows},
            {"MOVE_KEY_HYPERDRILL": 1013, "MOVE_KEY_TWINBEAM": 1042},
        )
        self.assertTrue(
            all(row["definition_status"] == "EXISTING_RUNTIME_NOT_A_NEW_P05_MOVE" for row in rows)
        )

    def test_save_contract_separates_identity_from_stored_slots(self) -> None:
        save = self.contract["save_compatibility"]
        self.assertEqual(
            save["moves"]["numeric_capacity"],
            "U16_CURRENT_CANONICAL_IDS_0_TO_1062",
        )
        self.assertEqual(save["moves"]["pp_change_migration"], "NOT_REQUIRED_NO_ADOPTED_PP_CHANGE")
        self.assertEqual(
            save["abilities"]["storage_model"],
            "ABILITY_SLOT_BITS_PLUS_SPECIES_TABLE_DERIVATION",
        )
        assertions = {
            assertion
            for evidence in save["evidence"]
            for assertion in evidence["assertions"]
        }
        self.assertIn("stored_move_slots_are_u16", assertions)
        self.assertIn("stored_ability_is_selection_bits_not_canonical_ability_id", assertions)

    def test_validator_rejects_invented_or_false_ready_content(self) -> None:
        mutations = []

        performance = copy.deepcopy(self.contract)
        performance["move_content"]["adopted_performance_adjustments"] = [
            {"move_key": "MOVE_KEY_INVENTED"}
        ]
        mutations.append(performance)

        move_effect = copy.deepcopy(self.contract)
        move_effect["move_content"]["non_adopted_move_candidates"][0]["effect_policy"][
            "effect_mapping"
        ] = "EFFECT_HIT"
        mutations.append(move_effect)

        move_replacement = copy.deepcopy(self.contract)
        move_replacement["move_content"]["non_adopted_move_candidates"][0][
            "exclusion"
        ]["replacement_move_key"] = "MOVE_KEY_TELEPORT"
        mutations.append(move_replacement)

        ability_id = copy.deepcopy(self.contract)
        ability_id["ability_content"]["new_ability_requirements"][0]["canonical_id"] = 312
        mutations.append(ability_id)

        temporary_official = copy.deepcopy(self.contract)
        temporary_row = next(
            row
            for row in temporary_official["ability_content"]["assignments"]
            if row["temporary_replaceable"]
        )
        temporary_row["official_confirmed"] = True
        mutations.append(temporary_official)

        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                with self.assertRaises(ModernizationP05Error):
                    validate_p05_contract(mutation)

    def test_tracked_outputs_are_exactly_reproducible(self) -> None:
        outputs = render_outputs(self.contract)
        self.assertEqual(
            set(outputs),
            {
                "content/modernization/p05_battle_content_contract.json",
                "content/modernization/p05_runtime_handoff.json",
                "content/modernization/p05_data_only_patch_plan.json",
            },
        )
        for relative, expected in outputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), expected, relative)
            # JSON decodeも行い、途中切れの生成物を許可しない。
            self.assertIsInstance(json.loads(expected), dict)


if __name__ == "__main__":
    unittest.main()
