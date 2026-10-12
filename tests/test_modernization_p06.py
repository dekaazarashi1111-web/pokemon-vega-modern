#!/usr/bin/env python3
"""工程6の採用差分0・候補隔離・Species consumer契約のfocused test。"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p06_species import (
    P06SpeciesError,
    _validate_projection,
    audit_p06,
    calculate_stat,
)


class ModernizationP06Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "content/modernization/p06_species_adjustment_contract.json").read_text(encoding="utf-8")
        )
        cls.projection = json.loads(
            (ROOT / "content/modernization/p06_review_projection.json").read_text(encoding="utf-8")
        )
        cls.report = audit_p06(ROOT)

    def test_adopted_delta_is_empty_and_runtime_patch_is_forbidden(self) -> None:
        self.assertEqual("PASS", self.report["status"])
        self.assertEqual(0, self.report["adopted_delta_count"])
        self.assertFalse(self.report["runtime_patch_authorized"])
        self.assertFalse(self.report["implementation_ready"])
        self.assertFalse(self.report["rom_modified"])
        self.assertEqual("CHECKPOINT_NOT_P06_DONE", self.report["completion_state"])

    def test_review_archive_projection_is_complete_and_deterministic(self) -> None:
        review = self.report["review_projection"]
        self.assertEqual("PASS", review["archive_rebuild"])
        self.assertEqual(194, review["review_record_count"])
        self.assertEqual(
            {"base_stats": 21, "types": 7, "abilities": 190},
            review["field_candidate_counts"],
        )
        self.assertEqual(1, review["confirmed_transcription_or_id_bug_field_count"])
        self.assertEqual(217, review["original_restoration_review_field_count"])

    def test_scyther_discrepancy_is_separated_but_not_adopted(self) -> None:
        scyther = next(row for row in self.projection["records"] if row["species_key"] == "SPECIES_KEY_SCYTHER")
        self.assertEqual("FORM_KEY_BASE", scyther["form_key"])
        stats = scyther["fields"]["base_stats"]
        self.assertEqual("CONFIRMED_TRANSCRIPTION_OR_ID_BUG_REVIEW_ONLY", stats["classification"])
        self.assertEqual("NOT_ADOPTED", stats["adoption_status"])
        self.assertEqual(570, stats["before_total"])
        self.assertEqual(500, stats["target_total"])
        self.assertEqual(
            {"hp": 70, "attack": 110, "defense": 80, "sp_attack": 55, "sp_defense": 80, "speed": 105},
            stats["target"],
        )
        self.assertEqual("ORIGINAL_RESTORATION_REVIEW_ONLY", scyther["fields"]["abilities"]["classification"])

    def test_all_archive_fields_remain_review_only(self) -> None:
        self.assertTrue(self.projection["records"])
        identities = set()
        for row in self.projection["records"]:
            identity = (row["species_key"], row["form_key"])
            self.assertNotIn(identity, identities)
            identities.add(identity)
            self.assertEqual("FORM_KEY_BASE", row["form_key"])
            self.assertEqual("REVIEW_ONLY_NOT_ADOPTED", row["record_status"])
            self.assertTrue(row["fields"])
            for field in row["fields"].values():
                self.assertEqual("NOT_ADOPTED", field["adoption_status"])

    def test_unsubmitted_vega_custom_references_have_no_delta(self) -> None:
        candidates = self.contract["review_partition"]["vega_custom_candidates"]
        self.assertEqual({"SPECIES_KEY_VEGA_220", "SPECIES_KEY_VEGA_373"}, {row["species_key"] for row in candidates})
        self.assertTrue(all(row["submitted_delta"] is None for row in candidates))
        self.assertTrue(all(row["status"] == "SPEC_NOT_SUBMITTED_NOT_ADOPTED" for row in candidates))

    def test_consumer_roots_and_ability_slots_are_exact(self) -> None:
        consumer = self.report["runtime_consumer"]
        self.assertEqual("PASS", consumer["status"])
        self.assertEqual(1621, consumer["species_count"])
        self.assertEqual(32, consumer["stride"])
        self.assertEqual("0x09600000", consumer["root_address"])
        self.assertEqual(105, consumer["repoint_count"])
        self.assertEqual([6, 7], consumer["type_offsets"])
        self.assertEqual([22, 26, 28], consumer["ability_u16_offsets"])
        self.assertLess(consumer["max_type_id_used"], 24)
        self.assertLess(consumer["max_ability_id_used"], 312)

    def test_stat_formula_boundaries_for_review_target(self) -> None:
        self.assertEqual(177, calculate_stat(70, level=50, iv=31, ev=252, is_hp=True))
        self.assertEqual(344, calculate_stat(70, level=100, iv=31, ev=252, is_hp=True))
        self.assertEqual(162, calculate_stat(110, level=50, iv=31, ev=252, is_hp=False))
        self.assertEqual(
            178,
            calculate_stat(
                110,
                level=50,
                iv=31,
                ev=252,
                is_hp=False,
                nature_numerator=11,
                nature_denominator=10,
            ),
        )
        self.assertEqual(
            99,
            calculate_stat(
                105,
                level=50,
                iv=0,
                ev=0,
                is_hp=False,
                nature_numerator=9,
                nature_denominator=10,
            ),
        )

    def test_unapproved_delta_injection_fails_closed(self) -> None:
        broken_contract = copy.deepcopy(self.contract)
        broken_contract["adoption"]["adopted_delta_count"] = 1
        broken_contract["adoption"]["adopted_delta_records"] = [{"species_key": "SPECIES_KEY_SCYTHER"}]
        with self.assertRaisesRegex(P06SpeciesError, "未承認delta"):
            _validate_projection(broken_contract, self.projection)


if __name__ == "__main__":
    unittest.main()
