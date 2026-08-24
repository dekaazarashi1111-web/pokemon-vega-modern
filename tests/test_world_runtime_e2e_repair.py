from __future__ import annotations

import struct
import unittest

from tools.regression.rom_runtime import _Blob
from tools.world_runtime_e2e_repair import (
    COOLDOWN_STOCK,
    BATTLE_TRANSITION_START_HOOK_EXPECTED,
    BROKEN_BATTLE_TRANSITION,
    CODEX_READ_KEYS_BRIDGE_ADAPTER,
    CODEX_READ_KEYS_TOP_ADAPTER,
    ENEMY_PARTY_COUNT_ADDRESS,
    FIELD_INPUT_STOCK_BODY,
    SCRIPT_CONTEXT_IS_ENABLED,
    SAFE_BATTLE_TRANSITION,
    STOCK_BATTLE_TRANSITION_START_BODY,
    TRAINER_PARTY_DELEGATE,
    TRAINER_TABLE_ADDRESS,
    WILD_STOCK_HOOK,
    _add_direction_wild_encounter,
    _add_battle_transition_router,
    _add_finditem,
    _add_field_input_script_owner,
    _add_hidden_flag_runtime,
    _add_hidden_item,
    _add_trainer_party_count_wrapper,
    _add_world_read_keys_router,
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
        _add_hidden_flag_runtime(blob)
        _add_finditem(blob, "item", 988, 2, 0x140D)
        raw = blob.finish(0x1000)
        start = blob.labels["item"]
        self.assertEqual(
            raw[start:start + 12],
            bytes.fromhex("1a0080dc031a018002000901"),
        )
        self.assertIn(bytes.fromhex("1a00800d1423"), raw[start:])

    def test_hidden_item_commits_flag_only_after_success(self) -> None:
        blob = _Blob()
        _add_hidden_flag_runtime(blob)
        _add_hidden_item(blob, "hidden", 13, 1, 0x134C)
        raw = blob.finish(0x1000)
        main_start = blob.labels["hidden"]
        main_end = blob.labels["hidden::success"]
        set_pointer = struct.pack(
            "<I", 0x08001000 + blob.labels["runtime::hidden_flag_set"] | 1
        )
        self.assertIn(bytes.fromhex("0900"), raw[main_start:main_end])
        self.assertNotIn(set_pointer, raw[main_start:main_end])
        self.assertEqual(raw[main_end:main_end + 6], bytes.fromhex("1a00804c1323"))
        self.assertIn(set_pointer, raw[main_end:])

    def test_party_count_wrapper_replays_stock_builder_and_syncs_snapshot(self) -> None:
        blob = _Blob()
        start = _add_trainer_party_count_wrapper(blob)
        raw = blob.finish(0x100000)
        self.assertEqual(start, 0)
        self.assertEqual(raw[40:44], bytes.fromhex("044b1847"))
        self.assertEqual(
            struct.unpack_from("<4I", raw, 48),
            (
                0x020385E2,
                TRAINER_TABLE_ADDRESS,
                ENEMY_PARTY_COUNT_ADDRESS,
                TRAINER_PARTY_DELEGATE,
            ),
        )

    def test_world_read_keys_router_separates_field_and_codex_paths(self) -> None:
        blob = _Blob()
        start = _add_world_read_keys_router(blob)
        raw = blob.finish(0x1000)
        self.assertEqual(start, 0)
        self.assertEqual(len(raw), 76)
        self.assertEqual(
            struct.unpack_from("<2I", raw, 68),
            (CODEX_READ_KEYS_TOP_ADAPTER, CODEX_READ_KEYS_BRIDGE_ADAPTER),
        )

    def test_field_input_owner_preserves_stock_then_consumes_script_a(self) -> None:
        blob = _Blob()
        start = _add_field_input_script_owner(blob)
        raw = blob.finish(0x1000)
        self.assertEqual(start, 0)
        self.assertEqual(len(raw), 60)
        self.assertEqual(
            struct.unpack_from("<2I", raw, 52),
            (FIELD_INPUT_STOCK_BODY, SCRIPT_CONTEXT_IS_ENABLED),
        )

    def test_wild_gate_requires_changed_player_object_coordinates(self) -> None:
        blob = _Blob()
        start = _add_direction_wild_encounter(blob)
        raw = blob.finish(0x1000)
        self.assertEqual(start, 0)
        self.assertEqual(len(raw), 144)
        self.assertEqual(raw[:8], bytes.fromhex("31b51e494a790f2a"))
        self.assertEqual(
            struct.unpack_from("<5I", raw, 124),
            (0x02036FAC, 0x02036D6C, 0x0203EDF0,
             0x0000A753, 0x08082F9D),
        )
        self.assertEqual(WILD_STOCK_HOOK, bytes.fromhex("00b515f0d7ff0006"))
        self.assertEqual(COOLDOWN_STOCK, bytes.fromhex("c1f7"))

    def test_broken_battle_transition_is_normalized_before_stock_start(self) -> None:
        blob = _Blob()
        start = _add_battle_transition_router(blob)
        raw = blob.finish(0x1000)
        self.assertEqual(start, 0)
        self.assertEqual(len(raw), 24)
        self.assertEqual(BROKEN_BATTLE_TRANSITION, 4)
        self.assertEqual(SAFE_BATTLE_TRANSITION, 8)
        self.assertEqual(
            raw[:20],
            bytes.fromhex("042800d1082030b5041c2406240e014b1847c046"),
        )
        self.assertEqual(
            struct.unpack_from("<I", raw, 20)[0],
            STOCK_BATTLE_TRANSITION_START_BODY,
        )
        self.assertEqual(
            BATTLE_TRANSITION_START_HOOK_EXPECTED,
            bytes.fromhex("30b5041c2406240e"),
        )


if __name__ == "__main__":
    unittest.main()
