from __future__ import annotations

import struct
import unittest
from pathlib import Path

from scripts.build_stage61_display_npc_event_audit import (
    FACTORY_PREPARE_ADAPTER_SYMBOL,
    FACTORY_PREPARE_FAULT_SETTER_SYMBOL,
    FACTORY_PREPARE_ORIGINAL_ENTRY,
    FACTORY_PREPARE_ORIGINAL_SPAN_SIZE,
    FACTORY_PREPARE_POINTER_SITE,
    FACTORY_PREPARE_SCRIPT_ADDRESS,
    FACTORY_PREPARE_SCRIPT_SIZE,
    GBA_BASE,
    ROOT,
    Stage61BuildError,
    _apply_factory_prepare_error_adapter,
    _compile_runtime,
)
from tools.stage61_interaction_oracle import (
    _facility_native_operation,
    _runtime_symbol_pointer,
)


RUNTIME_SOURCE = Path(
    "overlays/stage61_display_npc_event_audit/"
    "stage61_display_npc_event_audit.c"
)
STAGE60_ROM = ROOT / "build/stages/60_wild_species_root_repair.gba"
TEST_LOAD_ADDRESS = 0x09447B00


class Stage61FactoryPrepareErrorAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage60 = STAGE60_ROM.read_bytes()
        cls.code, cls.symbols, cls.nm_text, _manifest = _compile_runtime(
            RUNTIME_SOURCE,
            TEST_LOAD_ADDRESS,
            {"STAGE61_KANTO_NAME_TABLE": 0x09D00000},
        )

    def _materialize(self) -> tuple[bytearray, list[dict], dict]:
        output = bytearray(self.stage60)
        code_offset = TEST_LOAD_ADDRESS - GBA_BASE
        output[code_offset:code_offset + len(self.code)] = self.code
        declared = [{
            "name": "test_stage61_payload",
            "start": code_offset,
            "end_exclusive": code_offset + len(self.code),
        }]
        report = _apply_factory_prepare_error_adapter(
            self.stage60, output, declared, self.symbols, self.nm_text,
        )
        return output, declared, report

    def test_current_link_exports_one_shot_setter_and_physical_adapter(self) -> None:
        self.assertIn(FACTORY_PREPARE_ADAPTER_SYMBOL, self.symbols)
        self.assertIn(FACTORY_PREPARE_FAULT_SETTER_SYMBOL, self.symbols)
        self.assertEqual(self.symbols[FACTORY_PREPARE_ADAPTER_SYMBOL] & 1, 0)
        self.assertEqual(self.symbols[FACTORY_PREPARE_FAULT_SETTER_SYMBOL] & 1, 0)
        self.assertLess(len(self.code), 16 * 1024)
        self.assertEqual(
            _runtime_symbol_pointer(
                FACTORY_PREPARE_ADAPTER_SYMBOL,
                {"current": {"symbols": self.symbols}},
            ),
            self.symbols[FACTORY_PREPARE_ADAPTER_SYMBOL] | 1,
        )
        self.assertEqual(
            _facility_native_operation(
                "factory", FACTORY_PREPARE_ADAPTER_SYMBOL,
            ),
            "PrepareBattle",
        )

    def test_pointer_only_patch_and_source_bound_arm_schema_are_exact(self) -> None:
        output, declared, report = self._materialize()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["assertions"].values()))
        self.assertEqual(report["arm_schema"], {
            "state_address": "0x0203F220",
            "state_size": 1280,
            "state_magic": "0x324D4846",
            "last_status_offset": "0x20",
            "active_offset": "0x62",
            "phase_offset": "0x6A",
            "reserved_header_offset": "0x7D",
            "reserved_header_size": 4,
            "arm_hex": "5346acb9",
            "active_value": 1,
            "active_phase": 3,
            "error_status": 0,
            "var_result_address": "0x02037004",
        })
        self.assertEqual(declared[-1]["start"], FACTORY_PREPARE_POINTER_SITE - GBA_BASE)
        self.assertEqual(declared[-1]["size"], 4)

        script = slice(
            FACTORY_PREPARE_SCRIPT_ADDRESS - GBA_BASE,
            FACTORY_PREPARE_SCRIPT_ADDRESS - GBA_BASE
            + FACTORY_PREPARE_SCRIPT_SIZE,
        )
        before = self.stage60[script]
        after = bytes(output[script])
        changed = [
            index for index, pair in enumerate(zip(before, after))
            if pair[0] != pair[1]
        ]
        self.assertEqual(changed, [1, 2, 3])
        self.assertTrue(set(changed).issubset({1, 2, 3, 4}))
        self.assertEqual(
            struct.unpack_from("<I", after, 1)[0],
            self.symbols[FACTORY_PREPARE_ADAPTER_SYMBOL] | 1,
        )
        original = slice(
            FACTORY_PREPARE_ORIGINAL_ENTRY - GBA_BASE,
            FACTORY_PREPARE_ORIGINAL_ENTRY - GBA_BASE
            + FACTORY_PREPARE_ORIGINAL_SPAN_SIZE,
        )
        self.assertEqual(bytes(output[original]), self.stage60[original])
        self.assertEqual(
            {row["path"] for row in report["source_binding"]},
            {
                "overlays/factory_high_modes_v2/factory_high_modes_v2.c",
                "overlays/factory_high_modes_v2/factory_high_modes_v2.h",
                RUNTIME_SOURCE.as_posix(),
                "scripts/build_stage61_display_npc_event_audit.py",
                "tools/stage61_facility_sessions.py",
            },
        )

    def test_script_or_original_delegate_drift_fails_closed(self) -> None:
        script_tamper = bytearray(self.stage60)
        script_tamper[FACTORY_PREPARE_SCRIPT_ADDRESS - GBA_BASE + 31] ^= 1
        with self.assertRaisesRegex(Stage61BuildError, "physical script"):
            _apply_factory_prepare_error_adapter(
                bytes(script_tamper), bytearray(script_tamper), [],
                self.symbols, self.nm_text,
            )

        delegate_tamper = bytearray(self.stage60)
        delegate_tamper[FACTORY_PREPARE_ORIGINAL_ENTRY - GBA_BASE] ^= 1
        with self.assertRaisesRegex(Stage61BuildError, "original delegate"):
            _apply_factory_prepare_error_adapter(
                bytes(delegate_tamper), bytearray(delegate_tamper), [],
                self.symbols, self.nm_text,
            )

    def test_source_requires_valid_active_phase_and_zeroizes_before_fault(self) -> None:
        source = (ROOT / RUNTIME_SOURCE).read_text(encoding="utf-8")
        self.assertIn(
            "state->magic_inverse != ~(u32)STAGE61_FACTORY_STATE_MAGIC",
            source,
        )
        self.assertIn(
            "state->phase != STAGE61_FACTORY_PHASE_ACTIVE", source,
        )
        adapter_start = source.index(
            "u16 FactoryHighModesV2_PrepareBattleStage61Adapter(void)"
        )
        adapter = source[adapter_start:]
        clear_at = adapter.index("stage61_factory_prepare_fault_clear(state);")
        status_at = adapter.index(
            "state->last_status = STAGE61_FACTORY_STATUS_ERROR;"
        )
        delegate_at = adapter.index("return FN_FACTORY_PREPARE_BATTLE();")
        self.assertLess(clear_at, status_at)
        self.assertLess(status_at, delegate_at)


if __name__ == "__main__":
    unittest.main()
