from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_stage61_display_npc_event_audit as builder


ROOT = Path(__file__).resolve().parents[1]
STAGE60 = ROOT / "build/stages/60_wild_species_root_repair.gba"


class Stage61SpeciesSentinelGuardTests(unittest.TestCase):
    def test_all_five_stage09_unconditional_guards_are_closed(self) -> None:
        raw = STAGE60.read_bytes()
        patches = builder.SPECIES_BOUND_CALLSITE_PATCHES
        self.assertEqual(len(patches), 5)
        self.assertIn(
            (
                0x00043746,
                bytes.fromhex("ce204000844204e0"),
                4,
                bytes.fromhex("04d9"),
            ),
            patches,
        )
        for offset, expected, register, branch in patches:
            with self.subTest(address=f"0x{builder.GBA_BASE + offset:08X}"):
                self.assertEqual(raw[offset:offset + 8], expected)
                self.assertEqual(branch[0], expected[6])
                self.assertEqual(branch[1], 0xD9)  # Thumb BLS
                replacement = (
                    builder.thumb_bl(
                        builder.GBA_BASE + offset,
                        builder.SPECIES_BOUND_THUNK_ADDRESS,
                    )
                    + expected[4:6]
                    + branch
                )
                self.assertEqual(len(replacement), len(expected))
                self.assertEqual(replacement[4:6], expected[4:6])
                self.assertEqual(register, expected[4] & 7)

    def test_post_catch_palette_guard_preserves_stock_fallback_target(self) -> None:
        offset, expected, register, branch = next(
            row for row in builder.SPECIES_BOUND_CALLSITE_PATCHES
            if row[0] == 0x00043746
        )
        self.assertEqual(register, 4)
        branch_pc = builder.GBA_BASE + offset + 6 + 4
        self.assertEqual(branch_pc + branch[0] * 2, 0x08043758)
        # The canonical normal and shiny palette tables are exactly 1621 rows
        # of eight bytes apart, so valid species IDs are 0..1620 inclusive.
        self.assertEqual(0x09F597F8 - 0x09F56550, 1621 * 8)
        self.assertEqual(
            builder.SPECIES_BOUND_THUNK,
            bytes.fromhex("0048704754060000"),  # ldr r0; bx lr; .word 1620
        )


if __name__ == "__main__":
    unittest.main()
