#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from collections import Counter
import json
import unittest

from tools.stage61_map_lifecycle import (
    ATTEMPT_DISPATCH,
    ATTEMPT_NO_CONDITION_MATCH,
    ATTEMPT_TAG_ABSENT,
    Stage61MapLifecycleError,
    SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD,
    apply_destination_engine_clear,
    clear_destination_temp_vars,
    decode_map_lifecycle_topology,
    lifecycle_attempts,
    resolve_attempt,
    resolve_attempt_result,
)


ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / "build/stages/61_display_npc_event_audit.gba"


class Stage61MapLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = ROM_PATH.read_bytes()

    def test_map_001_000_topology_preserves_exact_dispatch_roots(self) -> None:
        topology = decode_map_lifecycle_topology(self.rom, 1, 0)
        self.assertEqual(
            [row["tag"] for row in topology["outer_rows"]],
            [3, 1, 4, 2],
        )
        state = {0x4077: 3}
        self.assertEqual(resolve_attempt(topology, 3, state)["root_pc"], 0x0887E7A2)
        self.assertEqual(resolve_attempt(topology, 1, state)["root_pc"], 0x086A5B10)
        self.assertEqual(resolve_attempt(topology, 4, state)["root_pc"], 0x08861650)
        self.assertEqual(resolve_attempt(topology, 2, state)["root_pc"], 0x08861680)

    def test_map_002_010_temp_clear_and_pre_field_input_are_distinct(self) -> None:
        topology = decode_map_lifecycle_topology(self.rom, 2, 10)
        self.assertEqual(
            [row["tag"] for row in topology["outer_rows"]],
            [5, 7, 3, 1, 2],
        )
        self.assertEqual(resolve_attempt(topology, 3, {})["root_pc"], 0x0816E61F)
        self.assertEqual(resolve_attempt(topology, 1, {})["root_pc"], 0x0816E609)
        self.assertEqual(resolve_attempt(topology, 5, {})["root_pc"], 0x0816E5C5)
        self.assertEqual(resolve_attempt(topology, 7, {})["root_pc"], 0x0816E5F9)

        pretransition = {0x4000: 1, 0x400D: 0x11, 0x406F: 9}
        after_clear = clear_destination_temp_vars(pretransition)
        self.assertEqual(after_clear[0x4000], 0)
        self.assertEqual(after_clear[0x400D], 0)
        self.assertEqual(after_clear[0x406F], 9)
        row0 = resolve_attempt(topology, 2, after_clear)
        self.assertEqual(row0["selected_condition_index"], 0)
        self.assertEqual(row0["root_pc"], 0x0816E65F)

        before_field_input = dict(after_clear)
        before_field_input[0x4000] = 1
        before_field_input[0x400D] = 0x11
        row1 = resolve_attempt(topology, 2, before_field_input)
        self.assertEqual(row1["selected_condition_index"], 1)
        self.assertEqual(row1["root_pc"], 0x0816E63A)

    def test_connection_omits_tag4_but_warp_attempts_it(self) -> None:
        connection = lifecycle_attempts(
            "CONNECTION", include_field_return=False,
        )
        warp = lifecycle_attempts("STOCK_WARP", include_field_return=True)
        self.assertEqual(
            [row["tag"] for row in connection],
            [None, 3, 1, 5, 2],
        )
        self.assertEqual(
            [row["tag"] for row in warp],
            [None, 3, 1, 5, 4, 2, 5, 7],
        )
        self.assertEqual(
            [row["phase"] for row in warp[-2:]],
            ["FIELD_RETURN_RESUME", "FIELD_RETURN_RETURN_TO_FIELD"],
        )

    def test_destination_engine_clear_is_pure_and_explicit(self) -> None:
        variables = {0x4000: 7, 0x400F: 9, 0x4010: 11}
        flags = {
            0x0000: True,
            0x001F: True,
            0x0020: True,
            **{
                identifier: True
                for identifier in SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD
            },
        }
        before_variables = dict(variables)
        before_flags = dict(flags)

        transform = apply_destination_engine_clear(variables, flags)

        self.assertEqual(variables, before_variables)
        self.assertEqual(flags, before_flags)
        self.assertEqual(transform["kind"], "STAGE61_MAP_ENGINE_TRANSFORM")
        self.assertEqual(transform["operation"], "CLEAR_TEMP_FIELD_EVENT_DATA")
        self.assertEqual(transform["phase"], "DESTINATION_TEMP_CLEAR")
        self.assertEqual(
            [row["id"] for row in transform["variable_writes"]],
            list(range(0x4000, 0x4010)),
        )
        self.assertEqual(
            [row["id"] for row in transform["temporary_flag_writes"]],
            list(range(0x0000, 0x0020)),
        )
        self.assertEqual(
            [row["id"] for row in transform["system_flag_writes"]],
            list(SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD),
        )
        self.assertTrue(all(
            transform["variables"][identifier] == 0
            for identifier in range(0x4000, 0x4010)
        ))
        self.assertTrue(all(
            transform["flags"][identifier] is False
            for identifier in (
                *range(0x0000, 0x0020),
                *SYSTEM_FLAGS_CLEARED_ON_DESTINATION_LOAD,
            )
        ))
        self.assertEqual(transform["variables"][0x4010], 11)
        self.assertIs(transform["flags"][0x0020], True)

    def test_conditional_rhs_varget_contract_is_fail_closed(self) -> None:
        topology = decode_map_lifecycle_topology(self.rom, 2, 10)
        condition = topology["by_tag"]["2"]["conditions"][0]
        mutated = bytearray(self.rom)
        value_offset = condition["record_address"] - 0x08000000 + 2
        mutated[value_offset:value_offset + 2] = (0x4000).to_bytes(2, "little")

        with self.assertRaisesRegex(
            Stage61MapLifecycleError, "conditional RHS即値契約違反",
        ):
            decode_map_lifecycle_topology(bytes(mutated), 2, 10)

        malformed_outer = dict(topology["by_tag"]["2"])
        malformed_outer["conditions"] = [
            {**condition, "value": 0x4000},
        ]
        with self.assertRaisesRegex(
            Stage61MapLifecycleError, "conditional RHS即値契約違反",
        ):
            resolve_attempt_result(
                {"by_tag": {"2": malformed_outer}},
                2,
                {condition["variable"]: 0},
            )
        with self.assertRaisesRegex(
            Stage61MapLifecycleError, "conditional LHS state不足",
        ):
            resolve_attempt_result(topology, 2, {})

    def test_attempt_result_distinguishes_absent_no_match_and_dispatch(self) -> None:
        topology = decode_map_lifecycle_topology(self.rom, 2, 10)
        absent = resolve_attempt_result(topology, 4, {})
        self.assertEqual(absent, {"tag": 4, "result": ATTEMPT_TAG_ABSENT})

        conditions = topology["by_tag"]["2"]["conditions"]
        forbidden_by_variable: dict[int, set[int]] = {}
        for condition in conditions:
            forbidden_by_variable.setdefault(condition["variable"], set()).add(
                condition["value"],
            )
        no_match_state = {
            variable: next(
                candidate for candidate in range(0x10000)
                if candidate not in forbidden
            )
            for variable, forbidden in forbidden_by_variable.items()
        }
        no_match = resolve_attempt_result(topology, 2, no_match_state)
        self.assertEqual(no_match["result"], ATTEMPT_NO_CONDITION_MATCH)
        self.assertEqual(no_match["outer_index"], 4)
        self.assertIsNone(resolve_attempt(topology, 2, no_match_state))

        dispatch_state = clear_destination_temp_vars({})
        dispatch = resolve_attempt_result(topology, 2, dispatch_state)
        self.assertEqual(dispatch["result"], ATTEMPT_DISPATCH)
        self.assertEqual(dispatch["selected_condition_index"], 0)
        self.assertEqual(dispatch["owner_id"], conditions[0]["owner_id"])

    def test_outer_duplicate_tag_is_fail_closed(self) -> None:
        topology = decode_map_lifecycle_topology(self.rom, 2, 10)
        table_pointer = topology["table_pointer"]
        self.assertIsInstance(table_pointer, int)
        mutated = bytearray(self.rom)
        # row 0 is tag5 and row 1 is tag7.  Alter only row 1's tag byte.
        mutated[table_pointer - 0x08000000 + 5] = 5
        with self.assertRaisesRegex(Stage61MapLifecycleError, "outer tag重複"):
            decode_map_lifecycle_topology(bytes(mutated), 2, 10)

    def test_all_678_physical_maps_decode_with_exact_tag_partition(self) -> None:
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(len(inventory["surfaces"]), 678)
        outer_counts: Counter[int] = Counter()
        condition_counts: Counter[int] = Counter()
        nonempty = 0
        for surface in inventory["surfaces"]:
            group, number = (
                int(value) for value in surface["physical_map"].split("/")
            )
            topology = decode_map_lifecycle_topology(
                self.rom, group, number,
            )
            if topology["outer_rows"]:
                nonempty += 1
            for row in topology["outer_rows"]:
                outer_counts[row["tag"]] += 1
                if row["dispatch_kind"] == "CONDITION_TABLE":
                    condition_counts[row["tag"]] += len(row["conditions"])
        self.assertEqual(nonempty, 189)
        self.assertEqual(
            outer_counts,
            Counter({1: 91, 2: 66, 3: 120, 4: 39, 5: 44, 7: 2}),
        )
        self.assertEqual(condition_counts, Counter({2: 210, 4: 160}))


if __name__ == "__main__":
    unittest.main()
