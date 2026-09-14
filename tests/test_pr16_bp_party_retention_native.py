"""Acceptance boundary tests for the repaired native party-retention witness."""
from pathlib import Path
import copy
import sys
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts")]
import pr16_bp_party_retention_native as p


class RetentionNativeTests(unittest.TestCase):
    SHA = "1" * 64

    def fixture(self):
        checkpoint = {
            "frame": 20,
            "party_sha256": "2" * 64,
            "changed_bytes": 0,
            "individuals": [{"personality": 1}],
            "exchanged_slots": [2],
        }
        return {
            "classification": "DIAGNOSTIC_ONLY_NOT_ACCEPTANCE",
            "candidate_sha256": self.SHA,
            "snapshot_count": 7,
            "exchange_slot": 2,
            "committed": copy.deepcopy(checkpoint),
            "first_changed": None,
            "next_chooser": copy.deepcopy(checkpoint),
            "next_action": copy.deepcopy(checkpoint),
            "active_battler": {"personality": 1},
            "exchanged_individual_retained": True,
            "all_three_individuals_retained": True,
            "exact600_retained": True,
            "observation_boundary": "READ_ONLY_FRAME_SNAPSHOTS_NOT_CPU_FUNCTION_ENTRY_RETURN",
            "native_bp_earning_accepted": False,
            "p05_native_bp_gap_closed": False,
            "release_ready": False,
        }

    def test_exact_retention_is_accepted_without_bp_scope(self):
        result = p.accept_identity(self.fixture(), self.SHA)
        self.assertTrue(result["native_party_retention_accepted"])
        self.assertTrue(result["exact600_retained"])
        self.assertFalse(result["native_bp_earning_accepted"])
        self.assertFalse(result["release_ready"])

    def test_any_post_commit_change_fails_closed(self):
        for key, value in (
            ("first_changed", {"frame": 21}),
            ("exact600_retained", False),
            ("all_three_individuals_retained", False),
            ("exchanged_individual_retained", False),
        ):
            row = self.fixture()
            row[key] = value
            with self.assertRaises(ValueError):
                p.accept_identity(row, self.SHA)

    def test_checkpoint_hash_or_candidate_mismatch_fails(self):
        row = self.fixture()
        row["next_action"]["party_sha256"] = "3" * 64
        with self.assertRaises(ValueError):
            p.accept_identity(row, self.SHA)
        with self.assertRaises(ValueError):
            p.accept_identity(self.fixture(), "4" * 64)

    def test_bp_and_release_overclaim_fail(self):
        for key in ("native_bp_earning_accepted", "p05_native_bp_gap_closed", "release_ready"):
            row = self.fixture()
            row[key] = True
            with self.assertRaises(ValueError):
                p.accept_identity(row, self.SHA)

    def test_scope_replacement_is_exact(self):
        class Identity:
            STATUS = "OLD_STATUS"
            CASE = "old-case"
            SCOPE = "OLD_SCOPE"

            @staticmethod
            def assemble_controller():
                return "OLD_STATUS old-case OLD_SCOPE"

        text = p.controller_for_scope(Identity)
        self.assertEqual(text, f"{p.STATUS} {p.CASE} {p.SCOPE}")
        with self.assertRaises(ValueError):
            p.replace_once("xx", "x", "y")


if __name__ == "__main__":
    unittest.main()
