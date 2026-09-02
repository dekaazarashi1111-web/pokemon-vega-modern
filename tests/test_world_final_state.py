from __future__ import annotations

import unittest

from tools.world_final_state import (
    allocate_objects_with_stances,
    audit_conversation_placements,
    exact_reverse_entrance_seed_index,
    reachable_player_tiles,
)


def _flat(width: int, height: int) -> list[int]:
    # collision=0, elevation=0
    return [0 for _ in range(width * height)]


class WorldFinalStateTests(unittest.TestCase):
    def test_reverse_warp_uses_only_exact_destination_row(self) -> None:
        rows = {
            "SOURCE": {
                "map_header": {"map_key": "SOURCE"},
                "warps": [{
                    "source_warp_index": 0, "x": 1, "y": 1,
                    "dest_map": "TARGET", "dest_warp_id": "1",
                }],
                "connections": [],
            },
            "TARGET": {
                "map_header": {"map_key": "TARGET"},
                "warps": [
                    {"source_warp_index": 0, "x": 0, "y": 0,
                     "dest_map": "RUNTIME_EXTERNAL", "dest_warp_id": "0"},
                    {"source_warp_index": 1, "x": 3, "y": 2,
                     "dest_map": "RUNTIME_EXTERNAL", "dest_warp_id": "0"},
                ],
                "connections": [],
            },
        }
        grids = {key: (5, 4, _flat(5, 4)) for key in rows}
        result = exact_reverse_entrance_seed_index(rows, grids)
        self.assertIn((3, 2), result["TARGET"]["seeds"])
        self.assertNotIn((0, 0), result["TARGET"]["seeds"])
        self.assertNotIn((1, 1), result["SOURCE"]["seeds"])

    def test_reverse_connection_applies_direction_and_offset(self) -> None:
        rows = {
            "SOURCE": {
                "map_header": {"map_key": "SOURCE"}, "warps": [],
                "connections": [{
                    "direction": "right", "offset": 1,
                    "map": "TARGET",
                }],
            },
            "TARGET": {
                "map_header": {"map_key": "TARGET"}, "warps": [],
                "connections": [],
            },
        }
        source = _flat(4, 5)
        target = _flat(6, 5)
        # Only source (3,3) -> target (0,2) is usable.
        for y in range(5):
            if y != 3:
                source[y * 4 + 3] = 1 << 10
        result = exact_reverse_entrance_seed_index(
            rows, {"SOURCE": (4, 5, source), "TARGET": (6, 5, target)},
        )
        self.assertEqual(result["TARGET"]["seeds"], {(0, 2)})
        self.assertEqual(result["SOURCE"]["seeds"], set())

    def test_dynamic_warp_is_not_an_entrance(self) -> None:
        rows = {
            "ELEVATOR": {
                "map_header": {"map_key": "ELEVATOR"},
                "warps": [{
                    "source_warp_index": 0, "x": 1, "y": 1,
                    "dest_map": "RUNTIME_DYNAMIC_WARP",
                    "dest_warp_id": "WARP_ID_DYNAMIC",
                }],
                "connections": [],
            },
        }
        result = exact_reverse_entrance_seed_index(
            rows, {"ELEVATOR": (3, 3, _flat(3, 3))},
        )
        self.assertEqual(result["ELEVATOR"]["seeds"], set())
        self.assertEqual(
            len(result["ELEVATOR"]["dynamic_or_external_outgoing_warps"]),
            1,
        )

    def test_isolated_reverse_warp_cycle_is_local_not_global_proof(self) -> None:
        rows = {
            "A": {
                "map_header": {"map_key": "A"},
                "warps": [{
                    "source_warp_index": 0, "x": 1, "y": 1,
                    "dest_map": "B", "dest_warp_id": "0",
                }],
                "connections": [],
            },
            "B": {
                "map_header": {"map_key": "B"},
                "warps": [{
                    "source_warp_index": 0, "x": 1, "y": 1,
                    "dest_map": "A", "dest_warp_id": "0",
                }],
                "connections": [],
            },
        }
        grids = {key: (3, 3, _flat(3, 3)) for key in rows}
        result = exact_reverse_entrance_seed_index(rows, grids)
        self.assertEqual(result["A"]["seeds"], {(1, 1)})
        self.assertEqual(result["B"]["seeds"], {(1, 1)})
        for report in result.values():
            self.assertEqual(
                report["reachability_scope"],
                "STRUCTURAL_EXACT_INCOMING_CANDIDATE_NOT_GLOBAL_ROOT",
            )
            self.assertIsNone(report["globally_reachable_from_new_game"])

    def test_five_objects_reserve_distinct_reachable_stances(self) -> None:
        blocks = _flat(9, 9)
        placements = allocate_objects_with_stances(
            blocks, 9, 9, {(0, 4)}, set(), [(4, 4)] * 5,
        )
        audit = audit_conversation_placements(
            blocks, 9, 9, {(0, 4)}, set(), placements,
        )
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(len({item.object_tile for item in placements}), 5)
        self.assertEqual(len({item.stance_tile for item in placements}), 5)
        # 旧greedyの十字囲い込みは中央の会話stanceを失う。
        self.assertFalse(
            {(4, 3), (3, 4), (5, 4), (4, 5)}
            <= {item.object_tile for item in placements}
        )

    def test_final_object_occupancy_is_part_of_bfs(self) -> None:
        blocks = _flat(5, 3)
        reached = reachable_player_tiles(
            blocks, 5, 3, {(0, 1)}, {(2, 0), (2, 1), (2, 2)},
        )
        self.assertNotIn((4, 1), reached)

    def test_exact_arrival_may_be_collision_bearing_but_egress_may_not(self) -> None:
        blocks = _flat(5, 3)
        # Engine door/ladder arrival at (0,1) is collision-bearing.  The
        # exact tile remains a seed, while traversal after arrival may enter
        # only collision-zero tiles and therefore stops at the wall x=2.
        blocks[1 * 5 + 0] = 1 << 10
        blocks[0 * 5 + 2] = 1 << 10
        blocks[1 * 5 + 2] = 1 << 10
        blocks[2 * 5 + 2] = 1 << 10
        reached = reachable_player_tiles(blocks, 5, 3, {(0, 1)})
        self.assertIn((0, 1), reached)
        self.assertIn((1, 1), reached)
        self.assertNotIn((3, 1), reached)

    def test_out_of_bounds_arrival_is_not_seeded(self) -> None:
        reached = reachable_player_tiles(
            _flat(3, 3), 3, 3, {(-1, 1), (3, 1)},
        )
        self.assertEqual(reached, set())

    def test_warp_or_coord_tile_is_never_used_as_stance(self) -> None:
        blocks = _flat(7, 7)
        reserved = {(3, 2), (2, 3)}
        placements = allocate_objects_with_stances(
            blocks, 7, 7, {(0, 3)}, set(), [(3, 3)],
            reserved_tiles=reserved,
        )
        self.assertNotIn(placements[0].object_tile, reserved)
        self.assertNotIn(placements[0].stance_tile, reserved)


if __name__ == "__main__":
    unittest.main()
