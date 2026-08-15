#!/usr/bin/env python3
"""Exact-ROM static acceptance plus optional mGBA fixture result enforcement."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

GBA_BASE = 0x08000000


class AcceptanceError(ValueError):
    pass


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise AcceptanceError(f"not integer: {value!r}")


def rom_offset(address: int, size: int, rom_size: int) -> int:
    value = address - GBA_BASE
    if value < 0 or value + size > rom_size:
        raise AcceptanceError(f"address outside ROM: 0x{address:08X}+{size}")
    return value


def read_u32(rom: bytes, address: int) -> int:
    return struct.unpack_from("<I", rom, rom_offset(address, 4, len(rom)))[0]


def expected_script(wrapper: int) -> bytes:
    return b"\x6A\x5A\x23" + struct.pack("<I", wrapper | 1) + b"\x27\x6C\x02"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--stage-metadata", type=Path, required=True)
    parser.add_argument("--runtime-bin", type=Path, required=True)
    parser.add_argument("--emulator-command", nargs="+")
    parser.add_argument("--emulator-result", type=Path)
    parser.add_argument("--require-emulator", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    try:
        rom = args.rom.read_bytes()
        metadata = json.loads(args.stage_metadata.read_text(encoding="utf-8"))
        expected_sha = metadata.get("output_sha256")
        if sha(rom) != expected_sha:
            raise AcceptanceError("exact ROM SHA differs from stage metadata")
        runtime = metadata["runtime"]
        runtime_payload = args.runtime_bin.read_bytes()
        if sha(runtime_payload) != runtime["payload_sha256"]:
            raise AcceptanceError("runtime payload input differs")
        runtime_address = integer(runtime["address"])
        start = rom_offset(runtime_address, len(runtime_payload), len(rom))
        if rom[start:start + len(runtime_payload)] != runtime_payload:
            raise AcceptanceError("runtime payload is not present at linked address")

        map_meta = metadata["map_scripts"]
        patches = map_meta.get("patches", [])
        if not patches:
            raise AcceptanceError("no map host patches in stage metadata")
        for patch in patches:
            pointer_site = integer(patch["pointer_patch_address"])
            script_address = integer(patch["script_after_address"])
            wrapper = integer(patch["wrapper_address"])
            if read_u32(rom, pointer_site) != script_address:
                raise AcceptanceError(f"host pointer differs: {patch['host_key']}")
            script = expected_script(wrapper)
            script_start = rom_offset(script_address, len(script), len(rom))
            if rom[script_start:script_start + len(script)] != script:
                raise AcceptanceError(f"host script bytes differ: {patch['host_key']}")
            if sha(script) != patch["script_sha256"]:
                raise AcceptanceError(f"host script metadata hash differs: {patch['host_key']}")

        # Re-run static content/reachability validation against the exact package.
        completed = subprocess.run(
            [sys.executable, str(package / "scripts/validate_acquisition_content.py"), "--package", str(package)],
            text=True, capture_output=True, check=False,
        )
        if completed.returncode:
            raise AcceptanceError((completed.stderr or completed.stdout).strip())

        emulator_status = "NOT_REQUESTED"
        emulator_cases = 0
        if args.emulator_command:
            completed = subprocess.run(args.emulator_command, text=True, capture_output=True, check=False)
            if completed.returncode:
                raise AcceptanceError(f"emulator command failed: {(completed.stderr or completed.stdout).strip()}")
            emulator_status = "COMMAND_PASS"
        if args.emulator_result:
            result = json.loads(args.emulator_result.read_text(encoding="utf-8"))
            observed = {row["case_key"]: row for row in result.get("cases", [])}
            required_cases = rows(package / "tests/exact_rom_acceptance_cases.csv")
            missing = [row["case_key"] for row in required_cases if row["case_key"] not in observed]
            failed = [key for key, row in observed.items() if row.get("status") != "PASS"]
            if missing or failed:
                raise AcceptanceError(f"emulator cases incomplete/failed: missing={missing[:10]} failed={failed[:10]}")
            emulator_status = "ALL_CASES_PASS"
            emulator_cases = len(required_cases)
        if args.require_emulator and emulator_status != "ALL_CASES_PASS":
            raise AcceptanceError("release acceptance requires complete emulator result JSON")

        report = {
            "schema_version": 1,
            "status": "PASS",
            "rom_sha256": sha(rom),
            "runtime_payload_sha256": sha(runtime_payload),
            "map_host_patch_count": len(patches),
            "static_content_validation": "PASS",
            "emulator_status": emulator_status,
            "emulator_case_count": emulator_cases,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, AcceptanceError) as error:
        print(f"exact-ROM acquisition acceptance failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
