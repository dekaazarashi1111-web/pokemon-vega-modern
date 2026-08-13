from __future__ import annotations

import copy
import hashlib
import re
import struct
import unittest
from pathlib import Path

from tools.engine import cfru_script_table_gate as gate


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TABLE = (
    ROOT
    / "vendor/upstream/CFRU-JP/assembly/data/battle_script_commands_table.s"
)


def _source_entries() -> tuple[list[str], list[str]]:
    groups: dict[str, list[str]] = {"main": [], "secondary": []}
    current: str | None = None
    for line in SOURCE_TABLE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "gBattleScriptingCommandsTable:":
            current = "main"
        elif stripped == "gBattleScriptingCommandsTable2:":
            current = "secondary"
        elif current is not None and stripped.startswith(".word "):
            groups[current].append(stripped.split()[1])
    return groups["main"], groups["secondary"]


class ScriptTableFixture:
    IMAGE_SIZE = 0x50000
    MAIN_OFFSET = 0x30000
    SECONDARY_OFFSET = MAIN_OFFSET + gate.MAIN_ENTRY_COUNT * 4
    BOUNDARY_OFFSET = SECONDARY_OFFSET + gate.SECONDARY_ENTRY_COUNT * 4

    def __init__(self) -> None:
        self.main_source, self.secondary_source = _source_entries()
        self.offsets: dict[str, int] = {
            gate.MAIN_SYMBOL: gate.ROM_BASE + self.MAIN_OFFSET,
            gate.SECONDARY_SYMBOL: gate.ROM_BASE + self.SECONDARY_OFFSET,
            gate.SECONDARY_BOUNDARY_SYMBOL: gate.ROM_BASE + self.BOUNDARY_OFFSET,
        }
        next_target = gate.ROM_BASE + 0x38000
        for source in self.main_source + self.secondary_source:
            if source == "NULL" or source.startswith("0x") or source in self.offsets:
                continue
            self.offsets[source] = next_target
            next_target += 2

        image = bytearray(self.IMAGE_SIZE)
        for index, source in enumerate(self.main_source):
            struct.pack_into(
                "<I", image, self.MAIN_OFFSET + index * 4, self.pointer(source)
            )
        for index, source in enumerate(self.secondary_source):
            struct.pack_into(
                "<I", image, self.SECONDARY_OFFSET + index * 4, self.pointer(source)
            )
        main_address = self.offsets[gate.MAIN_SYMBOL]
        for site in gate.DEFAULT_ROOT_SITES:
            struct.pack_into("<I", image, site, main_address)
        self.image = bytes(image)

    def pointer(self, source: str) -> int:
        if source == "NULL":
            return 0
        if source.startswith("0x"):
            return int(source, 16)
        return self.offsets[source] | 1

    def mutate_u32(self, offset: int, value: int) -> bytes:
        image = bytearray(self.image)
        struct.pack_into("<I", image, offset, value)
        return bytes(image)


class SourceContractTests(unittest.TestCase):
    def test_fixed_source_counts_and_null_bitmap(self) -> None:
        main, secondary = _source_entries()
        self.assertEqual(len(main), 256)
        self.assertEqual(len(secondary), 57)
        self.assertEqual(
            tuple(index for index, source in enumerate(secondary) if source == "NULL"),
            gate.SECONDARY_NULL_INDICES,
        )
        self.assertNotIn("NULL", main)
        self.assertEqual(main[0xFF], gate.SECONDARY_DISPATCH_SYMBOL)


class LinkedScriptTableGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ScriptTableFixture()

    def assert_rejected(
        self,
        *,
        image: bytes | None = None,
        offsets: dict[str, int] | None = None,
        root_sites: tuple[int, ...] | None = None,
    ) -> None:
        with self.assertRaises(gate.CFRUScriptTableGateError):
            gate.validate_script_command_tables(
                self.fixture.image if image is None else image,
                self.fixture.offsets if offsets is None else offsets,
                root_sites,
            )

    def test_valid_linked_tables_return_deterministic_metadata_snapshot(self) -> None:
        report = gate.validate_script_command_tables(
            self.fixture.image, self.fixture.offsets
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source_contract"]["main_entry_count"], 256)
        self.assertEqual(report["source_contract"]["secondary_entry_count"], 57)
        self.assertEqual(report["tables"]["main"]["entry_count"], 256)
        self.assertEqual(report["tables"]["main"]["null_indices"], [])
        self.assertEqual(report["tables"]["secondary"]["entry_count"], 57)
        self.assertEqual(
            report["tables"]["secondary"]["null_indices"],
            list(gate.SECONDARY_NULL_INDICES),
        )
        self.assertEqual(len(report["tables"]["main"]["entry_sha256"]), 256)
        self.assertEqual(len(report["tables"]["secondary"]["entry_sha256"]), 57)
        self.assertEqual(len(report["target_snapshot"]["main"]), 256)
        self.assertEqual(len(report["target_snapshot"]["secondary"]), 57)
        self.assertEqual(
            report["dispatch"]["pointer"],
            self.fixture.offsets[gate.SECONDARY_DISPATCH_SYMBOL] | 1,
        )
        self.assertTrue(report["roots"]["uses_default_sites"])
        self.assertEqual(report["roots"]["count"], 5)
        self.assertEqual(report["image"]["sha256"], hashlib.sha256(self.fixture.image).hexdigest())
        self.assertRegex(report["snapshot_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            report,
            gate.validate_script_command_tables(self.fixture.image, self.fixture.offsets),
        )

    def test_unknown_in_range_target_is_rejected(self) -> None:
        unknown = gate.ROM_BASE + 0x3F001
        image = self.fixture.mutate_u32(self.fixture.MAIN_OFFSET, unknown)
        self.assert_rejected(image=image)

    def test_ambiguous_unknown_command_symbol_is_rejected(self) -> None:
        offsets = copy.copy(self.fixture.offsets)
        offsets["atk00_unknown_alias"] = gate.ROM_BASE + 0x3F100
        self.assert_rejected(offsets=offsets)

    def test_main_null_is_rejected(self) -> None:
        image = self.fixture.mutate_u32(self.fixture.MAIN_OFFSET + 0x20 * 4, 0)
        self.assert_rejected(image=image)

    def test_secondary_null_contract_is_fail_closed(self) -> None:
        with self.subTest("allowed NULL changed to command"):
            image = self.fixture.mutate_u32(
                self.fixture.SECONDARY_OFFSET,
                gate.ROM_BASE + 0x3F001,
            )
            self.assert_rejected(image=image)
        with self.subTest("required command changed to NULL"):
            image = self.fixture.mutate_u32(
                self.fixture.SECONDARY_OFFSET + 0x02 * 4,
                0,
            )
            self.assert_rejected(image=image)

    def test_each_root_must_point_to_main_table(self) -> None:
        for site in gate.DEFAULT_ROOT_SITES:
            with self.subTest(site=hex(site)):
                image = self.fixture.mutate_u32(
                    site, self.fixture.offsets[gate.SECONDARY_SYMBOL]
                )
                self.assert_rejected(image=image)

    def test_main_and_secondary_count_boundaries_are_exact(self) -> None:
        with self.subTest("main has 255 entries"):
            offsets = copy.copy(self.fixture.offsets)
            offsets[gate.SECONDARY_SYMBOL] -= 4
            self.assert_rejected(offsets=offsets)
        with self.subTest("main has 257 entries"):
            offsets = copy.copy(self.fixture.offsets)
            offsets[gate.SECONDARY_SYMBOL] += 4
            self.assert_rejected(offsets=offsets)
        with self.subTest("secondary has 56 entries"):
            offsets = copy.copy(self.fixture.offsets)
            offsets[gate.SECONDARY_BOUNDARY_SYMBOL] -= 4
            self.assert_rejected(offsets=offsets)
        with self.subTest("secondary has 58 entries"):
            offsets = copy.copy(self.fixture.offsets)
            offsets[gate.SECONDARY_BOUNDARY_SYMBOL] += 4
            self.assert_rejected(offsets=offsets)

    def test_non_thumb_and_out_of_image_targets_are_rejected(self) -> None:
        source = self.fixture.main_source[0]
        with self.subTest("non-Thumb linked symbol"):
            offsets = copy.copy(self.fixture.offsets)
            offsets[source] |= 1
            self.assert_rejected(offsets=offsets)
        with self.subTest("target outside image"):
            offsets = copy.copy(self.fixture.offsets)
            outside = gate.ROM_BASE + self.fixture.IMAGE_SIZE + 0x100
            offsets[source] = outside
            image = self.fixture.mutate_u32(self.fixture.MAIN_OFFSET, outside | 1)
            self.assert_rejected(image=image, offsets=offsets)

    def test_main_ff_secondary_dispatch_target_is_not_interchangeable(self) -> None:
        replacement = self.fixture.pointer(self.fixture.main_source[0xFE])
        image = self.fixture.mutate_u32(
            self.fixture.MAIN_OFFSET + 0xFF * 4, replacement
        )
        self.assert_rejected(image=image)

    def test_missing_required_symbols_are_rejected(self) -> None:
        for symbol in (
            gate.MAIN_SYMBOL,
            gate.SECONDARY_SYMBOL,
            gate.SECONDARY_BOUNDARY_SYMBOL,
            gate.SECONDARY_DISPATCH_SYMBOL,
            self.fixture.main_source[0],
        ):
            with self.subTest(symbol=symbol):
                offsets = copy.copy(self.fixture.offsets)
                offsets.pop(symbol)
                self.assert_rejected(offsets=offsets)

    def test_custom_root_seam_still_requires_five_valid_unique_sites(self) -> None:
        valid = (0x100, 0x104, 0x108, 0x10C, 0x110)
        image = bytearray(self.fixture.image)
        for site in valid:
            struct.pack_into("<I", image, site, self.fixture.offsets[gate.MAIN_SYMBOL])
        report = gate.validate_script_command_tables(bytes(image), self.fixture.offsets, valid)
        self.assertFalse(report["roots"]["uses_default_sites"])
        self.assertEqual([row["rom_offset"] for row in report["roots"]["records"]], list(valid))

        for roots in (
            valid[:4],
            (0x100, 0x100, 0x108, 0x10C, 0x110),
            (0x101, 0x104, 0x108, 0x10C, 0x110),
            (0x100, 0x104, 0x108, 0x10C, self.fixture.IMAGE_SIZE),
        ):
            with self.subTest(roots=roots):
                self.assert_rejected(root_sites=roots)

    def test_non_bytes_and_invalid_offset_values_are_rejected(self) -> None:
        with self.assertRaises(gate.CFRUScriptTableGateError):
            gate.validate_script_command_tables(bytearray(self.fixture.image), self.fixture.offsets)  # type: ignore[arg-type]
        for value in (True, -1, 0x1_0000_0000):
            with self.subTest(value=value):
                offsets = copy.copy(self.fixture.offsets)
                offsets["irrelevant"] = value
                self.assert_rejected(offsets=offsets)


if __name__ == "__main__":
    unittest.main()
