#!/usr/bin/env python3
"""工程2 actual-consumer checkpointの過大主張防止focused tests。"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_modernization_p02_acceptance as gate  # noqa: E402


class ModernizationP02AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / gate.DEFAULT_CONFIG).read_text(encoding="utf-8")
        )
        cls.evidence = json.loads(
            (ROOT / cls.config["output"]).read_text(encoding="utf-8")
        )

    def test_hidden_ability_readback_contract_is_exact_and_bounded(self) -> None:
        result = self.evidence["runtime_result"]
        gate._validate_runner_result(result, self.config)
        self.assertEqual(
            result["hidden_ability_readback"],
            {
                "bit_mask": 0x10,
                "conditional_item_consumed_cases": 6,
                "negative_branch_cases": 6,
                "regular_branch_cases": 12,
                "before_selection": True,
                "after_selection": True,
                "after_species_write": True,
                "after_calculate_stats": True,
                "all_observed_preserved": True,
            },
        )
        self.assertTrue(
            self.evidence["claims"]["hidden_ability_bit_readback_verified"]
        )
        self.assertFalse(self.evidence["claims"]["post_scene_ability_form_e2e"])
        self.assertFalse(self.evidence["claims"]["full_evolution_acceptance"])
        self.assertFalse(self.evidence["release_ready"])

    def test_validator_rejects_each_hidden_readback_overclaim(self) -> None:
        mutations = {
            "conditional_item_consumed_cases": 5,
            "negative_branch_cases": 5,
            "regular_branch_cases": 11,
            "before_selection": False,
            "after_selection": False,
            "after_species_write": False,
            "after_calculate_stats": False,
            "all_observed_preserved": False,
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                tampered = copy.deepcopy(self.evidence["runtime_result"])
                tampered["hidden_ability_readback"][key] = value
                with self.assertRaisesRegex(
                    gate.ModernizationP02AcceptanceError,
                    "hidden ability bit実read-back",
                ):
                    gate._validate_runner_result(tampered, self.config)

    def test_legacy_true_field_cannot_replace_actual_readback(self) -> None:
        tampered = copy.deepcopy(self.evidence["runtime_result"])
        self.assertTrue(
            tampered["target_application"]["hidden_ability_bit_preserved"]
        )
        del tampered["hidden_ability_readback"]
        with self.assertRaisesRegex(
            gate.ModernizationP02AcceptanceError,
            "hidden ability bit実read-back",
        ):
            gate._validate_runner_result(tampered, self.config)

    def test_runner_reports_measured_readbacks_not_a_fixed_true_literal(self) -> None:
        source = (
            ROOT / self.config["runtime"]["runner_source"]
        ).read_text(encoding="utf-8")
        self.assertIn(
            "bool apply_hidden_after_species_write = "
            "p02a_hidden_ability_bit(core);",
            source,
        )
        self.assertIn(
            "bool apply_hidden_after_calculate_stats = "
            "p02a_hidden_ability_bit(core);",
            source,
        )
        self.assertIn(r'\"hidden_ability_bit_preserved\":%s', source)
        self.assertNotIn(r'\"hidden_ability_bit_preserved\":true', source)


if __name__ == "__main__":
    unittest.main()
