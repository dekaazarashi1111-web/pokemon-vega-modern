from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_factory_special_event_runtime as builder


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "overlays/factory_special_event_runtime/factory_special_event_runtime.c"
)


class FactorySpecialEventRuntimeTest(unittest.TestCase):
    def test_manifest_catalog_binds_unique_49_streak_event(self) -> None:
        catalog, header, encoded = builder._catalog_outputs(ROOT)
        reward = catalog["reward"]
        self.assertEqual(catalog["selected_keys"], [builder.MANIFEST_KEY])
        self.assertEqual(reward["trigger_kind"], "SPECIAL_EVENT")
        self.assertEqual(reward["streak"], 49)
        self.assertEqual(reward["unlock_key"], "FACTORY_MASTER")
        self.assertEqual(
            reward["unlock_signal"],
            "VegaModernSaveData.league_ii_cleared",
        )
        self.assertEqual(reward["repeatability"], "ONCE")
        self.assertEqual(reward["claim_key"], "CLAIM_KEY_STREAK_049_EVENT")
        self.assertEqual((reward["claim_bit"], reward["claim_mask"]), (8, 0x100))
        self.assertEqual(json.loads(encoded), catalog)
        self.assertIn(b"FACTORY_SPECIAL_EVENT_STREAK_THRESHOLD 49u", header)
        self.assertIn(b"FACTORY_SPECIAL_EVENT_CLAIM_BIT 8u", header)
        self.assertIn(b"FACTORY_SPECIAL_EVENT_CLAIM_MASK 0x00000100u", header)

    def test_wrapper_calls_stage29_before_special_event_logic(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        stage29_call = source.index("u16 base_result = FN_STAGE29_COMPLETE();")
        apply_call = source.index("apply_special_event_claim();", stage29_call)
        self.assertLess(stage29_call, apply_call)
        self.assertIn(
            "base_result == FACTORY_SPECIAL_EVENT_BASE_RESULT",
            source,
        )
        self.assertIn("set_result(base_result);", source[apply_call:])

    def test_master_threshold_and_once_guards_are_fail_closed(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        validate = source.index("if (!ledger_valid())")
        master = source.index("if (!gVegaModernSaveData->league_ii_cleared)")
        threshold = source.index("< FACTORY_SPECIAL_EVENT_STREAK_THRESHOLD")
        once = source.index("& FACTORY_SPECIAL_EVENT_CLAIM_MASK) == 0u")
        self.assertLess(validate, master)
        self.assertLess(master, threshold)
        self.assertLess(threshold, once)

    def test_claim_transaction_snapshots_and_rolls_back_post_stage29_ledger(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        snapshot = source.index(
            "copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData"
        )
        set_claim = source.index(
            "reward_claim_bits |=\n        FACTORY_SPECIAL_EVENT_CLAIM_MASK",
            snapshot,
        )
        transaction = source.index("factory.transaction_id++;", set_claim)
        finalize = source.index("FN_SAVE_FINALIZE(gVegaModernSaveData);", transaction)
        persist = source.index("if (!persist_save_sector())", finalize)
        rollback = source.index("rollback_special_event();", persist)
        self.assertLess(snapshot, set_claim)
        self.assertLess(set_claim, transaction)
        self.assertLess(transaction, finalize)
        self.assertLess(finalize, persist)
        self.assertLess(persist, rollback)
        self.assertIn(
            "copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData",
            source,
        )
        self.assertNotIn("TrySavingData", source)


if __name__ == "__main__":
    unittest.main()
