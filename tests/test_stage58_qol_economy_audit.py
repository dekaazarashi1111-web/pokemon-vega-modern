from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage58_qol_economy_audit import (  # noqa: E402
    STAGE57_ROM,
    STAGE57_SHA256,
    apply_patch_plan,
    build_audit,
)


class Stage58QolEconomyAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom_path = ROOT / STAGE57_ROM
        cls.rom = cls.rom_path.read_bytes()
        cls.report = build_audit(ROOT)

    def test_stage57_identity_and_upstream_evidence_are_exact(self) -> None:
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), STAGE57_SHA256)
        self.assertTrue(self.report["input"]["stage57_exact"])
        self.assertEqual(self.report["status"], "REPAIR_REQUIRED")
        for key in ("stage36_quick", "stage36_full", "stage40", "stage56", "stage57"):
            self.assertEqual(self.report["existing_validation"][key]["status"], "PASS")
        self.assertTrue(all(row["rooted_in_stage57"] for row in self.report["runtime_symbols"]))

    def test_effect_evidence_does_not_treat_purchase_as_effect(self) -> None:
        effects = self.report["qol_effect_items"]
        self.assertEqual(effects["count"], 36)
        self.assertEqual(effects["callback_bound_count"], 36)
        self.assertEqual(effects["effect_execution_proven_count"], 13)
        self.assertEqual(effects["effect_execution_unproven_count"], 23)
        self.assertEqual(effects["effect_then_fresh_core_reload_proven_count"], 0)
        self.assertEqual(effects["effect_then_fresh_core_reload_unproven_count"], 36)
        self.assertEqual(effects["missable_after_sale_count"], 0)
        unproven = set(effects["effect_execution_unproven"])
        self.assertIn("ITEM_KEY_ABILITY_CAPSULE", unproven)
        self.assertIn("ITEM_KEY_ABILITY_PATCH", unproven)
        self.assertEqual(sum(key.endswith("_MINT") for key in unproven), 21)

    def test_money_arbitrage_duplicate_owner_and_raid_leak_are_quantified(self) -> None:
        economy = self.report["economy"]
        self.assertEqual(economy["collection_money_rows"], 86)
        self.assertEqual(economy["money_buy_sell_arbitrage_count"], 1)
        self.assertEqual(economy["money_buy_sell_arbitrage"][0], {
            "item_key": "ITEM_KEY_HONEY",
            "item_id": 410,
            "buy_money": 300,
            "sell_money": 450,
            "profit_per_cycle": 150,
            "repeatability": "REPEATABLE",
        })
        self.assertEqual(economy["projected_money_buy_sell_arbitrage_count"], 0)
        self.assertEqual(economy["collection_qol_bp_duplicate_count"], 47)
        self.assertEqual(economy["projected_collection_qol_bp_duplicate_count"], 0)
        self.assertEqual(economy["research_daily_point_cap"], 116)
        self.assertTrue(economy["bp_research_to_money_direct_conversion"])
        self.assertFalse(economy["money_to_bp_research_reverse_conversion"])
        self.assertEqual(economy["same_currency_infinite_profit_cycle_count"], 1)
        self.assertEqual(economy["t19_bp_money_per_point_ceiling"], 1250)
        self.assertEqual(economy["collection_bp_money_per_point_ceiling"], 2000)
        self.assertEqual(
            economy["projected_collection_bp_money_per_point_ceiling"], 1250,
        )
        self.assertEqual(economy["t23_research_money_per_point_ceiling"], 125)
        self.assertEqual(
            economy["collection_research_money_per_point_ceiling"], 1187.5,
        )
        self.assertEqual(
            economy["projected_collection_research_money_per_point_ceiling"], 125,
        )
        self.assertEqual(economy["collection_research_reprice_count"], 71)
        self.assertEqual(economy["collection_research_daily_money_conversion_max"], 134750)
        self.assertEqual(
            economy["projected_collection_research_daily_money_conversion_max"], 14500,
        )

        raid = self.report["raid_rewards"]
        self.assertEqual(raid["low_pool_pre_entry_total_weight"], 550)
        self.assertEqual(raid["exp_candy_xs_pre_entry_weight"], 90)
        self.assertAlmostEqual(raid["exp_candy_xs_pre_entry_probability"], 90 / 550)
        self.assertEqual(raid["pre_unlock_leak_count"], 1)
        self.assertEqual(raid["projected_pre_unlock_leak_count"], 0)

    def test_patch_plan_is_exact_non_overlapping_and_memory_replayable(self) -> None:
        plan = self.report["patch_plan"]
        self.assertEqual(plan["count"], 121)
        self.assertEqual(plan["pending_count"], 121)
        self.assertEqual(plan["applied_count"], 0)
        self.assertEqual(plan["overlap_count"], 0)
        self.assertTrue(all(row["state"] == "PENDING" for row in plan["rows"]))
        keys = {row["key"] for row in plan["rows"]}
        self.assertIn("COLLECTION_HONEY_MONEY_ARBITRAGE", keys)
        self.assertIn("LOW_RAID_EXP_CANDY_XS_UNLOCK", keys)
        self.assertIn("QOL_ABILITY_PATCH_REACQUISITION", keys)
        self.assertIn("COLLECTION_QOL_OWNER_ITEM_KEY_ABILITY_PATCH", keys)
        self.assertIn(
            "COLLECTION_RESEARCH_PRICE_ITEM_KEY_MASTERPIECE_TEACUP", keys,
        )

        by_key = {row["key"]: row for row in plan["rows"]}
        self.assertEqual(by_key["COLLECTION_HONEY_MONEY_ARBITRAGE"]["address"], "0x0940C3C2")
        self.assertEqual(by_key["COLLECTION_HONEY_MONEY_ARBITRAGE"]["expected_hex"], "2c01")
        self.assertEqual(by_key["COLLECTION_HONEY_MONEY_ARBITRAGE"]["replacement_hex"], "8403")
        self.assertEqual(by_key["LOW_RAID_EXP_CANDY_XS_UNLOCK"]["address"], "0x094084AC")
        self.assertEqual(by_key["QOL_ABILITY_PATCH_REACQUISITION"]["address"], "0x0938152F")

        patched = apply_patch_plan(self.rom, self.report)
        self.assertNotEqual(patched, self.rom)
        patched_path = ROOT / ".local/stage58_qol_economy_test.gba"
        # build_audit accepts a byte-exact file, but unit tests do not write a
        # derived ROM.  Instead, applying the same report twice proves every
        # expected/replacement gate is idempotent in memory.
        self.assertEqual(apply_patch_plan(patched, self.report), patched)
        self.assertFalse(patched_path.exists())

    def test_stage58_completion_requires_effect_and_reload_cases(self) -> None:
        cases = self.report["required_stage58_verification_cases"]
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({case["id"] for case in cases}), 10)
        self.assertTrue(all(case["required"] for case in cases))
        self.assertTrue(all(case["verification"] == "EXACT_ROM_MGBA"
                            for case in cases))
        ids = {case["id"] for case in cases}
        self.assertIn("T19_ABILITY_PATCH_TRANSACTION", ids)
        self.assertIn("QOL_NORMAL_BAG_UI_5_FAMILIES", ids)
        self.assertIn("QOL_EFFECT_FRESH_RELOAD_36", ids)
        self.assertIn("ACTUAL_TRAINER_FACTORY_EARN_PURCHASE_RELOAD", ids)
        normal_bag = next(
            case for case in cases
            if case["id"] == "QOL_NORMAL_BAG_UI_5_FAMILIES"
        )
        self.assertEqual(
            ["normal_bag_ui_family_paths"], normal_bag["tests"],
        )
        self.assertIn("未証明23品", self.report["decision"]["completion_gate"])

    def test_transaction_proof_distinguishes_balance_injection_from_real_earn(self) -> None:
        evidence = self.report["transaction_evidence"]
        self.assertIn("残高注入", evidence["currency_acquisition"]["MONEY"])
        self.assertIn("残高注入", evidence["currency_acquisition"]["BP"])
        self.assertIn("6活動", evidence["currency_acquisition"]["RESEARCH"])
        self.assertFalse(evidence["purchase_routes"]["T19_QOL_BP"]["purchase_persist_failure_rollback"])
        self.assertTrue(evidence["purchase_routes"]["T23_RESEARCH"]["success_all_23"])
        self.assertFalse(
            evidence["purchase_routes"]["STAGE56_COLLECTION_MONEY_BP_RESEARCH"]
            ["fresh_core_reload_after_purchase"]
        )

    def test_stage58_rom_is_auditable_with_exact_metadata_callback(self) -> None:
        stage58_rom = ROOT / "build/stages/58_qol_world_convenience_debug.gba"
        metadata_path = ROOT / "build/stages/58_qol_world_convenience_debug.json"
        self.assertTrue(stage58_rom.exists())
        self.assertTrue(metadata_path.exists())

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        callback = metadata["qol_item_bag_adapter"]["replacement_callback"]
        report = build_audit(
            ROOT, stage58_rom, require_stage57_identity=False,
            hyper_service_item_callback=callback,
        )

        self.assertFalse(report["input"]["stage57_exact"])
        self.assertEqual(report["patch_plan"]["pending_count"], 0)
        self.assertEqual(report["patch_plan"]["applied_count"], 121)
        hyper_rows = [
            row for row in report["qol_effect_items"]["rows"]
            if row["effect_kind"] == "HYPER_SERVICE_ITEM"
        ]
        self.assertEqual(len(hyper_rows), 2)
        self.assertTrue(all(
            row["entry_route"] == "BAG_FIELD_CALLBACK_ADAPTER_TO_SERVICE_17"
            for row in hyper_rows
        ))


if __name__ == "__main__":
    unittest.main()
