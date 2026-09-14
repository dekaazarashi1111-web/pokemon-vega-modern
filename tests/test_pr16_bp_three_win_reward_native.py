"""Focused source/acceptance tests for the native three-win 9-BP witness.

The dedicated workflow extends the already accepted retained prefix in one
process.  These tests only validate the new transformation and fail-closed
result boundary; they do not replay prior native acceptance cases.
"""
from pathlib import Path
import copy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]

import pr16_bp_three_win_reward_native as p
import pr16_bp_win_exchange as win


class ThreeWinRewardNativeTests(unittest.TestCase):
    SHA = "1" * 64

    def fixture(self):
        return {
            "schema_version": 1,
            "status": p.STATUS,
            "scope": p.SCOPE,
            "case": p.CASE,
            "candidate_sha256": self.SHA,
            "battle_outcome": 1,
            "second_battle_outcome": 1,
            "third_battle_outcome": 1,
            "second_reward_pending": 2,
            "second_streak": 2,
            "second_bp": 0,
            "third_reward_pending": 3,
            "third_streak": 3,
            "third_bp_before_complete": 0,
            "bp_before_reward": 0,
            "bp_after_reward": 9,
            "bp_delta": 9,
            "bp_earned": 9,
            "reward_final_pending": 0,
            "reward_final_streak": 3,
            "reward_final_marker": 0,
            "reward_final_snapshot_valid": 0,
            "reward_final_party_count": 1,
            "special_result": 9,
            "original_party_restored_bytes": 600,
            "native_three_win_reward_accepted": True,
            "native_bp_earning_accepted": True,
            "p05_native_bp_gap_closed": True,
            "release_ready": False,
            "second_afterbattle_frame": 100,
            "third_afterbattle_frame": 200,
            "reward_complete_frame": 220,
        }

    def test_exact_three_win_reward_is_scoped_acceptance(self):
        accepted = p.accept_reward(self.fixture(), self.SHA)
        self.assertEqual(accepted["classification"], "SCOPED_ACCEPTANCE")
        self.assertEqual(accepted["native_battle_wins_observed"], 3)
        self.assertEqual(accepted["bp_delta"], 9)
        self.assertEqual(accepted["special_result"], 9)
        self.assertTrue(accepted["native_bp_earning_accepted"])
        self.assertFalse(accepted["native_bp_spending_accepted"])
        self.assertFalse(accepted["release_ready"])
        self.assertEqual(accepted["accepted_native_cases_replayed"], 0)

    def test_reward_amount_and_transient_ledgers_fail_closed(self):
        mutations = (
            ("second_reward_pending", 1),
            ("second_streak", 1),
            ("second_bp", 1),
            ("third_reward_pending", 2),
            ("third_streak", 2),
            ("third_bp_before_complete", 9),
            ("bp_before_reward", 1),
            ("bp_after_reward", 8),
            ("bp_delta", 8),
            ("bp_earned", 8),
            ("special_result", 8),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                row = self.fixture()
                row[key] = value
                with self.assertRaises(ValueError):
                    p.accept_reward(row, self.SHA)

    def test_completion_restore_and_scope_overclaim_fail_closed(self):
        mutations = (
            ("reward_final_pending", 1),
            ("reward_final_streak", 2),
            ("reward_final_marker", 2),
            ("reward_final_snapshot_valid", 1),
            ("reward_final_party_count", 3),
            ("original_party_restored_bytes", 500),
            ("native_three_win_reward_accepted", False),
            ("native_bp_earning_accepted", False),
            ("p05_native_bp_gap_closed", False),
            ("release_ready", True),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                row = self.fixture()
                row[key] = value
                with self.assertRaises(ValueError):
                    p.accept_reward(row, self.SHA)

    def test_identity_and_three_native_wins_are_required(self):
        with self.assertRaises(ValueError):
            p.accept_reward(self.fixture(), "2" * 64)
        for key in ("battle_outcome", "second_battle_outcome", "third_battle_outcome"):
            row = self.fixture()
            row[key] = 2
            with self.assertRaises(ValueError):
                p.accept_reward(row, self.SHA)

    def test_controller_extends_only_unobserved_suffix(self):
        text = p.controller_for_scope(win)
        self.assertEqual(text.count(p.STATUS), 1)
        self.assertEqual(text.count(p.CASE), 1)
        self.assertEqual(text.count(p.SCOPE), 1)
        self.assertIn(
            "br_battle_return(struct mCore *c,const uint8_t *original,unsigned counter,unsigned expected_streak)",
            text,
        )
        self.assertIn(
            "wx_exchange_next(struct mCore *c,const uint8_t *original,unsigned counter,unsigned observed_win,unsigned expected_streak)",
            text,
        )
        self.assertIn("br_battle_return(c,party,counter,1U)", text)
        self.assertIn("br_battle_return(c,original,counter,2U)", text)
        self.assertIn("wx_exchange_next(c,party,counter,finish.outcome,1U)", text)
        self.assertIn("wx_exchange_next(c,original,counter,second.outcome,2U)", text)
        self.assertIn("struct RWResult reward=rw_three_win(c,party,counter);", text)
        self.assertIn("unsigned prefix_identity_checks=wx_identity_checks;", text)
        self.assertIn(",exchange.opening,prefix_identity_checks);", text)
        self.assertNotIn(",exchange.opening,wx_identity_checks);", text)
        self.assertIn(r'\"native_bp_earning_accepted\":true', text)
        self.assertIn(r'\"p05_native_bp_gap_closed\":true', text)
        self.assertIn(r'\"release_ready\":false', text)

    def test_new_controller_source_has_no_game_memory_write_or_direct_call(self):
        source = (ROOT / p.SOURCE).read_text()
        for forbidden in ("write8(", "write16(", "write32(", "call_preserving("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertIn("b_frame(c,", source)
        self.assertIn("br_move(c,&w)", source)
        self.assertIn("br_switch(c,&w)", source)
        self.assertIn("RW_EXPECTED_BP 9U", source)
        self.assertIn("original party", source)

    def test_duplicate_json_keys_fail(self):
        with self.assertRaises(ValueError):
            p.strict('{"x":1,"x":2}')
        row = copy.deepcopy(self.fixture())
        self.assertEqual(p.strict(p.stable(row)), row)


if __name__ == "__main__":
    unittest.main()
