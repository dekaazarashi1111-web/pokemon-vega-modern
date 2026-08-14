"""固定CFRUの技タイプ・有効度表示を結合したstage 24の限定回帰。"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_battle_ui import (  # noqa: E402
    EXPECTED_CFRU_COMMIT,
    RESERVED_ITEM_PLACEHOLDERS,
    RESERVED_SPECIES_PLACEHOLDERS,
    STAGE24,
    STAGE24_META,
    UPSTREAM_SYMBOLS,
    _battle_core_contract,
    _build_stage,
    audit_owner,
    audit_source,
)


class BattleUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads((ROOT / STAGE24_META).read_text(encoding="utf-8"))
        cls.fixture = json.loads(
            (ROOT / "build/stages/24_mgba_battle_ui.json").read_text(encoding="utf-8")
        )
        cls.policy = json.loads(
            (ROOT / "build/stages/24_mgba_battle_policy.json").read_text(encoding="utf-8")
        )

    def test_source_abi_is_pinned_and_original_ui_macros_were_disabled(self) -> None:
        audit = audit_source(ROOT)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["commit"], EXPECTED_CFRU_COMMIT)
        self.assertTrue(audit["source_lock_verified"])
        self.assertTrue(audit["source_checkout_clean"])
        self.assertFalse(any(audit["profile_ui_macros_active"].values()))
        self.assertEqual(len(audit["linked_symbols"]), 17)
        self.assertEqual(
            audit["linked_symbols"]["MoveSelectionDisplayMoveType"],
            {
                "address": UPSTREAM_SYMBOLS["MoveSelectionDisplayMoveType"][0],
                "size": UPSTREAM_SYMBOLS["MoveSelectionDisplayMoveType"][1],
            },
        )
        self.assertEqual(
            audit["linked_symbols"]["MoveSelectionDisplayMoveEffectiveness"],
            {
                "address": UPSTREAM_SYMBOLS[
                    "MoveSelectionDisplayMoveEffectiveness"
                ][0],
                "size": UPSTREAM_SYMBOLS[
                    "MoveSelectionDisplayMoveEffectiveness"
                ][1],
            },
        )

    def test_battle_core_pin_ignores_elapsed_time_but_keeps_ui_abi(self) -> None:
        metadata = json.loads(
            (ROOT / "build/stages/06_battle_core.json").read_text(encoding="utf-8")
        )
        pinned = json.loads(
            (ROOT / "config/battle_ui.json").read_text(encoding="utf-8")
        )["inputs"]["battle_core_metadata"]
        expected = {key: pinned[key] for key in _battle_core_contract(metadata)}
        self.assertEqual(_battle_core_contract(metadata), expected)

        elapsed_changed = copy.deepcopy(metadata)
        for index, run in enumerate(elapsed_changed["upstream_runs"], 1):
            run["elapsed_seconds"] = index * 0.001
        self.assertEqual(
            _battle_core_contract(elapsed_changed),
            _battle_core_contract(metadata),
        )

        abi_changed = copy.deepcopy(metadata)
        abi_changed["upstream_runs"][-1]["linked_object"]["sha256"] = "0" * 64
        self.assertNotEqual(
            _battle_core_contract(abi_changed),
            _battle_core_contract(metadata),
        )

    def test_all_move_menu_profiles_share_the_fixed_cfru_owner(self) -> None:
        audit = audit_owner(ROOT)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["address_audit"]["rows"], 15)
        self.assertEqual(
            audit["address_audit"]["profiles"],
            ["baseline", "factory-like", "minimal"],
        )
        self.assertEqual(audit["address_audit"]["classifications"], {"CFRU": 15})
        self.assertTrue(audit["global_owner_shared_by_normal_factory_raid"])

    def test_stage_build_is_deterministic_and_changes_only_two_entries(self) -> None:
        first, first_meta = _build_stage(ROOT)
        second, second_meta = _build_stage(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(first_meta, second_meta)
        self.assertEqual(first[STAGE24.as_posix()], (ROOT / STAGE24).read_bytes())
        self.assertEqual(first_meta["status"], "PASS")
        self.assertEqual(len(first_meta["patches"]), 2)
        self.assertEqual(
            {row["address"] for row in first_meta["patches"]},
            {
                UPSTREAM_SYMBOLS["MoveSelectionDisplayMoveType"][0],
                UPSTREAM_SYMBOLS["MoveSelectionDisplayMoveEffectiveness"][0],
            },
        )
        self.assertTrue(all(first_meta["invariants"].values()))

    def test_effectiveness_stab_stellar_and_input_routes_pass(self) -> None:
        value = self.fixture
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["process_runs"], 2)
        self.assertEqual(value["warnings_errors"], 0)
        self.assertEqual(
            {row["name"]: row["class"] for row in value["effect_cases"]},
            {
                "NORMAL_1X": 0,
                "SUPER_2X_OR_MORE": 1,
                "RESISTED_HALF_OR_LESS": 2,
                "NO_EFFECT_0X": 3,
                "SUPER_AND_STAB": 1,
            },
        )
        for row in value["effect_cases"]:
            self.assertEqual(row["class"], row["palette_group"])
            self.assertTrue(row["effect_label"])
            self.assertTrue(row["entry_completed"])
        self.assertTrue(next(
            row for row in value["effect_cases"] if row["name"] == "SUPER_AND_STAB"
        )["stab"])
        self.assertEqual(
            value["type_cases"],
            {"stellar": 24, "tera_blast_selected": 24, "tera_blast_clear": 10},
        )
        self.assertEqual(value["matrix_multipliers"], [500, 2000, 4000, 250, 0])
        self.assertTrue(value["double_target_specific"])
        self.assertTrue(value["actual_menu_path"])
        self.assertEqual(
            value["l_move_details"],
            {
                "opened": True,
                "accuracy_label": True,
                "closed": True,
                "pointer_stable": True,
                "button_mode": 1,
            },
        )
        self.assertTrue(value["input_return"])

    def test_live_names_and_factory_raid_regressions_pass(self) -> None:
        strings = self.metadata["string_audit"]
        self.assertTrue(all(not values for values in strings["live_unresolved"].values()))
        self.assertEqual(set(strings["reserved_inert_item_ids"]), RESERVED_ITEM_PLACEHOLDERS)
        self.assertEqual(
            set(strings["reserved_non_dex_species_ids"]),
            RESERVED_SPECIES_PLACEHOLDERS,
        )
        self.assertTrue(all(value == 0 for value in strings["first_battle_placeholder_item_entries"]))
        self.assertEqual(self.policy["status"], "PASS")
        self.assertEqual(self.policy["facility"]["matrix_cases"], 24)
        self.assertTrue(self.policy["facility"]["runtime_cleaned"])
        self.assertEqual(self.policy["raid"]["shield_breaks"], 5)
        self.assertTrue(self.policy["raid"]["raid_state_completion_scheduler_e2e"])
        self.assertTrue(self.policy["raid"]["runtime_cleaned"])
        self.assertTrue(all(self.metadata["acceptance"].values()))

    def test_adapter_uses_precomputed_visual_results_and_no_factory_bytes(self) -> None:
        source = (ROOT / "overlays/battle_ui/battle_ui.c").read_text(encoding="utf-8")
        self.assertIn("move_results[position][slot]", source)
        self.assertIn("z_move_results[position][slot]", source)
        self.assertIn("VegaBattleUI_ClassifyResult", source)
        self.assertNotIn("1×", source)
        self.assertNotIn("factory.gba", source.lower())
        self.assertIn("Factory ROMのbyteや独自相性表は持たず", source)
        runner = (ROOT / "tools/mgba_battle_ui_smoke.c").read_text(encoding="utf-8")
        self.assertNotIn("fopen(", runner)
        self.assertIn("run_multi_target_double(core, &field)", runner)


if __name__ == "__main__":
    unittest.main()
