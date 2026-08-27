from __future__ import annotations

import struct
import unittest

from tools.regression.rom_runtime import _Blob
from tools.t02.rom_inventory import COMMAND_LENGTHS
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
    REWARD_BUSY,
    REWARD_RESULT_CODES,
    REWARD_RESULT_MESSAGE_KEYS,
    REWARD_SCIENTIST_FIELD_NATIVE,
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
    _add_reward_scientist_safe_script,
    _add_trainer_party_count_wrapper,
    _add_world_read_keys_router,
    _script_root_is_finite,
    _select_initial_trainer,
)


class WorldRuntimeE2ERepairTest(unittest.TestCase):
    def test_script_walker_uses_firered_warp_and_showmonpic_sizes(self) -> None:
        for opcode in (
            0x39, 0x3A, 0x3B, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0xC4, 0xD1,
        ):
            self.assertEqual(COMMAND_LENGTHS[opcode], 8)
        self.assertEqual(COMMAND_LENGTHS[0x75], 5)

    def test_erased_source_script_is_rejected_before_owner_transfer(self) -> None:
        self.assertFalse(_script_root_is_finite(bytes((0xFF,)), 0x08000000))
        self.assertTrue(
            _script_root_is_finite(bytes((0x6C, 0x02)), 0x08000000)
        )

    def test_reward_scientist_waits_only_for_busy_async_menu(self) -> None:
        blob = _Blob()
        messages = {key: bytes((0xFF,)) for key in set(REWARD_RESULT_MESSAGE_KEYS.values())}
        _add_reward_scientist_safe_script(blob, messages)
        payload_offset = 0x1000
        raw = blob.finish(payload_offset)
        root = blob.labels["script::reward_encounter_scientist_safe"]
        wait = blob.labels["script::reward_encounter_scientist_wait"]
        self.assertEqual(raw[root:root + 3], bytes((0x6A, 0x5A, 0x23)))
        self.assertEqual(
            struct.unpack_from("<I", raw, root + 3)[0],
            REWARD_SCIENTIST_FIELD_NATIVE,
        )
        self.assertEqual(
            raw[root + 7:root + 14],
            bytes((0x21, 0x0D, 0x80, REWARD_BUSY, 0x00, 0x06, 0x01)),
        )
        self.assertEqual(
            struct.unpack_from("<I", raw, root + 14)[0],
            0x08000000 + payload_offset + wait,
        )
        cursor = root + 18
        for result in REWARD_RESULT_CODES:
            if result == REWARD_BUSY:
                continue
            self.assertEqual(
                raw[cursor:cursor + 7],
                bytes((0x21, 0x0D, 0x80, result, 0x00, 0x06, 0x01)),
            )
            target = struct.unpack_from("<I", raw, cursor + 7)[0]
            expected = (
                0x08000000 + payload_offset
                + blob.labels[
                    "script::reward_encounter_scientist_message::"
                    + REWARD_RESULT_MESSAGE_KEYS[result]
                ]
            )
            self.assertEqual(target, expected)
            cursor += 11
        self.assertEqual(raw[cursor], 0x05)
        self.assertEqual(
            struct.unpack_from("<I", raw, cursor + 1)[0],
            0x08000000 + payload_offset
            + blob.labels["script::reward_encounter_scientist_message::error"],
        )
        self.assertEqual(raw[wait:wait + 3], bytes((0x27, 0x6C, 0x02)))
        for key in set(REWARD_RESULT_MESSAGE_KEYS.values()):
            message = blob.labels[f"script::reward_encounter_scientist_message::{key}"]
            self.assertEqual(raw[message:message + 2], bytes((0x0F, 0x00)))
            self.assertEqual(raw[message + 6:message + 10], bytes((0x09, 0x04, 0x6C, 0x02)))

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
