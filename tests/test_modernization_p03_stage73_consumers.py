from __future__ import annotations

import unittest
from pathlib import Path

from tools import modernization_p03_stage73_consumers as core


ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path("config/modernization_p03_stage73_consumers.json")


class ModernizationP03Stage73ConsumersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 82MiB固定ZIPの全route streamはtest process内で1回だけ。
        cls.audit = core.build_preflight(ROOT, CONFIG)
        cls.config = core.read_config(ROOT, CONFIG)

    def test_five_selected_groups_and_group_hashes_are_exact(self) -> None:
        self.assertEqual(self.audit["source_route_count"], 118528)
        self.assertEqual(self.audit["selection_boundary"]["five_group_selected_count"], 40570)
        self.assertEqual(
            {name: row["selected_count"] for name, row in self.audit["consumer_groups"].items()},
            {"egg": 2563, "shared_egg": 5023, "pre_evolution_carry": 35141,
             "reminder": 295, "form_change": 70},
        )
        for name, row in self.audit["consumer_groups"].items():
            expected = self.config["consumer_groups"][name]
            self.assertEqual(row["source_group_sha256"], expected["source_group_sha256"])
            self.assertEqual(row["selected_group_sha256"], expected["selected_group_sha256"])

    def test_runtime_existing_owner_and_supply_claims_are_separate(self) -> None:
        egg = self.audit["consumer_groups"]["egg"]
        self.assertEqual((egg["stage73_scope_count"], egg["special_breeding_existing_owner"],
                          egg["exact_override_pending_runtime_hook"]), (41, 1, 40))
        shared = self.audit["consumer_groups"]["shared_egg"]
        self.assertEqual((shared["direct_egg_overlap"], shared["shared_only"]), (2272, 2751))
        carry = self.audit["consumer_groups"]["pre_evolution_carry"]
        self.assertEqual((carry["existing_generic_move_slot_persistence_semantics"],
                          carry["machine_tutor_upstream_supply_dependency"],
                          carry["new_runtime_materialized_count"]), (35141, 23578, 0))
        form = self.audit["consumer_groups"]["form_change"]
        self.assertEqual((form["existing_generic_carry_owner"], form["existing_fixed_transition_owner"],
                          form["rotom_transition_owner_missing"], form["new_runtime_materialized_count"]),
                         (61, 4, 5, 0))

    def test_side_change_and_false_serialization_are_fail_closed(self) -> None:
        boundary = self.audit["selection_boundary"]
        self.assertEqual((boundary["side_change_global_excluded_count"],
                          boundary["side_change_five_group_excluded_count"]), (159, 72))
        self.assertEqual(boundary["browt_pombon_gecqua_adopted_count"], 0)
        self.assertTrue(all(value == 0 for value in self.audit["prohibited_coercions"].values()))
        self.assertFalse(self.audit["claims"]["stage73_completion_claim_allowed"])

    def test_pending_stage72_identity_rejects_rom_work(self) -> None:
        self.assertEqual(self.audit["status"], "PASS_PREFLIGHT_PARENT_PENDING")
        with self.assertRaisesRegex(core.ModernizationP03Stage73ConsumersError,
                                    "Stage72 identity未確定"):
            core.require_pinned_parent(self.config)


if __name__ == "__main__":
    unittest.main()
