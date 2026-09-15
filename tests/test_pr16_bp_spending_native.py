from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pr16_bp_spending_native as spending


class BpSpendingContractTests(unittest.TestCase):
    def row(self) -> dict[str, object]:
        return {
            "status": spending.STATUS,
            "scope": spending.SCOPE,
            "case": spending.CASE,
            "candidate_sha256": "a" * 64,
            "native_three_win_reward_accepted": True,
            "native_bp_earning_accepted": True,
            "bp_before_purchase": 9,
            "bp_after_purchase": 8,
            "bp_after_continue": 8,
            "item_id": spending.ITEM_ID,
            "catalog_index": 0,
            "price_bp": spending.PRICE_BP,
            "purchase_result": 0,
            "item_count_before": 2,
            "item_count_after_purchase": 3,
            "item_count_after_continue": 3,
            "save_counter_before_purchase": 10,
            "save_counter_after_purchase": 11,
            "save_counter_after_manual": 12,
            "save_counter_after_continue": 12,
            "automatic_saves": 1,
            "manual_saves": 1,
            "fresh_cores": 2,
            "physical_shop_local_id": 3,
            "native_bp_spending_accepted": True,
            "p05_native_bp_spending_closed": True,
            "release_ready": False,
        }

    def test_accepts_exact_purchase_and_persistence(self) -> None:
        accepted = spending.accept_spending(self.row(), "a" * 64)
        self.assertTrue(accepted["native_bp_spending_accepted"])
        self.assertEqual(accepted["purchase"]["bp_after"], 8)
        self.assertEqual(accepted["persistence"]["item_count_after_continue"], 3)

    def test_rejects_missing_bp_debit(self) -> None:
        row = copy.deepcopy(self.row())
        row["bp_after_purchase"] = 9
        with self.assertRaises(spending.BpSpendingError):
            spending.accept_spending(row, "a" * 64)

    def test_rejects_unpersisted_item(self) -> None:
        row = copy.deepcopy(self.row())
        row["item_count_after_continue"] = 2
        with self.assertRaises(spending.BpSpendingError):
            spending.accept_spending(row, "a" * 64)

    def test_field_wait_cannot_confirm_after_idle_appears(self) -> None:
        source = (ROOT / spending.SOURCE).read_text()
        start = source.index("static void bs_wait_field")
        end = source.index("static void bs_wait_menu", start)
        wait = source[start:end]
        self.assertIn("bool idle=b_field(c);", wait)
        self.assertIn("!idle && read8(c,P02S_FIELD_LOCK)", wait)
        self.assertIn("?QOL_KEY_B:0U", wait)
        self.assertNotIn("?QOL_KEY_A:0U", wait)


if __name__ == "__main__":
    unittest.main()
