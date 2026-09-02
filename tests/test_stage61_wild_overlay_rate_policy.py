from __future__ import annotations

import json
import unittest

from scripts.build_stage61_display_npc_event_audit import (
    DEFAULT_CONFIG,
    GBA_BASE,
    ROOT,
    _wild_overlay_rate_plan,
)


class Stage61WildOverlayRatePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = json.loads((ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8"))

        def read_input(key: str) -> bytes:
            return (ROOT / config["inputs"][key]["path"]).read_bytes()

        cls.stage60 = read_input("stage60_rom")
        cls.plan = _wild_overlay_rate_plan(
            cls.stage60, read_input("wild_overlay_rate_policy")
        )

    def test_candidate_count_buckets_and_route501(self) -> None:
        report = self.plan["report"]
        self.assertEqual(report["entry_count"], 95)
        self.assertEqual(report["normal_entry_count"], 48)
        self.assertEqual(report["non_normal_entry_count"], 47)
        self.assertEqual(
            report["after_rate_counts"],
            {"20": 19, "30": 11, "40": 6, "50": 12},
        )
        self.assertEqual(report["route501_regression"]["candidate_count"], 8)
        self.assertEqual(
            report["route501_regression"]["after_rate_percent"], 50
        )
        self.assertEqual(
            report["stage61_table_sha256"],
            "da77542c7070098485aa98d268101b6c88ef50df2842485cfae40d2964a5d4f5",
        )

    def test_only_threshold_and_rate_bytes_change(self) -> None:
        report = self.plan["report"]
        table_address = int(report["table_address"], 0)
        table_offset = table_address - GBA_BASE
        table_size = 95 * 104
        before = self.stage60[table_offset:table_offset + table_size]
        after = bytearray(before)
        for patch in self.plan["patches"]:
            offset = int(patch["address"]) - table_address
            expected = bytes(patch["expected"])
            replacement = bytes(patch["replacement"])
            self.assertEqual(after[offset:offset + len(expected)], expected)
            after[offset:offset + len(replacement)] = replacement
        changed = [
            index for index, (left, right) in enumerate(zip(before, after))
            if left != right
        ]
        self.assertEqual(len(changed), 96)
        self.assertEqual({index % 104 for index in changed}, {4, 6})
        self.assertTrue(all(
            before[index * 104:(index + 1) * 104]
            == after[index * 104:(index + 1) * 104]
            for index in range(95)
            if before[index * 104 + 3] != 0
        ))


if __name__ == "__main__":
    unittest.main()
