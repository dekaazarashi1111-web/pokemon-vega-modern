#!/usr/bin/env python3
"""Stage 30へFactory Trial 100連勝色違い記念枠を実ROM接続する。"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from scripts import build_factory_reward_runtime as stage28_builder  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/30_factory_special_event_runtime.gba")
INPUT_META = Path("build/stages/30_factory_special_event_runtime.json")
INPUT_ALLOC = Path("build/stages/30_allocation.json")
STAGE26_META = Path("build/stages/26_acquisition_events.json")
ACQUISITION_SYMBOLS = Path("generated/runtime/acquisition_events_symbols.json")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
OUTPUT_ROM = Path("build/stages/31_factory_shiny_memorial_runtime.gba")
OUTPUT_META = Path("build/stages/31_factory_shiny_memorial_runtime.json")
OUTPUT_ALLOC = Path("build/stages/31_allocation.json")
RUNTIME_BIN = Path("generated/runtime/factory_shiny_memorial_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/factory_shiny_memorial_runtime_symbols.json")
CATALOG_HEADER = Path("generated/runtime/factory_shiny_memorial_catalog_generated.h")
CATALOG_JSON = Path("generated/runtime/factory_shiny_memorial_catalog.json")
MGBA_FIXTURE = Path("build/stages/31_mgba_factory_shiny_memorial_smoke.json")
REPORT = Path("reports/generated/factory_shiny_memorial_runtime.md")
PATCH_INCREMENTAL = Path(
    "build/patches/factory-special-event-stage30-to-factory-shiny-memorial-stage31.bps"
)
PATCH_CUMULATIVE = Path(
    "build/patches/vega-modern-kanto-v1.4.0-to-factory-shiny-memorial-stage31.bps"
)
RUNNER = Path("tools/mgba_factory_shiny_memorial_smoke.c")

EXPECTED_INPUT_SHA256 = "e605841d83c6f8e9acd7dbd58b5b4f3d7b262d0274c4c5b4369f0728dc25bf38"
EXPECTED_BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "factory_shiny_memorial_runtime_payload"
MANIFEST_KEY = "FACILITY_REWARD_KEY_STREAK_100"
EXPECTED_THRESHOLD = 100
EXPECTED_CLAIM_BIT = 9
EXPECTED_CLAIM_MASK = 1 << EXPECTED_CLAIM_BIT
EXPECTED_POOL_COUNT = 137
EXPECTED_RECOVERY_BYTES = bytes.fromhex("f0b587b000f0a0ff")
RECOVERY_PATCH_SIZE = 8
REQUIRED_ENTRYPOINTS = {
    "FactoryShinyMemorialRuntime_Probe",
    "FactoryShinyMemorialRuntime_Complete",
    "FactoryShinyMemorialRuntime_ClaimPending",
    "FactoryShinyMemorialRuntime_RecoverDispatch",
}
ACQ_REQUIRED_SYMBOLS = {
    "VegaAcq_RecoverPending",
    "VegaAcqEngine_GetPending",
    "VegaAcqEngine_IsSpeciesRegistered",
    "VegaAcqEngine_SetSpeciesRegistered",
    "VegaAcqEngine_FinalizeInMemory",
}
LINKED_REQUIRED = {
    "CreateCompressedMonFromBoxMon",
    "GetBoxMonDataAt",
    "GetCompressedMonPtr",
    "GiveMonToPlayer",
    "ZeroBoxMonAt",
}


class FactoryShinyMemorialBuildError(ValueError):
    """入力、manifest、取得台帳ABI、配置、または受入条件の違反。"""


def _fail(message: str) -> NoReturn:
    raise FactoryShinyMemorialBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return stage28_builder._sha(raw)


def _stable(value: object) -> bytes:
    return stage28_builder._stable(value)


def _rows(path: Path) -> list[dict[str, str]]:
    return stage28_builder._rows(path)


def _read_json(path: Path) -> dict[str, Any]:
    return stage28_builder._read_json(path)


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    return stage28_builder._run(command, label, cwd=cwd)


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    return stage28_builder._u32(raw, offset, label)


def _rom_offset(address: int, size: int, label: str) -> int:
    return stage28_builder._rom_offset(address, size, label)


def _thumb(address: int, label: str) -> int:
    if not GBA_ROM_BASE <= address < GBA_ROM_BASE + ROM_SIZE:
        _fail(f"{label} is outside ROM: 0x{address:08X}")
    return address | 1


def _input_contract(
    root: Path,
) -> tuple[
    bytes, bytes, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, int]
]:
    stage = (root / INPUT_ROM).read_bytes()
    base = (root / BASE_ROM).read_bytes()
    stage30_meta = _read_json(root / INPUT_META)
    previous_alloc = _read_json(root / INPUT_ALLOC)
    stage26_meta = _read_json(root / STAGE26_META)
    acquisition = _read_json(root / ACQUISITION_SYMBOLS)
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_INPUT_SHA256:
        _fail("stage30 input size or hash differs")
    if len(base) != ROM_SIZE or _sha(base) != EXPECTED_BASE_SHA256:
        _fail("v1.4.0 base size or hash differs")
    if stage30_meta.get("task") != "USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME":
        _fail("stage30 metadata task differs")
    if stage30_meta.get("output", {}).get("sha256") != EXPECTED_INPUT_SHA256:
        _fail("stage30 metadata output hash differs")
    if previous_alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage30 allocator overlap contract failed")

    stage30_complete = int(stage30_meta.get("entrypoints", {}).get(
        "FactorySpecialEventRuntime_Complete", 0,
    ))
    script = int(stage30_meta.get("completion_chain", {}).get("script", 0))
    script_offset = _rom_offset(script, 6, "Factory completion script")
    if stage[script_offset] != 0x23:
        _fail("Factory completion script no longer starts with callnative")
    if _u32(stage, script_offset + 1, "Stage30 completion pointer") != stage30_complete:
        _fail("Factory completion script no longer targets Stage30 wrapper")

    raw_symbols = acquisition.get("symbols", {})
    if not isinstance(raw_symbols, dict) or not ACQ_REQUIRED_SYMBOLS <= set(raw_symbols):
        _fail("acquisition symbol contract is incomplete")
    symbols = {name: int(raw_symbols[name]) for name in ACQ_REQUIRED_SYMBOLS}
    recovery = symbols["VegaAcq_RecoverPending"]
    recovery_offset = _rom_offset(recovery, RECOVERY_PATCH_SIZE, "VegaAcq_RecoverPending")
    if stage[recovery_offset:recovery_offset + RECOVERY_PATCH_SIZE] != EXPECTED_RECOVERY_BYTES:
        _fail("VegaAcq_RecoverPending entry bytes differ")
    if symbols["VegaAcqEngine_GetPending"] != recovery + 0xF48:
        _fail("acquisition recover/GetPending relative ABI differs")

    linked = stage26_meta.get("runtime", {}).get("linked_abi", {})
    if not isinstance(linked, dict) or not LINKED_REQUIRED <= set(linked):
        _fail("stage26 linked mon-storage ABI is incomplete")
    for name in LINKED_REQUIRED:
        _thumb(int(linked[name]), f"linked ABI {name}")
    for name, address in symbols.items():
        _thumb(address, f"acquisition symbol {name}")
    return stage, base, stage30_meta, previous_alloc, stage26_meta, symbols


def _claim_bit_from_manifest(rows: list[dict[str, str]], target_key: str) -> int:
    claim_rows = [
        row for row in rows
        if row.get("status") == "ACTIVE"
        and row.get("repeatability") == "ONCE"
        and row.get("claim_key") not in (None, "", "NONE")
        and row.get("trigger_kind") in {
            "TRIAL_FIRST", "STREAK", "SPECIAL_EVENT", "SHINY_MEMORIAL"
        }
    ]
    keys = [row.get("facility_reward_key", "") for row in claim_rows]
    claims = [row.get("claim_key", "") for row in claim_rows]
    if len(keys) != len(set(keys)) or len(claims) != len(set(claims)):
        _fail("Factory one-time claim rows are not unique")
    try:
        return keys.index(target_key) + 1  # bit 0 belongs to the base Facility claim.
    except ValueError:
        _fail("100-streak manifest row is absent from one-time claim ordering")


def _format_u16(values: list[int]) -> str:
    lines = []
    for start in range(0, len(values), 12):
        lines.append("    " + ", ".join(f"{value}u" for value in values[start:start + 12]))
    return ",\n".join(lines)


def _catalog_outputs(root: Path) -> tuple[dict[str, Any], bytes, bytes]:
    reward_rows = _rows(root / "manifests/facility_rewards.csv")
    selected = [
        row for row in reward_rows
        if row.get("facility_reward_key") == MANIFEST_KEY
    ]
    if len(selected) != 1:
        _fail("Factory 100-streak memorial manifest row is not unique")
    row = selected[0]
    try:
        streak = int(row.get("streak") or "0", 0)
        amount = int(row.get("amount") or "0", 0)
        quantity = int(row.get("quantity") or "0", 0)
    except ValueError as error:
        _fail(f"Factory 100-streak numeric field differs: {error}")
    claim_bit = _claim_bit_from_manifest(reward_rows, MANIFEST_KEY)
    if (
        row.get("status") != "ACTIVE"
        or row.get("trigger_kind") != "SHINY_MEMORIAL"
        or streak != EXPECTED_THRESHOLD
        or row.get("currency_key") != "NONE"
        or amount != 0
        or row.get("item_key") != "ITEM_KEY_NONE"
        or quantity != 0
        or row.get("unlock_key") != "FACTORY_MASTER"
        or row.get("repeatability") != "ONCE"
        or row.get("claim_key") != "CLAIM_KEY_STREAK_100_SHINY"
        or claim_bit != EXPECTED_CLAIM_BIT
    ):
        _fail("Factory 100-streak memorial semantics differ")

    registry_rows = _rows(
        root / "vendor/vega_acquisition/content/collectible_species_registry.csv"
    )
    special_rows = _rows(
        root / "vendor/vega_acquisition/content/special_event_catalog_125.csv"
    )
    try:
        excluded = {int(special["canonical_id"], 0) for special in special_rows}
    except (KeyError, ValueError) as error:
        _fail(f"special-event exclusion catalog differs: {error}")
    collection_source = (
        root / "vendor/vega_acquisition/generated/acquisition_collection_defs.c"
    ).read_text(encoding="ascii")
    collection_values = [
        tuple(int(value) for value in match)
        for match in re.findall(
            r"\{(\d+)u, (\d+)u, (\d+)u, (\d+)u, (\d+)u, (\d+)u\}",
            collection_source,
        )
    ]
    if len(collection_values) != len(registry_rows):
        _fail("acquisition collection definition count differs")

    pool: list[dict[str, Any]] = []
    for species_row in registry_rows:
        try:
            national = int(species_row.get("national_no") or "0", 0)
            canonical = int(species_row.get("canonical_id") or "0", 0)
            internal = int(species_row.get("vega_internal_id") or "0", 0)
        except ValueError:
            continue
        if not (
            species_row.get("base_or_form") == "BASE"
            and species_row.get("target_status") == "REQUIRED_BASE"
            and species_row.get("completion_weight") == "1"
            and species_row.get("route_required") == "yes"
            and species_row.get("is_official") == "true"
            and 1 <= national <= 386
            and canonical > 0
            and canonical == internal
            and canonical not in excluded
        ):
            continue
        definition = collection_values[canonical]
        if definition[0] != canonical or definition[1] == 0xFFFF:
            _fail(f"collection ledger mapping differs for species {canonical}")
        pool.append({
            "species_id": internal,
            "canonical_id": canonical,
            "national_no": national,
            "ledger_bit_index": definition[1],
            "species_key": species_row["species_key"],
            "display_name": species_row["display_name"],
        })
    species_ids = [int(entry["species_id"]) for entry in pool]
    national_ids = [int(entry["national_no"]) for entry in pool]
    ledger_bits = [int(entry["ledger_bit_index"]) for entry in pool]
    if (
        len(pool) != EXPECTED_POOL_COUNT
        or len(species_ids) != len(set(species_ids))
        or len(national_ids) != len(set(national_ids))
        or len(ledger_bits) != len(set(ledger_bits))
        or any(entry["canonical_id"] in excluded for entry in pool)
    ):
        _fail("nonlegendary shiny memorial pool contract differs")

    header = f"""#ifndef VEGA_FACTORY_SHINY_MEMORIAL_CATALOG_GENERATED_H
