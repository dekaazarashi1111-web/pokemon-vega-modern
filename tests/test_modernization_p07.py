#!/usr/bin/env python3
"""工程7のlayer/precedence/conflict focused tests。"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_modernization_p07 import render_outputs  # noqa: E402
from tools.modernization_identity import load_manifests  # noqa: E402
from tools.modernization_p07_learnsets import (  # noqa: E402
    ModernizationP07Error,
    NORMAL_TO_VEGA,
    VEGA_TO_NORMAL,
    build_p07_contract,
    validate_and_resolve_additions,
    validate_and_resolve_deletions,
    validate_p07_contract,
)


class ModernizationP07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # private ZIPのhash確認を各testで繰り返さない。
        cls.contract = build_p07_contract(ROOT)
        cls.manifests = load_manifests(ROOT)
        cls.p04_unallocated = frozenset(
            cls.contract["source_evidence"]["upstream_contract_audit"][
                "p04_unallocated_species_keys"
            ]
        )

    @staticmethod
    def _row(
        change_key: str,
        direction: str,
        species_key: str,
        move_key: str,
        *,
        method: str = "level_up",
        route_kind: str = "direct",
        level: int | None = 20,
        conditions: dict | None = None,
        availability: dict | None = None,
    ) -> dict:
        return {
            "change_key": change_key,
            "direction": direction,
            "target_species_key": species_key,
            "target_form_key": "",
            "move_key": move_key,
            "route_kind": route_kind,
            "method": method,
            "level": level,
            "conditions": conditions or {},
            "availability": availability
            or {
                "timing_ja": "中盤以降",
                "restriction_ja": "対象系統のみ",
                "relearn_policy": "同じ独自layerから再習得",
            },
            "intent_ja": "提出済み案のfixture",
            "source_decision_ref": "TEST_ADOPTED_DECISION",
            "p06_review_key": "P06_TEST_REVIEW",
            "existing_moveset_policy": "NEW_GENERATION_AND_LEARNING_ONLY",
        }

    def _resolve(self, rows: list[dict], *, p06_ready: bool = True) -> list[dict]:
        return validate_and_resolve_additions(
            rows,
            self.manifests["species"],
            self.manifests["moves"],
            p04_unallocated_species_keys=self.p04_unallocated,
            unavailable_move_keys=frozenset({"MOVE_KEY_ALLYSWITCH"}),
            p06_ready=p06_ready,
        )

    def test_no_unsubmitted_cross_distribution_is_adopted(self) -> None:
        self.assertEqual(
            self.contract["summary"]["normal_species_to_vega_move_adopted"], 0
        )
        self.assertEqual(
            self.contract["summary"]["vega_species_to_normal_move_adopted"], 0
        )
        self.assertEqual(self.contract["summary"]["explicit_deletions_adopted"], 0)
        self.assertEqual(
            self.contract["adopted_delta"]["submission_status"],
            "NO_P07_DISTRIBUTION_ROWS_SUBMITTED",
        )
        self.assertEqual(self.contract["adopted_delta"]["invented_rows"], [])

    def test_layer_precedence_keeps_original_and_custom_separate(self) -> None:
        model = self.contract["layer_model"]
        self.assertEqual(
            model["precedence_low_to_high"],
            [
                "BASE_EXISTING",
                "P03_ORIGINAL_RESTORATION",
                "P07_NORMAL_SPECIES_TO_VEGA_MOVE",
                "P07_VEGA_SPECIES_TO_NORMAL_MOVE",
                "P07_EXPLICIT_DELETION",
            ],
        )
        original = model["layers"]["P03_ORIGINAL_RESTORATION"]
        self.assertEqual(original["operation"], "REPLACE_TARGET_LEARNSET_WITH_FIXED_REFERENCE")
        self.assertEqual(original["routes"], 118_369)
        self.assertFalse(original["custom_distribution"])
        for layer in (
            "P07_NORMAL_SPECIES_TO_VEGA_MOVE",
            "P07_VEGA_SPECIES_TO_NORMAL_MOVE",
            "P07_EXPLICIT_DELETION",
        ):
            self.assertEqual(model["layers"][layer]["records"], [])

    def test_p03_targets_only_normal_species_and_side_change_stays_excluded(self) -> None:
        audit = self.contract["source_evidence"]["upstream_contract_audit"]
        self.assertEqual(
            audit["p03_species_classifications"],
            {
                "DPE_FORM_APPEND": 275,
                "DPE_SPECIES_APPEND": 820,
                "VEGA_DPE_CANONICAL": 205,
            },
        )
        self.assertEqual(audit["p03_vega_original_target_count"], 0)
        self.assertEqual(audit["p04_learnset_distribution_fields"], 0)
        side = audit["side_change_1063"]
        self.assertEqual(side["p03_source_route_count"], 159)
        self.assertEqual(side["p03_adopted_route_count"], 0)
        self.assertEqual(side["p03_excluded_route_count"], 159)
        self.assertIsNone(side["canonical_id"])
        self.assertIsNone(side["replacement_move_key"])
        self.assertEqual(
            side["status"], "P03_NOT_ADOPTED_USER_DECISION_NOT_P07_CUSTOM"
        )

    def test_direction_domains_resolve_by_keys(self) -> None:
        normal_to_vega = self._row(
            "P07_TEST_NORMAL_TO_VEGA",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
        )
        vega_to_normal = self._row(
            "P07_TEST_VEGA_TO_NORMAL",
            VEGA_TO_NORMAL,
            "SPECIES_KEY_VEGA_001",
            "MOVE_KEY_POUND",
        )
        rows = self._resolve([normal_to_vega, vega_to_normal])
        by_key = {row["change_key"]: row for row in rows}
        self.assertEqual(by_key["P07_TEST_NORMAL_TO_VEGA"]["target_species_id"], 649)
        self.assertEqual(by_key["P07_TEST_NORMAL_TO_VEGA"]["move_id"], 292)
        self.assertEqual(by_key["P07_TEST_NORMAL_TO_VEGA"]["species_domain"], "NORMAL_SPECIES")
        self.assertEqual(by_key["P07_TEST_NORMAL_TO_VEGA"]["move_domain"], "VEGA_MOVE")
        self.assertEqual(by_key["P07_TEST_VEGA_TO_NORMAL"]["target_species_id"], 1)
        self.assertEqual(by_key["P07_TEST_VEGA_TO_NORMAL"]["move_id"], 1)

    def test_wrong_direction_and_duplicate_consumer_conflicts_fail(self) -> None:
        wrong = self._row(
            "P07_TEST_WRONG",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_VEGA_001",
            "MOVE_KEY_POUND",
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([wrong])

        first = self._row(
            "P07_TEST_DUPLICATE_A",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
            level=20,
        )
        second = self._row(
            "P07_TEST_DUPLICATE_B",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
            level=30,
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([first, second])

    def test_route_specific_conditions_are_not_flattened(self) -> None:
        pre_evolution = self._row(
            "P07_TEST_PRE_EVOLUTION",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
            route_kind="pre_evolution",
            method="level_up",
            level=None,
            conditions={
                "donor_species_key": "SPECIES_KEY_WEEDLE",
                "donor_learning_level": 12,
            },
        )
        row = self._resolve([pre_evolution])[0]
        self.assertEqual(row["consumer"], "pre_evolution_carry")
        self.assertIsNone(row["level"])
        self.assertEqual(
            row["condition_identity"],
            {
                "donor_species_key": "SPECIES_KEY_WEEDLE",
                "donor_species_id": 415,
                "donor_form_key": "",
            },
        )

        missing_donor = copy.deepcopy(pre_evolution)
        missing_donor["change_key"] = "P07_TEST_PRE_EVOLUTION_BAD"
        missing_donor["conditions"] = {}
        with self.assertRaises(ModernizationP07Error):
            self._resolve([missing_donor])

        unknown_donor = copy.deepcopy(pre_evolution)
        unknown_donor["change_key"] = "P07_TEST_PRE_EVOLUTION_UNKNOWN"
        unknown_donor["conditions"]["donor_species_key"] = "SPECIES_KEY_NOT_REAL"
        with self.assertRaises(ModernizationP07Error):
            self._resolve([unknown_donor])

        shared = self._row(
            "P07_TEST_SHARED_BAD",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
            route_kind="shared_egg",
            method="shared_egg",
            level=None,
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([shared])

    def test_machine_and_tutor_require_full_supply_contract(self) -> None:
        incomplete = self._row(
            "P07_TEST_MACHINE_BAD",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
            method="tm",
            level=None,
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([incomplete])

        complete = copy.deepcopy(incomplete)
        complete["change_key"] = "P07_TEST_MACHINE_GOOD"
        complete["availability"].update(
            {
                "supply_key": "ITEM_KEY_TEST_TM",
                "runtime_slot_key": "TM_SLOT_TEST",
                "cost_policy": "ONE_ITEM_CONSUMED",
                "unlock_key": "UNLOCK_TEST",
                "cancel_policy": "CANCEL_PRESERVES_ITEM_AND_MOVESET",
            }
        )
        self.assertEqual(self._resolve([complete])[0]["consumer"], "machine")

    def test_p04_side_change_and_p06_dependencies_block_nonempty_rows(self) -> None:
        p04_species = sorted(self.p04_unallocated)[0]
        p04_row = self._row(
            "P07_TEST_P04_BLOCKED",
            NORMAL_TO_VEGA,
            p04_species,
            "MOVE_KEY_VEGA_292",
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([p04_row])

        side_change = self._row(
            "P07_TEST_SIDE_CHANGE_BLOCKED",
            VEGA_TO_NORMAL,
            "SPECIES_KEY_VEGA_001",
            "MOVE_KEY_ALLYSWITCH",
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([side_change])

        ready_shape = self._row(
            "P07_TEST_P06_BLOCKED",
            NORMAL_TO_VEGA,
            "SPECIES_KEY_CATERPIE",
            "MOVE_KEY_VEGA_292",
        )
        with self.assertRaises(ModernizationP07Error):
            self._resolve([ready_shape], p06_ready=False)

    def test_explicit_deletion_must_resolve_exact_lower_layer_identity(self) -> None:
        addition = self._resolve(
            [
                self._row(
                    "P07_TEST_DELETE_TARGET",
                    NORMAL_TO_VEGA,
                    "SPECIES_KEY_CATERPIE",
                    "MOVE_KEY_VEGA_292",
                )
            ]
        )
        deletion = {
            "deletion_key": "P07_DELETE_TEST_TARGET",
            "target_layer": "P07_NORMAL_SPECIES_TO_VEGA_MOVE",
            "target_change_key": "P07_TEST_DELETE_TARGET",
            "p03_route_id": None,
            "reason_ja": "明示採用された削除fixture",
            "source_decision_ref": "TEST_DELETE_DECISION",
        }
        resolved = validate_and_resolve_deletions([deletion], addition)
        self.assertEqual(resolved[0]["verification"], "TARGET_CUSTOM_CHANGE_RESOLVED")

        missing = copy.deepcopy(deletion)
        missing["deletion_key"] = "P07_DELETE_TEST_MISSING"
        missing["target_change_key"] = "P07_TEST_DOES_NOT_EXIST"
        with self.assertRaises(ModernizationP07Error):
            validate_and_resolve_deletions([missing], addition)

        duplicate = copy.deepcopy(deletion)
        duplicate["deletion_key"] = "P07_DELETE_TEST_TARGET_AGAIN"
        with self.assertRaises(ModernizationP07Error):
            validate_and_resolve_deletions([deletion, duplicate], addition)

    def test_contract_validator_rejects_false_done_or_invented_rows(self) -> None:
        mutations = []
        false_done = copy.deepcopy(self.contract)
        false_done["runtime_handoff"]["runtime_implemented"] = True
        mutations.append(false_done)

        invented = copy.deepcopy(self.contract)
        invented["adopted_delta"]["normal_species_to_vega_move"] = [
            {"change_key": "P07_INVENTED"}
        ]
        mutations.append(invented)

        summary = copy.deepcopy(self.contract)
        summary["summary"]["vega_species_to_normal_move_adopted"] = 1
        mutations.append(summary)

        false_p06_ready = copy.deepcopy(self.contract)
        false_p06_ready["inputs"]["p06"]["p06_ready_for_p07"] = True
        mutations.append(false_p06_ready)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ModernizationP07Error):
                    validate_p07_contract(mutation)

    def test_generated_outputs_are_deterministic(self) -> None:
        outputs = render_outputs(self.contract)
        self.assertEqual(
            set(outputs),
            {
                "content/modernization/p07_layered_learnset_contract.json",
                "content/modernization/p07_runtime_handoff.json",
            },
        )
        for relative, raw in outputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), raw, relative)
            self.assertIsInstance(json.loads(raw), dict)


if __name__ == "__main__":
    unittest.main()
