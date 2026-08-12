#!/usr/bin/env python3
"""Resolve patch-only overlap into exact output conflicts using a clean ROM.

The clean ROM never leaves the local machine. This tool applies the Vega IPS and
Factory UPS independently in memory, then classifies every byte touched by both
patches as SAME_TARGET or DIFFERENT_TARGET. It does not create a merged ROM.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_CRC32 = 0x3B2056E9


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve().parent
analyzer = load_module(HERE / "analyze_patches.py", "vega_patch_analyzer")
builder = load_module(HERE / "build_reference_roms.py", "vega_reference_builder")


@dataclass(frozen=True)
class ExactRange:
    start: int
    end: int
    status: str

    @property
    def length(self) -> int:
        return self.end - self.start


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def merge_status_bytes(items: Iterable[tuple[int, str]]) -> list[ExactRange]:
    result: list[ExactRange] = []
    for offset, status in items:
        if result and result[-1].end == offset and result[-1].status == status:
            previous = result[-1]
            result[-1] = ExactRange(previous.start, offset + 1, status)
        else:
            result.append(ExactRange(offset, offset + 1, status))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify exact Vega/Factory output conflicts using clean FireRed Rev 0"
    )
    parser.add_argument("clean_rom", type=Path)
    parser.add_argument("vega_ips", type=Path)
    parser.add_argument("factory_ups", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("exact_audit"))
    parser.add_argument(
        "--write-reference-roms",
        action="store_true",
        help="also write the two independently patched reference ROMs; never redistribute them",
    )
    args = parser.parse_args()

    clean = args.clean_rom.read_bytes()
    clean_crc = zlib.crc32(clean) & 0xFFFFFFFF
    if clean_crc != EXPECTED_CRC32:
        raise SystemExit(
            f"Clean ROM CRC32 must be {EXPECTED_CRC32:08X}; got {clean_crc:08X}"
        )

    ips = analyzer.parse_ips(args.vega_ips)
    ups = analyzer.parse_ups(args.factory_ups)
    if ups["source_crc"] != clean_crc:
        raise SystemExit(
            f"UPS expects source CRC32 {ups['source_crc']:08X}, not {clean_crc:08X}"
        )

    vega = builder.apply_ips(clean, ips["data"])
    factory, factory_crc = builder.apply_ups(clean, ups["data"])

    overlaps = analyzer.intersect_ranges(ips["ranges"], ups["ranges"])
    status_bytes: list[tuple[int, str]] = []
    same_count = 0
    different_count = 0
    for region in overlaps:
        for offset in range(region.start, region.end):
            vega_byte = vega[offset] if offset < len(vega) else 0
            factory_byte = factory[offset] if offset < len(factory) else 0
            status = "SAME_TARGET" if vega_byte == factory_byte else "DIFFERENT_TARGET"
            status_bytes.append((offset, status))
            if status == "SAME_TARGET":
                same_count += 1
            else:
                different_count += 1

    exact_ranges = merge_status_bytes(status_bytes)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for number, region in enumerate(exact_ranges, start=1):
        vega_bytes = vega[region.start : region.end]
        factory_bytes = factory[region.start : region.end]
        clean_bytes = clean[region.start : region.end]
        rows.append(
            {
                "id": number,
                "status": region.status,
                "file_offset_start": f"0x{region.start:08X}",
                "file_offset_end_inclusive": f"0x{region.end - 1:08X}",
                "gba_address_start": f"0x{0x08000000 + region.start:08X}",
                "gba_address_end_inclusive": f"0x{0x08000000 + region.end - 1:08X}",
                "length": region.length,
                "clean_hex": clean_bytes.hex().upper(),
                "vega_target_hex": vega_bytes.hex().upper(),
                "factory_target_hex": factory_bytes.hex().upper(),
            }
        )

    csv_path = args.out_dir / "exact_conflicts.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "inputs": {
            "clean_rom_size": len(clean),
            "clean_crc32": f"{clean_crc:08X}",
            "clean_sha256": sha256_bytes(clean),
            "vega_ips": args.vega_ips.name,
            "factory_ups": args.factory_ups.name,
        },
        "outputs": {
            "vega_size": len(vega),
            "vega_crc32": f"{zlib.crc32(vega) & 0xFFFFFFFF:08X}",
            "vega_sha256": sha256_bytes(vega),
            "factory_size": len(factory),
            "factory_crc32": f"{factory_crc:08X}",
            "factory_sha256": sha256_bytes(factory),
        },
        "comparison": {
            "double_touched_bytes": same_count + different_count,
            "same_target_bytes": same_count,
            "different_target_bytes": different_count,
            "exact_status_range_count": len(exact_ranges),
            "same_target_percent": round(
                100 * same_count / (same_count + different_count), 8
            )
            if same_count + different_count
            else 0,
            "different_target_percent": round(
                100 * different_count / (same_count + different_count), 8
            )
            if same_count + different_count
            else 0,
        },
        "ranges": rows,
    }
    json_path = args.out_dir / "exact_conflicts.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = args.out_dir / "exact_conflicts.md"
    c = summary["comparison"]
    lines = [
        "# Clean ROMを使った厳密競合判定",
        "",
        f"- Clean CRC32: `{clean_crc:08X}`",
        f"- Vega output CRC32: `{summary['outputs']['vega_crc32']}`",
        f"- Factory output CRC32: `{summary['outputs']['factory_crc32']}`",
        f"- 両パッチが触るbytes: **{c['double_touched_bytes']:,}**",
        f"- 同じ値へ変更: **{c['same_target_bytes']:,}**",
        f"- 異なる値へ変更: **{c['different_target_bytes']:,}**",
        "",
        "`SAME_TARGET`でも、周辺のポインタ依存やRAM/save構造が互換とは限りません。",
        "`DIFFERENT_TARGET`は、少なくともバイト単位で明確な移植判断が必要です。",
        "このツールは統合ROMを生成しません。",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.write_reference_roms:
        refs = args.out_dir / "reference_roms"
        refs.mkdir(exist_ok=True)
        (refs / "vega_reference.gba").write_bytes(vega)
        (refs / "factory_reference.gba").write_bytes(factory)
        print("Reference ROMs written for local analysis. Do not redistribute them.")

    print(json.dumps(summary["comparison"], ensure_ascii=False, indent=2))
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