#define VEGA_FACTORY_SHINY_MEMORIAL_CATALOG_GENERATED_H

#include <stdint.h>

#define FACTORY_SHINY_MEMORIAL_STREAK_THRESHOLD {streak}u
#define FACTORY_SHINY_MEMORIAL_CLAIM_BIT {claim_bit}u
#define FACTORY_SHINY_MEMORIAL_CLAIM_MASK 0x{1 << claim_bit:08X}u
#define FACTORY_SHINY_MEMORIAL_POOL_COUNT {len(pool)}u

static const uint16_t gFactoryShinyMemorialSpecies[FACTORY_SHINY_MEMORIAL_POOL_COUNT] = {{
{_format_u16(species_ids)}
}};

static const uint16_t gFactoryShinyMemorialNational[FACTORY_SHINY_MEMORIAL_POOL_COUNT] = {{
{_format_u16(national_ids)}
}};

static const uint16_t gFactoryShinyMemorialLedgerBits[FACTORY_SHINY_MEMORIAL_POOL_COUNT] = {{
{_format_u16(ledger_bits)}
}};

#endif /* VEGA_FACTORY_SHINY_MEMORIAL_CATALOG_GENERATED_H */
""".encode("ascii")
    reward = {
        "facility_reward_key": MANIFEST_KEY,
        "trigger_kind": row["trigger_kind"],
        "streak": streak,
        "unlock_key": row["unlock_key"],
        "unlock_signal": "VegaModernSaveData.league_ii_cleared",
        "repeatability": row["repeatability"],
        "claim_key": row["claim_key"],
        "claim_bit": claim_bit,
        "claim_mask": 1 << claim_bit,
    }
    catalog = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "source": [
            "manifests/facility_rewards.csv",
            "vendor/vega_acquisition/content/collectible_species_registry.csv",
            "vendor/vega_acquisition/content/special_event_catalog_125.csv",
        ],
        "selected_keys": [MANIFEST_KEY],
        "reward": reward,
        "pool": {
            "count": len(pool),
            "filters": {
                "base_or_form": "BASE",
                "target_status": "REQUIRED_BASE",
                "route_required": "yes",
                "completion_weight": 1,
                "official_national_range": [1, 386],
                "exclude_special_event_catalog_125": True,
                "canonical_equals_vega_internal": True,
            },
            "species_sha256": _sha(struct.pack(f"<{len(species_ids)}H", *species_ids)),
            "ledger_bits_sha256": _sha(struct.pack(f"<{len(ledger_bits)}H", *ledger_bits)),
            "entries": pool,
        },
        "header_sha256": _sha(header),
    }
    return catalog, header, _stable(catalog)


def _compile_runtime(
    root: Path,
    load_address: int,
    generated_header: bytes,
    stage30_meta: dict[str, Any],
    stage26_meta: dict[str, Any],
    acq_symbols: dict[str, int],
) -> tuple[bytes, dict[str, int]]:
    compiler = stage28_builder._arm_tool(root, "arm-none-eabi-gcc")
    objcopy = stage28_builder._arm_tool(root, "arm-none-eabi-objcopy")
    nm = stage28_builder._arm_tool(root, "arm-none-eabi-nm")
    source = root / "overlays/factory_shiny_memorial_runtime/factory_shiny_memorial_runtime.c"
    if not source.is_file():
        _fail(f"Factory shiny memorial source missing: {source}")
    stage30_complete = int(
        stage30_meta["entrypoints"]["FactorySpecialEventRuntime_Complete"]
    )
    linked = stage26_meta["runtime"]["linked_abi"]
    recovery = int(acq_symbols["VegaAcq_RecoverPending"])
    get_pending = int(acq_symbols["VegaAcqEngine_GetPending"])
    definitions = {
        "VEGA_STAGE30_COMPLETE_ADDRESS": _thumb(stage30_complete, "Stage30 complete"),
        "VEGA_ACQ_GET_PENDING_ADDRESS": _thumb(get_pending, "GetPending"),
        "VEGA_ACQ_GET_PENDING_THUMB_LITERAL": _thumb(get_pending, "GetPending literal"),
        "VEGA_ACQ_RECOVER_CONTINUATION_THUMB_LITERAL": _thumb(
            recovery + RECOVERY_PATCH_SIZE, "recover continuation"
        ),
        "VEGA_ACQ_IS_SPECIES_REGISTERED_ADDRESS": _thumb(
            int(acq_symbols["VegaAcqEngine_IsSpeciesRegistered"]),
            "IsSpeciesRegistered",
        ),
        "VEGA_ACQ_SET_SPECIES_REGISTERED_ADDRESS": _thumb(
            int(acq_symbols["VegaAcqEngine_SetSpeciesRegistered"]),
            "SetSpeciesRegistered",
        ),
        "VEGA_ACQ_FINALIZE_IN_MEMORY_ADDRESS": _thumb(
            int(acq_symbols["VegaAcqEngine_FinalizeInMemory"]),
            "FinalizeInMemory",
        ),
        "VEGA_ACQ_GIVE_MON_ADDRESS": _thumb(int(linked["GiveMonToPlayer"]), "GiveMon"),
        "VEGA_ACQ_GET_BOX_MON_DATA_ADDRESS": _thumb(
            int(linked["GetBoxMonDataAt"]), "GetBoxMonDataAt"
        ),
        "VEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS": _thumb(
            int(linked["ZeroBoxMonAt"]), "ZeroBoxMonAt"
        ),
    }
    with tempfile.TemporaryDirectory(prefix="vega-factory-shiny-memorial-") as temporary:
        directory = Path(temporary)
        (directory / "factory_shiny_memorial_catalog_generated.h").write_bytes(
            generated_header
        )
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common",
            *(f"-D{name}=0x{value:08X}" for name, value in definitions.items()),
            f"-I{directory}", f"-I{root}",
            f"-I{root / 'overlays/factory_shiny_memorial_runtime'}",
            f"-I{root / 'overlays/save_migration'}",
        ]
        obj = directory / "factory_shiny_memorial_runtime.o"
        _run([*common, "-c", str(source), "-o", str(obj)],
             "compile Factory shiny memorial")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.FactoryShinyMemorialRuntime_*))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n",
            encoding="ascii",
        )
        elf = directory / "factory_shiny_memorial.elf"
        binary = directory / "factory_shiny_memorial.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,FactoryShinyMemorialRuntime_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Factory shiny memorial")
        undefined = _run([nm, "-u", str(elf)],
                         "Factory shiny memorial undefined-symbol audit")
        if undefined:
            _fail("Factory shiny memorial has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "Factory shiny memorial objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)],
                         "Factory shiny memorial nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing:
            _fail(f"Factory shiny memorial exports differ: missing={missing}")
        code = binary.read_bytes()
        if not code or len(code) > 32 * 1024:
            _fail(f"unexpected Factory shiny memorial size: {len(code)}")
        for name in REQUIRED_ENTRYPOINTS:
            address = symbols[name]
            if address & 1 or not load_address <= address < load_address + len(code):
                _fail(f"Factory shiny memorial symbol outside/alignment: {name}=0x{address:08X}")
        return code, symbols


def _build_payload(
    root: Path,
    generated_header: bytes,
    payload_offset: int,
    stage30_meta: dict[str, Any],
    stage26_meta: dict[str, Any],
    acq_symbols: dict[str, int],
    catalog: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    code_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols = _compile_runtime(
        root, code_address, generated_header, stage30_meta, stage26_meta,
        acq_symbols,
    )
    payload = bytearray(PAYLOAD_HEADER_SIZE + len(code))
    payload[PAYLOAD_HEADER_SIZE:] = code
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    stage30_complete = int(
        stage30_meta["entrypoints"]["FactorySpecialEventRuntime_Complete"]
    )
    recovery = int(acq_symbols["VegaAcq_RecoverPending"])
    values = [
        1,
        len(payload),
        len(code),
        int(catalog["reward"]["streak"]),
        int(catalog["reward"]["claim_bit"]),
        int(catalog["reward"]["claim_mask"]),
        int(catalog["pool"]["count"]),
        stage30_complete,
        entrypoints["FactoryShinyMemorialRuntime_Probe"],
        entrypoints["FactoryShinyMemorialRuntime_Complete"],
        entrypoints["FactoryShinyMemorialRuntime_ClaimPending"],
        entrypoints["FactoryShinyMemorialRuntime_RecoverDispatch"],
        recovery,
        (recovery + RECOVERY_PATCH_SIZE) | 1,
        int(acq_symbols["VegaAcqEngine_GetPending"]) | 1,
        0,
    ]
    struct.pack_into("<8s16I", payload, 0, b"VEGASM31", *values)
    return bytes(payload), {
        "payload": {
            "magic": "VEGASM31",
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload),
            "sha256": _sha(payload),
            "header_size": PAYLOAD_HEADER_SIZE,
            "code_offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "code_address": code_address,
            "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": entrypoints,
        "symbols": {
            f"native::{name}": symbols[name]
            for name in sorted(symbols)
            if code_address <= symbols[name] < code_address + len(code)
        },
    }


def _allocation(
    root: Path,
    previous: dict[str, Any],
    size: int,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = stage28_builder._previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "Factory Trial 100-streak shiny memorial transaction runtime",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage31 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Factory shiny memorial allocation is not unique")
    return matches[0], report


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage, base, stage30_meta, previous_alloc, stage26_meta, acq_symbols = (
        _input_contract(root)
    )
    catalog, generated_header, catalog_json = _catalog_outputs(root)
    script_address = int(stage30_meta["completion_chain"]["script"])
    script_offset = _rom_offset(script_address, 6, "Factory completion script")
    old_complete = int(
        stage30_meta["entrypoints"]["FactorySpecialEventRuntime_Complete"]
    )
    recovery_address = int(acq_symbols["VegaAcq_RecoverPending"])
    recovery_offset = _rom_offset(
        recovery_address, RECOVERY_PATCH_SIZE, "VegaAcq_RecoverPending"
    )

    preliminary, _ = _build_payload(
        root, generated_header, 0, stage30_meta, stage26_meta, acq_symbols,
        catalog,
    )
    allocation, _ = _allocation(root, previous_alloc, len(preliminary), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime = _build_payload(
        root, generated_header, payload_offset, stage30_meta, stage26_meta,
        acq_symbols, catalog,
    )
    if len(payload) != len(preliminary):
        _fail("address-dependent Factory shiny memorial payload size changed")
    allocation, allocation_report = _allocation(
        root, previous_alloc, len(payload), _sha(payload),
    )
    if int(allocation["start"]) != payload_offset:
        _fail("Factory shiny memorial allocation changed after final link")
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Factory shiny memorial destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    pointer_site = script_offset + 1
    if _u32(output, pointer_site, "Stage30 completion pointer") != old_complete:
        _fail("Stage30 completion pointer differs before Stage31 patch")
    replacement = int(runtime["entrypoints"]["FactoryShinyMemorialRuntime_Complete"])
    struct.pack_into("<I", output, pointer_site, replacement)

    dispatch = int(runtime["entrypoints"]["FactoryShinyMemorialRuntime_RecoverDispatch"])
    recovery_jump = struct.pack("<HHI", 0x4B00, 0x4718, dispatch)
    if output[recovery_offset:recovery_offset + RECOVERY_PATCH_SIZE] != EXPECTED_RECOVERY_BYTES:
        _fail("recovery entry changed before Stage31 patch")
    output[recovery_offset:recovery_offset + RECOVERY_PATCH_SIZE] = recovery_jump

    patches = [
        {
            "label": "Factory Trial completion Stage31 shiny memorial wrapper",
            "script_address": script_address,
            "site_address": GBA_ROM_BASE + pointer_site,
            "site_offset": pointer_site,
            "opcode": 0x23,
            "expected_pointer": old_complete,
            "replacement_pointer": replacement,
        },
        {
            "label": "acquisition pending recovery Stage31 dispatch",
            "site_address": recovery_address,
            "site_offset": recovery_offset,
            "expected_bytes": EXPECTED_RECOVERY_BYTES.hex(),
            "replacement_bytes": recovery_jump.hex(),
            "replacement_pointer": dispatch,
            "continuation": (recovery_address + RECOVERY_PATCH_SIZE) | 1,
        },
    ]

    allowed = [
        (payload_offset, payload_end),
        (pointer_site, pointer_site + 4),
        (recovery_offset, recovery_offset + RECOVERY_PATCH_SIZE),
    ]
    changed = [
        index for index, (before, after) in enumerate(zip(stage, output))
        if before != after
    ]
    outside = [
        index for index in changed
        if not any(start <= index < end for start, end in allowed)
    ]
    if outside:
        _fail(f"stage31 changed bytes outside declared spans: {outside[:8]}")

    output_raw = bytes(output)
    incremental = stage28_builder._sparse_bps(stage, output_raw)
    cumulative = stage28_builder._sparse_bps(base, output_raw)
    if apply_bps(stage, incremental) != output_raw:
        _fail("stage30 to stage31 BPS round-trip differs")
    if apply_bps(base, cumulative) != output_raw:
        _fail("v1.4.0 to stage31 cumulative BPS round-trip differs")

    ram = stage28_builder._ram_audit(root)
    reward = catalog["reward"]
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {
            "path": INPUT_ROM.as_posix(),
            "size": len(stage),
            "sha256": _sha(stage),
            "upstream_task": stage30_meta.get("task"),
        },
        "base_release": {
            "path": BASE_ROM.as_posix(),
            "size": len(base),
            "sha256": _sha(base),
        },
        "output": {
            "path": OUTPUT_ROM.as_posix(),
            "size": len(output_raw),
            "sha256": _sha(output_raw),
        },
        **runtime,
        "catalog": {
            "path": CATALOG_JSON.as_posix(),
            "header_path": CATALOG_HEADER.as_posix(),
            "selected_row_count": 1,
            "reward": reward,
            "pool_count": catalog["pool"]["count"],
            "pool_species_sha256": catalog["pool"]["species_sha256"],
        },
        "patches": patches,
        "completion_chain": {
            "script": script_address,
            "stage30_complete": old_complete,
            "stage31_complete": replacement,
            "order": [
                "FactorySpecialEventRuntime_Complete",
                "recover custom acquisition journal if present",
                "on result 9: gate Factory Master + Trial streak 100 + claim bit 9",
                "deliver one marked nonlegendary shiny to party or PC",
                "commit Pokedex + acquisition collection + Factory claim",
            ],
            "base_result_preserved": 9,
        },
        "recovery_hook": {
            "original_entry": recovery_address,
            "expected_bytes": EXPECTED_RECOVERY_BYTES.hex(),
            "dispatch": dispatch,
            "continuation": (recovery_address + RECOVERY_PATCH_SIZE) | 1,
            "normal_pending_behavior": "trampoline reproduces overwritten prologue then resumes original +8 body",
            "custom_discriminator": {
                "magic": "VEGA_ACQ_PENDING_MAGIC",
                "event_index_high_bit": True,
                "mode": 0xF1,
                "reserved": [0x53, 0x31],
            },
        },
        "transaction": {
            "pool_selection": "Random multiply-high over generated 137-entry pool",
            "shiny": "personality XOR is zero against player trainer ID",
            "idempotency_marker": "personality high byte D3, low byte pool index; party/PC scan repairs a missing sector31 journal",
            "write_ahead": [
                "PREPARED pending -> sector31",
                "create and deliver marker shiny",
                "STAGED token -> sector31",
                "normal save -> STAGED sector31 rewrite",
                "Pokedex + collection + claim bit 9 + transaction increment",
                "normal save -> sector31 commit",
            ],
            "capacity_failure": "no pending, mon, claim, Pokedex, or collection mutation",
            "persistence_failure": "claim remains clear; STAGED journal and/or marker mon provides retry proof",
            "destination_tokens": {
                "party": "0x10000000 | slot",
                "box": "0x20000000 | box<<8 | position",
            },
        },
        "linked_abi": {
            name: int(value)
            for name, value in stage26_meta["runtime"]["linked_abi"].items()
            if name in LINKED_REQUIRED
        },
        "acquisition_symbols": {
            name: int(value) for name, value in sorted(acq_symbols.items())
        },
        "ram_audit": ram,
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(),
            "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patches": {
            "incremental": {
                "path": PATCH_INCREMENTAL.as_posix(),
                "source_sha256": _sha(stage),
                "target_sha256": _sha(output_raw),
                "size": len(incremental),
                "sha256": _sha(incremental),
                "exact": True,
            },
            "cumulative": {
                "path": PATCH_CUMULATIVE.as_posix(),
                "source_sha256": _sha(base),
                "target_sha256": _sha(output_raw),
                "size": len(cumulative),
                "sha256": _sha(cumulative),
                "exact": True,
            },
        },
        "change_audit": {
            "changed_byte_count": len(changed),
            "declared_spans": [
                {"kind": "payload", "start": payload_offset, "end_exclusive": payload_end},
                {"kind": "callnative pointer", "start": pointer_site, "end_exclusive": pointer_site + 4},
                {"kind": "recovery dispatch", "start": recovery_offset, "end_exclusive": recovery_offset + RECOVERY_PATCH_SIZE},
            ],
            "outside_declared_span_count": len(outside),
        },
        "invariants": {
            "manifest_selected_row_1": catalog["selected_keys"] == [MANIFEST_KEY],
            "shiny_memorial_threshold_100": reward["streak"] == EXPECTED_THRESHOLD,
            "factory_master_gate": reward["unlock_key"] == "FACTORY_MASTER",
            "claim_key_bit_9": reward["claim_bit"] == EXPECTED_CLAIM_BIT,
            "pool_count_137": catalog["pool"]["count"] == EXPECTED_POOL_COUNT,
            "special_catalog_excluded": all(
                entry["canonical_id"] not in {
                    int(row["canonical_id"], 0)
                    for row in _rows(root / "vendor/vega_acquisition/content/special_event_catalog_125.csv")
                }
                for entry in catalog["pool"]["entries"]
            ),
            "completion_wrapper_physically_bound": _u32(
                output_raw, pointer_site, "Stage31 wrapper pointer",
            ) == replacement,
            "recovery_dispatch_physically_bound": output_raw[
                recovery_offset:recovery_offset + RECOVERY_PATCH_SIZE
            ] == recovery_jump,
            "stage30_complete_called_first": True,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "ram_overlap_zero": ram["overlap_count"] == 0,
            "declared_changes_only": not outside,
            "incremental_bps_exact": True,
            "cumulative_bps_exact": True,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("Factory shiny memorial runtime invariant failed")
    symbols_doc = {
        "schema_version": 1,
        "task": TASK,
        "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"],
        "symbols": runtime["symbols"],
        "completion_chain": metadata["completion_chain"],
        "recovery_hook": metadata["recovery_hook"],
        "catalog": metadata["catalog"],
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbols_doc),
        CATALOG_HEADER.as_posix(): generated_header,
        CATALOG_JSON.as_posix(): catalog_json,
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CUMULATIVE.as_posix(): cumulative,
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    runner = root / RUNNER
    if not runner.is_file():
        _fail(f"Factory shiny memorial mGBA runner missing: {runner}")
    with tempfile.TemporaryDirectory(prefix="vega-factory-shiny-memorial-smoke-") as temporary:
        temp = Path(temporary)
        executable = temp / "mgba-factory-shiny-memorial-smoke"
        _run([
            stage28_builder._host_cc(root), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(RUNNER), "-o", str(executable), "-lmgba",
        ], "Factory shiny memorial libmGBA smoke compile", cwd=root)
        entry = metadata["entrypoints"]
        linked = metadata["linked_abi"]
        acq = metadata["acquisition_symbols"]
        common_args = [
            hex(entry["FactoryShinyMemorialRuntime_Probe"]),
            hex(entry["FactoryShinyMemorialRuntime_Complete"]),
            hex(entry["FactoryShinyMemorialRuntime_ClaimPending"]),
            hex(entry["FactoryShinyMemorialRuntime_RecoverDispatch"]),
            hex(acq["VegaAcqEngine_FinalizeInMemory"] | 1),
            hex(acq["VegaAcqEngine_GetPending"] | 1),
            hex(linked["GiveMonToPlayer"] | 1),
            hex(linked["GetBoxMonDataAt"] | 1),
            hex(linked["GetCompressedMonPtr"] | 1),
            hex(linked["CreateCompressedMonFromBoxMon"] | 1),
            hex(linked["ZeroBoxMonAt"] | 1),
            hex(acq["VegaAcqEngine_IsSpeciesRegistered"] | 1),
            hex(metadata["symbols"]["native::gFactoryShinyMemorialSpecies"]),
            hex(metadata["symbols"]["native::gFactoryShinyMemorialNational"]),
            hex(metadata["symbols"]["native::gFactoryShinyMemorialLedgerBits"]),
            hex(metadata["completion_chain"]["script"]),
            hex(metadata["completion_chain"]["stage30_complete"]),
            hex(metadata["recovery_hook"]["original_entry"]),
            str(metadata["catalog"]["pool_count"]),
        ]
        processes: list[tuple[subprocess.Popen[str], Path, Path]] = []
        for index in (1, 2):
            rom = temp / f"31_factory_shiny_memorial_run{index}.gba"
            save = temp / f"31_factory_shiny_memorial_run{index}.sav"
            rom.write_bytes(stage)
            process = subprocess.Popen(
                [str(executable), str(rom), str(save), *common_args],
                cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            processes.append((process, rom, save))
            if index == 1:
                time.sleep(1.0)
        payloads: list[str] = []
        for index, (process, _rom, _save) in enumerate(processes, start=1):
            try:
                stdout, stderr = process.communicate(timeout=180)
            except subprocess.TimeoutExpired as error:
                for pending, _, _ in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending, _, _ in processes:
                    pending.communicate()
                detail = ((error.stderr or error.stdout) or "").strip()
                _fail(f"Factory shiny memorial exact-ROM run {index} timed out: {detail}")
            if process.returncode:
                for pending, _, _ in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending, _, _ in processes:
                    if pending is not process:
                        pending.communicate()
                detail = (stderr or stdout).strip()
                _fail(
                    f"Factory shiny memorial exact-ROM run {index} failed "
                    f"({process.returncode}): {detail}"
                )
            payloads.append(stdout.strip())
        first, second = (json.loads(payload) for payload in payloads)
        if first != second or first.get("status") != "PASS":
            _fail("Factory shiny memorial exact-ROM smoke is not deterministic PASS")
        first["process_runs"] = 2
        first["rom_sha256"] = _sha(stage)
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    checks = mgba["checks"]
    reward = metadata["catalog"]["reward"]
    text = f"""# Factory Trial 100-streak shiny memorial runtime / Stage 31

