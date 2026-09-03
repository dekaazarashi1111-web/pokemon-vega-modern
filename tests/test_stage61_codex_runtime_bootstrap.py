from __future__ import annotations

import struct
import unittest
from pathlib import Path

from scripts.build_stage61_display_npc_event_audit import (
    CODEX_BOOTSTRAP_ADAPTER_SYMBOL,
    CODEX_READ_KEYS_ROOT,
    CODEX_READ_KEYS_STAGE60_POINTER,
    CODEX_READ_KEYS_STAGE60_PREIMAGE,
    CODEX_READ_KEYS_TOP_ADAPTER,
    GBA_BASE,
    ROOT,
    _apply_codex_runtime_bootstrap_adapter,
    _compile_runtime,
)


RUNTIME_SOURCE = Path(
    "overlays/stage61_display_npc_event_audit/"
    "stage61_display_npc_event_audit.c"
)
STAGE60_ROM = ROOT / "build/stages/60_wild_species_root_repair.gba"
TEST_LOAD_ADDRESS = 0x09447B00


class Stage61CodexRuntimeBootstrapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage60 = STAGE60_ROM.read_bytes()
        cls.code, cls.symbols, _nm, _manifest = _compile_runtime(
            RUNTIME_SOURCE,
            TEST_LOAD_ADDRESS,
            {
                "STAGE61_KANTO_NAME_TABLE": 0x09D00000,
                "STAGE61_TRAINER_REMATCH_ALIAS_TABLE": 0x09D01000,
                "STAGE61_TRAINER_REMATCH_ALIAS_COUNT": 1,
                "STAGE61_CHANGEKIT_GET_REMATCH": 0x09302DD9,
            },
        )

    def test_root_changes_only_to_current_bootstrap_symbol(self) -> None:
        output = bytearray(self.stage60)
        declared: list[dict] = []
        report = _apply_codex_runtime_bootstrap_adapter(
            self.stage60, output, declared, self.symbols,
        )
        root = CODEX_READ_KEYS_ROOT - GBA_BASE
        self.assertEqual(
            self.stage60[root:root + 4], CODEX_READ_KEYS_STAGE60_PREIMAGE,
        )
        self.assertEqual(
            struct.unpack_from("<I", output, root)[0],
            self.symbols[CODEX_BOOTSTRAP_ADAPTER_SYMBOL] | 1,
        )
        self.assertEqual(declared[-1]["start"], root)
        self.assertEqual(declared[-1]["size"], 4)
        self.assertEqual(report["valid_runtime_delegate"],
                         f"0x{CODEX_READ_KEYS_STAGE60_POINTER:08X}")
        self.assertEqual(report["cold_boot_delegate"],
                         f"0x{CODEX_READ_KEYS_TOP_ADAPTER:08X}")
        self.assertTrue(all(report["assertions"].values()))

    def test_source_checks_both_mailbox_and_state_before_delegating(self) -> None:
        source = (ROOT / RUNTIME_SOURCE).read_text(encoding="utf-8")
        self.assertIn("stage61_read32(state + 4u) != ~0x32524243u", source)
        self.assertIn("stage61_read16(mailbox + 22u) != 44u", source)
        self.assertIn("stage61_read32(mailbox + 40u) != ~nonce", source)
        self.assertIn("FN_CODEX_READ_KEYS_TOP();", source)
        self.assertIn("FN_STAGE60_READ_KEYS();", source)


if __name__ == "__main__":
    unittest.main()
