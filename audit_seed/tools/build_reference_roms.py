#!/usr/bin/env python3
"""Build separate Vega and Factory reference ROMs from a user-owned clean ROM.

This intentionally does NOT create a merged ROM. It validates the clean ROM,
applies each patch independently, and checks the UPS target CRC. The outputs are
for local analysis/testing only and must not be redistributed.
"""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

EXPECTED_CLEAN_CRC32 = 0x3B2056E9


def read_vli(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 1
    while True:
        byte = data[pos]
        pos += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            return value, pos
        shift <<= 7
        value += shift


def apply_ips(source: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b"PATCH"):
        raise ValueError("invalid IPS header")
    output = bytearray(source)
    pos = 5
    while patch[pos : pos + 3] != b"EOF":
        offset = int.from_bytes(patch[pos : pos + 3], "big")
        pos += 3
        length = int.from_bytes(patch[pos : pos + 2], "big")
        pos += 2
        if length:
            payload = patch[pos : pos + length]
            pos += length
        else:
            length = int.from_bytes(patch[pos : pos + 2], "big")
            pos += 2
            payload = bytes([patch[pos]]) * length
            pos += 1
        needed = offset + length
        if needed > len(output):
            output.extend(b"\x00" * (needed - len(output)))
        output[offset:needed] = payload
    pos += 3
    if len(patch) - pos == 3:
        target_size = int.from_bytes(patch[pos : pos + 3], "big")
        del output[target_size:]
        if len(output) < target_size:
            output.extend(b"\x00" * (target_size - len(output)))
    return bytes(output)


def apply_ups(source: bytes, patch: bytes) -> tuple[bytes, int]:
    if not patch.startswith(b"UPS1"):
        raise ValueError("invalid UPS header")
    if (zlib.crc32(patch[:-4]) & 0xFFFFFFFF) != struct.unpack("<I", patch[-4:])[0]:
        raise ValueError("UPS patch CRC mismatch")

    pos = 4
    input_size, pos = read_vli(patch, pos)
    output_size, pos = read_vli(patch, pos)
    source_crc, target_crc, _ = struct.unpack("<III", patch[-12:])

    if len(source) != input_size:
        raise ValueError(f"UPS input size mismatch: {len(source)} != {input_size}")
    actual_source_crc = zlib.crc32(source) & 0xFFFFFFFF
    if actual_source_crc != source_crc:
        raise ValueError(
            f"UPS source CRC mismatch: {actual_source_crc:08X} != {source_crc:08X}"
        )

    output = bytearray(output_size)
    output[: min(len(source), output_size)] = source[:output_size]
    footer = len(patch) - 12
    offset = 0
    while pos < footer:
        relative, pos = read_vli(patch, pos)
        offset += relative
        while True:
            byte = patch[pos]
            pos += 1
            if byte == 0:
                break
            source_byte = source[offset] if offset < len(source) else 0
            output[offset] = source_byte ^ byte
            offset += 1
        offset += 1

    actual_target_crc = zlib.crc32(output) & 0xFFFFFFFF
    if actual_target_crc != target_crc:
        raise ValueError(
            f"UPS target CRC mismatch: {actual_target_crc:08X} != {target_crc:08X}"
        )
    return bytes(output), target_crc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("clean_rom", type=Path)
    parser.add_argument("vega_ips", type=Path)
    parser.add_argument("factory_ups", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("reference_roms"))
    args = parser.parse_args()

    clean = args.clean_rom.read_bytes()
    clean_crc = zlib.crc32(clean) & 0xFFFFFFFF
    if clean_crc != EXPECTED_CLEAN_CRC32:
        raise SystemExit(
            f"Clean ROM CRC32 must be {EXPECTED_CLEAN_CRC32:08X}; got {clean_crc:08X}"
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    vega = apply_ips(clean, args.vega_ips.read_bytes())
    factory, factory_crc = apply_ups(clean, args.factory_ups.read_bytes())

    vega_path = args.out_dir / "vega_reference.gba"
    factory_path = args.out_dir / "factory_reference.gba"
    vega_path.write_bytes(vega)
    factory_path.write_bytes(factory)

    print(f"clean CRC32   : {clean_crc:08X}")
    print(f"vega CRC32    : {zlib.crc32(vega) & 0xFFFFFFFF:08X}")
    print(f"factory CRC32 : {factory_crc:08X}")
    print(f"wrote {vega_path}")
    print(f"wrote {factory_path}")
    print("Do not redistribute generated ROM files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
