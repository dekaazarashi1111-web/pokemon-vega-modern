"""ROM-free regressions for the Stage68 shop / Stage69 map cross-link."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "stage79_factory_map_tested", ROOT / "scripts/run_modernization_stage79_cumulative_mgba.py")
assert SPEC and SPEC.loader
STAGE79 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGE79)


class FactoryMapContractTest(unittest.TestCase):
    def setUp(self):
        self.shop = {
            "entrypoints": dict(zip(("MegaShop_Probe", "MegaShop_EnsureSave",
                "MegaShop_GetBalance", "MegaShop_IsUnlocked", "MegaShop_IsClaimed",
                "MegaShop_PurchaseByIndex", "MegaShop_Open"),
                (155525969, 155526001, 155526033, 155526077, 155526129, 155526161, 155526221))),
            "scripts": {"npc_address": 155530592},
            "item_tables": {"item_data": {"new_address": 155531232}},
            "map": {"group_id": 96, "map_id": 5, "header_address": 153877972,
                    "events_after_address": 155531192, "objects_after_address": 155530856,
                    "old_scripts_pointer": 154724552, "object_count_after": 14},
        }
        self.current = {"map": {
            "group_id": 96, "map_id": 5, "header_address": 153877972,
            "events_after_address": 155595088, "old_events_pointer": 155531192,
            "old_objects_pointer": 155530856, "old_scripts_pointer": 154724552,
            "object_count_before": 14, "object_count_after": 15,
            "old_event_counts": [14, 10, 0, 7],
            "existing_14_objects_preserved": True, "stage68_shop_local14_preserved": True,
            "map_scripts_preserved": True, "gift_object": {"local_id": 15}}}
        self.domain = {"contract_source": "shop", "map_contract_source": "map"}
        self.patch = mock.patch.object(STAGE79, "_fixed_json", side_effect=self.source)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def source(self, descriptor, label):
        if descriptor == "shop":
            return copy.deepcopy(self.shop)
        if descriptor == "map":
            return copy.deepcopy(self.current)
        raise ValueError(f"missing fixed source: {label}")

    def test_cumulative_map_relocation_preserves_shop_abi_and_price_inputs(self):
        before = copy.deepcopy(self.shop)
        args, symbols = STAGE79._mega_shop_arguments(self.domain)
        self.assertEqual(args, [155525969, 155526001, 155526033, 155526077,
            155526129, 155526161, 155526221, 155530592, 155595088, 154724552, 155531232])
        self.assertEqual(symbols, before)
        self.assertEqual(self.shop, before)

    def rejected(self, **changes):
        self.current["map"].update(changes)
        with self.assertRaisesRegex(ValueError, "Factory map provenance/count"):
            STAGE79._mega_shop_arguments(self.domain)

    def test_reject_more_objects_instead_of_accepting_a_range(self):
        self.rejected(object_count_after=16)

    def test_reject_stale_fourteen_object_map(self):
        self.rejected(object_count_after=14)

    def test_reject_unrelated_predecessor(self):
        self.rejected(old_events_pointer=155531196)

    def test_reject_unrelated_object_array(self):
        self.rejected(old_objects_pointer=155530880)

    def test_reject_map_script_replacement(self):
        self.rejected(old_scripts_pointer=154724556)

    def test_reject_map_header_replacement(self):
        self.rejected(header_address=153877976)

    def test_reject_lost_shop(self):
        self.rejected(stage68_shop_local14_preserved=False)

    def test_reject_lost_original_objects(self):
        self.rejected(existing_14_objects_preserved=False)

    def test_reject_different_gift_npc(self):
        self.rejected(gift_object={"local_id": 16})

    def test_reject_wrong_map_counts(self):
        self.rejected(old_event_counts=[14, 10, 1, 7])

    def test_missing_map_provenance_is_not_optional(self):
        del self.domain["map_contract_source"]
        with self.assertRaises(ValueError):
            STAGE79._mega_shop_arguments(self.domain)

    def test_historical_runner_default_and_stage79_exact_count(self):
        historical = (ROOT / "tools/mgba_modernization_mega_shop_smoke.c").read_text()
        cumulative = (ROOT / "tools/mgba_modernization_stage79_mega_shop_smoke.c").read_text()
        self.assertIn("#ifndef MEGA_EXPECTED_FACTORY_OBJECT_COUNT", historical)
        self.assertIn("#define MEGA_EXPECTED_FACTORY_OBJECT_COUNT 14U", historical)
        self.assertIn("read8(core, events) != MEGA_EXPECTED_FACTORY_OBJECT_COUNT", historical)
        self.assertIn("index < MEGA_EXPECTED_FACTORY_OBJECT_COUNT", historical)
        self.assertIn("#define MEGA_EXPECTED_FACTORY_OBJECT_COUNT 15U", cumulative)
        self.assertIn('#include "mgba_modernization_mega_shop_smoke.c"', cumulative)


if __name__ == "__main__":
    unittest.main()
