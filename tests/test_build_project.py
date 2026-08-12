#!/usr/bin/env python3
"""T03 stage driverの副作用なしfocused unit tests。"""

from __future__ import annotations

import unittest

from scripts.build_project import (
    GBA_ROM_BASE,
    HarnessBuildError,
    apply_ips,
    expand_rom_ff,
    expected_byte_assertions,
    gba_header_checksum,
    insert_declared_module,
    validate_smoke_result,
    validate_gba_header,
)


class BuildProjectTests(unittest.TestCase):
    def test_ips_literal_rle_and_truncate_are_deterministic(self) -> None:
        source = b"\x00" * 16
        patch = (
            b"PATCH"
            + b"\x00\x00\x01\x00\x02\xAA\xBB"
            + b"\x00\x00\x04\x00\x00\x00\x03\xCC"
            + b"EOF\x00\x00\x08"
        )
        first = apply_ips(source, patch)
        second = apply_ips(source, patch)
        self.assertEqual(first, second)
        self.assertEqual(first, b"\x00\xAA\xBB\x00\xCC\xCC\xCC\x00")
        self.assertEqual(source, b"\x00" * 16)

    def test_ips_extends_with_zero_and_rejects_malformed_streams(self) -> None:
        patch = b"PATCH\x00\x00\x03\x00\x02\x11\x22EOF"
        self.assertEqual(apply_ips(b"\xAA", patch), b"\xAA\x00\x00\x11\x22")
        cases = (
            b"WRONG",
            b"PATCH\x00\x00",
            b"PATCH\x00\x00\x00\x00\x01",
            b"PATCHEOFjunk",
            b"PATCH\x00\x00\x00\x00\x00\x00\x00\xFFEOF",
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(HarnessBuildError):
                    apply_ips(b"", value)

    def test_ff_expansion_and_shrink_rejection(self) -> None:
        self.assertEqual(expand_rom_ff(b"\x01\x02", 5), b"\x01\x02\xFF\xFF\xFF")
        self.assertEqual(expand_rom_ff(b"abc", 3), b"abc")
        with self.assertRaisesRegex(HarnessBuildError, "smaller"):
            expand_rom_ff(b"abcd", 3)
        with self.assertRaisesRegex(HarnessBuildError, "integer"):
            expand_rom_ff(b"", True)

    def test_gba_header_identity_and_checksum(self) -> None:
        rom = bytearray(0xC0)
        rom[0xA0:0xAC] = b"POKEMON FIRE"
        rom[0xAC:0xB0] = b"BPRJ"
        rom[0xBD] = gba_header_checksum(rom)
        result = validate_gba_header(
            bytes(rom), expected_title="POKEMON FIRE", expected_game_code="BPRJ"
        )
        self.assertEqual(result["stored_checksum"], result["computed_checksum"])
        self.assertFalse(result["checksum_fix_applied"])
        rom[0xBD] ^= 1
        with self.assertRaisesRegex(HarnessBuildError, "checksum"):
            validate_gba_header(
                bytes(rom), expected_title="POKEMON FIRE", expected_game_code="BPRJ"
            )

    def test_expected_byte_assertions_normalize_thumb_address(self) -> None:
        rom = b"\x10\x20\x30\x40"
        rows = expected_byte_assertions(
            rom,
            {"entry": f"0x{GBA_ROM_BASE + 1:08X}"},
            {"entry": "10203040"},
        )
        self.assertEqual(rows[0]["rom_offset"], "0x00000000")
        self.assertEqual(rows[0]["actual_hex"], "10203040")
        with self.assertRaisesRegex(HarnessBuildError, "failed"):
            expected_byte_assertions(
                rom,
                {"entry": f"0x{GBA_ROM_BASE + 1:08X}"},
                {"entry": "10203041"},
            )

    def test_module_insertion_changes_only_declared_ff_span(self) -> None:
        source = b"\xAA" * 4 + b"\xFF" * 8 + b"\xBB" * 4
        output, assertion = insert_declared_module(
            source, b"\x70\x47", start=4, expected_fill=0xFF
        )
        self.assertEqual(output[:4], source[:4])
        self.assertEqual(output[4:6], b"\x70\x47")
        self.assertEqual(output[6:], source[6:])
        self.assertEqual(assertion["gba_address"], "0x08000004")
        with self.assertRaisesRegex(HarnessBuildError, "expected-byte"):
            insert_declared_module(source, b"\x70\x47", start=3, expected_fill=0xFF)

    def test_module_insertion_rejects_empty_and_out_of_bounds(self) -> None:
        for module, start in ((b"", 0), (b"x", -1), (b"xx", 3)):
            with self.subTest(module=module, start=start):
                with self.assertRaises(HarnessBuildError):
                    insert_declared_module(
                        b"\xFF" * 4, module, start=start, expected_fill=0xFF
                    )

    def test_smoke_result_contract_rejects_saved_metadata_tampering(self) -> None:
        observation = {
            "title_framebuffer_fnv1a64": "0123456789abcdef",
            "title_pixel_transitions": 101,
            "new_game": {"map_group": 4, "map_number": 0, "x": 10, "y": 2},
            "movement": {"key": 32, "x": 6, "y": 2},
            "save": {"status": 1, "size": 0x20000},
            "load": {"status": 1, "restored": True, "fresh_core": True},
        }
        checks = {
            "title": True,
            "new_game": True,
            "basic_map_movement": True,
            "save": True,
            "load": True,
            "observable_equivalence": True,
        }
        config = {
            "expected_title_framebuffer_fnv1a64": "0123456789abcdef",
            "movement_keys": [32],
            "save_status_ok": 1,
            "expected_new_game": observation["new_game"],
            "expected_movement": observation["movement"],
        }
        valid = {
            "schema_version": 1,
            "status": "PASS",
            "measurement": "libmGBA_reference_candidate_behavior",
            "checks": checks,
            "reference": observation,
            "candidate": observation,
            "artifacts_written": [],
        }
        validate_smoke_result(valid, config)
        mutations = (
            {**valid, "checks": {**checks, "load": False}},
            {
                **valid,
                "candidate": {**observation, "new_game": {"map_group": 99}},
            },
            {
                **valid,
                "reference": {
                    **observation,
                    "load": {"status": 1, "restored": False, "fresh_core": True},
                },
                "candidate": {
                    **observation,
                    "load": {"status": 1, "restored": False, "fresh_core": True},
                },
            },
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(HarnessBuildError):
                    validate_smoke_result(mutation, config)


if __name__ == "__main__":
    unittest.main()
