from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_factory_repeat_reward_runtime as builder


ROOT = Path(__file__).resolve().parents[1]


class FactoryRepeatRewardRuntimeTest(unittest.TestCase):
    def test_manifest_catalog_binds_only_two_repeat_rows(self) -> None:
        stage28_catalog = json.loads(
            (ROOT / builder.INPUT_CATALOG).read_text(encoding="utf-8")
        )
        catalog, header, encoded = builder._catalog_outputs(ROOT, stage28_catalog)
        self.assertEqual(catalog["selected_keys"], list(builder.MANIFEST_KEYS))
        self.assertEqual(catalog["required_first_claim_mask"], 0x0E)
        self.assertEqual(
            [(row["item_id"], row["quantity"], row["battle_points"])
             for row in catalog["rewards"]],
            [(432, 1, 1), (2, 1, 2)],
        )
        self.assertEqual(json.loads(encoded), catalog)
        self.assertIn(b"FACTORY_REPEAT_REWARD_COUNT 2u", header)
        self.assertIn(b"FACTORY_REPEAT_REWARD_REQUIRED_CLAIM_MASK 0x0Eu", header)

    def test_wrapper_captures_first_claim_eligibility_before_stage28(self) -> None:
        source = (
            ROOT
            / "overlays/factory_repeat_reward_runtime/factory_repeat_reward_runtime.c"
        ).read_text(encoding="utf-8")
        eligibility = source.index(
            "u8 repeat_eligible = repeat_eligible_before_completion();"
        )
        stage28_call = source.index("u16 base_result = FN_STAGE28_COMPLETE();")
        repeat_apply = source.index("apply_repeat_reward();", stage28_call)
        self.assertLess(eligibility, stage28_call)
        self.assertLess(stage28_call, repeat_apply)
        self.assertIn("base_result == FACTORY_REPEAT_REWARD_BASE_RESULT", source)

    def test_repeat_item_and_bp_are_coupled_before_persistence(self) -> None:
        source = (
            ROOT
            / "overlays/factory_repeat_reward_runtime/factory_repeat_reward_runtime.c"
        ).read_text(encoding="utf-8")
        add_item = source.index("FN_ADD_BAG_ITEM(item, quantity)")
        add_bp = source.index("FN_FACTORY_ADD_BP(gVegaModernSaveData, battle_points)")
        standard_save = source.index("persist_standard_save()", add_bp)
        sector_save = source.index("persist_save_sector()", standard_save)
        self.assertLess(add_item, add_bp)
        self.assertLess(add_bp, standard_save)
        self.assertLess(standard_save, sector_save)
        self.assertIn("rollback_repeat_reward(item, quantity);", source)


if __name__ == "__main__":
    unittest.main()
