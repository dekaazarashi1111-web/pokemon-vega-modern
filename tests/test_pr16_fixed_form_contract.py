from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pr16_fixed_form_contract.py"
spec = importlib.util.spec_from_file_location("fixed_form_contract", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixtures() -> tuple[dict, dict]:
    rows = []
    forms = []
    for offset, target in enumerate(m.EXPECTED_TARGET_ORDER):
        expected = m.EXPECTED_TARGETS[target]
        rows.append(
            {
                "target_species_id": target,
                "target_species_key": expected["species_key"],
                "reference_id": f"ref-{target}",
                "source_route": {
                    "route_id": f"route-{target}",
                    "route_kind": "direct",
                    "method": "battle_transform",
                    "project_move_id": 500 + offset,
                    "official_move_id": 700 + offset,
                },
            }
        )
        forms.append(
            {
                "base_species": expected["base_species"],
                "base_species_key": expected["base_species_key"],
                "species_key": expected["species_key"],
                "target_species": target,
                "method": "FORM_CHANGE_SERVICE",
                "method_id": 4,
                "unlock": "FINAL_LEAGUE_CLEARED",
                "unlock_id": 15,
                "distributable": True,
            }
        )
    owner = {
        "route_count": 4,
        "species_count": 4,
        "species": list(m.EXPECTED_TARGET_ORDER),
        "rows": rows,
    }
    model = {"forms": forms, "service_form_indices": [0, 1, 2, 3]}
    return owner, model


class FixedFormContractTests(unittest.TestCase):
    def test_exact_four_targets_validate(self) -> None:
        owner, model = fixtures()
        plans = m.validate(owner, model)
        self.assertEqual(
            [row["target_species"] for row in plans],
            list(m.EXPECTED_TARGET_ORDER),
        )
        self.assertEqual([row["service_index"] for row in plans], [0, 1, 2, 3])
        self.assertTrue(all(row["native_acceptance_required"] for row in plans))

    def test_direct_owner_is_required(self) -> None:
        owner, model = fixtures()
        owner["rows"][0]["source_route"]["route_kind"] = "form_change"
        with self.assertRaisesRegex(m.ContractError, "direct ownership"):
            m.validate(owner, model)

    def test_all_targets_must_remain_in_authored_service(self) -> None:
        owner, model = fixtures()
        model["service_form_indices"].pop()
        with self.assertRaisesRegex(m.ContractError, "left the authored FORM service"):
            m.validate(owner, model)

    def test_unlock_and_method_are_fail_closed(self) -> None:
        owner, model = fixtures()
        model["forms"][0]["unlock_id"] = 6
        with self.assertRaisesRegex(m.ContractError, "unlock id changed"):
            m.validate(owner, model)

    def test_case_matrix_covers_every_fixed_target(self) -> None:
        covered = {
            target
            for case in m.CASE_MATRIX
            for target in case["targets"]
        }
        self.assertEqual(covered, set(m.EXPECTED_TARGET_ORDER))
        self.assertEqual(len({case["id"] for case in m.CASE_MATRIX}), len(m.CASE_MATRIX))
        self.assertTrue(
            all(case["required_witnesses"] for case in m.CASE_MATRIX)
        )

    def test_contract_status_cannot_be_misread_as_acceptance(self) -> None:
        self.assertEqual(m.STATUS, "PASS_FIXED_FORM_CONTRACT_NATIVE_PENDING")
        self.assertNotIn("ACCEPTED", m.STATUS)


if __name__ == "__main__":
    unittest.main()
