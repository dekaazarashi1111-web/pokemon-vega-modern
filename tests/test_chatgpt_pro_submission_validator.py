from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT / "templates/chatgpt_pro_design_packets/tools/validate_submission.py"
)
SPEC = importlib.util.spec_from_file_location("chatgpt_pro_submission_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class RewardEncounterValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = {
            "custom": {
                "bp_prices": {
                    "RANDOM": 8,
                    "HABITAT": 15,
                    "TYPE": 25,
                    "RARE": 50,
                }
            }
        }
        self.services = [
            {"tier": tier, "credit_cost": "1", "bp_direct_price": str(price)}
            for tier, price in self.spec["custom"]["bp_prices"].items()
        ]
        self.pools = [
            {"tier": tier, "species_key": f"SPECIES_{tier}_{index}"}
            for tier in self.spec["custom"]["bp_prices"]
            for index in range(6)
        ]

    def validate(self, services: list[dict[str, str]]) -> list[str]:
        errors: list[str] = []
        VALIDATOR._custom_reward(
            {
                "encounter_services.csv": services,
                "encounter_pool_entries.csv": self.pools,
            },
            self.spec,
            {"forbidden_reward_species": set()},
            errors,
        )
        return errors

    def test_accepts_exactly_one_service_per_tier(self) -> None:
        self.assertEqual(self.validate(self.services), [])

    def test_rejects_duplicate_and_missing_tier(self) -> None:
        services = self.services[:-1] + [self.services[0].copy()]
        self.assertIn(
            "encounter_services.csv: exactly one service for each tier is required",
            self.validate(services),
        )


if __name__ == "__main__":
    unittest.main()
