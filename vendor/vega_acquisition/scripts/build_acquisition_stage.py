#!/usr/bin/env python3
"""Apply a linked acquisition runtime and exact host scripts to one pinned ROM stage."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

GBA_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024


class StageError(ValueError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise StageError(f"expected integer: {value!r}")


def allocation(contract: dict[str, Any], name: str) -> tuple[int, int, int]:
    matches: list[dict[str, Any]] = []
    value = contract.get("allocations")
    if isinstance(value, dict) and isinstance(value.get(name), dict):
        matches.append({"name": name, **value[name]})
    elif isinstance(value, list):
        matches += [row for row in value if isinstance(row, dict) and row.get("name", row.get("allocation_name")) == name]
    for key in ("regions", "rows", "entries"):
        value = contract.get(key)
        if isinstance(value, list):
            matches += [row for row in value if isinstance(row, dict) and row.get("name", row.get("allocation_name")) == name]
    if len(matches) != 1:
        raise StageError(f"allocation {name} absent or ambiguous")
    row = matches[0]
    if "fill_byte" not in row:
        raise StageError(f"allocation {name} lacks fill_byte")
    return integer(row.get("address", row.get("start"))), integer(row.get("size", row.get("capacity", row.get("length")))), integer(row["fill_byte"])


def metadata_sha(metadata: dict[str, Any]) -> str:
    for key in ("sha256", "output_sha256", "rom_sha256", "stage_sha256"):
        value = metadata.get(key)
        if isinstance(value, str) and len(value) == 64:
            return value.lower()
    raise StageError("stage metadata lacks SHA-256")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input-rom", type=Path, required=True)
    parser.add_argument("--stage-metadata", type=Path, required=True)
    parser.add_argument("--allocation-contract", type=Path, required=True)
    parser.add_argument("--runtime-bin", type=Path, required=True)
    parser.add_argument("--runtime-meta", type=Path, required=True)
    parser.add_argument("--runtime-symbols", type=Path, required=True)
    parser.add_argument("--output-rom", type=Path, required=True)
    parser.add_argument("--output-metadata", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    try:
        stage = json.loads(args.stage_metadata.read_text(encoding="utf-8"))
        contract = json.loads(args.allocation_contract.read_text(encoding="utf-8"))
        runtime_meta = json.loads(args.runtime_meta.read_text(encoding="utf-8"))
        rom = bytearray(args.input_rom.read_bytes())
        payload = args.runtime_bin.read_bytes()
        if len(rom) != ROM_SIZE:
            raise StageError(f"input stage must be 32 MiB, got {len(rom)}")
        if sha(rom) != metadata_sha(stage):
            raise StageError("input ROM SHA differs from stage metadata")
        if sha(payload) != runtime_meta.get("payload_sha256"):
            raise StageError("runtime payload SHA differs from runtime metadata")
        runtime_address, runtime_capacity, fill = allocation(contract, "acquisition_runtime")
        map_address, map_capacity, _ = allocation(contract, "acquisition_map_scripts")
        if max(runtime_address, map_address) < min(runtime_address + runtime_capacity, map_address + map_capacity):
            raise StageError("runtime and map-script allocations overlap")
        if integer(runtime_meta.get("address")) != runtime_address or len(payload) > runtime_capacity:
            raise StageError("runtime metadata/allocation mismatch")
        start = runtime_address - GBA_BASE
        if start < 0 or start + runtime_capacity > len(rom):
            raise StageError("runtime allocation outside ROM")
        if any(value != fill for value in rom[start:start + runtime_capacity]):
            raise StageError("runtime allocation does not match declared fill_byte")
        rom[start:start + len(payload)] = payload

        with tempfile.TemporaryDirectory() as temp_text:
            temp = Path(temp_text)
            interim_rom = temp / "runtime_injected.gba"
            interim_rom.write_bytes(rom)
            interim_meta = dict(stage)
            interim_meta["sha256"] = sha(rom)
            interim_meta["input_sha256"] = metadata_sha(stage)
            interim_meta["acquisition_runtime"] = runtime_meta
            interim_meta_path = temp / "runtime_injected.json"
            interim_meta_path.write_text(json.dumps(interim_meta, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            serializer_meta = temp / "map_scripts.json"
            command = [
                sys.executable, str(package / "scripts/serialize_acquisition_events.py"),
                "--rom", str(interim_rom), "--stage-metadata", str(interim_meta_path),
                "--runtime-symbols", str(args.runtime_symbols),
                "--allocation-contract", str(args.allocation_contract),
                "--patch-manifest", str(package / "generated/map_script_patch_manifest.json"),
                "--output-rom", str(args.output_rom),
                "--output-metadata", str(serializer_meta),
            ]
            completed = subprocess.run(command, text=True, capture_output=True, check=False)
            if completed.returncode:
                raise StageError((completed.stderr or completed.stdout).strip())
            map_meta = json.loads(serializer_meta.read_text(encoding="utf-8"))
        final = {
            "schema_version": 1,
            "task": "VEGA_ACQUISITION_STAGE",
            "status": "BUILT_REQUIRES_EXACT_ROM_ACCEPTANCE",
            "input_rom": str(args.input_rom), "input_sha256": metadata_sha(stage),
            "runtime": runtime_meta,
            "map_scripts": map_meta,
            "output_rom": str(args.output_rom),
            "output_sha256": hashlib.sha256(args.output_rom.read_bytes()).hexdigest(),
        }
        args.output_metadata.parent.mkdir(parents=True, exist_ok=True)
        args.output_metadata.write_text(json.dumps(final, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, StageError) as error:
        print(f"acquisition stage build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
