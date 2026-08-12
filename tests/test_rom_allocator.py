#!/usr/bin/env python3
"""Focused tests for the deterministic 32 MiB ROM allocator."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.rom_allocator import (
    GBA_ROM_BASE,
    REGION_CSV_FIELDS,
    ROM_SIZE,
    RomAllocationError,
    RomAllocator,
    RomRegion,
    build_allocation_report,
    build_allocation_report_from_csv,
    load_regions_csv,
    validate_regions,
)


class RomAllocatorTests(unittest.TestCase):
    def region(
        self,
        name: str,
        start: int,
        end: int,
        *,
        alignment: int = 4,
        kind: str = "allocatable",
    ) -> RomRegion:
        return RomRegion(name, start, end, alignment, kind, "test", f"{name} use")

    def write_csv(self, directory: Path, rows: list[dict[str, object]]) -> Path:
        path = directory / "rom_regions.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=REGION_CSV_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_csv_schema_hex_decimal_and_canonical_region_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_csv(
                Path(temporary),
                [
                    {
                        "name": "extension_b",
                        "start": "0x01001000",
                        "end_exclusive": str(0x01002000),
                        "alignment": "0x10",
                        "kind": "allocatable",
                        "owner": "port",
                        "purpose": "second extension bank",
                    },
                    {
                        "name": "extension_a",
                        "start": "0x01000000",
                        "end_exclusive": "0x01001000",
                        "alignment": "16",
                        "kind": "reserved",
                        "owner": "vega",
                        "purpose": "preserved data",
                    },
                ],
            )
            regions = load_regions_csv(path)
        self.assertEqual([region.name for region in regions], ["extension_a", "extension_b"])
        self.assertEqual(regions[1].start, 0x01001000)
        self.assertEqual(regions[1].alignment, 16)

    def test_csv_header_and_regular_file_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            bad = directory / "bad.csv"
            bad.write_text("name,start,end_exclusive\nx,0,4\n", encoding="utf-8")
            with self.assertRaisesRegex(RomAllocationError, "header mismatch"):
                load_regions_csv(bad)
            target = self.write_csv(
                directory,
                [
                    {
                        "name": "x",
                        "start": 0,
                        "end_exclusive": 4,
                        "alignment": 4,
                        "kind": "allocatable",
                        "owner": "test",
                        "purpose": "test",
                    }
                ],
            )
            link = directory / "regions-link.csv"
            link.symlink_to(target)
            with self.assertRaisesRegex(RomAllocationError, "non-symlink"):
                load_regions_csv(link)

    def test_csv_rejects_physical_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "blank.csv"
            path.write_text(
                ",".join(REGION_CSV_FIELDS)
                + "\n\nmodules,0,16,4,allocatable,test,test use\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RomAllocationError, "line 2 is blank"):
                load_regions_csv(path)

    def test_regions_reject_overlap_duplicate_out_of_bounds_and_bad_alignment(self) -> None:
        cases = (
            (
                [
                    self.region("reserved_a", 0x100, 0x200, kind="reserved"),
                    self.region("reserved_b", 0x180, 0x280, kind="reserved"),
                ],
                "overlapping ROM regions",
            ),
            ([self.region("same", 0, 4), self.region("same", 4, 8)], "duplicate"),
            ([self.region("outside", ROM_SIZE, ROM_SIZE + 4)], "outside"),
            ([self.region("empty", 4, 4)], "outside"),
            ([self.region("bad_align", 4, 16, alignment=3)], "power of two"),
            ([self.region("misaligned", 2, 16, alignment=4)], "not aligned"),
        )
        for regions, pattern in cases:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(RomAllocationError, pattern):
                    validate_regions(regions)

    def test_adjacent_regions_and_exact_32_mib_end_are_allowed(self) -> None:
        regions = validate_regions(
            [
                self.region("first", ROM_SIZE - 0x2000, ROM_SIZE - 0x1000),
                self.region("last", ROM_SIZE - 0x1000, ROM_SIZE),
            ]
        )
        self.assertEqual(regions[-1].end_exclusive, ROM_SIZE)

    def test_public_api_rejects_zero_regions(self) -> None:
        with self.assertRaisesRegex(RomAllocationError, "at least one"):
            validate_regions([])
        with self.assertRaisesRegex(RomAllocationError, "at least one"):
            RomAllocator([])

    def test_first_fit_is_aligned_deterministic_and_reuses_holes(self) -> None:
        region = self.region("modules", 0x01000000, 0x01000100, alignment=4)
        requests = [
            {"name": "middle", "region": "modules", "size": 0x10, "start": 0x01000040},
            {"name": "head", "region": "modules", "size": 3},
            {"name": "aligned", "region": "modules", "size": 8, "alignment": 16},
            {"name": "tail_of_hole", "region": "modules", "size": 0x24},
        ]
        first = build_allocation_report([region], requests)
        second = build_allocation_report([region], requests)
        self.assertEqual(first, second)
        self.assertEqual(
            [item["start"] for item in first["allocations"]],
            [0x01000040, 0x01000000, 0x01000010, 0x01000018],
        )
        self.assertEqual(first["allocations"][0]["placement"], "EXPLICIT")
        self.assertEqual(first["allocations"][1]["placement"], "FIRST_FIT")

    def test_t03_partition_accepts_noop_only_in_integration_region(self) -> None:
        allocator = RomAllocator(
            [
                self.region("vega_base", 0, 0x01000000, kind="reserved"),
                self.region(
                    "cfru_payload", 0x01000000, 0x01200000, kind="reserved"
                ),
                self.region("integration_modules", 0x01200000, 0x01600000),
                self.region(
                    "dpe_payload", 0x01600000, 0x01F50000, kind="reserved"
                ),
                self.region("future_tail", 0x01F50000, ROM_SIZE),
            ]
        )
        noop = allocator.allocate(
            "noop_adapter", "integration_modules", 0x40, start=0x01200000
        )
        self.assertEqual(noop.start, 0x01200000)
        self.assertEqual(noop.to_report()["gba_start"], 0x09200000)
        for name in ("cfru_payload", "dpe_payload"):
            with self.subTest(region=name):
                with self.assertRaisesRegex(RomAllocationError, "reserved"):
                    allocator.allocate(f"bad_{name}", name, 4)

    def test_explicit_allocation_must_be_aligned_inside_region_and_disjoint(self) -> None:
        allocator = RomAllocator([self.region("modules", 0x100, 0x200, alignment=8)])
        allocator.allocate("base", "modules", 0x20, start=0x140)
        cases = (
            (
                {
                    "name": "misaligned",
                    "region": "modules",
                    "size": 4,
                    "start": 0x104,
                },
                "not aligned",
            ),
            ({"name": "before", "region": "modules", "size": 8, "start": 0xF8}, "outside"),
            ({"name": "past", "region": "modules", "size": 16, "start": 0x1F8}, "outside"),
            ({"name": "collision", "region": "modules", "size": 8, "start": 0x150}, "overlap"),
        )
        for request, pattern in cases:
            with self.subTest(name=request["name"]):
                with self.assertRaisesRegex(RomAllocationError, pattern):
                    allocator.allocate_request(request)

    def test_duplicate_zero_unknown_reserved_and_exhaustion_fail(self) -> None:
        allocator = RomAllocator(
            [
                self.region("tiny", 0, 8),
                self.region("owned", 8, 16, kind="reserved"),
            ]
        )
        allocator.allocate("only", "tiny", 8)
        cases = (
            ({"name": "only", "region": "tiny", "size": 1}, "duplicate"),
            ({"name": "zero", "region": "tiny", "size": 0}, "greater than zero"),
            ({"name": "unknown", "region": "missing", "size": 1}, "unknown"),
            ({"name": "reserved", "region": "owned", "size": 1}, "reserved"),
            ({"name": "full", "region": "tiny", "size": 1}, "does not fit"),
        )
        for request, pattern in cases:
            with self.subTest(name=request["name"]):
                with self.assertRaisesRegex(RomAllocationError, pattern):
                    allocator.allocate_request(request)

    def test_report_schema_addresses_summaries_and_no_raw_bytes(self) -> None:
        allocator = RomAllocator(
            [
                self.region("modules", 0x01000000, 0x01000100),
                self.region("guard", 0x01000100, 0x01000200, kind="reserved"),
            ]
        )
        digest = "A" * 64
        allocation = allocator.allocate(
            "noop",
            "modules",
            12,
            owner="vega_adapter",
            purpose="no-op module",
            content_sha256=digest,
        )
        report = allocator.report()
        self.assertEqual(set(report), {"schema_version", "regions", "allocations", "summaries"})
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(allocation.start, 0x01000000)
        self.assertEqual(report["allocations"][0]["gba_start"], GBA_ROM_BASE + 0x01000000)
        self.assertEqual(report["allocations"][0]["content_sha256"], digest.lower())
        self.assertEqual(report["summaries"]["overlap_count"], 0)
        self.assertEqual(report["summaries"]["allocated_bytes"], 12)
        serialized = json.dumps(report, sort_keys=True)
        for forbidden in ("raw_bytes", "timestamp", "generated_at", "userfile/"):
            self.assertNotIn(forbidden, serialized.lower())

    def test_request_schema_rejects_raw_bytes_and_invalid_digest(self) -> None:
        allocator = RomAllocator([self.region("modules", 0, 0x100)])
        with self.assertRaisesRegex(RomAllocationError, "unknown fields"):
            allocator.allocate_request(
                {"name": "secret", "region": "modules", "size": 4, "data": b"ROM!"}
            )
        with self.assertRaisesRegex(RomAllocationError, "64 hex"):
            allocator.allocate_request(
                {
                    "name": "digest",
                    "region": "modules",
                    "size": 4,
                    "content_sha256": "not-a-digest",
                }
            )

    def test_report_from_csv_has_stable_json_and_expected_usage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_csv(
                Path(temporary),
                [
                    {
                        "name": "modules",
                        "start": "0x1000000",
                        "end_exclusive": "0x1001000",
                        "alignment": "4",
                        "kind": "allocatable",
                        "owner": "integration",
                        "purpose": "linked modules",
                    }
                ],
            )
            requests = [
                {"name": "one", "region": "modules", "size": "0x20"},
                {"name": "two", "region": "modules", "size": 16, "alignment": 16},
            ]
            first = build_allocation_report_from_csv(path, requests)
            second = build_allocation_report_from_csv(path, requests)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )
        usage = first["summaries"]["region_usage"]
        self.assertEqual(usage[0]["allocation_count"], 2)
        self.assertEqual(usage[0]["allocated_bytes"], 0x30)
        self.assertEqual(usage[0]["remaining_bytes"], 0x1000 - 0x30)


if __name__ == "__main__":
    unittest.main()
