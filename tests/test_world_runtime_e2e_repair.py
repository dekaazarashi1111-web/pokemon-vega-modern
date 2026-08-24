from __future__ import annotations

import struct
import unittest

from tools.regression.rom_runtime import _Blob
from tools.world_runtime_e2e_repair import (
    COOLDOWN_STOCK,
    ENEMY_PARTY_COUNT_ADDRESS,
    NEW_BATTLE_STRUCT_POINTER_ADDRESS,
    TRAINER_PARTY_CONTINUATION_RETURN,
    TRAINER_PARTY_SETUP_FIRST_CALL,
    TRAINER_TABLE_ADDRESS,
    WILD_STOCK_HOOK,
    _add_finditem,
    _add_hidden_item,
    _add_trainer_party_count_wrapper,
    _select_initial_trainer,
)


class WorldRuntimeE2ERepairTest(unittest.TestCase):
    def test_initial_trainer_prefers_authored_kind_two(self) -> None:
        rows = [
            {"command_address": 0x09000020, "kind": 3, "trainer_id": 8},
            {"command_address": 0x09000011, "kind": 2, "trainer_id": 7},
            {"command_address": 0x09000030, "kind": 5, "trainer_id": 9},
        ]
        self.assertEqual(_select_initial_trainer(rows), rows[1])
        self.assertIsNone(_select_initial_trainer([rows[2]]))

    def test_standard_item_uses_stock_find_item_contract(self) -> None:
        blob = _Blob()
        _add_finditem(blob, "item", 988, 2)
        self.assertEqual(
            blob.finish(0),
            bytes.fromhex("1a0080dc031a01800200090102"),
        )

    def test_hidden_item_commits_flag_only_after_success(self) -> None:
        blob = _Blob()
        _add_hidden_item(blob, "hidden", 13, 1, 0x134C)
        raw = blob.finish(0x1000)
        main_end = blob.labels["hidden::success"]
        self.assertIn(bytes.fromhex("0900"), raw[:main_end])
        self.assertNotIn(bytes.fromhex("294c13"), raw[:main_end])
        self.assertEqual(raw[main_end:main_end + 3], bytes.fromhex("294c13"))

    def test_party_count_wrapper_replays_stock_builder_and_syncs_snapshot(self) -> None:
        blob = _Blob()
        start = _add_trainer_party_count_wrapper(blob)
        raw = blob.finish(0x100000)
        self.assertEqual(start, 0)
        self.assertEqual(raw[40:46], bytes.fromhex("5746e0b5a3b0"))
        self.assertEqual(
            struct.unpack_from("<6I", raw, 60),
            (
                0x020385E2,
                TRAINER_TABLE_ADDRESS,
                ENEMY_PARTY_COUNT_ADDRESS,
                NEW_BATTLE_STRUCT_POINTER_ADDRESS,
                TRAINER_PARTY_CONTINUATION_RETURN,
                TRAINER_PARTY_SETUP_FIRST_CALL,
            ),
        )

    def test_global_wild_symptom_patches_are_stock(self) -> None:
        self.assertEqual(WILD_STOCK_HOOK, bytes.fromhex("00b515f0d7ff0006"))
        self.assertEqual(COOLDOWN_STOCK, bytes.fromhex("c1f7"))


if __name__ == "__main__":
    unittest.main()
