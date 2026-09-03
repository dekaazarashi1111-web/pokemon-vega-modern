from __future__ import annotations

import unittest

from tools.npc_placement_integrity import (
    NpcPlacementIntegrityError,
    build_explicit_added_owner_manifest,
    decode_local_object_target,
)


class NpcPlacementIntegrityTests(unittest.TestCase):
    def test_manifest_uses_only_explicit_addition_sources(self) -> None:
        npcs = [
            {"npc_id": "OBJECT:001/002:000", "group": 1, "map": 2,
             "object_index": 0, "local_id": 1},
            {"npc_id": "OBJECT:001/002:001", "group": 1, "map": 2,
             "object_index": 1, "local_id": 2},
            {"npc_id": "OBJECT:003/004:000", "group": 3, "map": 4,
             "object_index": 0, "local_id": 7},
        ]
        document = build_explicit_added_owner_manifest(
            npcs,
            {"maps": [{"group_id": 1, "map_id": 2, "new_objects": [{
                "local_id": 2, "owner_kind": "NORMAL",
                "encounter_key": "ENC_TEST",
            }]}]},
            [{"group": 3, "map": 4, "local_id": 7, "role": "STAGE58_TEST"}],
            [],
        )
        self.assertEqual(document["owner_ids"], [
            "OBJECT:001/002:001", "OBJECT:003/004:000",
        ])
        self.assertNotIn("OBJECT:001/002:000", document["owner_ids"])
        self.assertTrue(all(document["assertions"].values()))

    def test_unknown_explicit_addition_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            NpcPlacementIntegrityError, "final ownerへ解決できません",
        ):
            build_explicit_added_owner_manifest(
                [{"group": 1, "map": 2, "object_index": 0, "local_id": 1}],
                {"maps": [{"group_id": 1, "map_id": 2, "new_objects": [{
                    "local_id": 9, "owner_kind": "NORMAL",
                }]}]},
                [], [],
            )

    def test_at_target_map_is_not_source_map(self) -> None:
        decoded = decode_local_object_target(
            0x50, bytes.fromhex("500100785634120549"), 1, 73,
        )
        self.assertEqual(
            (decoded["target_group"], decoded["target_map"], decoded["local_id"]),
            (5, 73, 1),
        )
        self.assertTrue(decoded["target_is_explicit_map"])

    def test_dynamic_local_id_is_not_static_owner(self) -> None:
        decoded = decode_local_object_target(
            0x53, bytes.fromhex("530080"), 1, 73,
        )
        self.assertTrue(decoded["dynamic_local_id"])
        self.assertEqual((decoded["target_group"], decoded["target_map"]), (1, 73))


if __name__ == "__main__":
    unittest.main()
