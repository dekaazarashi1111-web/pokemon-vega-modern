from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path

from tools.continue_save_freeze_repair import (
    ARMV4T_WRAPPER,
    GBA_ROM_BASE,
    LEGACY_WRAPPER,
    WILD_HOOK_OFFSET,
    ContinueSaveFreezeRepairError,
    repair_stage50_rom,
)


ROOT = Path(__file__).resolve().parents[1]


class ContinueSaveFreezeRepairTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage50 = (ROOT / "build/stages/50_interaction_ownership_repair.gba").read_bytes()
        cls.metadata50 = json.loads(
            (ROOT / "build/stages/50_interaction_ownership_repair.json").read_text()
        )
        cls.output = (ROOT / "build/stages/51_continue_save_freeze_repair.gba").read_bytes()
        cls.repaired, cls.audit = repair_stage50_rom(cls.stage50, cls.metadata50)

    def test_generated_stage51_is_exact_repair(self) -> None:
        self.assertEqual(self.output, self.repaired)
        self.assertEqual(self.audit["outside_wrapper_changes"], 0)
        self.assertTrue(self.audit["legacy_blx_register_removed"])
        self.assertTrue(self.audit["armv4t_tail_call"])

    def test_wrapper_uses_armv4t_tail_call(self) -> None:
        offset = self.audit["wrapper_offset"]
        self.assertEqual(self.stage50[offset:offset + len(LEGACY_WRAPPER)], LEGACY_WRAPPER)
        self.assertEqual(self.output[offset:offset + len(ARMV4T_WRAPPER)], ARMV4T_WRAPPER)
        self.assertNotIn(struct.pack("<H", 0x4798), ARMV4T_WRAPPER)
        self.assertEqual(struct.unpack_from("<H", ARMV4T_WRAPPER, 10)[0], 0x4718)

    def test_hook_and_save_abi_are_unchanged(self) -> None:
        target = struct.unpack_from("<I", self.output, WILD_HOOK_OFFSET + 4)[0]
        self.assertEqual(target, (GBA_ROM_BASE + self.audit["wrapper_offset"]) | 1)
        self.assertEqual(
            self.output[WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + 8],
            self.stage50[WILD_HOOK_OFFSET:WILD_HOOK_OFFSET + 8],
        )

    def test_fail_closed_on_non_stage50_wrapper(self) -> None:
        broken = bytearray(self.stage50)
        broken[self.audit["wrapper_offset"]] ^= 1
        with self.assertRaises(ContinueSaveFreezeRepairError):
            repair_stage50_rom(bytes(broken), self.metadata50)


if __name__ == "__main__":
    unittest.main()
