from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_factory_shiny_memorial_runtime as builder


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "overlays/factory_shiny_memorial_runtime/factory_shiny_memorial_runtime.c"
)


class FactoryShinyMemorialRuntimeTest(unittest.TestCase):
    def test_manifest_catalog_and_nonlegendary_pool_are_deterministic(self) -> None:
        catalog, header, encoded = builder._catalog_outputs(ROOT)
        reward = catalog["reward"]
        pool = catalog["pool"]
        entries = pool["entries"]

        self.assertEqual(catalog["selected_keys"], [builder.MANIFEST_KEY])
        self.assertEqual(reward["trigger_kind"], "SHINY_MEMORIAL")
        self.assertEqual(reward["streak"], 100)
        self.assertEqual(reward["unlock_key"], "FACTORY_MASTER")
        self.assertEqual(
            reward["unlock_signal"],
            "VegaModernSaveData.league_ii_cleared",
        )
        self.assertEqual(reward["repeatability"], "ONCE")
        self.assertEqual(reward["claim_key"], "CLAIM_KEY_STREAK_100_SHINY")
        self.assertEqual((reward["claim_bit"], reward["claim_mask"]), (9, 0x200))
        self.assertEqual(pool["count"], 137)
        self.assertEqual(len({row["species_id"] for row in entries}), 137)
        self.assertEqual(len({row["national_no"] for row in entries}), 137)
        self.assertEqual(len({row["ledger_bit_index"] for row in entries}), 137)
        self.assertTrue(all(1 <= row["national_no"] <= 386 for row in entries))

        swinub = next(row for row in entries if row["species_id"] == 340)
        self.assertEqual(swinub["national_no"], 220)
        self.assertEqual(json.loads(encoded), catalog)
        self.assertIn(b"FACTORY_SHINY_MEMORIAL_STREAK_THRESHOLD 100u", header)
        self.assertIn(b"FACTORY_SHINY_MEMORIAL_CLAIM_BIT 9u", header)
        self.assertIn(b"FACTORY_SHINY_MEMORIAL_POOL_COUNT 137u", header)
        self.assertIn(b"gFactoryShinyMemorialNational", header)
        self.assertIn(b"gFactoryShinyMemorialLedgerBits", header)

    def test_wrapper_calls_stage30_first_and_preserves_its_result(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        stage30_call = source.index("u16 base_result = FN_STAGE30_COMPLETE();")
        claim_call = source.index(
            "(void)FactoryShinyMemorialRuntime_ClaimPending();",
            stage30_call,
        )
        result_write = source.index("set_result(base_result);", claim_call)
        self.assertLess(stage30_call, claim_call)
        self.assertLess(claim_call, result_write)
        self.assertIn(
            "base_result == FACTORY_SHINY_BASE_RESULT",
            source[stage30_call:claim_call],
        )

    def test_claim_uses_preflight_and_prepared_staged_write_ahead_order(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        capacity = source.index("if (!storage_available())")
        selection = source.index("pool_index = (u16)", capacity)
        prepared = source.index("FACTORY_SHINY_PHASE_PREPARED", selection)
        prepared_save = source.index("if (!persist_finalized_sector())", prepared)
        create = source.index("if (!create_shiny", prepared_save)
        staged = source.index("FACTORY_SHINY_PHASE_STAGED", create)
        staged_save = source.index("if (!persist_finalized_sector())", staged)
        standard_save = source.index("if (!persist_standard()", staged_save)
        commit = source.index("result = commit_staged(", standard_save)
        self.assertLess(capacity, selection)
        self.assertLess(selection, prepared)
        self.assertLess(prepared, prepared_save)
        self.assertLess(prepared_save, create)
        self.assertLess(create, staged)
        self.assertLess(staged, staged_save)
        self.assertLess(staged_save, standard_save)
        self.assertLess(standard_save, commit)

    def test_commit_uses_generated_national_and_collection_mappings(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        national = source.index(
            "u16 national = gFactoryShinyMemorialNational[pool_index];"
        )
        ledger = source.index(
            "u16 ledger_bit = gFactoryShinyMemorialLedgerBits[pool_index];"
        )
        collection = source.index("set_collection_bit(ledger_bit, 1u);", ledger)
        seen = source.index("FACTORY_SHINY_DEX_SET_SEEN", collection)
        caught = source.index("FACTORY_SHINY_DEX_SET_CAUGHT", seen)
        claim = source.index(
            "reward_claim_bits |=\n        FACTORY_SHINY_MEMORIAL_CLAIM_MASK",
            national,
        )
        self.assertLess(ledger, collection)
        self.assertLess(collection, seen)
        self.assertLess(seen, caught)
        self.assertLess(national, claim)
        self.assertNotIn("FN_ACQ_SET_REGISTERED(", source)
        self.assertNotIn("SpeciesToNationalPokedexNum", source)

    def test_custom_recovery_is_dispatched_without_breaking_normal_pending(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        dispatch = source.index("FactoryShinyMemorialRuntime_RecoverDispatch")
        custom_check = source.index("if (pending_is_custom(pending))", dispatch)
        custom_recover = source.index("return recover_custom(pending);", custom_check)
        original_recover = source.index("return call_original_recover();", custom_recover)
        marker_repair = source.index("if (find_marker(&token, &pool_index, &species))")
        capacity = source.index("if (!storage_available())", marker_repair)
        self.assertLess(custom_check, custom_recover)
        self.assertLess(custom_recover, original_recover)
        self.assertLess(marker_repair, capacity)
        self.assertIn("VEGA_ACQ_RECOVER_CONTINUATION_THUMB_LITERAL", source)


if __name__ == "__main__":
    unittest.main()
