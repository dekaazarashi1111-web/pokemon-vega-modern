from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "pr16_p03_form_gap_inventory.py"
)
spec = importlib.util.spec_from_file_location("form_gap_inventory", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(species: int, route_kind: str, method: str = "level_up") -> dict:
    return {
        "target_species_id": species,
        "source_route": {
            "route_kind": route_kind,
            "method": method,
        },
    }


class FormGapInventoryTests(unittest.TestCase):
    def test_three_owners_are_disjoint(self) -> None:
        self.assertEqual(m.classify(row(386, "form_change")), "generic_carry")
        self.assertEqual(
            m.classify(row(1260, "direct", "battle_transform")),
            "fixed_transition",
        )
        self.assertEqual(
            m.classify(row(894, "direct", "form_move")),
            "rotom_transition",
        )

    def test_unknown_direct_owner_fails(self) -> None:
        with self.assertRaises(m.InventoryError):
            m.classify(row(386, "direct"))

    def test_fixed_or_rotom_cannot_be_generic(self) -> None:
        for species in sorted(m.FIXED_FORM_SPECIES | m.ROTOM_FORM_SPECIES):
            with self.subTest(species=species), self.assertRaises(m.InventoryError):
                m.classify(row(species, "form_change"))

    def test_unknown_route_kind_fails(self) -> None:
        with self.assertRaises(m.InventoryError):
            m.classify(row(386, "shared_egg"))

    def test_expected_owner_total_is_seventy(self) -> None:
        self.assertEqual(
            m.EXPECTED,
            {"generic_carry": 61, "fixed_transition": 4, "rotom_transition": 5},
        )
        self.assertEqual(sum(m.EXPECTED.values()), 70)


if __name__ == "__main__":
    unittest.main()
