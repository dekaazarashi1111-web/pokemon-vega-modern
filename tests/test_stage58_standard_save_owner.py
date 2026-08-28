#!/usr/bin/env python3
"""Stage58 standard-save visibility probeのsource/ABI契約を固定する。"""

from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "build/stages/58_qol_world_convenience_debug.gba"
METADATA = ROOT / "build/stages/58_qol_world_convenience_debug.json"
PROBE = ROOT / "tests/mgba_stage58_standard_save_owner_probe.c"


class Stage58StandardSaveOwnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = ROM.read_bytes()
        cls.metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        cls.source = PROBE.read_text(encoding="utf-8")

    def test_exact_rom_identity(self) -> None:
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(
            hashlib.sha256(self.rom).hexdigest(),
            self.metadata["output"]["sha256"],
        )

    def test_set_bag_pockets_pointers_exact_abi(self) -> None:
        def word(address: int) -> int:
            offset = address - 0x08000000
            return struct.unpack_from("<I", self.rom, offset)[0]

        offset = 0x0809984C - 0x08000000
        self.assertEqual(
            self.rom[offset:offset + 8],
            bytes.fromhex("0f4910480268c423"),
        )
        self.assertEqual(word(0x0809988C), 0x020397D8)  # gBagPockets
        self.assertEqual(word(0x08099890), 0x03005048)  # gSaveBlock1Ptr slot
        self.assertEqual(word(0x08099894), 0x0000054C)  # berry pocket offset

    def test_probe_is_read_only_and_json_only(self) -> None:
        self.assertIn(
            "PROBE_SET_BAG_POCKETS_POINTERS = 0x0809984DU", self.source,
        )
        self.assertIn("QOL_LOAD_GAME_DATA", self.source)
        self.assertIn("standard_save_item_restored", self.source)
        self.assertIn("set_bag_pockets_repairs_visibility", self.source)
        self.assertNotIn("fprintf(stderr", self.source)
        self.assertNotIn("write8(core", self.source)
        self.assertNotIn("write16(core", self.source)
        self.assertNotIn("write32(core", self.source)
        self.assertNotIn("QOL_TRY_SAVING_DATA", self.source)


if __name__ == "__main__":
    unittest.main()
