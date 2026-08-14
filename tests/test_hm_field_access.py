"""HM所持を正本にするstage 22 runtimeの限定回帰。"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_hm_field_access import (  # noqa: E402
    HM_ROWS,
    STAGE22,
    STAGE22_META,
    _build_stage,
)


class HMFieldAccessTests(unittest.TestCase):
    def test_runtime_uses_vega_hm_ids_and_never_writes_moves(self) -> None:
        source = (ROOT / "overlays/hm_field_access/hm_field_access.c").read_text(
            encoding="utf-8"
        )
        self.assertEqual([row[3] for row in HM_ROWS], list(range(339, 347)))
        for item in range(339, 347):
            self.assertIn(f"= {item}u", source)
        self.assertIn("VEGA_MOVE_FLASH = 148u", source)
        self.assertIn("VEGA_MOVE_DIVE = 291u", source)
        self.assertIn("return 0u;", source)
        self.assertNotIn("SetMonMoveSlot", source)
        self.assertNotIn("MON_DATA_MOVE", source)
        self.assertNotIn("FLAG_BADGE", source)

    def test_stage_build_is_deterministic_and_declared_only(self) -> None:
        first, first_meta = _build_stage(ROOT)
        second, second_meta = _build_stage(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(first_meta, second_meta)
        self.assertEqual(first_meta["status"], "PASS")
        self.assertEqual(len(first_meta["hm_contract"]), 8)
        self.assertTrue(all(first_meta["invariants"].values()))
        self.assertEqual(
            first[STAGE22.as_posix()], (ROOT / STAGE22).read_bytes()
        )
        self.assertEqual(
            json.loads(first[STAGE22_META.as_posix()]),
            json.loads((ROOT / STAGE22_META).read_text(encoding="utf-8")),
        )

    def test_exact_rom_fixture_covers_party_and_surf_boundaries(self) -> None:
        fixture = json.loads(
            (ROOT / "build/stages/22_mgba_hm_field_access.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(fixture["status"], "PASS")
        self.assertEqual(fixture["process_runs"], 2)
        self.assertEqual(fixture["warnings_errors"], 0)
        self.assertEqual(fixture["move_writes"], 0)
        self.assertEqual(fixture["new_story_flags"], 0)
        self.assertEqual(len(fixture["hm_cases"]), 8)
        for row in fixture["hm_cases"]:
            self.assertEqual(
                [variant["party"] for variant in row["party_variants"]],
                ["EMPTY", "UNLEARNED", "LEARNED"],
            )
            for variant in row["party_variants"]:
                self.assertEqual(variant["before"], 6)
                self.assertEqual(variant["after"], 0)
                self.assertEqual(variant["after_restore"], 0)
                self.assertEqual(variant["bag_count"], 1)
            self.assertEqual(row["callback"]["missing"], 0)
            self.assertEqual(
                row["callback"]["owned"], row["callback"]["original_map_gate"]
            )
        self.assertEqual(
            fixture["surf_state_boundary"],
            {
                "land_not_surfing": 0,
                "land_requires_surfing": 6,
                "surf_rejects_land_only": 6,
                "surf_requires_surfing": 0,
            },
        )

    def test_runner_and_patch_leave_save_and_story_ownership_untouched(self) -> None:
        runner = (ROOT / "tools/mgba_hm_field_access_smoke.c").read_text(
            encoding="utf-8"
        )
        metadata = json.loads((ROOT / STAGE22_META).read_text(encoding="utf-8"))
        self.assertIn("read_only\\\":true", runner)
        self.assertNotIn("fopen(", runner)
        self.assertNotIn("Save_", runner)
        self.assertTrue(metadata["invariants"]["new_story_or_save_flags_unchanged"])
        patched_addresses = {row["address"] for row in metadata["patches"]}
        self.assertNotIn("0x0203D000", patched_addresses)
        self.assertNotIn("0x02037004", patched_addresses)


if __name__ == "__main__":
    unittest.main()