## 結論

- Stage 30の完了wrapperを先に呼び、ACTIVE `{reward['facility_reward_key']}`をFactory Master、Trial streak {reward['streak']}以上、claim bit {reward['claim_bit']}未設定へ接続した。
- 非伝説・非幻等をspecial catalog 125から除外した旧図鑑安全範囲の{metadata['catalog']['pool_count']}種poolから、Lv50の色違い1体をparty優先、満杯時PCへ配布する。
- 取得pending slotをPREPARED/STAGED write-ahead journalとして再利用し、Pokedex、取得台帳、Factory claimを通常save＋sector 31でcommitする。
- 色違いpersonalityにもpool index markerを持たせ、sector 31が通常save後に失われてもparty/PC scanで既配布を検出して二重配布を防ぐ。
- 容量不足、sector書込失敗、通常save失敗ではclaim bit 9を消費せず、後続受取を維持する。

## ROM結合

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Payload: `{metadata['payload']['address']:#010x}` / {metadata['payload']['size']} bytes
- Completion script: `{metadata['completion_chain']['script']:#010x}`
- Stage 30 complete: `{metadata['completion_chain']['stage30_complete']:#010x}`
- Stage 31 complete: `{metadata['completion_chain']['stage31_complete']:#010x}`
- Recovery dispatch: `{metadata['recovery_hook']['original_entry']:#010x}` -> `{metadata['recovery_hook']['dispatch']:#010x}`
- Allocator overlap: {metadata['allocation']['overlap_count']}
- Declared span外変更: {metadata['change_audit']['outside_declared_span_count']}
- Incremental/cumulative BPS exact: {metadata['release_patches']['incremental']['exact']} / {metadata['release_patches']['cumulative']['exact']}

