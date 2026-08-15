#!/usr/bin/env python3
"""Compile and link the data-driven acquisition runtime into a named allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REQUIRED_ADAPTER_SYMBOLS = {
    "VegaAcqEngine_AdapterProbe", "VegaAcqEngine_GetPending",
    "VegaAcqEngine_IsUnlockSatisfied", "VegaAcqEngine_IsEventConditionSatisfied",
    "VegaAcqEngine_IsSpeciesRegistered", "VegaAcqEngine_SetSpeciesRegistered",
    "VegaAcqEngine_GetClaimCount", "VegaAcqEngine_SetClaimCount",
    "VegaAcqEngine_Preflight", "VegaAcqEngine_StartCaptureBattle",
    "VegaAcqEngine_StageOperation", "VegaAcqEngine_RollbackOperation",
    "VegaAcqEngine_FinalizeOperation", "VegaAcqEngine_IsOperationDurable",
    "VegaAcqEngine_FinalizeInMemory",
    "VegaAcqEngine_PersistAll",
    "VegaAcqEngine_SelectHostEvent", "VegaAcqEngine_ShowResult",
}
REQUIRED_OUTPUT_SYMBOLS = {
    "VegaAcq_Probe", "VegaAcq_OpenHost", "VegaAcq_Begin",
    "VegaAcq_ResolveBattle", "VegaAcq_RecoverPending",
}


class BuildError(ValueError):
    pass


def run(command: list[str], label: str, cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise BuildError(f"{label} failed ({completed.returncode}): {detail}")
    return completed.stdout


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_int(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise BuildError(f"not an integer address/size: {value!r}")


def allocation(contract: dict[str, Any], name: str) -> tuple[int, int]:
    candidates: list[dict[str, Any]] = []
    value = contract.get("allocations")
    if isinstance(value, dict):
        row = value.get(name)
        if isinstance(row, dict):
            candidates.append({"name": name, **row})
    elif isinstance(value, list):
        candidates += [row for row in value if isinstance(row, dict) and row.get("name", row.get("allocation_name")) == name]
    # Accept the repository allocation report's common list keys without guessing an address.
    for key in ("regions", "rows", "entries"):
        rows = contract.get(key)
        if isinstance(rows, list):
            candidates += [row for row in rows if isinstance(row, dict) and row.get("name", row.get("allocation_name")) == name]
    if len(candidates) != 1:
        raise BuildError(f"named allocation {name!r} is absent or ambiguous")
    row = candidates[0]
    address = parse_int(row.get("address", row.get("start")))
    size = parse_int(row.get("size", row.get("capacity", row.get("length"))))
    if not (0x08000000 <= address < 0x0A000000) or size <= 0:
        raise BuildError(f"allocation outside 32 MiB GBA ROM: 0x{address:08X}+{size}")
    return address, size


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--allocation-contract", type=Path, required=True)
    parser.add_argument("--adapter-source", type=Path, required=True)
    parser.add_argument("--output-bin", type=Path, required=True)
    parser.add_argument("--output-symbols", type=Path, required=True)
    parser.add_argument("--output-meta", type=Path, required=True)
    parser.add_argument("--tool-prefix", default=os.environ.get("ARM_NONE_EABI_PREFIX", "arm-none-eabi-"))
    args = parser.parse_args()
    package = args.package.resolve()
    try:
        contract = json.loads(args.allocation_contract.read_text(encoding="utf-8"))
        address, capacity = allocation(contract, "acquisition_runtime")
        adapter = args.adapter_source.resolve()
        if adapter.name == "acquisition_engine_adapter_fail_closed.c" or "Deliberately unusable reference adapter" in adapter.read_text(encoding="utf-8"):
            raise BuildError("fail-closed adapter cannot be used for a release runtime")
        adapter_text = adapter.read_text(encoding="utf-8")
        missing_adapter = sorted(symbol for symbol in REQUIRED_ADAPTER_SYMBOLS if symbol not in adapter_text)
        if missing_adapter:
            raise BuildError(f"adapter source lacks required functions: {missing_adapter}")

        gcc = shutil.which(args.tool_prefix + "gcc")
        objcopy = shutil.which(args.tool_prefix + "objcopy")
        nm = shutil.which(args.tool_prefix + "nm")
        if not gcc or not objcopy or not nm:
            raise BuildError("ARM GNU toolchain not found; set ARM_NONE_EABI_PREFIX")

        sources = [
            package / "overlays/acquisition_runtime/acquisition_runtime.c",
            package / "overlays/acquisition_runtime/acquisition_save_migration.c",
            package / "generated/acquisition_event_defs.c",
            package / "generated/acquisition_collection_defs.c",
            package / "generated/acquisition_host_defs.c",
            package / "generated/acquisition_host_wrappers.c",
            adapter,
        ]
        for source in sources:
            if not source.is_file():
                raise BuildError(f"missing source {source}")

        with tempfile.TemporaryDirectory() as temp_text:
            temp = Path(temp_text)
            objects: list[Path] = []
            common = [
                "-mcpu=arm7tdmi", "-mthumb", "-mthumb-interwork", "-Os",
                "-ffreestanding", "-fno-builtin", "-fdata-sections", "-ffunction-sections",
                "-fno-common", "-Wall", "-Wextra", "-Werror", "-std=c11",
                "-I", str(package),
            ]
            for index, source in enumerate(sources):
                obj = temp / f"{index:02d}_{source.stem}.o"
                run([gcc, *common, "-c", str(source), "-o", str(obj)], f"compile {source.name}", package)
                objects.append(obj)
            linker = temp / "acquisition.ld"
            linker.write_text(f"""SECTIONS
{{
  . = 0x{address:08X};
  .text : {{ KEEP(*(.text.VegaAcq_Probe)) *(.text*) *(.rodata*) }}
  .data : {{ *(.data*) }}
  .bss (NOLOAD) : {{ *(.bss*) *(COMMON) }}
  /DISCARD/ : {{ *(.comment*) *(.ARM.attributes*) }}
}}
""", encoding="ascii")
            elf = temp / "acquisition.elf"
            run([gcc, "-mcpu=arm7tdmi", "-mthumb", "-mthumb-interwork", "-nostdlib",
                 "-Wl,--gc-sections", f"-Wl,-T,{linker}", *map(str, objects), "-o", str(elf)],
                "link acquisition runtime", package)
            args.output_bin.parent.mkdir(parents=True, exist_ok=True)
            run([objcopy, "-O", "binary", str(elf), str(args.output_bin)], "objcopy runtime", package)
            payload = args.output_bin.read_bytes()
            if not payload or len(payload) > capacity:
                raise BuildError(f"runtime payload {len(payload)} exceeds allocation {capacity}")
            symbols: dict[str, int] = {}
            for line in run([nm, "-n", str(elf)], "read symbols", package).splitlines():
                fields = line.split()
                if len(fields) == 3:
                    try:
                        symbols[fields[2]] = int(fields[0], 16)
                    except ValueError:
                        pass
            missing_output = sorted(REQUIRED_OUTPUT_SYMBOLS - set(symbols))
            wrapper_symbols = [key for key in symbols if key.startswith("VegaAcqHost_")]
            if missing_output or not wrapper_symbols:
                raise BuildError(f"linked runtime symbols incomplete: core={missing_output}, wrappers={len(wrapper_symbols)}")
            args.output_symbols.parent.mkdir(parents=True, exist_ok=True)
            args.output_symbols.write_text(json.dumps({"schema_version": 1, "allocation_name": "acquisition_runtime", "base_address": address, "symbols": symbols}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            meta = {
                "schema_version": 1,
                "status": "LINKED_REQUIRES_EXACT_ROM_ACCEPTANCE",
                "allocation_name": "acquisition_runtime",
                "address": address,
                "capacity": capacity,
                "payload_size": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "adapter_source": str(adapter),
                "adapter_sha256": sha(adapter),
                "wrapper_symbol_count": len(wrapper_symbols),
            }
            args.output_meta.parent.mkdir(parents=True, exist_ok=True)
            args.output_meta.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, BuildError, json.JSONDecodeError) as error:
        print(f"acquisition runtime build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
