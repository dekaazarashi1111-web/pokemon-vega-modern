from __future__ import annotations
import copy
import sys
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pr16_bp_spending_native as spending
from test_pr16_bp_shop_observer_abi import BpShopObserverAbiTests

class BpSpendingContractTests(unittest.TestCase):
    def row(self) -> dict[str, object]:
        before = 2
        return {
            "status": spending.STATUS, "scope": spending.SCOPE, "case": spending.CASE,
            "candidate_sha256": "a" * 64,
            "native_three_win_reward_accepted": True, "native_bp_earning_accepted": True,
            "reward_settled_frame": 100, "reward_field_frame": 160,
            "base_reward_bp": spending.BASE_REWARD_BP,
            "active_repeat_reward_bp": spending.REPEAT_REWARD_BP,
            "reward_wrapper_saves": spending.REWARD_WRAPPER_SAVES,
            "bp_before_purchase": spending.STABLE_REWARD_BP,
            "bp_after_purchase": spending.STABLE_REWARD_BP - spending.PRICE_BP,
            "bp_after_continue": spending.STABLE_REWARD_BP - spending.PRICE_BP,
            "item_id": spending.ITEM_ID, "catalog_index": spending.CATALOG_INDEX,
            "price_bp": spending.PRICE_BP, "purchase_result": 0,
            "item_count_before": before, "item_count_after_purchase": before + 1,
            "item_count_after_continue": before + 1,
            "save_counter_before_purchase": 10, "save_counter_after_purchase": 11,
            "save_counter_after_manual": 12, "save_counter_after_continue": 12,
            "automatic_saves": 1, "manual_saves": 1, "fresh_cores": 2,
            "physical_shop_local_id": 3,
            "native_bp_spending_accepted": True,
            "p05_native_bp_spending_closed": True, "release_ready": False,
        }

    def test_accepts_exact_purchase_and_persistence(self) -> None:
        accepted = spending.accept_spending(self.row(), "a" * 64)
        self.assertEqual(accepted["purchase"]["catalog_index"], 0)
        self.assertEqual(accepted["purchase"]["bp_after"], 8)

    def test_rejects_missing_debit_or_persistence(self) -> None:
        for key, value in (("bp_after_purchase", 12), ("item_count_after_continue", 2)):
            row = copy.deepcopy(self.row()); row[key] = value
            with self.assertRaises(spending.BpSpendingError):
                spending.accept_spending(row, "a" * 64)

    def test_source_contracts(self) -> None:
        source = (ROOT / spending.SOURCE).read_text()
        for marker in (
            "#define BS_ITEM_ID 0x00C3U", "#define BS_CATALOG_INDEX 0U",
            "#define BS_PRICE_BP 4U", "BS_STATE + 0x64U", "BS_STATE + 0x66U",
            "BS_STATE + 0x68U", "BS_STATE + 0x6AU", "b_to(c,BS_SHOP_X,BS_SHOP_Y)",
            ")&15U)==BS_FACING_NORTH",
        ):
            self.assertIn(marker, source)
        route = source[source.index("static void bs_walk_to_shop"):source.index("static void bs_wait_save_counter")]
        self.assertNotIn("call_preserving", route)
        self.assertNotIn("write", route)

if __name__ == "__main__":
    unittest.main()