## focused exact-ROM smoke

- completion/recovery physical binding: {checks['physical_binding']}
- ABI probe/save initialization: {checks['probe_and_save_init']}
- Factory Master/100 threshold gates: {checks['master_and_threshold_gates']}
- party delivery + forced shiny + Dex/ledger: {checks['party_shiny_atomic_commit']}
- once suppression + Stage30 coexistence: {checks['once_and_stage30_coexistence']}
- party full -> PC delivery: {checks['pc_delivery']}
- party/PC full -> no claim + retry: {checks['capacity_retry']}
- PREPARED/STAGED recovery: {checks['journal_recovery']}
- sector31 failure -> no consume + retry: {checks['sector_failure_retry']}
- normal save failure -> no consume + retry: {checks['standard_save_failure_retry']}
- normal acquisition recovery trampoline: {checks['normal_recovery_trampoline']}
- sector31 reload + exact party restore: {checks['sector31_reload_and_party_restore']}
- deterministic process runs: {mgba['process_runs']}

ユーザー指示どおりfresh全監査は再実行せず、Stage 31 builder、manifest/pool生成、allocator、変更span、BPS往復、libmGBA exact-ROM smokeに限定して検証した。
"""
    return text.encode("utf-8")


def _validate_mgba_result(mgba: dict[str, Any], stage: bytes) -> None:
    expected_checks = {
        "physical_binding",
        "probe_and_save_init",
        "master_and_threshold_gates",
        "party_shiny_atomic_commit",
        "once_and_stage30_coexistence",
        "pc_delivery",
        "capacity_retry",
        "journal_recovery",
        "sector_failure_retry",
        "standard_save_failure_retry",
        "normal_recovery_trampoline",
        "sector31_reload_and_party_restore",
    }
    checks = mgba.get("checks")
    if (
        mgba.get("schema_version") != 1
        or mgba.get("status") != "PASS"
        or mgba.get("process_runs") != 2
        or mgba.get("rom_sha256") != _sha(stage)
        or not isinstance(checks, dict)
        or set(checks) != expected_checks
        or not all(checks.values())
        or mgba.get("pool_count") != EXPECTED_POOL_COUNT
        or mgba.get("artifacts_written") != []
    ):
        _fail("Factory shiny memorial exact-ROM fixture contract differs")


def collect_outputs(
    root: Path = ROOT, *, run_exact: bool = True,
) -> dict[str, bytes]:
    outputs = build_runtime_outputs(root)
    repeated = build_runtime_outputs(root)
    if outputs != repeated:
        _fail("Factory shiny memorial runtime build is not byte deterministic")
    stage = outputs[OUTPUT_ROM.as_posix()]
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    if run_exact:
        mgba = _mgba_fixture(root, stage, metadata)
    else:
        fixture_path = Path(root) / MGBA_FIXTURE
        if not fixture_path.is_file():
            _fail("Factory shiny memorial exact-ROM fixture is missing; run build first")
        mgba = _read_json(fixture_path)
    _validate_mgba_result(mgba, stage)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(),
        "status": mgba["status"],
        "process_runs": mgba["process_runs"],
        "all_checks": all(mgba["checks"].values()),
    }
    metadata["invariants"]["exact_rom_process_runs_2"] = mgba["process_runs"] == 2
    metadata["invariants"]["exact_rom_all_checks"] = all(mgba["checks"].values())
    if not all(metadata["invariants"].values()):
        _fail("Factory shiny memorial exact-ROM invariant failed")
    outputs[OUTPUT_META.as_posix()] = _stable(metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


def _write_outputs(root: Path, outputs: dict[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: dict[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (root / relative).is_file() or (root / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Factory shiny memorial generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only"))
    args = parser.parse_args()
    try:
        if args.mode == "build-runtime-only":
            outputs = build_runtime_outputs(ROOT)
            _write_outputs(ROOT, outputs)
        else:
            outputs = collect_outputs(ROOT, run_exact=args.mode == "build")
            if args.mode == "build":
                _write_outputs(ROOT, outputs)
            else:
                _check_outputs(ROOT, outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError,
            FactoryShinyMemorialBuildError) as error:
        print(f"Factory shiny memorial runtime build failed: {error}",
              file=__import__("sys").stderr)
        return 1
    print(
        f"Factory shiny memorial runtime {args.mode}: PASS "
        f"stage={_sha(outputs[OUTPUT_ROM.as_posix()])} artifacts={len(outputs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
